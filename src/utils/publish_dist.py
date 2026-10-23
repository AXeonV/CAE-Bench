"""Publish one task's public Agent materials as a reproducible ZIP.

Usage: python src/utils/publish_dist.py --task <task> [--output dist]
Only explicitly selected documents, shared tools and public sample assets ship.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import zipfile

from caeoj.sdk import load_problem
from caeoj_tools.task_paths import task_directory
from caeoj_tools.files import atomic_replace
from caeoj.case_grading import prepare_case
from caeoj.validation import ContractError, validate_input, validate_output

PROJECT_ROOT = Path(__file__).resolve().parents[2]
from caeoj_tools.assembly import read_public_file, runtime_materials, validate_public_runtime
from caeoj_tools.source_repair import configuration as repair_configuration

PUBLIC_FILES = ("LICENSE", "docs/CONTRACT.md", "docs/GRADING.md")


INSTALLATION = """安装共享工具：`python -m pip install .`。已预装工具的评测环境可直接使用。
Python 代码最低版本见 pyproject.toml，锁定依赖所需版本由安装器检查；执行 OS／架构以题面为准。
Gmsh 需要系统动态库（Linux 环境预置 libglu1-mesa、libgl1 等）；运行环境应提前准备齐全，普通 pip 安装不负责安装系统库。
h5py、NumPy、Gmsh、jsonschema 是协议依赖；额外求解依赖由程序选择。
"""


def agent_readme(task_path, sample, *, include_install=True, source_repair=False, kind="graded"):
    installation = INSTALLATION if include_install else ""
    if source_repair:
        sample_note = '该样例输出为随机格式示例，不是数值答案或正确修复的依据。' if kind == 'format' else ''
        grade_command = (f'python -m caeoj grade --input {task_path}/samples/{sample}/input/problem.json --output result.h5 --grading {task_path}/samples/{sample}/reference/grading.json' if kind != 'format' else '')
        return f'''# 源码修复材料

阅读 `{task_path}/instruction.md`、同题 DATA.md 和 `docs/CONTRACT.md`。公开样例位于 `{task_path}/samples/`，基线源码与可信驱动源码位于本题 `public/`。

{installation}

本题提交题面指定的源码替换文件，构建与数据驱动由固定环境提供。按题面操作修改源码、完成构建或语法检查，再用以下命令运行和检查样例。{sample_note}

```text
python {task_path}/public/run_case.py --input {task_path}/samples/{sample}/input/problem.json --output result.h5
{grade_command}
```

MANIFEST.json 记录公开资产的 SHA-256。源码修复、数据与评分的完整要求以三份公开文档为准。
'''.encode('utf-8')
    prefix = f'{task_path}/samples/{sample}'
    description = ('公开格式示例仅提供输入与数值随机的 output/result.h5；随机输出不代表正确解，不能用作数值参考。'
                   if kind == 'format' else '以下命令所用数值样例的 reference/grading.json 供本地判分使用，不是额外题意。')
    commands = [f'python -m caeoj validate-input {prefix}/input/problem.json',
                f'python solve.py --input {prefix}/input/problem.json --output result.h5',
                f'python -m caeoj validate-output --input {prefix}/input/problem.json --output result.h5']
    if kind != 'format':
        commands.append(f'python -m caeoj grade --input {prefix}/input/problem.json --output result.h5 --grading {prefix}/reference/grading.json')
    return (f'# 解题材料\n\n阅读 `{task_path}/instruction.md`、同题 DATA.md 和 `docs/CONTRACT.md` 即可确定完整任务与数据规则。'
            f'公开示例在 `{task_path}/samples/`。{description}\n\n{installation}\n'
            '在理解输入、编写和调试程序时可随时使用：\n\n```text\n'+'\n'.join(commands)+'\n```\n\n'
            '校验器检查结构、引用及声明约束，不验证或纠正物理结果。\n'
            '可用 `caeoj.sdk` 的 `load_problem`、`read_constant`、`read_field`、`write_result` 读写数据；'
            '用法见 CONTRACT.md 和本题 DATA.md。\n\n'
            '本包只含公开解题材料。MANIFEST.json 记录所含文件的 SHA-256。\n').encode('utf-8')


def sample_kind(task_dir, name, root):
    manifest = task_dir/'data-manifest.json'
    if manifest.exists():
        return json.loads(read_public_file(root, manifest))['samples'][name].get('kind', 'graded')
    marker = task_dir/'samples'/name/'example.json'
    if marker.exists():
        if json.loads(read_public_file(root, marker)) != {'kind': 'format'}:
            raise ValueError('Invalid format example declaration')
        return 'format'
    return 'graded'


def collect_materials(task, root=PROJECT_ROOT):
    root = Path(root).resolve()
    task_dir = task_directory(task, root)
    task_path = task_dir.relative_to(root).as_posix()
    if (task_dir / 'data-manifest.json').is_file():
        from caeoj_tools.data_pool import verify
        verify(task_dir, strict=True, samples_only=True)
    files, runtime = runtime_materials({task: task_dir}, root)

    def add(path):
        files[path.relative_to(root).as_posix()] = read_public_file(root, path)

    for name in PUBLIC_FILES:
        add(root / name)
    add(task_dir / "instruction.md")
    if (task_dir / "DATA.md").is_file():
        add(task_dir / "DATA.md")
    extra_manifest = task_dir / 'public-materials.json'
    if extra_manifest.is_file():
        extra = json.loads(read_public_file(root, extra_manifest))
        if set(extra) != {'version', 'files'} or extra['version'] != 1 or not isinstance(extra['files'], list):
            raise ValueError('Invalid public-materials.json')
        seen = set()
        for record in extra['files']:
            if not isinstance(record, dict) or set(record) != {'path', 'sha256'}:
                raise ValueError('Invalid public material record')
            relative = record['path']
            if (not isinstance(relative, str) or not relative.startswith('public/')
                    or '\\' in relative or any(p in ('', '.', '..') for p in relative.split('/'))
                    or relative in seen):
                raise ValueError('Extra public material must be a unique path under public/')
            seen.add(relative)
            data = read_public_file(root, task_dir / relative)
            if hashlib.sha256(data).hexdigest() != record['sha256']:
                raise ValueError('Public material hash mismatch: ' + relative)
            files[f'{task_path}/{relative}'] = data
    paths = sorted((task_dir / "samples").glob("*/input/problem.json"))
    if not paths:
        raise ValueError(f"No complete public samples in {task_path}/samples; add them before publishing")
    samples = []
    for path in paths:
        # Check the path before allowing the contract loader to read it.
        add(path)
        manifest = json.loads(files[path.relative_to(root).as_posix()])
        assets = [manifest["data_file"]]
        assets += [item["file"] for item in manifest["geometries"].values()]
        assets += [item["file"] for item in manifest["meshes"].values()]
        for name in assets:
            asset = path.parent / name
            if not asset.resolve().is_relative_to(path.parent.resolve()):
                raise ValueError(f"Sample asset escapes its input directory: {name}")
            add(asset)
        diagnostics = validate_input(path)
        if not diagnostics["valid"]:
            raise ContractError(diagnostics)
        sample = path.parent.parent
        kind = sample_kind(task_dir, sample.name, root)
        if kind == 'format':
            result = sample/'output/result.h5'
            add(result)
            diagnostics = validate_output(path, result)
            if not diagnostics['valid']: raise ContractError(diagnostics)
            samples.append(sample.name)
            continue
        prepared = prepare_case(load_problem(path), sample/'reference/grading.json')
        for name in prepared.evidence['assets']:
            add(sample/'reference'/name)
        result = sample/'output/result.h5'
        if result.is_file():
            add(result)
            diagnostics = validate_output(path, result)
            if not diagnostics['valid']: raise ContractError(diagnostics)
            from caeoj.case_grading import grade_case
            grade = grade_case(path, result, sample/'reference/grading.json')
            if grade['score'] != 1: raise ValueError('Public submission example fails its case evaluation')
        samples.append(sample.name)
    kinds = {name: sample_kind(task_dir, name, root) for name in samples}
    files["README.md"] = agent_readme(task_path, samples[0], source_repair=bool(repair_configuration(task_dir, root)), kind=kinds[samples[0]])
    manifest = {"task": task, "public_samples": samples, "sample_kinds": kinds, "assembly": runtime["id"],
                "files": {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())}}
    files["MANIFEST.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return files, samples


def collect_bundle(tasks, root=PROJECT_ROOT):
    """Assemble several independent tasks into one public installation."""
    tasks = sorted(set(tasks))
    if not tasks:
        raise ValueError('Select at least one task')
    if len(tasks) == 1:
        return collect_materials(tasks[0], root)
    if any(repair_configuration(task_directory(task, root), root) for task in tasks):
        raise ValueError('Source-repair tasks require a separate submission environment')
    root = Path(root).resolve()
    directories = {task: task_directory(task, root) for task in tasks}
    files, runtime = runtime_materials(directories, root)
    samples = {}
    for task in tasks:
        single, samples[task] = collect_materials(task, root)
        for name, data in single.items():
            if name.startswith('src/') or name in ('README.md', 'MANIFEST.json', 'pyproject.toml'):
                continue
            if name in files and files[name] != data:
                raise ValueError(f'Conflicting public material: {name}')
            files[name] = data
    readme = ['# 解题材料', '', INSTALLATION,
              '以下每题分别阅读 instruction.md、DATA.md 与通用 docs/CONTRACT.md；使用同一套 caeoj 命令与 SDK。', '']
    for task, directory in directories.items():
        readme.append(agent_readme(directory.relative_to(root).as_posix(), samples[task][0], include_install=False, kind=sample_kind(directory, samples[task][0], root)).decode())
    files['README.md'] = ('\n'.join(readme)).encode()
    manifest = {'tasks': tasks, 'public_samples': samples, 'sample_kinds': {task: {n: sample_kind(directories[task], n, root) for n in names} for task, names in samples.items()}, 'assembly': runtime['id'],
                'files': {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())}}
    files['MANIFEST.json'] = (json.dumps(manifest, ensure_ascii=False, indent=2)+'\n').encode()
    return files, samples


def publish(task, output=None, root=PROJECT_ROOT):
    root = Path(root).resolve()
    tasks = [task] if isinstance(task, str) else sorted(set(task))
    files, samples = collect_bundle(tasks, root)
    validate_public_runtime(files)
    artifact = tasks[0] if len(tasks) == 1 else "multi-"+hashlib.sha256("\n".join(tasks).encode()).hexdigest()[:12]
    output = Path(output).resolve() if output is not None else root / "dist"
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"{artifact}-agent.zip"
    # Atomic replacement leaves an existing release intact if building fails.
    handle, temporary = tempfile.mkstemp(prefix=f".{artifact}-agent-", suffix=".tmp", dir=output)
    try:
        with os.fdopen(handle, 'wb') as stream:
            with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
                for name, data in sorted(files.items()):
                    entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                    entry.create_system = 3
                    entry.external_attr = 0o100644 << 16
                    entry.compress_type = zipfile.ZIP_DEFLATED
                    bundle.writestr(entry, data, compresslevel=9)
        atomic_replace(temporary, archive)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {"archive": str(archive), "file_count": len(files), "public_samples": samples,
            "sha256": hashlib.sha256(archive.read_bytes()).hexdigest()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True, action="append", help="Unique task directory name under qbank/<chapter>/<section>/")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "dist", help="ZIP output directory")
    args = parser.parse_args(argv)
    try:
        result = publish(args.task, args.output)
    except (OSError, ValueError, KeyError, RuntimeError, ContractError) as exc:
        parser.exit(1, f"Publish failed: {exc}\n")
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
