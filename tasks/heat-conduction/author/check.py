"""Run a local program against the analytic suite; no Agent."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import uuid

from caeoj.grading import grade_files
from caeoj.sdk import load_problem, load_result
from caeoj.validation import ContractError, write_json

TASK_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = TASK_ROOT.parents[1]


def check(program, report_path, task_root=TASK_ROOT):
    task_root, program, report_path = Path(task_root).resolve(), Path(program).resolve(), Path(report_path).resolve()
    config = json.loads((task_root / "judge-config.json").read_text(encoding="utf-8"))
    paths = sorted((task_root / "cases").glob("*/problem.json"))
    if not paths:
        raise ValueError("No heat cases; run author/generate.py first")
    results = []
    root = report_path.parent / ("run-" + uuid.uuid4().hex[:12])
    for path in paths:
        directory = root / path.parent.name
        directory.mkdir(parents=True)
        output = directory / "result.npz"
        try:
            problem = load_problem(path)
        except ContractError as exc:
            results.append({"case": path.parent.name, "score": None, "status": "input_error", "contract": exc.report})
            continue
        reference = task_root / "reference" / path.parent.name / "reference.npz"
        try:
            load_result(problem, reference)
        except ContractError as exc:
            results.append({"case": path.parent.name, "score": None, "status": "reference_error", "contract": exc.report})
            continue
        try:
            execution = subprocess.run([sys.executable, str(program), "--input", str(path), "--output", str(output)],
                cwd=directory, capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=config["timeout_seconds"])
            (directory / "stdout.log").write_text(execution.stdout, encoding="utf-8")
            (directory / "stderr.log").write_text(execution.stderr, encoding="utf-8")
            if execution.returncode:
                grade = {"score": 0, "status": "runtime_error", "exit_code": execution.returncode}
            elif not output.is_file():
                grade = {"score": 0, "status": "missing_output"}
            else:
                grade = grade_files(path, output, reference,
                                    atol=config["atol"], rtol=config["rtol"])
        except subprocess.TimeoutExpired as exc:
            for name, data in (("stdout", exc.stdout), ("stderr", exc.stderr)):
                (directory / f"{name}.log").write_bytes(data or b"")
            grade = {"score": 0, "status": "timeout"}
        except OSError as exc:
            grade = {"score": None, "status": "runner_error", "message": str(exc)}
        results.append({"case": path.parent.name, "output": str(output), **grade})
    infrastructure_ok = all(item["score"] is not None for item in results)
    count = sum(item["score"] == 1 for item in results)
    report = {"task": "heat-conduction", "status": "graded" if infrastructure_ok else "runner_error",
              "score": count if infrastructure_ok else None, "passed_cases": count, "total_cases": len(results),
              "passed": infrastructure_ok and count == len(results),
              "tolerance": {"atol": config["atol"], "rtol": config["rtol"]}, "cases": results}
    write_json(report_path, report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--program", type=Path, default=Path(__file__).with_name("baseline.py"))
    parser.add_argument("--report", type=Path, default=PROJECT_ROOT / "runs/heat/report.json")
    args = parser.parse_args()
    report = check(args.program, args.report)
    print(json.dumps(report, indent=2))
    raise SystemExit(2 if report["score"] is None else 0 if report["passed"] else 1)
