import argparse
import csv
import shutil
import subprocess
from pathlib import Path


SIM_CASES = [
    {
        "name": "traffic_fsm",
        "bug_class": "fsm_bug",
        "rtl": "results/generated_rtl_v5/ex003_fsm_wrong_transition.sv",
        "tb": "testbenches/traffic_fsm_tb.sv",
    },
    {
        "name": "mod6_counter",
        "bug_class": "counter_width_boundary",
        "rtl": "results/generated_rtl_v5/ex025_counter_mod6_wrong_terminal.sv",
        "tb": "testbenches/mod6_counter_tb.sv",
    },
]


def run_command(command: list[str]) -> tuple[int, str, str]:
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run behavioral simulations for generated RTL repairs."
    )
    parser.add_argument(
        "--build-dir",
        type=str,
        default="results/sim_build",
        help="Directory for compiled simulation outputs.",
    )
    parser.add_argument(
        "--report",
        type=str,
        default="results/simulation_report_v5.csv",
        help="CSV report path.",
    )

    args = parser.parse_args()

    if shutil.which("iverilog") is None:
        raise RuntimeError("Could not find iverilog. Install Icarus Verilog or add it to PATH.")

    if shutil.which("vvp") is None:
        raise RuntimeError("Could not find vvp. Install Icarus Verilog or add it to PATH.")

    base_dir = Path(__file__).resolve().parent.parent
    build_dir = base_dir / args.build_dir
    report_path = base_dir / args.report

    build_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    report_rows = []

    print("=== Running RTL Behavioral Simulations ===\n")

    for case in SIM_CASES:
        name = case["name"]
        bug_class = case["bug_class"]
        rtl_path = base_dir / case["rtl"]
        tb_path = base_dir / case["tb"]
        sim_out = build_dir / f"{name}.out"

        print(f"Running {name}...")

        if not rtl_path.exists():
            print(f"  FAIL: Missing RTL file: {rtl_path}")
            report_rows.append(
                {
                    "name": name,
                    "bug_class": bug_class,
                    "rtl": case["rtl"],
                    "testbench": case["tb"],
                    "compile_pass": False,
                    "simulation_pass": False,
                    "stdout": "",
                    "stderr": f"Missing RTL file: {rtl_path}",
                }
            )
            continue

        if not tb_path.exists():
            print(f"  FAIL: Missing testbench file: {tb_path}")
            report_rows.append(
                {
                    "name": name,
                    "bug_class": bug_class,
                    "rtl": case["rtl"],
                    "testbench": case["tb"],
                    "compile_pass": False,
                    "simulation_pass": False,
                    "stdout": "",
                    "stderr": f"Missing testbench file: {tb_path}",
                }
            )
            continue

        compile_cmd = [
            "iverilog",
            "-g2012",
            "-o",
            str(sim_out),
            str(rtl_path),
            str(tb_path),
        ]

        compile_code, compile_stdout, compile_stderr = run_command(compile_cmd)
        compile_pass = compile_code == 0

        if not compile_pass:
            print("  FAIL: compile failed")
            report_rows.append(
                {
                    "name": name,
                    "bug_class": bug_class,
                    "rtl": case["rtl"],
                    "testbench": case["tb"],
                    "compile_pass": False,
                    "simulation_pass": False,
                    "stdout": compile_stdout,
                    "stderr": compile_stderr,
                }
            )
            continue

        sim_cmd = ["vvp", str(sim_out)]
        sim_code, sim_stdout, sim_stderr = run_command(sim_cmd)

        simulation_pass = sim_code == 0 and "ALL TESTS PASSED" in sim_stdout

        if simulation_pass:
            print("  PASS")
        else:
            print("  FAIL: simulation failed")

        report_rows.append(
            {
                "name": name,
                "bug_class": bug_class,
                "rtl": case["rtl"],
                "testbench": case["tb"],
                "compile_pass": compile_pass,
                "simulation_pass": simulation_pass,
                "stdout": sim_stdout,
                "stderr": sim_stderr,
            }
        )

    with report_path.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "name",
            "bug_class",
            "rtl",
            "testbench",
            "compile_pass",
            "simulation_pass",
            "stdout",
            "stderr",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(report_rows)

    total = len(report_rows)
    compile_passes = sum(row["compile_pass"] for row in report_rows)
    sim_passes = sum(row["simulation_pass"] for row in report_rows)

    print("\n=== Simulation Summary ===")
    print(f"Compile passed: {compile_passes}/{total}")
    print(f"Simulation passed: {sim_passes}/{total}")
    print(f"Report saved to: {report_path}")

    if sim_passes != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()