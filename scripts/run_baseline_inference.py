import argparse
import json
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


DEFAULT_MODEL = "Qwen/Qwen2.5-Coder-7B-Instruct"


def load_jsonl(file_path: Path) -> list[dict]:
    """Load a JSONL file into a list of Python dictionaries."""
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
    """
    Build the final text sent to the model.

    If the tokenizer supports a chat template, use it.
    Otherwise, fall back to the raw prompt text.
    """
    if hasattr(tokenizer, "apply_chat_template"):
        messages = [
            {"role": "user", "content": prompt}
        ]
        return tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

    return prompt


def generate_response(
    model,
    tokenizer,
    prompt_text: str,
    max_new_tokens: int,
) -> str:
    """Generate a response from the model for one prompt."""
    inputs = tokenizer(prompt_text, return_tensors="pt")

    # Move tokenized inputs to the same device as the model
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=None,
            top_p=None,
            pad_token_id=tokenizer.pad_token_id,
        )

    input_length = inputs["input_ids"].shape[1]
    new_tokens = output_ids[0][input_length:]
    response = tokenizer.decode(new_tokens, skip_special_tokens=True)

    return response.strip()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run baseline inference on formatted eval prompts."
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help="Hugging Face model name or local model path.",
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
        default="results/baseline_eval_outputs.jsonl",
        help="Path to save generated outputs.",
    )
    parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=700,
        help="Maximum number of new tokens to generate per example.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit on number of eval examples to run.",
    )

    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent.parent
    input_path = base_dir / args.input
    output_path = base_dir / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loading eval data from: {input_path}")
    examples = load_jsonl(input_path)

    if args.limit is not None:
        examples = examples[: args.limit]

    print(f"Loaded {len(examples)} eval example(s).")

    print(f"Loading tokenizer for: {args.model}")
    tokenizer = AutoTokenizer.from_pretrained(args.model)

    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    print(f"Loading model for: {args.model}")
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        torch_dtype="auto",
        device_map="auto",
    )
    model.eval()

    print(f"Running baseline inference...")
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
            "model_name": args.model,
            "prompt": example["prompt"],
            "gold_response": example["response"],
            "model_output": model_output,
            "latency_seconds": round(latency_seconds, 3),
        }
        results.append(result)

    with output_path.open("w", encoding="utf-8") as f:
        for record in results:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print("\nBaseline inference complete.")
    print(f"Saved {len(results)} result(s) to: {output_path}")


if __name__ == "__main__":
    main()