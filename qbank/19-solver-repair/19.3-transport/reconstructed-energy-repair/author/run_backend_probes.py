"""Build a private probe image from frozen verifier materials; record live PIDs."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import time
import uuid

Q = Path(__file__).resolve().parents[1]
ROOT = Q.parents[3]
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--docker', default='docker')
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--modes', default='extra,baseline-compiler,baseline-runtime,syntax,valid,runtime-timeout')
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    args.work = args.work.resolve()
    args.work.mkdir(parents=True, exist_ok=True)
    context = args.work / 'context'
    context.mkdir(exist_ok=True)
    shutil.copyfile(Q / 'author/backend_probe.py', context / 'backend_probe.py')
    config = json.loads((Q / 'harbor/source-repair.json').read_text())
    for row in config['replacements']:
        shutil.copyfile(Q / 'author/generated' / row['submission'], context / row['submission'])
    (context / 'Dockerfile').write_text('FROM caeoj-su22602-verifier:preflight\nCOPY . /probe\n')
    with (args.work / 'image-build.log').open('w') as stream:
        subprocess.run([args.docker, 'build', '-t', 'caeoj-su22602-probes:v1', str(context)],
                       stdout=stream, stderr=subprocess.STDOUT, check=True)
    if args.prepare_only:
        raise SystemExit()
    for mode in args.modes.split(','):
        if mode not in ['extra', 'baseline-compiler', 'baseline-runtime', 'syntax', 'valid', 'runtime-timeout']:
            raise ValueError(mode)
        directory = args.work / mode
        directory.mkdir(exist_ok=True)
        name = 'su22602-probe-' + mode + '-' + uuid.uuid4().hex[:8]
        command = [args.docker, 'run', '--name', name, '--rm', '--network', 'none',
                   '--cpus', '4', '--memory', '8g', '-v', str(directory) + ':/logs',
                   'caeoj-su22602-probes:v1', 'python', '/probe/backend_probe.py', mode]
        state = {'mode': mode, 'container_name': name, 'command': command, 'started_unix': time.time()}
        with (directory / 'stdout.json').open('w') as stdout, (directory / 'stderr.log').open('w') as stderr:
            proc = subprocess.Popen(command, text=True, stdout=stdout, stderr=stderr)
            state.update(status='running', host_cli_pid=proc.pid)
            (directory / 'run-state.json').write_text(json.dumps(state, indent=2))
            try:
                result = proc.wait(timeout=2300)
            except subprocess.TimeoutExpired:
                state.update(status='outer-timeout-container-status-required', elapsed_seconds=time.time()-state['started_unix'])
                (directory / 'run-state.json').write_text(json.dumps(state, indent=2))
                raise
        state.update(status='completed', exit_code=result, elapsed_seconds=time.time()-state['started_unix'])
        (directory / 'run-state.json').write_text(json.dumps(state, indent=2))
        print(json.dumps(state), flush=True)
        if result:
            raise RuntimeError((directory / 'stderr.log').read_text())
        assert json.loads((directory / 'stdout.json').read_text())['passed']
