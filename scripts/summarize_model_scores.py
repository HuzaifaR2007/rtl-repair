import argparse
import csv
from pathlib import Path


SCORE_COLUMNS = [
    "fix_correctness",
    "format_adherence",
    "explanation_quality",
    "verification_quality",
]

REQUIRED_COLUMNS = [
    "id",
    "bug_class",
    *SCORE_COLUMNS,
    "total_8",
]


def load_scores(csv_path: Path) -> list[dict]:
    """
    Load score rows from a CSV file.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Score file not found: {csv_path}")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        raise ValueError(f"No rows found in score file: {csv_path}")

    missing_columns = set(REQUIRED_COLUMNS) - set(reader.fieldnames or [])
    if missing_columns:
        raise ValueError(
            f"Missing required column(s): {sorted(missing_columns)}"
        )

    return rows


def safe_int(value: str, column_name: str, row_id: str) -> int:
    """
    Convert a CSV value to int with a useful error message.
    """
    try:
        return int(value)
    except ValueError as e:
        raise ValueError(
            f"Invalid integer in row '{row_id}', column '{column_name}': {value}"
        ) from e


def summarize_scores(rows: list[dict]) -> None:
    """
    Print score summary for a model score CSV.
    """
    total_examples = len(rows)
    total_score = 0
    max_score = total_examples * 8

    category_totals = {column: 0 for column in SCORE_COLUMNS}
    bug_class_totals: dict[str, dict[str, int]] = {}

    print("=== Per-Example Scores ===")

    for row in rows:
        row_id = row["id"]
        bug_class = row["bug_class"]

        row_scores = {
            column: safe_int(row[column], column, row_id)
            for column in SCORE_COLUMNS
        }

        total_8 = safe_int(row["total_8"], "total_8", row_id)

        expected_total = sum(row_scores.values())
        if total_8 != expected_total:
            print(
                f"WARNING: {row_id} total_8 is {total_8}, "
                f"but category sum is {expected_total}"
            )

        total_score += total_8

        for column, score in row_scores.items():
            category_totals[column] += score

        if bug_class not in bug_class_totals:
            bug_class_totals[bug_class] = {
                "score": 0,
                "max": 0,
                "count": 0,
            }

        bug_class_totals[bug_class]["score"] += total_8
        bug_class_totals[bug_class]["max"] += 8
        bug_class_totals[bug_class]["count"] += 1

        print(
            f"{row_id}: {total_8}/8 "
            f"(fix={row_scores['fix_correctness']}, "
            f"format={row_scores['format_adherence']}, "
            f"explanation={row_scores['explanation_quality']}, "
            f"verification={row_scores['verification_quality']})"
        )

    overall_percent = (total_score / max_score) * 100

    print("\n=== Overall Summary ===")
    print(f"Examples scored: {total_examples}")
    print(f"Total score: {total_score}/{max_score}")
    print(f"Overall percent: {overall_percent:.1f}%")
    print(f"Average per example: {total_score / total_examples:.2f}/8")

    print("\n=== Category Summary ===")
    for column in SCORE_COLUMNS:
        category_max = total_examples * 2
        category_score = category_totals[column]
        category_percent = (category_score / category_max) * 100

        readable_name = column.replace("_", " ")
        print(f"{readable_name}: {category_score}/{category_max} ({category_percent:.1f}%)")

    print("\n=== Bug-Class Summary ===")
    for bug_class, stats in sorted(bug_class_totals.items()):
        percent = (stats["score"] / stats["max"]) * 100
        print(
            f"{bug_class}: {stats['score']}/{stats['max']} "
            f"({percent:.1f}%) across {stats['count']} example(s)"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarize RTL repair model scoring CSV files."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to score CSV file, for example results/lora_v3_scores_350.csv",
    )

    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent.parent
    input_path = base_dir / args.input

    rows = load_scores(input_path)

    print(f"Loaded score file: {input_path}")
    print()
    summarize_scores(rows)


if __name__ == "__main__":
    main()