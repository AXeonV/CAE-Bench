"""Check fresh candidate and separate offline verifier environments per task."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import threading
import time
import zipfile


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    envroot = Path(__file__).resolve().parent
    release = envroot.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', action='append')
    parser.add_argument('--jobs', type=int, default=2)
    parser.add_argument('--output', type=Path, default=release.parent/(release.name+'-environment-checks'))
    args = parser.parse_args()
    assert args.jobs > 0
    config = json.loads((envroot/'runtime.json').read_text(encoding='utf-8'))
    catalog = json.loads((release/'catalog.json').read_text(encoding='utf-8'))
    tasks = [t for t in catalog['tasks'] if not args.task or t['task'] in args.task]
    assert tasks and (not args.task or {t['task'] for t in tasks} == set(args.task))
    output = args.output.resolve()
    assert not output.is_relative_to(release.resolve()), 'Validation output must be outside the immutable release'
    output.mkdir(parents=True, exist_ok=True)
    image = json.loads(subprocess.check_output(['docker', 'image', 'inspect', config['image']], text=True))[0]
    result = {'phase': 'running', 'started_unix': time.time(), 'image': config['image'],
              'image_id': image['Id'], 'expected_tasks': len(tasks), 'expected_containers': 2*len(tasks),
              'new_model_calls': 0, 'score_corrections': 0, 'tasks': []}
    lock = threading.Lock()

    def save():
        data = json.dumps(result, ensure_ascii=False, indent=2)
        path = output/'validation.json'
        temporary = path.with_suffix('.tmp')
        temporary.write_text(data, encoding='utf-8')
        for attempt in range(100):
            try:
                temporary.replace(path)
                break
            except PermissionError:
                if attempt == 99:
                    raise
                time.sleep(.05)

    def check_task(task):
        slug = task['task']
        context = output/'contexts'/slug
        context.mkdir(parents=True, exist_ok=True)
        archive = release/task['public_archive']
        shutil.copyfile(archive, context/'agent.zip')
        with zipfile.ZipFile(release/'qbank.zip') as bank:
            key = task['path']+'/harbor/requirements.txt'
            requirements = bank.read(key) if key in bank.namelist() else b''
        (context/'requirements.txt').write_bytes(requirements)
        record = {'task': slug, 'public_archive_sha256': digest(archive),
                  'task_requirements_sha256': hashlib.sha256(requirements).hexdigest(), 'roles': []}
        for role in ('candidate', 'verifier'):
            cidfile = output/(slug+'-'+role+'.cid')
            assert not cidfile.exists(), 'Existing container checkpoint requires inspection before rerun'
            command = ['docker', 'run', '--rm', '--platform', config['platform'], '--network', 'none',
                       '--cpus', '2', '--memory', '2g', '--cidfile', str(cidfile),
                       '--mount', f'type=bind,source={context},target=/material,readonly',
                       config['image'], 'python', '/opt/caeoj/install_and_check.py', slug]
            started = time.monotonic()
            execution = subprocess.run(command, text=True, encoding='utf-8', errors='replace',
                                       capture_output=True, timeout=300)
            (output/(slug+'-'+role+'.stdout.log')).write_text(execution.stdout, encoding='utf-8')
            (output/(slug+'-'+role+'.stderr.log')).write_text(execution.stderr, encoding='utf-8')
            assert execution.returncode == 0, f'{slug}/{role}: '+execution.stderr[-2000:]
            report = json.loads(execution.stdout.strip().splitlines()[-1])
            assert report['task'] == slug and report['offline_install'] and report['pip_check']
            assert report['environment']['status'] == 'passed'
            record['roles'].append({'role': role, 'network': 'none', 'fresh_container': True,
                                    'container_id': cidfile.read_text().strip(),
                                    'seconds': time.monotonic()-started, 'report': report})
        assert record['roles'][0]['container_id'] != record['roles'][1]['container_id']
        with lock:
            result['tasks'].append(record)
            save()
        print(slug+': independent fresh candidate and offline verifier passed', flush=True)

    save()
    try:
        with ThreadPoolExecutor(max_workers=args.jobs) as executor:
            for future in as_completed([executor.submit(check_task, task) for task in tasks]):
                future.result()
        assert len(result['tasks']) == len(tasks)
        result.update(phase='passed', completed_unix=time.time())
        save()
    except BaseException as exc:
        result.update(phase='failed', error=repr(exc), completed_unix=time.time())
        save()
        raise


if __name__ == '__main__':
    main()
