"""Repository maintenance CLI; excluded from candidate bundles."""
import argparse
import json
from pathlib import Path

from .author import PROJECT_ROOT, load_author_module
from .task_paths import task_directory


def main(argv=None):
    parser = argparse.ArgumentParser(prog='caeoj-maint')
    commands = parser.add_subparsers(dest='command', required=True)
    from .data_pool_cli import configure, run
    configure(commands.add_parser('data', help='Manage HF task pools and local assemblies'))
    make_parser = commands.add_parser('make-cases', help='Generate smoke-test author fixtures')
    make_parser.add_argument('--output')
    smoke_parser = commands.add_parser('smoke', help='Run the local smoke test; no Agent')
    smoke_parser.add_argument('--cases')
    smoke_parser.add_argument('--program')
    smoke_parser.add_argument('--report', default=str(PROJECT_ROOT / 'runs/smoke/report.json'))
    smoke_parser.add_argument('--timeout', type=float)
    args = parser.parse_args(argv)
    try:
        if args.command == 'data':
            result = run(args)
        elif args.command == 'make-cases':
            args.output = args.output or str(task_directory('smoke-test', PROJECT_ROOT) / 'cases')
            count = load_author_module('smoke-test', 'examples').make_cases(args.output)
            result = {'generated_cases': count, 'directory': str(Path(args.output).resolve())}
        else:
            task_dir = task_directory('smoke-test', PROJECT_ROOT)
            args.cases = args.cases or str(task_dir/'cases')
            args.program = args.program or str(task_dir/'solve.py')
            if (Path(args.cases).parent / 'data-manifest.json').is_file():
                from .data_pool import verify
                verify(Path(args.cases).parent)
            result = load_author_module('smoke-test', 'smoke').run_smoke(
                args.cases, args.program, args.report, args.timeout)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False))
    if 'passed' in result:
        return 0 if result['passed'] else 2 if result['status'] == 'runner_error' else 1
    if result.get('valid') is False:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
