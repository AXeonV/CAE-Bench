"""Assemble a temporary Harbor task under runs/ from a published public ZIP."""
import argparse
import json
from pathlib import Path
import re
import shutil
import tempfile

from publish_dist import PROJECT_ROOT, read_public_file
from caeoj.sdk import load_problem, load_result


def prepare(task, root=PROJECT_ROOT):
    root = Path(root).resolve()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', task):
        raise ValueError('Task must be a directory name')
    source = root / 'tasks' / task
    template = source / 'harbor'
    if not (template / 'task.toml').is_file():
        raise ValueError(f'No Harbor adapter for {task}')
    cases = sorted((source / 'cases').glob('*/problem.json'))
    if not cases:
        raise ValueError('Generate task cases before preparing Harbor')
    for path in cases:
        load_result(load_problem(path), source / 'reference' / path.parent.name / 'reference.npz')
    archive = root / 'dist' / f'{task}-agent.zip'
    if not archive.is_file():
        raise ValueError(f'Run src/utils/publish_dist.py --task {task} first')
    destination = root / 'runs/harbor/tasks' / task
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_symlink() or getattr(destination, 'is_junction', lambda: False)():
        raise ValueError('Generated task directory must not be a link')
    if not destination.resolve().is_relative_to(root / 'runs/harbor/tasks'):
        raise ValueError('Generated task directory escapes runs/harbor/tasks')
    with tempfile.TemporaryDirectory(dir=destination.parent, prefix=f'.{task}-') as temporary:
        staged = Path(temporary) / task

        def copy(path, relative):
            target = staged / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            data = read_public_file(root, path)
            if path.suffix in {'.sh', '.md', '.toml', '.py'} or path.name == 'Dockerfile':
                data = data.replace(b'\r\n', b'\n')
            target.write_bytes(data)

        for path in template.rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts:
                copy(path, path.relative_to(template))
        # Only the allowlisted public archive enters the agent image build context.
        copy(archive, Path('environment/agent.zip'))
        copy(source / 'author/baseline.py', Path('solution/baseline.py'))
        copy(source / 'judge-config.json', Path('tests/judge-config.json'))
        for path in cases:
            for asset in path.parent.iterdir():
                if asset.is_file():
                    copy(asset, Path('tests/cases') / path.parent.name / asset.name)
            copy(source / 'reference' / path.parent.name / 'reference.npz',
                 Path('tests/reference') / path.parent.name / 'reference.npz')
        # Replace only the checked generated task directory; preserve job logs.
        if destination.exists():
            shutil.rmtree(destination)
        # Copy rather than rename: Windows temporary directories have private
        # ACLs, which must not follow the published task into its destination.
        shutil.copytree(staged, destination)
    return {'task_directory': str(destination), 'cases': len(cases), 'archive': str(archive)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.task), indent=2))
