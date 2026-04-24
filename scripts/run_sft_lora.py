import argparse
from pathlib import Path

import torch
from datasets import load_dataset
from peft import LoraConfig
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from trl import SFTConfig, SFTTrainer


DEFAULT_MODEL = "Qwen/Qwen2.5-Coder-7B-Instruct"


def detect_compute_dtype() -> torch.dtype:
    if torch.cuda.is_available() and torch.cuda.is_bf16_supported():
        return torch.bfloat16
    return torch.float16


def load_and_prepare_datasets(train_path: Path, eval_path: Path):
    dataset = load_dataset(
        "json",
        data_files={
            "train": str(train_path),
            "eval": str(eval_path),
        },
    )

    def to_prompt_completion(example: dict) -> dict:
        return {
            "prompt": example["prompt"],
            "completion": example["response"],
        }

    train_ds = dataset["train"].map(
        to_prompt_completion,
        remove_columns=dataset["train"].column_names,
    )
    eval_ds = dataset["eval"].map(
        to_prompt_completion,
        remove_columns=dataset["eval"].column_names,
    )

    return train_ds, eval_ds


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LoRA SFT on RTL repair data.")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--train-file", type=str, default="data/formatted_train.jsonl")
    parser.add_argument("--eval-file", type=str, default="data/formatted_eval.jsonl")
    parser.add_argument("--output-dir", type=str, default="artifacts/qwen7b-rtl-lora-smoke")
    parser.add_argument("--max-length", type=int, default=1024)
    parser.add_argument("--epochs", type=float, default=3.0)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--train-batch-size", type=int, default=1)
    parser.add_argument("--eval-batch-size", type=int, default=1)
    parser.add_argument("--grad-accum", type=int, default=4)
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument(
        "--use-4bit",
        action="store_true",
        help="Load the base model in 4-bit for local QLoRA-style training.",
    )
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent.parent
    train_path = base_dir / args.train_file
    eval_path = base_dir / args.eval_file
    output_dir = base_dir / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    compute_dtype = detect_compute_dtype()

    print("Loading datasets...")
    train_ds, eval_ds = load_and_prepare_datasets(train_path, eval_path)
    print(f"Train examples: {len(train_ds)}")
    print(f"Eval examples: {len(eval_ds)}")

    print(f"Loading tokenizer: {args.model}")
    tokenizer = AutoTokenizer.from_pretrained(args.model, use_fast=True)

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

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

    print(f"Loading model: {args.model}")
    model = AutoModelForCausalLM.from_pretrained(args.model, **model_kwargs)

    if hasattr(model.config, "use_cache"):
        model.config.use_cache = False

    peft_config = LoraConfig(
        task_type="CAUSAL_LM",
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        bias="none",
    )

    training_args = SFTConfig(
        output_dir=str(output_dir),
        num_train_epochs=args.epochs,
        learning_rate=args.learning_rate,
        per_device_train_batch_size=args.train_batch_size,
        per_device_eval_batch_size=args.eval_batch_size,
        gradient_accumulation_steps=args.grad_accum,
        logging_steps=1,
        save_strategy="epoch",
        eval_strategy="epoch",
        report_to="none",
        max_length=args.max_length,
        completion_only_loss=True,
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        processing_class=tokenizer,
        peft_config=peft_config,
    )

    print("Starting training...")
    trainer.train()

    print("Saving adapter + tokenizer...")
    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))

    print(f"Done. Saved artifacts to: {output_dir}")


if __name__ == "__main__":
    main()