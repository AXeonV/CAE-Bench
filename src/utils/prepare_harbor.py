"""Assemble a temporary Harbor task under runs/ from a published public ZIP."""
import argparse
import json
import math
from pathlib import Path
import shutil
from string import Template
import tempfile
import tomllib
import zipfile

from publish_dist import PROJECT_ROOT, read_public_file, collect_materials
from caeoj.case_grading import prepare_case
from caeoj.sdk import load_problem
from caeoj_tools.task_paths import task_directory
from caeoj_tools.source_repair import configuration as repair_configuration, dockerfile as repair_dockerfile, oracle_sources

TEMPLATE_FILES = ('environment/Dockerfile', 'solution/solve.sh',
                  'tests/test.sh', 'tests/judge.py')
RESOURCE_FIELDS = {'agent': ('timeout_sec',),
                   'environment': ('build_timeout_sec', 'cpus', 'memory_mb', 'gpus', 'os'),
                   'verifier': ('timeout_sec', 'network_mode')}


def sample_materials(task_path, samples, files, kinds=None):
    """Describe only assets present in the verified public archive."""
    lines = ['公开样例材料：', '']
    for sample in samples:
        prefix = f'{task_path}/samples/{sample}/'
        lines.append(f'- 样例 `{sample}`：`/app/{prefix}`。')
        lines.append(f'  - 输入：`/app/{prefix}input/problem.json`。')
        references = sorted(name for name in files if name.startswith(prefix + 'reference/'))
        if references:
            lines.append('  - 参考与判分材料：' + '、'.join(f'`/app/{name}`' for name in references) + '。')
        example = prefix + 'output/result.h5'
        if example in files:
            if (kinds or {}).get(sample) == 'format':
                lines.append(f'  - 随机数值的格式示例：`/app/{example}`；仅说明输出格式，不是正确提交或数值参考。')
            else:
                lines.append(f'  - 完整提交示例：`/app/{example}`。')
    return '\n'.join(lines) + '\n'


def task_config(template, overrides, *, judge_config=None, case_count=None):
    """Keep the shared execution interface; allow task-specific resource limits."""
    config = tomllib.loads(template)
    for section, values in overrides.items():
        if section not in RESOURCE_FIELDS or not isinstance(values, dict):
            raise ValueError(f'Unsupported Harbor config section: {section}')
        for name, value in values.items():
            if name not in RESOURCE_FIELDS[section]:
                raise ValueError(f'Unsupported Harbor config field: {section}.{name}')
            if name in ('os', 'network_mode'):
                allowed = ('linux',) if name == 'os' else ('no-network',)
                if value not in allowed:
                    raise ValueError(f'Unsupported Harbor policy: {section}.{name}')
                config[section][name] = value
                continue
            expected = int if name in ('cpus', 'memory_mb') else float
            if name == 'gpus':
                if type(value) is not int or value != 0:
                    raise ValueError('This runner supports CPU-only tasks (gpus=0)')
                config[section][name] = value
                continue
            types = (int, float) if expected is float else (expected,)
            if type(value) not in types or value <= 0 or not math.isfinite(value):
                raise ValueError(f'Harbor resource must be positive: {section}.{name}')
            config[section][name] = value
    if judge_config is not None and 'verifier_budget' in judge_config:
        budget = judge_config['verifier_budget']
        if not isinstance(budget, dict) or set(budget) != {'base_seconds', 'per_case_overhead_seconds'}:
            raise ValueError('Invalid verifier_budget keys')
        values = [*budget.values(), judge_config['timeout_seconds']]
        if any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in values):
            raise ValueError('Verifier budget and solver timeout must be positive finite seconds')
        if type(case_count) is not int or case_count <= 0:
            raise ValueError('Auto verifier budget requires the actual positive case count')
        evaluation_timeout = judge_config.get('evaluation_timeout_seconds', 60)
        if type(evaluation_timeout) not in (int,float) or not math.isfinite(evaluation_timeout) or evaluation_timeout <= 0:
            raise ValueError('Invalid evaluation_timeout_seconds')
        required = budget['base_seconds'] + case_count * (
            judge_config['timeout_seconds'] + evaluation_timeout + budget['per_case_overhead_seconds'])
        if not math.isfinite(required):
            raise ValueError('Verifier budget overflow')
        config['verifier']['timeout_sec'] = max(config['verifier']['timeout_sec'], required)
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
    source = task_directory(task, root)
    repair = repair_configuration(source, root)
    public_cases = []
    if (source / 'data-manifest.json').is_file():
        from caeoj_tools.data_pool import verify
        public_cases = verify(source, strict=True)['public_cases']
    task_path = source.relative_to(root).as_posix()
    template = root / 'src/utils/harbor'
    cases = sorted((source / 'cases').glob('*/problem.json'))
    if not cases:
        raise ValueError('Generate task cases before preparing Harbor')
    for path in cases:
        prepare_case(load_problem(path), source/'reference'/path.parent.name/'grading.json')
    archive = root / 'dist' / f'{task}-agent.zip'
    if not archive.is_file():
        raise ValueError(f'Run src/utils/publish_dist.py --task {task} first')
    with zipfile.ZipFile(archive) as bundle:
        manifest = json.loads(bundle.read('MANIFEST.json'))
        current_files, _ = collect_materials(task, root)
        names = bundle.namelist()
        if (len(names) != len(current_files) or set(names) != set(current_files)
                or any(bundle.read(name) != data for name, data in current_files.items())):
            raise ValueError('Published materials are stale or modified; run publish_dist.py again')
        del current_files
    if manifest['task'] != task or not manifest['public_samples']:
        raise ValueError('Published archive must match the task and include a sample')
    config_path = source / 'harbor/task.toml'
    overrides = tomllib.loads(read_public_file(root, config_path).decode('utf-8')) if config_path.is_file() else {}
    judge_config = json.loads(read_public_file(root, source / 'judge-config.json'))
    rendered_config = task_config(read_public_file(root, template / 'task.toml').decode('utf-8'), overrides,
                                  judge_config=judge_config, case_count=len(cases))
    graded = [name for name in manifest['public_samples'] if manifest.get('sample_kinds', {}).get(name) != 'format']
    command_sample = graded[0] if graded else manifest['public_samples'][0]
    instruction = Template(read_public_file(root, template / 'instruction.md').decode('utf-8')).substitute(
        task=task, task_path=task_path, sample=command_sample, timeout_seconds=judge_config['timeout_seconds'],
        sample_materials=sample_materials(task_path, manifest['public_samples'], names, manifest.get('sample_kinds', {})))
    if repair:
        instruction = (f'# 修复求解器\n\n阅读 `/app/{task_path}/instruction.md`、该目录的 DATA.md 和 '
                       '`/app/docs/CONTRACT.md`。按题面修复指定源码并提交到 `/app/submission/`。'
                       '仅此目录传入独立 verifier；最终提交只包含题面列出的源码替换文件。'
                       '不提交 solve.py。编译和调用由可信后端执行。\n\n'
                       + sample_materials(task_path, manifest['public_samples'], names, manifest.get('sample_kinds', {})))
    resources = tomllib.loads(rendered_config)
    if repair:
        minimum = repair['build_timeout_seconds'] + repair.get('baseline_timeout_seconds', 60) + len(cases) * (
            judge_config['timeout_seconds'] + judge_config.get('evaluation_timeout_seconds', 60))
        if repair.get('baseline_probe'):
            minimum += min(60, repair['build_timeout_seconds'])
        if resources['verifier']['timeout_sec'] < minimum:
            raise ValueError('Verifier budget cannot cover source build, baseline check and all cases')
    if graded:
        instruction += f"公开样例判分：python -m caeoj grade --input /app/{task_path}/samples/{graded[0]}/input/problem.json --output /app/sample-result.h5 --grading /app/{task_path}/samples/{graded[0]}/reference/grading.json\n"
    environment = resources['environment']
    if 'cpus' in environment:
        instruction += f"本次环境 CPU 配额：{environment['cpus']} 核。\n"
    if 'memory_mb' in environment:
        instruction += f"可用内存：{environment['memory_mb']} MB。\n"
    if judge_config.get('max_output_bytes') is not None:
        instruction += f"每例结果文件大小上限：{judge_config['max_output_bytes']} 字节。\n"
    baseline = source / 'author/baseline.py'
    repair_oracle = oracle_sources(source, repair) if repair else []
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
            if repair and name == 'solution/solve.sh':
                continue
            if name == 'solution/solve.sh' and not baseline.is_file():
                continue
            copy(template / name, Path(name))
        (staged / 'task.toml').write_text(rendered_config, encoding='utf-8', newline='\n')
        (staged / 'instruction.md').write_text(instruction, encoding='utf-8', newline='\n')
        requirements = source / 'harbor/requirements.txt'
        requirement_lines = []
        if not repair:
            requirement_lines.extend(read_public_file(root, template/'environment/runtime-requirements.txt').decode('utf-8').splitlines())
        if requirements.is_file():
            requirement_lines.extend(read_public_file(root, requirements).decode('utf-8').splitlines())
        effective = list(dict.fromkeys(line.strip() for line in requirement_lines
                                      if line.strip() and not line.lstrip().startswith('#')))
        (staged/'environment/requirements.txt').write_text('\n'.join(effective)+'\n', encoding='utf-8', newline='\n')
        for relative in ('environment/check_environment.py', 'tests/check_environment.py'):
            copy(template/'environment/check_environment.py', Path(relative))
        # Only the allowlisted public archive enters the agent image build context.
        copy(archive, Path('environment/agent.zip'))
        # Harbor builds the separate verifier from tests/, not environment/.
        # Reuse the public runtime definition and install private files only there.
        copy(template / 'environment/Dockerfile', Path('tests/Dockerfile'))
        if repair:
            runtime_dockerfile = repair_dockerfile(repair)
            for path in ['environment/Dockerfile', 'tests/Dockerfile']:
                (staged / path).write_text(runtime_dockerfile, encoding='utf-8', newline='\n')
            copy(source / 'harbor/source-repair.json', Path('tests/source-repair.json'))
            copy(template / 'tests/source_repair.py', Path('tests/source_repair.py'))
            if repair_oracle:
                commands = ['#!/bin/bash', 'set -euo pipefail', 'mkdir -p /app/submission']
                for path in repair_oracle:
                    copy(path, Path('solution') / path.name)
                    commands.append(f'cp /solution/{path.name} /app/submission/{path.name}')
                (staged / 'solution/solve.sh').write_text('\n'.join(commands) + '\n', encoding='utf-8', newline='\n')
        with (staged / 'tests/Dockerfile').open('a', encoding='utf-8', newline='\n') as stream:
            stream.write('COPY . /tests\n')
        copy(archive, Path('tests/agent.zip'))
        shutil.copyfile(staged / 'environment/requirements.txt', staged / 'tests/requirements.txt')
        if baseline.is_file() and not repair:
            copy(baseline, Path('solution/baseline.py'))
        copy(source / 'judge-config.json', Path('tests/judge-config.json'))
        (staged/'tests/selection.json').write_text(json.dumps({'public_cases': public_cases}, indent=2)+'\n', encoding='utf-8')
        for path in cases:
            problem = load_problem(path)
            assets = [path.name, problem.manifest['data_file']]
            assets += [item['file'] for table in ('meshes', 'geometries')
                       for item in problem.manifest[table].values()]
            for name in dict.fromkeys(assets):
                copy(path.parent/name, Path('tests/cases')/path.parent.name/name)
            prepared = prepare_case(problem, source/'reference'/path.parent.name/'grading.json')
            for name in prepared.evidence['assets']:
                copy(source/'reference'/path.parent.name/name, Path('tests/reference')/path.parent.name/name)
            # Verify the copied package itself before replacing any old task.
            prepare_case(load_problem(staged/'tests/cases'/path.parent.name/path.name),
                         staged/'tests/reference'/path.parent.name/'grading.json')
        # Replace only the checked generated task directory; preserve job logs.
        if destination.exists():
            shutil.rmtree(destination)
        # Copy rather than rename: Windows temporary directories have private
        # ACLs, which must not follow the published task into its destination.
        shutil.copytree(staged, destination)
    return {'task_directory': str(destination), 'cases': len(cases), 'archive': str(archive),
            'oracle_available': bool(repair_oracle) if repair else baseline.is_file(), 'public_cases': public_cases}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.task), indent=2))
