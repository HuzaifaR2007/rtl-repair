import json
from pathlib import Path


def build_prompt(example: dict) -> str:
    """
    Build the model input prompt from one raw dataset example.
    """
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
        "- Keep the verification suggestion specific and practical.\n\n"
        "Return your answer using exactly this format:\n"
        "### Fixed RTL\n"
        "<corrected code>\n\n"
        "### Bug Explanation\n"
        "<short explanation>\n\n"
        "### Verification Suggestion\n"
        "<what to test next>\n\n"
        f"Design intent:\n{example['design_intent']}\n\n"
        f"Buggy RTL:\n{example['buggy_rtl']}"
    )


def build_response(example: dict) -> str:
    """
    Build the ideal target response from one raw dataset example.
    """
    return (
        f"### Fixed RTL\n{example['fixed_rtl']}\n\n"
        f"### Bug Explanation\n{example['explanation']}\n\n"
        f"### Verification Suggestion\n{example['verification_suggestion']}"
    )


def format_file(input_path: Path, output_path: Path) -> int:
    """
    Read a raw JSONL file and write a formatted JSONL file with:
    - id
    - bug_class (kept as metadata only)
    - prompt
    - response
    - text (prompt + response, useful for some trainers)

    Returns the number of formatted examples written.
    """
    count = 0

    with input_path.open("r", encoding="utf-8") as infile, output_path.open(
        "w", encoding="utf-8"
    ) as outfile:
        for line_number, raw_line in enumerate(infile, start=1):
            line = raw_line.strip()

            if not line:
                continue

            try:
                example = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Invalid JSON in {input_path} at line {line_number}: {e}"
                ) from e

            prompt = build_prompt(example)
            response = build_response(example)

            formatted_example = {
                "id": example["id"],
                "bug_class": example["bug_class"],  # metadata only
                "prompt": prompt,
                "response": response,
                "text": f"{prompt}\n\n{response}",
            }

            outfile.write(json.dumps(formatted_example, ensure_ascii=False) + "\n")
            count += 1

    return count


def main() -> None:
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"

    train_input = data_dir / "train.jsonl"
    eval_input = data_dir / "eval.jsonl"

    train_output = data_dir / "formatted_train.jsonl"
    eval_output = data_dir / "formatted_eval.jsonl"

    train_count = format_file(train_input, train_output)
    eval_count = format_file(eval_input, eval_output)

    print("Formatting complete.")
    print(f"Wrote {train_count} example(s) to {train_output}")
    print(f"Wrote {eval_count} example(s) to {eval_output}")


if __name__ == "__main__":
    main()