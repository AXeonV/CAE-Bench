"""Assemble a temporary Harbor task under runs/ from a published public ZIP."""
import argparse
import json
from pathlib import Path
import re
import shutil
from string import Template
import tempfile
import tomllib
import zipfile

from publish_dist import PROJECT_ROOT, read_public_file
from caeoj.sdk import load_problem, load_result

TEMPLATE_FILES = ('environment/Dockerfile', 'solution/solve.sh',
                  'tests/test.sh', 'tests/judge.py')
RESOURCE_FIELDS = {'agent': ('timeout_sec',),
                   'environment': ('build_timeout_sec', 'cpus', 'memory_mb'),
                   'verifier': ('timeout_sec',)}


def task_config(template, overrides):
    """Keep the shared execution interface; allow task-specific resource limits."""
    config = tomllib.loads(template)
    for section, values in overrides.items():
        if section not in RESOURCE_FIELDS or not isinstance(values, dict):
            raise ValueError(f'Unsupported Harbor config section: {section}')
        for name, value in values.items():
            if name not in RESOURCE_FIELDS[section]:
                raise ValueError(f'Unsupported Harbor config field: {section}.{name}')
            expected = int if name in ('cpus', 'memory_mb') else float
            types = (int, float) if expected is float else (expected,)
            if type(value) not in types or value <= 0:
                raise ValueError(f'Harbor resource must be positive: {section}.{name}')
            config[section][name] = value
    # These config values are TOML-compatible scalar values or arrays of strings.
    lines = []
    for name, value in config.items():
        if not isinstance(value, dict):
            lines.append(f'{name} = {json.dumps(value, allow_nan=False)}')
    for section, values in config.items():
        if isinstance(values, dict):
            lines.extend(['', f'[{section}]'])
            lines.extend(f'{name} = {json.dumps(value, allow_nan=False)}' for name, value in values.items())
    return '\n'.join(lines) + '\n'


def prepare(task, root=PROJECT_ROOT):
    root = Path(root).resolve()
    if not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9_-])?', task):
        raise ValueError('Task must be a directory name')
    source = root / 'tasks' / task
    template = root / 'src/utils/harbor'
    cases = sorted((source / 'cases').glob('*/problem.json'))
    if not cases:
        raise ValueError('Generate task cases before preparing Harbor')
    for path in cases:
        load_result(load_problem(path), source / 'reference' / path.parent.name / 'reference.npz')
    archive = root / 'dist' / f'{task}-agent.zip'
    if not archive.is_file():
        raise ValueError(f'Run src/utils/publish_dist.py --task {task} first')
    with zipfile.ZipFile(archive) as bundle:
        manifest = json.loads(bundle.read('MANIFEST.json'))
    if manifest['task'] != task or not manifest['public_samples']:
        raise ValueError('Published archive must match the task and include a sample')
    config_path = source / 'harbor/task.toml'
    overrides = tomllib.loads(read_public_file(root, config_path).decode('utf-8')) if config_path.is_file() else {}
    rendered_config = task_config(read_public_file(root, template / 'task.toml').decode('utf-8'), overrides)
    judge_config = json.loads(read_public_file(root, source / 'judge-config.json'))
    instruction = Template(read_public_file(root, template / 'instruction.md').decode('utf-8')).substitute(
        task=task, sample=manifest['public_samples'][0], timeout_seconds=judge_config['timeout_seconds'],
        samples=', '.join(f'`/app/tasks/{task}/samples/{name}/`' for name in manifest['public_samples']))
    resources = tomllib.loads(rendered_config)
    instruction += '\n本次判分参数：绝对误差容限=' + str(judge_config['atol']) + \
        '，相对误差容限=' + str(judge_config['rtol']) + \
        '；逐项满足 |结果−参考| ≤ atol + rtol·|参考|。IDs、时间轴等结构要求仍须严格满足。\n'
    environment = resources['environment']
    if 'cpus' in environment:
        instruction += f"本次环境 CPU 配额：{environment['cpus']} 核。\n"
    if 'memory_mb' in environment:
        instruction += f"可用内存：{environment['memory_mb']} MB。\n"
    if 'max_output_bytes' in judge_config:
        instruction += f"每例结果文件大小上限：{judge_config['max_output_bytes']} 字节。\n"
    baseline = source / 'author/baseline.py'
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

        for name in TEMPLATE_FILES:
            if name == 'solution/solve.sh' and not baseline.is_file():
                continue
            copy(template / name, Path(name))
        (staged / 'task.toml').write_text(rendered_config, encoding='utf-8', newline='\n')
        (staged / 'instruction.md').write_text(instruction, encoding='utf-8', newline='\n')
        requirements = source / 'harbor/requirements.txt'
        if requirements.is_file():
            copy(requirements, Path('environment/requirements.txt'))
        else:
            (staged / 'environment/requirements.txt').write_text('', encoding='utf-8')
        # Only the allowlisted public archive enters the agent image build context.
        copy(archive, Path('environment/agent.zip'))
        # Harbor builds the separate verifier from tests/, not environment/.
        # Reuse the public runtime definition and install private files only there.
        copy(template / 'environment/Dockerfile', Path('tests/Dockerfile'))
        with (staged / 'tests/Dockerfile').open('a', encoding='utf-8', newline='\n') as stream:
            stream.write('COPY . /tests\n')
        copy(archive, Path('tests/agent.zip'))
        shutil.copyfile(staged / 'environment/requirements.txt', staged / 'tests/requirements.txt')
        if baseline.is_file():
            copy(baseline, Path('solution/baseline.py'))
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
    return {'task_directory': str(destination), 'cases': len(cases), 'archive': str(archive),
            'oracle_available': baseline.is_file()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.task), indent=2))
