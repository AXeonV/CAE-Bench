"""Install a verified direct-source workspace into existing question directories."""
import json
from pathlib import Path
import shutil
import tempfile

from caeoj_tools.public_examples import BINDING, INSTALLATION, verify_public_examples, verify_source_installation
from caeoj_tools.task_paths import task_directory
from .selection import contract_hash, identity
from .storage import PreparationError, atomic_json, digest

PAYLOAD = ('cases', 'reference', 'samples', BINDING.as_posix(), INSTALLATION.as_posix())


def verify_installed(selection, root):
    result = []
    for slug in sorted({e['task'] for e in selection['entries']}):
        task = task_directory(slug, root)
        receipt = verify_source_installation(task)
        if receipt is None or receipt['selection_sha256'] != selection['sha256']:
            raise PreparationError('Installed selection identity mismatch')
        if receipt['contract_sha256'] != contract_hash(task):
            raise PreparationError('Installed question contract has changed')
        public = verify_public_examples(task)
        expected = [{'case': link['case'], 'sample': sample,
                     'case_id': identity(next(e for e in selection['entries'] if e['task'] == slug and e['role'] == 'case' and e['id'] == link['case']))}
                    for sample, link in selection['examples'].get(slug, {}).items()]
        if public != expected:
            raise PreparationError('Installed public identities differ from selection')
        cases = [e['id'] for e in selection['entries'] if e['task'] == slug and e['role'] == 'case']
        if sorted(cases) != receipt['authorization']['cases']:
            raise PreparationError('Installed case coverage differs from selection')
        result.append({'task': slug, 'cases': len(cases), 'public_cases': public})
    return {'status': 'installed_verified', 'selection_sha256': selection['sha256'], 'tasks': result,
            'case_count': sum(r['cases'] for r in result)}


def install(workspace, selection, root, *, replace=False):
    from .pipeline import verify, cache_lock
    workspace, root = Path(workspace).resolve(), Path(root).resolve()
    if root == workspace or root.is_relative_to(workspace):
        raise PreparationError('Install target must be separate from preparation workspace')
    report = verify(workspace, selection)
    if not report['assembly_ready']:
        raise PreparationError('Blocked workspace cannot be installed')
    state = json.loads((workspace/'workspace.json').read_text())
    tasks = sorted({e['task'] for e in selection['entries']})
    for slug in tasks:
        source, target = task_directory(slug, workspace), task_directory(slug, root)
        for name in ('instruction.md', 'DATA.md', 'author/grading-template.json', 'judge-config.json'):
            if (source/name).read_bytes() != (target/name).read_bytes():
                raise PreparationError('Install target definitions differ from frozen workspace')
        if (target/'data-manifest.json').exists():
            raise PreparationError('Remove/reconcile HF selection before installing direct-source data')
        if any((target/p).is_symlink() for p in PAYLOAD):
            raise PreparationError('Installed data must not be a link')
        if any((target/p).exists() for p in PAYLOAD) and not replace:
            raise PreparationError('Existing task data requires explicit --replace; it will be backed up')
    required = sum(p.stat().st_size for slug in tasks for name in PAYLOAD[:-1]
                   for p in ([task_directory(slug, workspace)/name] if (task_directory(slug, workspace)/name).is_file()
                             else (task_directory(slug, workspace)/name).rglob('*')) if p.is_file())
    if required + 128*1024**2 > shutil.disk_usage(root).free:
        raise PreparationError('Insufficient free disk space for installed payload and metadata')
    with cache_lock(root/'runs/pdebench-install'):
        backup = Path(tempfile.mkdtemp(prefix='backup-', dir=root/'runs/pdebench-install'))
        completed = []
        try:
            for slug in tasks:
                source, target = task_directory(slug, workspace), task_directory(slug, root)
                saved = backup/slug; saved.mkdir()
                touched = set()
                completed.append((target, saved, touched))
                old_receipt = target/INSTALLATION
                if old_receipt.exists():
                    destination = saved/INSTALLATION; destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(old_receipt, destination)
                touched.add(INSTALLATION.as_posix())
                # The guard precedes every data move, including removal of the old binding.
                atomic_json(target/INSTALLATION, {'status': 'installing', 'selection_sha256': selection['sha256']})
                for name in PAYLOAD[:-1]:
                    old = target/name
                    if old.exists():
                        destination = saved/name; destination.parent.mkdir(parents=True, exist_ok=True)
                        old.rename(destination)
                        touched.add(name)
                for name in PAYLOAD[:-1]:
                    src, dest = source/name, target/name
                    if not src.exists(): continue
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    touched.add(name)
                    if src.is_dir(): shutil.copytree(src, dest)
                    else: shutil.copyfile(src, dest)
                files = {p.relative_to(target).as_posix(): digest(p)
                         for name in PAYLOAD[:-1] for p in ([target/name] if (target/name).is_file() else (target/name).rglob('*'))
                         if p.is_file()}
                authorization = state['public_examples'].get(slug, {
                    'cases': sorted(e['id'] for e in selection['entries'] if e['task'] == slug and e['role'] == 'case'),
                    'samples': sorted(e['id'] for e in selection['entries'] if e['task'] == slug and e['role'] == 'sample'),
                    'public_cases': []})
                atomic_json(target/INSTALLATION, {'schema_version': 1, 'task': slug,
                    'selection_sha256': selection['sha256'], 'contract_sha256': contract_hash(target),
                    'authorization': authorization, 'files': files})
                verify_source_installation(target)
                verify_public_examples(target)
            result = verify_installed(selection, root)
        except BaseException:
            for target, saved, touched in reversed(completed):
                for name in sorted(touched - {INSTALLATION.as_posix()}):
                    p = target/name
                    if p.is_dir(): shutil.rmtree(p)
                    else: p.unlink(missing_ok=True)
                    if (saved/name).exists():
                        p.parent.mkdir(parents=True, exist_ok=True); (saved/name).rename(p)
                if INSTALLATION.as_posix() in touched:
                    marker = target/INSTALLATION
                    if (saved/INSTALLATION).exists(): (saved/INSTALLATION).replace(marker)
                    else: marker.unlink(missing_ok=True)
            raise
        result['backup_directory'] = str(backup)
        atomic_json(workspace/'installation.json', result)
        return result
