"""Uniform candidate-facing contract checking and grading commands."""
import argparse
from importlib.metadata import PackageNotFoundError, version
import json

from .case_grading import grade_case
from .validation import ContractError, validate_input, validate_output


class UsageError(ValueError):
    """Command-line syntax error, emitted as structured JSON."""


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise UsageError(message)


def _version():
    try:
        return version('cae-bench-oj')
    except PackageNotFoundError:
        return 'uninstalled'


def main(argv=None):
    parser = Parser(prog='caeoj')
    parser.add_argument('--version', action='version', version=_version())
    commands = parser.add_subparsers(dest='command', required=True)
    input_parser = commands.add_parser('validate-input', help='Check input contract and assembled declarations')
    input_parser.add_argument('input')
    output_parser = commands.add_parser('validate-output', help='Check output contract, not answer accuracy')
    output_parser.add_argument('--input', required=True)
    output_parser.add_argument('--output', required=True)
    grade_parser = commands.add_parser('grade', help='Evaluate a complete submission using case grading.json')
    grade_parser.add_argument('--input', required=True)
    grade_parser.add_argument('--output', required=True)
    grade_parser.add_argument('--grading', required=True, help='Case reference/grading.json')
    info_parser = commands.add_parser('info', help='Describe installed tools and input contract support')
    info_parser.add_argument('--input', help='Input problem.json whose support should be inspected')
    try:
        args = parser.parse_args(argv)
        if args.command == 'validate-input':
            result = validate_input(args.input)
        elif args.command == 'validate-output':
            result = validate_output(args.input, args.output)
        elif args.command == 'info':
            from . import runtime
            result = runtime.bundle_info()
            if args.input:
                from .validation import read_json, schema_errors
                manifest = read_json(args.input)
                errors = schema_errors(manifest)
                if errors:
                    raise ContractError({'valid': False, 'errors': errors})
                result = runtime.describe(manifest)
            result = {'core_version': _version(), **result}
        else:
            result = grade_case(args.input, args.output, args.grading)
    except ContractError as exc:
        result = exc.report
    except (OSError, ValueError, RuntimeError, ImportError) as exc:
        print(json.dumps({'status': 'tool_error', 'error': type(exc).__name__,
                          'message': str(exc)}, indent=2, ensure_ascii=True))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False))
    if 'valid' in result:
        return 0 if result['valid'] else 1
    if 'score' in result:
        return 2 if result['score'] is None else 0 if result['score'] == 1 else 1
    return 0
