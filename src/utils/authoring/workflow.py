"""Resume authoring preparation, structure checks and review-only packaging.

No solver, participant agent, numerical grader or full-data download is invoked.
Agent dispatch belongs to the Codex coordinator; durable role tickets record it.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import os

ROOT = Path(__file__).resolve().parents[3]
STATE = ROOT / 'docs/authoring/state.json'


def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write('\n')
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def run(command, log):
    process = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    log.append({'command': command, 'returncode': process.returncode,
                'stdout': process.stdout, 'stderr': process.stderr})
    if process.returncode:
        raise RuntimeError(f'Command failed: {command}; {process.stderr}')


def check(task, log):
    base = ROOT / 'tasks' / task
    inputs = sorted((base / 'cases').glob('*/problem.json'))
    samples = sorted((base / 'samples').glob('*/input/problem.json'))
    if not inputs or not samples:
        raise RuntimeError('Need at least one source case and one complete public sample')
    run([sys.executable, '.agents/skills/caeoj-audit-data/scripts/inventory.py',
         '--task', f'tasks/{task}', '--output', f'runs/data-audit/{task}/inventory.json'], log)
    for path in inputs + samples:
        run([sys.executable, '-m', 'caeoj', 'validate-input', str(path)], log)
        reference = (base / 'reference' / path.parent.name / 'reference.npz'
                     if path in inputs else path.parent.parent / 'output/result.npz')
        if not reference.exists():
            raise RuntimeError(f'Source case lacks paired reference: {path}')
        run([sys.executable, '-m', 'caeoj', 'validate-output', '--input', str(path),
             '--output', str(reference)], log)
    pending_inputs = sorted((base / 'author/pending').glob('*/problem.json'))
    for path in pending_inputs:
        run([sys.executable, '-m', 'caeoj', 'validate-input', str(path)], log)
        status = json.loads((path.parent / 'status.json').read_text(encoding='utf-8'))
        if status.get('status') != 'pending_reference' or (path.parent / 'reference.npz').exists():
            raise RuntimeError(f'Pending input has inconsistent reference status: {path}')
    return len(inputs), len(samples), len(pending_inputs)


def review_package(task, log):
    run([sys.executable, 'src/utils/publish_dist.py', '--task', task, '--draft'], log)
    import zipfile
    archive = ROOT / 'dist' / f'{task}-draft.zip'
    with zipfile.ZipFile(archive) as bundle:
        manifest = json.loads(bundle.read('MANIFEST.json'))
        if manifest.get('draft') is not True:
            raise RuntimeError('Review artifact lacks draft marker')
        for name in bundle.namelist():
            parts = Path(name).parts
            if {'author', 'reference', 'cases', 'pending', 'harbor'} & set(parts):
                raise RuntimeError(f'Private material found: {name}')
        for name, expected in manifest['files'].items():
            if hashlib.sha256(bundle.read(name)).hexdigest() != expected:
                raise RuntimeError(f'Public manifest mismatch: {name}')
    return {'path': str(archive.relative_to(ROOT)), 'bytes': archive.stat().st_size,
            'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
            'file_count': len(manifest['files']) + 1,
            'separation_check': 'passed_allowlist_and_manifest_hashes'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['status', 'prepare', 'check', 'package'])
    parser.add_argument('--task', help='Registered task; omit to process all pilot candidates')
    args = parser.parse_args(argv)
    state = json.loads(STATE.read_text(encoding='utf-8'))
    if args.action == 'status':
        print(json.dumps(state, indent=2, ensure_ascii=False)); return 0
    candidates = [x for x in state['candidates'] if not args.task or x['task'] == args.task]
    if not candidates:
        parser.error('Unknown task')
    failures = 0
    for candidate in candidates:
        task = candidate['task']
        log = []
        try:
            if args.action == 'prepare':
                run([sys.executable, f'tasks/{task}/author/prepare.py', '--mode', 'sample'], log)
            if args.action in ('prepare', 'check', 'package'):
                count, sample_count, pending_count = check(task, log)
                candidate['checks']['structure'] = {'status': 'passed', 'cases': count,
                    'samples': sample_count, 'pending_inputs': pending_count,
                    'scope': 'format and references only, not numerical accuracy'}
            if args.action == 'package':
                candidate['artifact'] = review_package(task, log)
            candidate['last_action'] = {'action': args.action, 'status': 'completed'}
        except Exception as exc:
            failures += 1
            candidate['last_action'] = {'action': args.action, 'status': 'failed', 'error': str(exc)}
        finally:
            atomic_json(ROOT / f'runs/authoring/{task}/{args.action}.json', log)
            atomic_json(STATE, state)
    print(json.dumps({'action': args.action, 'failures': failures}, indent=2))
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
