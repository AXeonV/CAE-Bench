"""Refresh prose only in frozen verified public ZIPs; preserve every runtime/sample byte."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import zipfile

from caeoj_tools.assembly import runtime_materials

ROOT = Path('D:/Code/CAE-Bench-OJ')
WORK = ROOT / 'runs/prepublication-review-rc2'
STAGE = WORK / 'release-stage'
PUBLIC = WORK / 'refreshed-public'
PUBLIC.mkdir(exist_ok=True)
RELEASE = Path('C:/Users/Jim Zhou/CAE-OJ-Releases/caeoj-qbank-20261023-rc2')
plan = json.loads((ROOT / 'runs/release-assembly-rc2/plan.json').read_text(encoding='utf-8'))
reports = []
for task in plan['tasks']:
    original = Path(task['source_root']) / task['task_path']
    target = STAGE / task['task_path']
    target.mkdir(parents=True, exist_ok=True)
    for name in ['instruction.md', 'DATA.md', 'judge-config.json', 'harbor/task.toml']:
        source = ROOT / task['task_path'] / name
        if source.is_file():
            p = target / name
            p.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, p)
    for name in ['data-manifest.json', '.data-assembly.json']:
        shutil.copyfile(original / name, target / name)
    receipt = json.loads((original / '.data-assembly.json').read_text(encoding='utf-8'))
    for name in receipt['files']:
        p = target / name
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.exists():
            assert os.path.samefile(original / name, p)
        else:
            os.link(original / name, p)
    current_runtime, _ = runtime_materials({task['task']: target}, STAGE)
    archive = RELEASE / 'public' / f"{task['task']}-agent.zip"
    output = PUBLIC / archive.name
    changes = {}
    checked = 0
    with zipfile.ZipFile(archive) as old:
        manifest = json.loads(old.read('MANIFEST.json'))
        assert len(old.namelist()) == len(set(old.namelist()))
        assert set(old.namelist()) == set(manifest['files']) | {'MANIFEST.json'}
        for name, expected in current_runtime.items():
            assert old.read(name) == expected, (task['task'], name, 'runtime changed')
        for name in ['instruction.md', 'DATA.md']:
            key = task['task_path'] + '/' + name
            value = (target / name).read_bytes()
            if value != old.read(key):
                changes[key] = value
        with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as new:
            for info in old.infolist():
                if info.filename == 'MANIFEST.json':
                    continue
                h = hashlib.sha256()
                with old.open(info) as src, new.open(info, 'w', force_zip64=True) as dst:
                    # Stream immutable data; verify the source manifest even when replacing prose.
                    while block := src.read(1024 * 1024):
                        h.update(block)
                        if info.filename not in changes:
                            dst.write(block)
                    if info.filename in changes:
                        dst.write(changes[info.filename])
                assert h.hexdigest() == manifest['files'][info.filename]
                checked += 1
            for name, value in changes.items():
                manifest['files'][name] = hashlib.sha256(value).hexdigest()
            new.writestr('MANIFEST.json', (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    task['source_root'] = str(STAGE)
    task['public_archive'] = str(output)
    task['public_archive_sha256'] = hashlib.file_digest(output.open('rb'), 'sha256').hexdigest()
    reports.append({'task': task['task'], 'changed_members': sorted(changes),
                    'original_members_verified': checked, 'runtime_files_equal': len(current_runtime),
                    'all_other_uncompressed_bytes_unchanged': True,
                    'public_archive_sha256': task['public_archive_sha256']})
    (WORK / 'refresh-report.json').write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding='utf-8')
    print(task['task'], 'refreshed', len(changes), flush=True)
plan.update(release_id='caeoj-qbank-20261023-rc3', stage='reviewed_rc')
plan['capabilities']['statement_review_completed'] = True
plan['release_notes'] = [n.replace('题面与case联合审查、参考资格、资源校准及异机验收仍有待办', '参考资格、资源校准及异机验收仍有待办') for n in plan['release_notes']]
plan['release_notes'] += [
    '本版完成82题独立设计与考生材料审阅、全部743输入角色的数据契约审计；78题格式样例角色及24题提交入口已对齐。',
    '17题仍有未覆盖的合法输入分支；14题压力相对误差尺度的规范基准敏感性仍为设计待决。参考数值、预算及异机验收未因此获得认证。'
]
(WORK / 'reviewed-plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding='utf-8')
print('COMPLETE', len(reports), flush=True)
