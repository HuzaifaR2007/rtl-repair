import argparse
import json
import time
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig


DEFAULT_MODEL = "Qwen/Qwen2.5-Coder-7B-Instruct"


def load_jsonl(file_path: Path) -> list[dict]:
    records = []

    with file_path.open("r", encoding="utf-8") as f:
        for line_number, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line:
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Invalid JSON in {file_path} at line {line_number}: {e}"
                ) from e

    return records


def build_model_input(prompt: str, tokenizer) -> str:
    messages = [{"role": "user", "content": prompt}]

    if hasattr(tokenizer, "apply_chat_template"):
        return tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

    return prompt


def detect_compute_dtype() -> torch.dtype:
    if torch.cuda.is_available() and torch.cuda.is_bf16_supported():
        return torch.bfloat16
    return torch.float16


def generate_response(model, tokenizer, prompt_text: str, max_new_tokens: int) -> str:
    inputs = tokenizer(prompt_text, return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    input_length = inputs["input_ids"].shape[1]
    new_tokens = output_ids[0][input_length:]
    response = tokenizer.decode(new_tokens, skip_special_tokens=True)

    return response.strip()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run inference using a LoRA adapter on formatted eval prompts."
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help="Base Hugging Face model name.",
    )
    parser.add_argument(
        "--adapter",
        type=str,
        default="artifacts/qwen7b-rtl-lora-smoke",
        help="Path to saved LoRA adapter.",
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/formatted_eval.jsonl",
        help="Path to formatted eval JSONL file.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/lora_eval_outputs_350.jsonl",
        help="Path to save LoRA eval outputs.",
    )
    parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=350,
        help="Maximum new tokens to generate.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit on number of examples.",
    )
    parser.add_argument(
        "--use-4bit",
        action="store_true",
        help="Load the base model in 4-bit.",
    )

    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent.parent
    input_path = base_dir / args.input
    output_path = base_dir / args.output
    adapter_path = base_dir / args.adapter

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loading eval data from: {input_path}")
    examples = load_jsonl(input_path)

    if args.limit is not None:
        examples = examples[: args.limit]

    print(f"Loaded {len(examples)} eval example(s).")

    print(f"Loading tokenizer from adapter path: {adapter_path}")
    tokenizer = AutoTokenizer.from_pretrained(adapter_path, use_fast=True)

    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    compute_dtype = detect_compute_dtype()

    model_kwargs = {
        "device_map": "auto",
        "torch_dtype": compute_dtype,
    }

    if args.use_4bit:
        print("Using 4-bit quantized loading.")
        model_kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=compute_dtype,
        )

    print(f"Loading base model: {args.model}")
    base_model = AutoModelForCausalLM.from_pretrained(args.model, **model_kwargs)

    print(f"Loading LoRA adapter: {adapter_path}")
    model = PeftModel.from_pretrained(base_model, adapter_path)
    model.eval()

    print("Running LoRA inference...")
    results = []

    for i, example in enumerate(examples, start=1):
        print(f"  [{i}/{len(examples)}] Running {example['id']}...")

        prompt_text = build_model_input(example["prompt"], tokenizer)

        start_time = time.time()
        model_output = generate_response(
            model=model,
            tokenizer=tokenizer,
            prompt_text=prompt_text,
            max_new_tokens=args.max_new_tokens,
        )
        latency_seconds = time.time() - start_time

        result = {
            "id": example["id"],
            "bug_class": example["bug_class"],
            "base_model_name": args.model,
            "adapter_path": str(adapter_path),
            "prompt": example["prompt"],
            "gold_response": example["response"],
            "model_output": model_output,
            "latency_seconds": round(latency_seconds, 3),
        }

        results.append(result)

    with output_path.open("w", encoding="utf-8") as f:
        for record in results:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print("\nLoRA inference complete.")
    print(f"Saved {len(results)} result(s) to: {output_path}")


if __name__ == "__main__":
    main()