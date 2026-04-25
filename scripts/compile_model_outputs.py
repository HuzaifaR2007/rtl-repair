import argparse
import csv
import json
import re
import shutil
import subprocess
from pathlib import Path


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


def extract_fixed_rtl(model_output: str) -> str:
    """
    Extract the RTL code from the model output.

    Expected model format:

    ### Fixed RTL
    <code>

    ### Bug Explanation
    <text>

    This function also removes markdown code fences if the model used them.
    """
    fixed_heading = "### Fixed RTL"
    explanation_heading = "### Bug Explanation"

    if fixed_heading not in model_output:
        raise ValueError("Missing '### Fixed RTL' section")

    start_index = model_output.index(fixed_heading) + len(fixed_heading)

    if explanation_heading in model_output:
        end_index = model_output.index(explanation_heading)
        rtl = model_output[start_index:end_index]
    else:
        rtl = model_output[start_index:]

    rtl = rtl.strip()

    # Remove markdown code fences like ```verilog ... ```
    rtl = re.sub(r"^```(?:systemverilog|verilog|sv)?\s*", "", rtl, flags=re.IGNORECASE)
    rtl = re.sub(r"\s*```$", "", rtl)

    return rtl.strip()


def safe_filename(name: str) -> str:
    """
    Convert an example id into a safe filename.
    """
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", name)


def compile_sv_file(sv_path: Path, output_binary_path: Path) -> tuple[bool, str, str]:
    """
    Compile one SystemVerilog file using Icarus Verilog.
    """
    command = [
        "iverilog",
        "-g2012",
        "-o",
        str(output_binary_path),
        str(sv_path),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    passed = result.returncode == 0
    return passed, result.stdout, result.stderr


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract and compile fixed RTL from model output JSONL files."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to model output JSONL file.",
    )
    parser.add_argument(
        "--rtl-dir",
        type=str,
        default="results/generated_rtl",
        help="Directory where extracted RTL files will be saved.",
    )
    parser.add_argument(
        "--build-dir",
        type=str,
        default="results/compile_build",
        help="Directory where compiled output files will be saved.",
    )
    parser.add_argument(
        "--report",
        type=str,
        default="results/compile_report.csv",
        help="Path to compile report CSV.",
    )

    args = parser.parse_args()

    if shutil.which("iverilog") is None:
        raise RuntimeError(
            "Could not find 'iverilog'. Install Icarus Verilog or add it to PATH."
        )

    base_dir = Path(__file__).resolve().parent.parent

    input_path = base_dir / args.input
    rtl_dir = base_dir / args.rtl_dir
    build_dir = base_dir / args.build_dir
    report_path = base_dir / args.report

    rtl_dir.mkdir(parents=True, exist_ok=True)
    build_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    records = load_jsonl(input_path)

    report_rows = []

    print(f"Loaded {len(records)} model output(s) from {input_path}")
    print("Extracting and compiling generated RTL...\n")

    for record in records:
        example_id = record["id"]
        bug_class = record.get("bug_class", "")

        filename_base = safe_filename(example_id)
        sv_path = rtl_dir / f"{filename_base}.sv"
        binary_path = build_dir / f"{filename_base}.out"

        try:
            rtl = extract_fixed_rtl(record["model_output"])
            sv_path.write_text(rtl + "\n", encoding="utf-8")

            passed, stdout, stderr = compile_sv_file(sv_path, binary_path)

            status = "PASS" if passed else "FAIL"
            print(f"{example_id}: {status}")

            report_rows.append(
                {
                    "id": example_id,
                    "bug_class": bug_class,
                    "sv_path": str(sv_path.relative_to(base_dir)),
                    "compile_pass": passed,
                    "stdout": stdout.strip(),
                    "stderr": stderr.strip(),
                }
            )

        except Exception as e:
            print(f"{example_id}: ERROR - {e}")

            report_rows.append(
                {
                    "id": example_id,
                    "bug_class": bug_class,
                    "sv_path": str(sv_path.relative_to(base_dir)),
                    "compile_pass": False,
                    "stdout": "",
                    "stderr": str(e),
                }
            )

    with report_path.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "id",
            "bug_class",
            "sv_path",
            "compile_pass",
            "stdout",
            "stderr",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(report_rows)

    pass_count = sum(1 for row in report_rows if row["compile_pass"])
    total_count = len(report_rows)

    print("\n=== Compile Summary ===")
    print(f"Passed: {pass_count}/{total_count}")
    print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    main()