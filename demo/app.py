import argparse
import re
from pathlib import Path

import gradio as gr
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig


DEFAULT_MODEL = "Qwen/Qwen2.5-Coder-7B-Instruct"
DEFAULT_ADAPTER = "artifacts/qwen7b-rtl-lora-v5-demo-fix"


def detect_compute_dtype() -> torch.dtype:
    if torch.cuda.is_available() and torch.cuda.is_bf16_supported():
        return torch.bfloat16
    return torch.float16


def build_prompt(design_intent: str, buggy_rtl: str) -> str:
    return (
        "You are an RTL repair assistant specialized in Verilog/SystemVerilog.\n\n"
        "Task:\n"
        "Given the design intent and buggy RTL code, fix the bug, explain the issue, "
        "and suggest what to verify next.\n\n"
        "Rules:\n"
        "- Return only the three required sections.\n"
        "- Do not use markdown code fences.\n"
        "- Do not add extra commentary before or after the sections.\n"
        "- Keep the explanation concise and directly tied to the bug.\n"
        "- Keep the verification suggestion specific and practical.\n"
        "- If an input like tick is described as the advance, toggle, or step signal, "
        "do not change the transition to use !tick unless the design intent explicitly says so.\n\n"
        "- For always_ff sequential logic, do not explain the bug as a missing data-input sensitivity issue unless the design intent explicitly requires combinational behavior.\n"
        "- For modulo counters, explain off-by-one terminal-count bugs carefully: wrapping at N instead of N-1 usually means the counter includes one extra invalid state.\n"
        "Return your answer using exactly this format:\n"
        "### Fixed RTL\n"
        "<corrected code>\n\n"
        "### Bug Explanation\n"
        "<short explanation>\n\n"
        "### Verification Suggestion\n"
        "<what to test next>\n\n"
        f"Design intent:\n{design_intent.strip()}\n\n"
        f"Buggy RTL:\n{buggy_rtl.strip()}"
    )


def build_model_input(prompt: str, tokenizer) -> str:
    messages = [{"role": "user", "content": prompt}]

    if hasattr(tokenizer, "apply_chat_template"):
        return tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

    return prompt


def split_sections(output: str) -> tuple[str, str, str]:
    fixed = ""
    explanation = ""
    verification = ""

    fixed_match = re.search(
        r"### Fixed RTL\s*(.*?)(?=### Bug Explanation|$)",
        output,
        flags=re.DOTALL,
    )
    explanation_match = re.search(
        r"### Bug Explanation\s*(.*?)(?=### Verification Suggestion|$)",
        output,
        flags=re.DOTALL,
    )
    verification_match = re.search(
        r"### Verification Suggestion\s*(.*)",
        output,
        flags=re.DOTALL,
    )

    if fixed_match:
        fixed = fixed_match.group(1).strip()
    if explanation_match:
        explanation = explanation_match.group(1).strip()
    if verification_match:
        verification = verification_match.group(1).strip()

    fixed = re.sub(
        r"^```(?:systemverilog|verilog|sv)?\s*",
        "",
        fixed,
        flags=re.IGNORECASE,
    )
    fixed = re.sub(r"\s*```$", "", fixed).strip()

    return fixed, explanation, verification


class RTLRepairDemo:
    def __init__(self, model_name: str, adapter_path: str, use_4bit: bool):
        self.model_name = model_name
        self.adapter_path = adapter_path
        self.use_4bit = use_4bit

        self.tokenizer = None
        self.model = None

    def load(self) -> None:
        adapter_path = Path(self.adapter_path)

        print(f"Loading tokenizer from: {adapter_path}")
        self.tokenizer = AutoTokenizer.from_pretrained(adapter_path, use_fast=True)

        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        compute_dtype = detect_compute_dtype()

        model_kwargs = {
            "device_map": "auto",
            "torch_dtype": compute_dtype,
        }

        if self.use_4bit:
            print("Using 4-bit quantized loading.")
            model_kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
                bnb_4bit_compute_dtype=compute_dtype,
            )

        print(f"Loading base model: {self.model_name}")
        base_model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            **model_kwargs,
        )

        print(f"Loading LoRA adapter: {adapter_path}")
        self.model = PeftModel.from_pretrained(base_model, adapter_path)
        self.model.eval()

        print("Demo model loaded.")

    def repair(self, design_intent: str, buggy_rtl: str, max_new_tokens: int):
        if not design_intent.strip() or not buggy_rtl.strip():
            return "", "Please provide both design intent and buggy RTL.", ""

        prompt = build_prompt(design_intent, buggy_rtl)
        model_input = build_model_input(prompt, self.tokenizer)

        inputs = self.tokenizer(model_input, return_tensors="pt")
        inputs = {key: value.to(self.model.device) for key, value in inputs.items()}

        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        input_length = inputs["input_ids"].shape[1]
        new_tokens = output_ids[0][input_length:]
        output = self.tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

        fixed, explanation, verification = split_sections(output)

        return fixed, explanation, verification


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RTL Repair Gradio demo.")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--adapter", type=str, default=DEFAULT_ADAPTER)
    parser.add_argument("--use-4bit", action="store_true")
    parser.add_argument("--share", action="store_true")
    args = parser.parse_args()

    demo_model = RTLRepairDemo(
        model_name=args.model,
        adapter_path=args.adapter,
        use_4bit=args.use_4bit,
    )
    demo_model.load()

    example_intent = (
        "Two-state toggle FSM. Reset returns to S0. "
        "When tick is high, the FSM toggles between S0 and S1. "
        "When tick is low, it holds its current state."
    )

    example_rtl = """module toggle_fsm (
    input logic clk,
    input logic rst,
    input logic tick,
    output logic in_s0,
    output logic in_s1
);
    typedef enum logic {S0, S1} state_t;
    state_t state, next_state;

    always_ff @(posedge clk or posedge rst) begin
        if (rst)
            state <= S0;
        else
            state <= next_state;
    end

    always_comb begin
        next_state = state;
        case (state)
            S0: if (tick) next_state = S1;
            S1: if (tick) next_state = S1;
        endcase
    end

    assign in_s0 = (state == S0);
    assign in_s1 = (state == S1);
endmodule"""

    preset_examples = [
        [
            "Two-state toggle FSM. Reset returns to S0. When tick is high, the FSM toggles between S0 and S1. When tick is low, it holds its current state.",
            """module toggle_fsm (
    input logic clk,
    input logic rst,
    input logic tick,
    output logic in_s0,
    output logic in_s1
);
    typedef enum logic {S0, S1} state_t;
    state_t state, next_state;

    always_ff @(posedge clk or posedge rst) begin
        if (rst)
            state <= S0;
        else
            state <= next_state;
    end

    always_comb begin
        next_state = state;
        case (state)
            S0: if (tick) next_state = S1;
            S1: if (tick) next_state = S1;
        endcase
    end

    assign in_s0 = (state == S0);
    assign in_s1 = (state == S1);
endmodule""",
        ],
        [
            "2-to-4 combinational decoder with enable. When en is high, exactly one bit of y should be high based on sel. When en is low, y should be 0000.",
            """module decoder2to4 (
            input logic en,
            input logic [1:0] sel,
            output logic [3:0] y
);
            always_comb begin
                if (en) begin
                    case (sel)
                        2'b00: y = 4'b0001;
                        2'b01: y = 4'b0010;
                        2'b10: y = 4'b0100;
                        2'b11: y = 4'b1000;
                    endcase
                end
            end
        endmodule""",
        ],
        [
            "Modulo-6 counter that counts 0 through 5 when en is high, then wraps to 0. Reset clears the count to zero.",
            """module mod6_counter (
    input logic clk,
    input logic rst,
    input logic en,
    output logic [2:0] count
);
    always_ff @(posedge clk or posedge rst) begin
        if (rst)
            count <= 3'd0;
        else if (en) begin
            if (count == 3'd6)
                count <= 3'd0;
            else
                count <= count + 1'b1;
        end
    end
endmodule""",
        ],
    ]

    with gr.Blocks(title="RTL Repair") as app:
        gr.Markdown(
            "# RTL Repair\n"
            "Fine-tuned Verilog/SystemVerilog bug repair assistant.\n\n"
            "Paste a design intent and buggy RTL. The model returns fixed RTL, "
            "a concise bug explanation, and a verification suggestion."
        )

        with gr.Row():
            with gr.Column():
                design_intent = gr.Textbox(
                    label="Design Intent",
                    lines=5,
                    value=example_intent,
                )
                buggy_rtl = gr.Textbox(
                    label="Buggy RTL",
                    lines=22,
                    value=example_rtl,
                )

                gr.Examples(
                    examples=preset_examples,
                    inputs=[design_intent, buggy_rtl],
                    label="Preset Examples",
                )

                max_new_tokens = gr.Slider(
                    minimum=128,
                    maximum=700,
                    value=350,
                    step=32,
                    label="Max New Tokens",
                )

                repair_button = gr.Button("Repair RTL")

            with gr.Column():
                fixed_rtl = gr.Textbox(
                    label="Fixed RTL",
                    lines=22,
                )
                explanation = gr.Textbox(
                    label="Bug Explanation",
                    lines=6,
                )
                verification = gr.Textbox(
                    label="Verification Suggestion",
                    lines=6,
                )

        repair_button.click(
            fn=demo_model.repair,
            inputs=[design_intent, buggy_rtl, max_new_tokens],
            outputs=[fixed_rtl, explanation, verification],
        )

    app.launch(share=args.share)


if __name__ == "__main__":
    main()