"""Local smoke execution and aggregation; grading lives in grading.py."""
from pathlib import Path
import subprocess
import sys
import uuid

from .grading import grade_arrays
from .sdk import load_problem
from .validation import ContractError, output_support, read_hdf5, write_json

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run_smoke(cases, program, report_path, timeout=10):
    paths = sorted(Path(cases).glob("*/problem.json"))
    if not paths:
        raise ValueError("No smoke inputs found; run make-cases first.")
    program, report_path = Path(program).resolve(), Path(report_path).resolve()
    root = report_path.parent / ("run-" + uuid.uuid4().hex[:12])
    root.mkdir(parents=True)
    results = []
    for path in paths:
        directory = root / path.parent.name
        directory.mkdir()
        output = directory / "result.h5"
        try:
            problem = load_problem(path)
            if problem.manifest.get("task") != "echo-field" or problem.manifest["fields"] != problem.manifest["outputs"]:
                raise ContractError({"valid": False, "errors": [{"code": "E_ECHO", "path": "$",
                    "expected": "echo-field with identical input/output field declarations", "actual": "different",
                    "message": "Invalid echo task fixture; this rule belongs to the smoke runner."}]})
        except ContractError as exc:
            results.append({"case": path.parent.name, "status": "input_error", "score": None,
                            "contract": exc.report})
            continue
        reference_keys = output_support(problem) | {s["array"] for s in problem.manifest["outputs"].values()}
        reference = {key: problem.arrays[key] for key in reference_keys}
        try:
            execution = subprocess.run(
                [sys.executable, str(program), "--input", str(path.resolve()), "--output", str(output)],
                cwd=directory, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
            )
            (directory / "stdout.log").write_text(execution.stdout, encoding="utf-8")
            (directory / "stderr.log").write_text(execution.stderr, encoding="utf-8")
            if execution.returncode:
                grade = {"status": "runtime_error", "score": 0, "exit_code": execution.returncode}
            elif not output.is_file():
                grade = {"status": "missing_output", "score": 0}
            else:
                try:
                    grade = grade_arrays(problem, read_hdf5(output), reference)
                except ContractError as exc:
                    grade = {"status": "invalid_output", "score": 0, "contract": exc.report}
        except subprocess.TimeoutExpired:
            grade = {"status": "timeout", "score": 0}
        except OSError as exc:
            grade = {"status": "runner_error", "score": None, "message": str(exc)}
        results.append({"case": path.parent.name, **grade, "output": str(output)})
    infrastructure_ok = all(r["score"] is not None for r in results)
    passed = sum(r["score"] == 1 for r in results)
    report = {"task": "echo-field", "status": "graded" if infrastructure_ok else "runner_error",
              "passed_cases": passed, "total_cases": len(results),
              "score": passed if infrastructure_ok else None,
              "passed": infrastructure_ok and passed == len(results), "cases": results}
    write_json(report_path, report)
    return report
