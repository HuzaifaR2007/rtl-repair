import subprocess
import sys
from pathlib import Path


def run_step(name: str, command: list[str]) -> bool:
    print("\n" + "=" * 80)
    print(f"Running: {name}")
    print("=" * 80)

    result = subprocess.run(command, text=True)

    if result.returncode == 0:
        print(f"\nPASS: {name}")
        return True

    print(f"\nFAIL: {name}")
    return False


def main() -> None:
    base_dir = Path(__file__).resolve().parent.parent
    python = sys.executable

    checks = []

    checks.append(
        (
            "Dataset validation",
            [python, "scripts/validate_dataset.py"],
        )
    )

    checks.append(
        (
            "Format training data",
            [python, "scripts/format_training_data.py"],
        )
    )

    if (base_dir / "results/lora_v3_scores_350.csv").exists():
        checks.append(
            (
                "Summarize Local V3 scores",
                [
                    python,
                    "scripts/summarize_model_scores.py",
                    "--input",
                    "results/lora_v3_scores_350.csv",
                ],
            )
        )

    if (base_dir / "results/lora_amd_v1_scores_350.csv").exists():
        checks.append(
            (
                "Summarize AMD V1 scores",
                [
                    python,
                    "scripts/summarize_model_scores.py",
                    "--input",
                    "results/lora_amd_v1_scores_350.csv",
                ],
            )
        )

    if (base_dir / "results/lora_v5_eval_outputs_350.jsonl").exists():
        checks.append(
            (
                "Compile V5 generated RTL",
                [
                    python,
                    "scripts/compile_model_outputs.py",
                    "--input",
                    "results/lora_v5_eval_outputs_350.jsonl",
                    "--rtl-dir",
                    "results/generated_rtl_v5",
                    "--build-dir",
                    "results/compile_build_v5",
                    "--report",
                    "results/lora_v5_compile_report.csv",
                ],
            )
        )
    else:
        print(
            "Skipping V5 compile check because "
            "results/lora_v5_eval_outputs_350.jsonl was not found."
        )

    checks.append(
        (
            "Run behavioral simulation regression",
            [python, "scripts/run_simulation_checks.py"],
        )
    )

    passed = 0

    for name, command in checks:
        if run_step(name, command):
            passed += 1

    total = len(checks)

    print("\n" + "=" * 80)
    print("Project Check Summary")
    print("=" * 80)
    print(f"Passed: {passed}/{total}")

    if passed != total:
        raise SystemExit(1)

    print("All project checks passed.")


if __name__ == "__main__":
    main()