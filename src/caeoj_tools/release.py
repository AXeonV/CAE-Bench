"""Freeze already assembled tasks; never fetch, produce, or qualify numeric data.

Maintainer API: build(plan_path, output) -> catalog dict. Output must be empty;
on failure partial files remain for diagnosis, without a completion checksum file.
The same file ships as release.py and runs using only the Python standard library.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import zipfile


def _relative(value):
    if not isinstance(value, str) or not value or '\\' in value or ':' in value or '\0' in value:
        raise ValueError(f'Unsafe relative path: {value!r}')
    parts = value.split('/')
    if any(p in ('', '.', '..') or p.endswith((' ', '.')) or
           re.fullmatch(r'(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?', p) for p in parts) or PurePosixPath(value).is_absolute():
        raise ValueError(f'Unsafe relative path: {value!r}')
    return value


def _file(root, relative):
    root = Path(root)
    result = root / _relative(relative)
    cursor = result
    while True:
        if _linked(cursor):
            raise ValueError(f'Links are not allowed: {cursor}')
        if cursor == cursor.parent:
            break
        cursor = cursor.parent
    if not result.is_file():
        raise ValueError(f'Missing regular file: {result}')
    if not result.resolve().is_relative_to(root.resolve()):
        raise ValueError(f'File escapes root: {result}')
    return result


def _linked(path):
    return path.is_symlink() or (path.exists() and bool(getattr(path.lstat(), 'st_file_attributes', 0) & 0x400))


def _absolute(value):
    path = Path(value)
    if not path.is_absolute():
        raise ValueError(f'Expected absolute maintainer input path: {value}')
    return path


def _unlinked_ancestors(path):
    cursor = path
    while True:
        if _linked(cursor):
            raise ValueError(f'Linked filesystem path: {cursor}')
        if cursor == cursor.parent:
            break
        cursor = cursor.parent


def _hash_stream(stream):
    digest = hashlib.sha256()
    size = 0
    while chunk := stream.read(1024 * 1024):
        digest.update(chunk)
        size += len(chunk)
    return {'sha256': digest.hexdigest(), 'size_bytes': size}


def _record(path):
    with Path(path).open('rb') as stream:
        return _hash_stream(stream)


def _json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def _write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def _zip_members(archive):
    """Reject duplicate, nonregular, traversal and prefix-conflicting entries."""
    members = {}
    for info in archive.infolist():
        name = _relative(info.filename)
        mode = info.external_attr >> 16
        if info.is_dir() or stat.S_ISLNK(mode) or (stat.S_IFMT(mode) and not stat.S_ISREG(mode)):
            raise ValueError(f'Nonregular ZIP entry: {name}')
        if name in members:
            raise ValueError(f'Duplicate ZIP entry: {name}')
        members[name] = info
    folded = set()
    for name in members:
        key = name.casefold()
        if key in folded:
            raise ValueError(f'Case-insensitive ZIP collision: {name}')
        folded.add(key)
    for name in folded:
        if any(str(p) in folded for p in PurePosixPath(name).parents if str(p) != '.'):
            raise ValueError(f'ZIP file/directory collision: {name}')
    return members


def _snapshot(task_root):
    manifest = _json(_file(task_root, 'data-manifest.json'))
    receipt = _json(_file(task_root, '.data-assembly.json'))
    canonical = (json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
    if receipt.get('selection_sha256') != hashlib.sha256(canonical).hexdigest():
        raise ValueError('Manifest selection digest differs from assembly receipt')
    for role in ('cases', 'samples'):
        selected = manifest.get(role)
        if not isinstance(selected, dict) or set(receipt.get('scope', {}).get(role, [])) != set(selected):
            raise ValueError(f'Manifest/receipt {role} selection mismatch')
        for key in selected:
            _relative(key)
            if '/' in key:
                raise ValueError(f'Invalid {role} key: {key}')
    if not manifest['cases']:
        raise ValueError('Task has no selected cases')
    entries = receipt.get('files')
    if not isinstance(entries, dict) or not entries:
        raise ValueError('Missing assembly receipt files')
    for name, expected in entries.items():
        parts = _relative(name).split('/')
        if len(parts) < 3 or parts[0] not in ('cases', 'reference', 'samples'):
            raise ValueError(f'Unexpected receipt asset: {name}')
        selected = manifest['samples' if parts[0] == 'samples' else 'cases']
        if parts[1] not in selected:
            raise ValueError(f'Unselected receipt asset: {name}')
        actual = _record(_file(task_root, name))
        if actual != expected:
            raise ValueError(f'Assembly asset digest mismatch: {name}')
    # The saved descriptor is the complete producer inventory, not just a minimum
    # problem/grading pair. Detect a receipt that accidentally dropped one asset.
    descriptors = receipt.get('descriptors', {})
    derived = {}
    for role in ('cases', 'samples'):
        for key, selection in manifest[role].items():
            descriptor_path = selection['case']['path']
            if descriptor_path not in descriptors:
                raise ValueError(f'Missing saved case descriptor: {descriptor_path}')
            raw = descriptors[descriptor_path]
            if hashlib.sha256(raw.encode()).hexdigest() != selection['case']['sha256']:
                raise ValueError(f'Descriptor digest mismatch: {descriptor_path}')
            descriptor = json.loads(raw)
            if descriptor.get('case_id') != selection['case_id']:
                raise ValueError('Selection case_id differs from descriptor')
            format_only = role == 'samples' and selection.get('kind') == 'format'
            if role == 'samples' and format_only != (descriptor.get('example_kind') == 'format'):
                raise ValueError('Format sample selection/descriptor mismatch')
            if not descriptor.get('input', {}).get('complete') or (not format_only and not descriptor.get('reference', {}).get('complete')):
                raise ValueError(f'Incomplete selected descriptor: {descriptor_path}')
            groups = descriptor['input'].get('files', []) + descriptor['reference'].get('files', [])
            if len(groups) != len(set(groups)) or set(groups) != set(descriptor['files']):
                raise ValueError('Descriptor groups must partition declared files')
            if 'input/problem.json' not in descriptor['input']['files'] or (not format_only and 'reference/grading.json' not in descriptor['reference']['files']):
                raise ValueError('Descriptor lacks required input or grading entry point')
            example = descriptor.get('example')
            if example is not None and example not in descriptor['reference']['files']:
                raise ValueError('Example is not a declared reference asset')
            if format_only and example is None:
                raise ValueError('Format sample lacks an explicit example output')
            for name, expected in descriptor['files'].items():
                _relative(name)
                if not name.startswith(('input/', 'reference/')):
                    raise ValueError('Descriptor asset outside input/reference groups')
                if name.startswith('input/') != (name in descriptor['input']['files']):
                    raise ValueError('Misplaced descriptor group member')
                if format_only and name.startswith('reference/'):
                    if name == example:
                        derived[f'samples/{key}/output/result.h5'] = expected
                    continue
                if role == 'samples':
                    target = f'samples/{key}/{name}'
                elif name.startswith('input/'):
                    target = f'cases/{key}/{name[6:]}'
                elif name.startswith('reference/'):
                    target = f'reference/{key}/{name[10:]}'
                derived[target] = expected
                if role == 'samples' and name == example:
                    derived[f'samples/{key}/output/result.h5'] = expected
                if entries.get(target) != expected:
                    raise ValueError(f'Receipt omits/misbinds descriptor asset: {target}')
    if derived != entries:
        raise ValueError('Receipt assets differ from exact descriptor selection')
    files = dict(entries)
    for name in ('instruction.md', 'DATA.md', 'judge-config.json', 'data-manifest.json', '.data-assembly.json'):
        files[name] = _record(_file(task_root, name))
    if (task_root / 'harbor/task.toml').exists():
        files['harbor/task.toml'] = _record(_file(task_root, 'harbor/task.toml'))
    return manifest, files


def _readme(catalog):
    tasks = catalog['tasks']
    cases = sum(len(t['cases']) for t in tasks)
    samples = sum(len(t['samples']) for t in tasks)
    notes = ''.join(f'- {note}\n' for note in catalog.get('release_notes', []))
    notes_section = '\n## 本版范围与资格说明\n\n' + notes if notes else ''
    return f'''# {catalog['release_id']} — 内部候选发行版

本包是选中题目的材料与数据快照，不是完整模型执行器或全部题库正式发行。
包含{len(tasks)}题、{cases}个正式case角色、{samples}个公开样例角色；正式case与样例可能共享身份，不能相加视为独立工况数。
另有{len(catalog['excluded'])}项排除记录。逐题身份、选样映射、profile、limitations和排除原因见catalog.json。
文件存在与摘要通过不代表数值资格、资源校准或模型Benchmark已经通过。
{notes_section}

## 材料边界

- public/<task>-agent.zip是给考生的公开闭包。
- qbank.zip含正式输入与隐藏reference，只交给评测维护者；不要将整包交给考生或模型。
- licenses/按摘要保存许可原文，catalog记录每项所属题目及原文件名；第三方材料分别遵守自身许可，不受某一统一根许可证覆盖。
- 未包含求解器容器镜像、模型访问凭据或云账户；不宣称支持整仓patch提交或遇错即停的快速评分模式。

## 离线数据检查与单题提取

```text
python release.py list
python release.py verify
python release.py extract <task> <empty-dir>
```

以上命令使用标准库，数据已随包提供，无需再次从HF下载。verify流式校验全部资产；SHA256SUMS.json用于完整性检查，不是发行者数字签名。
extract仅供维护者使用：将该题私有材料与公开闭包合并到空目标，成功后写RELEASE-EXTRACT.json。失败目录不可作为完成工作区使用，应移走该目录并向新空目录重试。

各题使用独立工作区或虚拟环境。在提取后的目录执行：

```text
python -m pip install .
python -m caeoj validate-input <task-path>/cases/<case>/problem.json
python -m caeoj grade --input <task-path>/cases/<case>/problem.json --output result.h5 --grading <task-path>/reference/<case>/grading.json
```

<task-path>来自catalog的path。安装后的provider可能严格绑定不同题目，不要在同一环境交替覆盖安装多个题的包。
准备Python 3.11或更高版本；单题最低版本和锁定依赖以公开包pyproject.toml为准。普通pip安装可能需要预备wheel/网络，并不会安装Gmsh所需系统动态库；Linux通常需libGLU、libGL等，具体以题面和公开包说明为准。
上述命令验证数据、对已有result.h5判分，不运行考生模型，也不自动产生求解结果。公开format样例用于展示结构，不应充当数值答案；正式case按其真实reference配置评分。
'''


def build(plan_path, output):
    """Return catalog; write qbank.zip, public ZIPs, licenses, CLI and checksums.

    source_root and public_archive/license_files are local maintainer inputs only;
    they are never embedded as acquisition paths into the distributable catalog.
    profile and limitations are mandatory plan assertions, not computed grades.
    """
    plan = _json(plan_path)
    if not isinstance(plan.get('tasks'), list) or not plan['tasks']:
        raise ValueError('Release plan must select at least one task')
    notes = plan.get('release_notes', [])
    if not isinstance(notes, list) or any(not isinstance(note, str) or not note.strip() for note in notes):
        raise ValueError('Release notes must be a list of nonempty strings')
    output = Path(output).absolute()
    _unlinked_ancestors(output)
    # A release must not consume itself or overwrite any selected input.
    resolved_output = output.resolve()
    if Path(plan_path).resolve().is_relative_to(resolved_output):
        raise ValueError('Release output contains its input plan')
    for entry in plan['tasks']:
        source = (_absolute(entry['source_root']) / _relative(entry['task_path'])).resolve()
        if source.is_relative_to(resolved_output) or resolved_output.is_relative_to(source):
            raise ValueError('Release output and selected task root must be disjoint')
        for raw in [entry['public_archive'], *entry['license_files']]:
            if _absolute(raw).resolve().is_relative_to(resolved_output):
                raise ValueError('Release output contains an input asset')
    if _linked(output) or (output.exists() and any(output.iterdir())):
        raise ValueError('Release output must be an empty non-link directory')
    output.mkdir(parents=True, exist_ok=True)
    catalog = {'schema_version': 1, 'release_id': plan['release_id'],
               'stage': plan.get('stage', 'internal_rc'),
               'capabilities': plan.get('capabilities', {'dataset_offline': True, 'model_runner_included': False, 'fast_grading': False, 'repo_patch': False}),
               'qualification': 'Profiles are explicit plan declarations; file integrity is not numerical qualification.',
               'release_notes': notes,
               'tasks': [], 'excluded': plan.get('excluded', []), 'licenses': []}
    names, prefixes, members, task_ids = set(), set(), set(), set()
    for entry in plan['tasks']:
        slug = entry['task']
        if not isinstance(slug, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', slug):
            raise ValueError('Invalid task slug')
        prefix = _relative(entry['task_path'])
        if len(prefix.split('/')) != 4 or not prefix.startswith('qbank/'):
            raise ValueError('Task path must be qbank/chapter/section/task')
        if slug.casefold() in names or prefix.casefold() in prefixes:
            raise ValueError('Duplicate task or archive path')
        names.add(slug.casefold()); prefixes.add(prefix.casefold())
        if not isinstance(entry['profile'], str) or not entry['profile'].strip() or not isinstance(entry['limitations'], list) or any(not isinstance(x, str) or not x.strip() for x in entry['limitations']):
            raise ValueError('Explicit profile and limitations list required')
    (output / 'public').mkdir()
    (output / 'licenses').mkdir()
    with zipfile.ZipFile(output / 'qbank.zip', 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=1, allowZip64=True) as bank:
        for entry in plan['tasks']:
            source = _absolute(entry['source_root'])
            prefix = entry['task_path']
            task_root = source / prefix
            manifest, files = _snapshot(task_root)
            task_id = manifest['task_id']
            if not isinstance(task_id, str) or not task_id.strip() or task_id.casefold() in task_ids:
                raise ValueError('Missing or duplicate stable task_id')
            task_ids.add(task_id.casefold())
            for relative, expected in sorted(files.items()):
                name = f'{prefix}/{relative}'
                if name.casefold() in members:
                    raise ValueError(f'Archive collision: {name}')
                members.add(name.casefold())
                info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info._compresslevel = 1  # ZipFile.open uses the per-entry level.
                info.external_attr = 0o100644 << 16
                with _file(task_root, relative).open('rb') as src, bank.open(info, 'w', force_zip64=True) as dst:
                    digest = hashlib.sha256(); size = 0
                    while chunk := src.read(1024 * 1024):
                        digest.update(chunk); size += len(chunk); dst.write(chunk)
                if {'sha256': digest.hexdigest(), 'size_bytes': size} != expected:
                    raise ValueError(f'Asset changed during archive write: {name}')
            public_path = _absolute(entry['public_archive'])
            _file(public_path.parent, public_path.name)
            public_name = f'public/{entry["task"]}-agent.zip'
            shutil.copyfile(public_path, output / public_name)
            with zipfile.ZipFile(output / public_name) as z:
                public_members = _zip_members(z)
                if any('/author/' in '/' + n or (n.startswith('qbank/') and not n.startswith(prefix + '/')) for n in public_members):
                    raise ValueError('Public archive contains author or unrelated task materials')
                if any(n.startswith((prefix + '/cases/', prefix + '/reference/', prefix + '/harbor/')) or n in {prefix + '/' + s for s in ('.data-assembly.json', 'data-manifest.json', 'judge-config.json')} for n in public_members):
                    raise ValueError('Public archive contains private cases or references')
                for name in public_members:
                    if name.startswith(prefix + '/samples/') and name[len(prefix) + 1:] not in files:
                        raise ValueError('Public archive contains unselected sample asset')
                public_manifest = json.loads(z.read('MANIFEST.json'))
                declared = public_manifest['files']
                if set(declared) != set(public_members) - {'MANIFEST.json'}:
                    raise ValueError('Public archive manifest file set mismatch')
                for name, expected_hash in declared.items():
                    with z.open(name) as stream:
                        if _hash_stream(stream)['sha256'] != expected_hash:
                            raise ValueError(f'Public archive digest mismatch: {name}')
                for required in ('instruction.md', 'DATA.md'):
                    if f'{prefix}/{required}' not in public_members:
                        raise ValueError(f'Public archive lacks current task {required}')
                combined = {}
                for name in [*public_members, *(f'{prefix}/{r}' for r in files)]:
                    folded = name.casefold()
                    if folded in combined and combined[folded] != name:
                        raise ValueError('Public/private case-insensitive path collision')
                    combined[folded] = name
                for name in combined:
                    if any(str(p) in combined for p in PurePosixPath(name).parents if str(p) != '.'):
                        raise ValueError('Public/private file/directory collision')
                for relative, expected in files.items():
                    name = f'{prefix}/{relative}'
                    if name in public_members:
                        with z.open(name) as stream:
                            if _hash_stream(stream) != expected:
                                raise ValueError(f'Public/private material conflict: {name}')
            license_ids = []
            for raw in entry['license_files']:
                path = _absolute(raw); _file(path.parent, path.name)
                record = _record(path); license_id = record['sha256']
                dest = f'licenses/{license_id}.txt'
                if not (output / dest).exists():
                    shutil.copyfile(path, output / dest)
                if _record(output / dest) != record:
                    raise ValueError('License changed during release assembly')
                catalog['licenses'].append({'task': entry['task'], 'original_name': path.name, 'path': dest, **record})
                license_ids.append(license_id)
            catalog['tasks'].append({k: entry[k] for k in ('task', 'chapter', 'title', 'profile', 'limitations')} |
                {'task_id': manifest['task_id'], 'path': prefix, 'cases': manifest['cases'], 'samples': manifest['samples'],
                 'public_archive': public_name, 'bank_archive': 'qbank.zip', 'files': files,
                 'metadata_sha256': {n: files[n]['sha256'] for n in files if '/' not in n}, 'license_ids': license_ids})
    _write_json(output / 'catalog.json', catalog)
    (output / 'README.md').write_text(_readme(catalog), encoding='utf-8')
    shutil.copyfile(Path(__file__), output / 'release.py')
    checksums = {p.relative_to(output).as_posix(): _record(p) for p in sorted(output.rglob('*')) if p.is_file()}
    _write_json(output / 'SHA256SUMS.json', {'schema_version': 1, 'files': checksums})
    return catalog


def verify(root):
    """Stream-check all final artifacts against SHA256SUMS.json; raise on error."""
    root = Path(root).absolute()
    checksum = _json(_file(root, 'SHA256SUMS.json'))
    for name, expected in checksum['files'].items():
        if _record(_file(root, name)) != expected:
            raise ValueError(f'Release digest mismatch: {name}')
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if actual != set(checksum['files']) | {'SHA256SUMS.json'}:
        raise ValueError('Unexpected or unlisted release assets')
    return {'verified_files': len(checksum['files'])}


def extract(root, task, target):
    """Verify release, then merge one task and its public closure into empty target."""
    root = Path(root).absolute()
    verify(root)
    catalog = _json(root / 'catalog.json')
    entry = next((t for t in catalog['tasks'] if t['task'] == task), None)
    if entry is None:
        raise ValueError(f'Unknown task: {task}')
    # Check the combined namespace before writing. A public file must not become
    # a directory for private material, and byte-identical overlaps are allowed.
    merged = {}
    for archive_name, public in ((entry['public_archive'], True), (entry['bank_archive'], False)):
        with zipfile.ZipFile(_file(root, archive_name)) as z:
            for name, info in _zip_members(z).items():
                if not public and not name.startswith(entry['path'] + '/'):
                    continue
                folded = name.casefold()
                if folded in merged:
                    prior_archive, prior_name = merged[folded]
                    if prior_name != name:
                        raise ValueError('Cross-archive case collision')
                    with z.open(info) as current, zipfile.ZipFile(root / prior_archive) as previous:
                        with previous.open(prior_name) as old:
                            if _hash_stream(current) != _hash_stream(old):
                                raise ValueError(f'Conflicting extraction overlap: {name}')
                else:
                    merged[folded] = (archive_name, name)
    if 'release-extract.json' in merged:
        raise ValueError('Reserved extraction completion marker in payload')
    for name in merged:
        if any(str(p) in merged for p in PurePosixPath(name).parents if str(p) != '.'):
            raise ValueError(f'Cross-archive file/directory collision: {name}')
    target = Path(target).absolute()
    if target == root or root.is_relative_to(target) or target.is_relative_to(root):
        raise ValueError('Extraction target cannot contain the release')
    if _linked(target) or (target.exists() and any(target.iterdir())):
        raise ValueError('Extraction target must be empty and non-link')
    # Reject linked ancestors before creating or writing any payload.
    _unlinked_ancestors(target)
    target.mkdir(parents=True, exist_ok=True)
    written = {}
    for archive_name, public in ((entry['public_archive'], True), (entry['bank_archive'], False)):
        with zipfile.ZipFile(_file(root, archive_name)) as z:
            members = _zip_members(z)
            for name, info in members.items():
                if not public and not name.startswith(entry['path'] + '/'):
                    continue
                destination = target / name
                if name.casefold() in written:
                    if name != written[name.casefold()]:
                        raise ValueError('Extraction case collision')
                    with z.open(info) as src:
                        if _hash_stream(src) != _record(destination):
                            raise ValueError(f'Conflicting extraction overlap: {name}')
                    continue
                destination.parent.mkdir(parents=True, exist_ok=True)
                with z.open(info) as src, destination.open('xb') as dst:
                    shutil.copyfileobj(src, dst, 1024 * 1024)
                written[name.casefold()] = name
    for name, expected in entry['files'].items():
        if _record(_file(target, f'{entry["path"]}/{name}')) != expected:
            raise ValueError(f'Extracted task asset mismatch: {name}')
    _write_json(target / 'RELEASE-EXTRACT.json', {'release_id': catalog['release_id'], 'task': task, 'complete': True})
    return {'task': task, 'files': len(written), 'target': str(target)}


def main(argv=None):
    parser = argparse.ArgumentParser(description='Inspect, verify or extract a frozen CAE-OJ-Bench release.')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('list'); commands.add_parser('verify')
    sub = commands.add_parser('build'); sub.add_argument('--plan', type=Path, required=True); sub.add_argument('--output', type=Path, required=True)
    sub = commands.add_parser('extract'); sub.add_argument('task'); sub.add_argument('target', type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == 'build': result = build(args.plan, args.output)
        elif args.command == 'verify': result = verify(args.root)
        elif args.command == 'extract': result = extract(args.root, args.task, args.target)
        else:
            result = [{k: t[k] for k in ('task', 'chapter', 'title', 'profile', 'limitations')} for t in _json(_file(args.root, 'catalog.json'))['tasks']]
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        parser.exit(1, f'Release operation failed: {exc}\n')


if __name__ == '__main__':
    main()
