import csv
from pathlib import Path

CATEGORY_NAMES = [
    "fix_correctness",
    "format_adherence",
    "explanation_quality",
    "verification_quality",
]

def main() -> None:
    base_dir = Path(__file__).resolve().parent.parent
    score_file = base_dir / "results" / "baseline_scores_350.csv"

    rows = []
    with score_file.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    if not rows:
        print("No rows found in score file.")
        return

    total_examples = len(rows)
    total_score = 0
    category_totals = {name: 0 for name in CATEGORY_NAMES}

    print("=== Per-Example Scores ===")
    for row in rows:
        total_score += int(row["total_8"])
        for name in CATEGORY_NAMES:
            category_totals[name] += int(row[name])

        print(
            f"{row['id']}: {row['total_8']}/8 "
            f"(fix={row['fix_correctness']}, "
            f"format={row['format_adherence']}, "
            f"explanation={row['explanation_quality']}, "
            f"verification={row['verification_quality']})"
        )

    max_total = total_examples * 8
    percent = (total_score / max_total) * 100

    print("\n=== Overall Summary ===")
    print(f"Examples scored: {total_examples}")
    print(f"Total score: {total_score}/{max_total}")
    print(f"Overall percent: {percent:.1f}%")
    print(f"Average per example: {total_score / total_examples:.2f}/8")

    print("\n=== Category Summary ===")
    for name in CATEGORY_NAMES:
        category_max = total_examples * 2
        category_percent = (category_totals[name] / category_max) * 100
        print(
            f"{name}: {category_totals[name]}/{category_max} "
            f"({category_percent:.1f}%)"
        )

if __name__ == "__main__":
    main()