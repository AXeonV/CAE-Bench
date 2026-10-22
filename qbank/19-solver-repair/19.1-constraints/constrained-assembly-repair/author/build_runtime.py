"""Build a persistent, logged image of the actual defect-version Chrono core."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

TASK = Path(__file__).resolve().parents[1]
ROOT = TASK.parents[3]
DOCKER = Path('C:/Program Files/Docker/Docker/resources/bin/docker.exe')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    args = parser.parse_args()
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    context = work / 'context'
    context.mkdir(exist_ok=True)
    source = args.source.resolve()
    for name in ['src', 'cmake', 'template_project']:
        shutil.copytree(source / name, context / 'source' / name, dirs_exist_ok=True)
    for path in source.iterdir():
        if path.is_file() and path.name != 'CHANGELOG.md':
            shutil.copyfile(path, context / 'source' / path.name)
    # Runtime geometry/demos are outside the core API's dependency closure.
    (context / 'source/data').mkdir(exist_ok=True)
    (context / 'driver').mkdir(exist_ok=True)
    shutil.copyfile(TASK / 'public/driver.cpp', context / 'driver/driver.cpp')
    shutil.copyfile(TASK / 'public/CMakeLists.txt', context / 'driver/CMakeLists.txt')
    shutil.copyfile(TASK / 'author/runtime.Dockerfile', context / 'Dockerfile')
    command = [str(DOCKER), 'build', '--progress=plain', '-t', 'caeoj-chrono846-core:base', str(context)]
    status = {'pid': os.getpid(), 'started_unix': time.time(), 'command': command,
              'source': str(source), 'image': 'caeoj-chrono846-core:base', 'phase': 'building'}
    state = work / 'build-status.json'

    def save():
        temporary = state.with_suffix('.tmp')
        temporary.write_text(json.dumps(status, indent=2) + '\n', encoding='utf-8')
        temporary.replace(state)

    save()
    with (work / 'build.log').open('ab') as stream:
        process = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT)
        status['docker_pid'] = process.pid
        save()
        code = process.wait()
    status.update(returncode=code, finished_unix=time.time(), phase='built' if code == 0 else 'failed')
    if code == 0:
        info = subprocess.check_output([str(DOCKER), 'image', 'inspect', 'caeoj-chrono846-core:base'])
        status['image_id'] = json.loads(info)[0]['Id']
    status['log_sha256'] = hashlib.sha256((work / 'build.log').read_bytes()).hexdigest()
    save()
    raise SystemExit(code)


if __name__ == '__main__':
    main()
