import json
from pathlib import Path

REQUIRED_FIELDS = {
    "id",
    "design_intent",
    "bug_class",
    "buggy_rtl",
    "fixed_rtl",
    "explanation",
    "verification_suggestion",
}

ALLOWED_BUG_CLASSES = {
    "blocking_vs_nonblocking",
    "reset_logic",
    "fsm_bug",
    "counter_width_boundary",
    "incomplete_combinational_logic",
}


def validate_jsonl_file(file_path: Path, seen_ids: set[str]) -> tuple[int, int]:
    """
    Validate one JSONL dataset file.

    Returns:
        (valid_count, error_count)
    """
    valid_count = 0
    error_count = 0

    print(f"\nChecking {file_path}...")

    if not file_path.exists():
        print(f"  ERROR: File does not exist: {file_path}")
        return 0, 1

    with file_path.open("r", encoding="utf-8") as f:
        for line_number, raw_line in enumerate(f, start=1):
            line = raw_line.strip()

            # Ignore blank lines, but warn because JSONL usually should not have them
            if not line:
                print(f"  WARNING: Blank line at line {line_number}")
                continue

            # Step 1: parse JSON
            try:
                example = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"  ERROR line {line_number}: Invalid JSON -> {e}")
                error_count += 1
                continue

            # Step 2: ensure it's a dictionary/object
            if not isinstance(example, dict):
                print(f"  ERROR line {line_number}: JSON entry must be an object")
                error_count += 1
                continue

            # Step 3: check required fields
            missing_fields = REQUIRED_FIELDS - example.keys()
            if missing_fields:
                print(
                    f"  ERROR line {line_number}: Missing required field(s): "
                    f"{sorted(missing_fields)}"
                )
                error_count += 1
                continue

            # Step 4: check required fields are non-empty strings
            bad_fields = []
            for field in REQUIRED_FIELDS:
                value = example[field]

                if not isinstance(value, str):
                    bad_fields.append(f"{field} (must be a string)")
                    continue

                if value.strip() == "":
                    bad_fields.append(f"{field} (empty string)")

            if bad_fields:
                print(
                    f"  ERROR line {line_number}: Invalid field values: {bad_fields}"
                )
                error_count += 1
                continue

            # Step 5: validate bug_class
            if example["bug_class"] not in ALLOWED_BUG_CLASSES:
                print(
                    f"  ERROR line {line_number}: Invalid bug_class "
                    f"'{example['bug_class']}'"
                )
                error_count += 1
                continue

            # Step 6: check duplicate ids across all files
            example_id = example["id"]
            if example_id in seen_ids:
                print(f"  ERROR line {line_number}: Duplicate id '{example_id}'")
                error_count += 1
                continue

            seen_ids.add(example_id)
            valid_count += 1

    print(f"  Done: {valid_count} valid, {error_count} error(s)")
    return valid_count, error_count


def main() -> None:
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"

    files_to_check = [
        data_dir / "train.jsonl",
        data_dir / "eval.jsonl",
    ]

    total_valid = 0
    total_errors = 0
    seen_ids: set[str] = set()

    for file_path in files_to_check:
        valid_count, error_count = validate_jsonl_file(file_path, seen_ids)
        total_valid += valid_count
        total_errors += error_count

    print("\n=== Validation Summary ===")
    print(f"Valid examples: {total_valid}")
    print(f"Errors: {total_errors}")

    if total_errors == 0:
        print("Dataset validation PASSED")
    else:
        print("Dataset validation FAILED")


if __name__ == "__main__":
    main()