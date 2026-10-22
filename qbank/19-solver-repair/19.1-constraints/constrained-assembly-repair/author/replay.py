"""Run real pinned Chrono binaries with resource limits and preserve provenance."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import time
import numpy as np
from caeoj.sdk import load_problem, write_result
from caeoj.case_grading import grade_case
from caeoj_tools.grading_policy import author_policy, write_direct_grading

TASK = Path(__file__).resolve().parents[1]
DOCKER = 'C:/Program Files/Docker/Docker/resources/bin/docker.exe'
spec = importlib.util.spec_from_file_location('assembly_adapter', TASK / 'public/run_case.py')
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--image', required=True)
    parser.add_argument('--mode', choices=['reference', 'defect'], required=True)
    args = parser.parse_args()
    policy = author_policy(TASK)
    image = json.loads(subprocess.check_output([DOCKER, 'image', 'inspect', args.image]))[0]['Id']
    report = {'mode': args.mode, 'image': args.image, 'image_id': image, 'cases': []}
    for path in sorted((args.dataset / 'cases').glob('*/problem.json')):
        problem = load_problem(path)
        directory = args.dataset / 'replay' / args.mode / path.parent.name
        directory.mkdir(parents=True, exist_ok=True)
        text = adapter.serialize(problem)
        (directory / 'driver-input.txt').write_text(text, encoding='utf-8')
        command = [DOCKER, 'run', '--rm', '--network', 'none', '--cpus', '4', '--memory', '8g',
                   '--user', '1000:1000', '-i', args.image, '/opt/driver-build/assembly-driver']
        started = time.monotonic()
        execution = subprocess.run(command, input=text, capture_output=True, text=True, timeout=30)
        elapsed = time.monotonic() - started
        (directory / 'stdout.json').write_text(execution.stdout, encoding='utf-8')
        (directory / 'stderr.log').write_text(execution.stderr, encoding='utf-8')
        if execution.returncode:
            raise RuntimeError(f'{path.parent.name}: ' + execution.stderr)
        result = json.loads(execution.stdout)
        values = {name: np.asarray(result[name], dtype='float64')[None, :, :] for name in problem.manifest['outputs']}
        target = args.dataset / 'reference' / path.parent.name if args.mode == 'reference' else directory
        target.mkdir(parents=True, exist_ok=True)
        output = target / ('reference.h5' if args.mode == 'reference' else 'result.h5')
        write_result(output, problem, values)
        exact = json.loads((args.dataset / 'independent-checks' / (path.parent.name + '.json')).read_text())
        checks = {}
        for name, value in values.items():
            expected = np.asarray(exact[name], dtype='float64')[None, :, :]
            max_error = float(np.max(np.abs(value - expected)))
            atol = .01 if name == 'acceleration' else .05 if name == 'reaction' else 1e-8
            rtol = .0005 if name in ('acceleration', 'reaction') else 1e-8
            normalized = np.abs(value - expected) / (atol + rtol * np.abs(expected))
            checks[name] = {'max_absolute_error': max_error, 'max_tolerance_fraction': float(np.max(normalized)),
                            'passed': bool(np.all(normalized <= 1))}
        if args.mode == 'reference':
            if not all(row['passed'] for row in checks.values()):
                raise RuntimeError(f'Independent mechanics check failed: {path.parent.name}: {checks}')
            write_direct_grading(target, policy)
            graded = grade_case(path, output, target / 'grading.json')
        else:
            graded = grade_case(path, output, args.dataset / 'reference' / path.parent.name / 'grading.json')
        row = {'case': path.parent.name, 'command': command, 'elapsed_seconds': elapsed,
               'input_sha256': hashlib.sha256(text.encode()).hexdigest(), 'checks': checks,
               'score': graded['score'], 'output_sha256': hashlib.sha256(output.read_bytes()).hexdigest()}
        report['cases'].append(row)
        (args.dataset / f'{args.mode}-report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'case': row['case'], 'mode': args.mode, 'score': row['score'], 'checks': checks}), flush=True)


if __name__ == '__main__':
    main()
