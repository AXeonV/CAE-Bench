"""Local contract-checking CLI and smoke entry points."""
import argparse
from importlib.util import find_spec
import json
from pathlib import Path

from .grading import DEFAULT_ATOL, DEFAULT_RTOL, grade_files
from .validation import ContractError, validate_input, validate_output


def main(argv=None):
    parser = argparse.ArgumentParser(prog="caeoj")
    commands = parser.add_subparsers(dest="command", required=True)
    input_parser = commands.add_parser("validate-input", help="Check input fields and declared structure only")
    input_parser.add_argument("input")
    output_parser = commands.add_parser("validate-output", help="Check output contract, not answer accuracy")
    output_parser.add_argument("--input", required=True)
    output_parser.add_argument("--output", required=True)
    grade_parser = commands.add_parser("grade", help="Grade result arrays against a supplied reference NPZ")
    grade_parser.add_argument("--input", required=True)
    grade_parser.add_argument("--output", required=True)
    grade_parser.add_argument("--reference", required=True)
    grade_parser.add_argument("--atol", type=float, default=DEFAULT_ATOL)
    grade_parser.add_argument("--rtol", type=float, default=DEFAULT_RTOL)
    # Author-only modules are omitted from the public release.
    if all(find_spec(f"{__package__}.{name}") is not None for name in ("examples", "smoke")):
        project_root = Path(__file__).resolve().parents[2]
        make_parser = commands.add_parser("make-cases", help="Write local echo examples")
        make_parser.add_argument("--output", default=str(project_root / "tasks/echo-field/cases"))
        smoke_parser = commands.add_parser("smoke", help="Run a local echo program; no Agent")
        smoke_parser.add_argument("--cases", default=str(project_root / "tasks/echo-field/cases"))
        smoke_parser.add_argument("--program", default=str(project_root / "tasks/echo-field/solve.py"))
        smoke_parser.add_argument("--report", default=str(project_root / "runs/smoke/report.json"))
        smoke_parser.add_argument("--timeout", type=float, default=10)
    args = parser.parse_args(argv)
    try:
        if args.command == "validate-input":
            result = validate_input(args.input)
        elif args.command == "validate-output":
            result = validate_output(args.input, args.output)
        elif args.command == "make-cases":
            from .examples import make_cases
            count = make_cases(args.output)
            result = {"generated_cases": count, "directory": str(Path(args.output).resolve())}
        elif args.command == "grade":
            result = grade_files(args.input, args.output, args.reference, atol=args.atol, rtol=args.rtol)
        else:
            from .smoke import run_smoke
            if args.timeout <= 0:
                parser.error("--timeout must be positive")
            result = run_smoke(args.cases, args.program, args.report, args.timeout)
    except ContractError as exc:
        result = exc.report
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False))
    if "valid" in result:
        return 0 if result["valid"] else 1
    if "passed" in result:
        return 0 if result["passed"] else 2 if result["status"] == "runner_error" else 1
    if "score" in result:
        return 2 if result["score"] is None else 0 if result["score"] == 1 else 1
    return 0
