"""Execute controlled failure/isolation probes in fresh resource-limited containers."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import time

TASK = Path(__file__).resolve().parents[1]
DOCKER = 'C:/Program Files/Docker/Docker/resources/bin/docker.exe'
MODES = ['valid', 'syntax', 'baseline', 'compiler', 'extra', 'symlink', 'compile-timeout', 'runtime-timeout', 'generic']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--image', default='caeoj-chrono846-verifier:preflight')
    parser.add_argument('--modes', nargs='+', choices=MODES, default=MODES)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    probe = output/'probe'
    probe.mkdir(exist_ok=True)
    shutil.copyfile(TASK/'author/backend_probe.py', probe/'backend_probe.py')
    shutil.copyfile(TASK/'author/generated/ChAssemblyAnalysis.cpp', probe/'ChAssemblyAnalysis.cpp')
    results = []
    for mode in args.modes:
        command = [DOCKER, 'run', '--rm', '--network', 'none', '--cpus', '4', '--memory', '8g',
                   '--mount', f'type=bind,source={probe},target=/probe,readonly',
                   args.image, 'python', '/probe/backend_probe.py', mode]
        started = time.monotonic()
        run = subprocess.run(command, capture_output=True, text=True, timeout=120)
        (output/(mode+'-stdout.log')).write_text(run.stdout, encoding='utf-8')
        (output/(mode+'-stderr.log')).write_text(run.stderr, encoding='utf-8')
        if run.returncode:
            raise RuntimeError(f'{mode}: {run.stderr[-2500:]}')
        result = json.loads(run.stdout)
        assert result['mode'] == mode and result['passed']
        result.update(command=command, elapsed_seconds=time.monotonic()-started)
        results.append(result)
        (output/'report.json').write_text(json.dumps({'passed': len(results), 'expected': len(args.modes),
                            'results': results}, indent=2)+'\n', encoding='utf-8')
        print(json.dumps({'mode': mode, 'passed': True}), flush=True)


if __name__ == '__main__':
    main()
