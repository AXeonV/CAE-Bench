"""Unified repository data operations, dispatched by ``caeoj data``."""
import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import sys
import tempfile

from . import data_pool as pool
from . import data_lock as locks
from . import data_sources as sources


def project_root(explicit=None):
    if explicit:
        root = Path(explicit).expanduser().resolve()
    else:
        root = next((p for p in (Path.cwd(), *Path.cwd().parents)
                     if (p/'qbank').is_dir() and (p/'pyproject.toml').is_file()),
                    Path(__file__).resolve().parents[2])
    if not (root/'qbank').is_dir():
        raise pool.PoolError('Cannot locate qbank; provide --root <repository>')
    return root


def tasks(root, names=None, chapter=None):
    all_tasks = sorted(p.parent for p in (root/'qbank').glob('*/*/*/instruction.md'))
    # Keep the existing task locator's path/link checks for all consuming paths.
    from .task_paths import task_directory
    if chapter is not None:
        if not re.fullmatch(r'\d{1,2}(?:-[A-Za-z0-9-]+)?', chapter):
            raise pool.PoolError('Chapter must be a number or chapter directory name')
        normalized = chapter.zfill(2) if chapter.isdigit() else chapter
        all_tasks = [p for p in all_tasks if (p.relative_to(root/'qbank').parts[0] == normalized or
                     p.relative_to(root/'qbank').parts[0].startswith(normalized + '-'))]
    if names:
        selected = []
        for name in names:
            matches = [p for p in all_tasks if p.name == name]
            if re.fullmatch(r'caeoj-\d{6}', name):
                matches = [p for p in all_tasks if (p/'data-manifest.json').is_file() and
                           pool.manifest(p/'data-manifest.json')['task_id'] == name]
            if len(matches) != 1:
                raise pool.PoolError(f'Expected one task for {name}; found {len(matches)}')
            if matches[0] in selected:
                raise pool.PoolError('Repeated task selector: ' + name)
            selected.append(matches[0])
        all_tasks = selected
    if not all_tasks:
        raise pool.PoolError('No tasks match the selection')
    return [task_directory(p.name, root) for p in all_tasks]


def cache_root(root, args, config):
    path = Path(args.cache_dir or config.get('cache_dir') or root/'.caeoj/cache').expanduser()
    return path if path.is_absolute() else root/path


def source_configuration(args, config):
    if args.source_dir:
        if args.source:
            raise pool.PoolError('Use either --source or --source-dir')
        return {'type': 'local', 'root': str(args.source_dir.resolve())}
    name = args.source or config.get('default_source', 'hf')
    if name not in config.get('sources', {}):
        raise pool.PoolError(f'Source {name!r} is not configured; see caeoj data source list')
    return config['sources'][name]


@contextmanager
def discovery_store(value, source, revision, cache):
    """Lock creation downloads metadata only, never numerical payloads."""
    if source['type'] == 'local':
        yield pool.LocalStore(source['root'])
    elif source['type'] == 'hf':
        try:
            yield pool.HubStore(value['repository']['repo_id'], revision or 'main', cache/'hub')
        except Exception as exc:
            if type(exc).__module__.startswith(('huggingface_hub', 'httpx')):
                raise pool.PoolError(f'HF metadata lookup failed ({type(exc).__name__}); check repository access') from exc
            raise
    else:
        if revision:
            raise pool.PoolError('--revision only applies to Hugging Face lock creation')
        backend = sources.ScpTransport(source)
        with tempfile.TemporaryDirectory(prefix='caeoj-lock-') as directory:
            class MetadataStore:
                revision = 'scp'

                def get(self, name):
                    path = pool.within(directory, name)
                    if not path.exists():
                        path.parent.mkdir(parents=True, exist_ok=True)
                        backend.retrieve(name, path)
                        if path.stat().st_size > 16 * 1024**2:
                            raise pool.PoolError('Case metadata exceeds 16 MiB')
                    return path
            yield MetadataStore()


def inventory(task, kinds, cache):
    row = {'task': task.name, 'chapter': task.parents[1].name}
    if not (task/'data-manifest.json').is_file():
        return {**row, 'status': 'unregistered', 'size_bytes': None}
    value = pool.manifest(task/'data-manifest.json')
    row['task_id'] = value['task_id']
    if not (task/locks.LOCK).is_file():
        return {**row, 'status': 'unlocked', 'size_bytes': None,
                'hint': f'caeoj data lock --task {task.name} --source <source>'}
    lock = locks.read(task, value)
    planned = locks.plan(task, value, lock, kinds)
    local, objects = 0, {}
    for target, entry in planned['files'].items():
        if pool.matches(pool.within(task, target), entry):
            local += 1
        key = entry['sha256']
        objects.setdefault(key, entry)
    needed = {}
    for target, entry in planned['files'].items():
        if not pool.matches(pool.within(task, target), entry) and not pool.matches(pool.within(cache, 'objects/'+entry['sha256']), entry):
            # One physical source can appear as both a test and sample.
            if not any(pool.matches(pool.within(task, t), e) for t, e in planned['files'].items() if e['sha256'] == entry['sha256']):
                needed[entry['sha256']] = entry
    status = ('incomplete' if planned['incomplete'] else
              'present' if local == len(planned['files']) else 'missing' if local == 0 else 'partial')
    receipt_path = task/pool.RECEIPT
    receipt_bound = False
    if receipt_path.is_file():
        receipt = pool.checked_json(receipt_path)
        receipt_bound = (receipt.get('selection_sha256') == locks.selection_digest(value) and
                         receipt.get('data_lock_sha256') == locks.selection_digest(lock))
    if status == 'present' and not receipt_bound:
        status = 'needs-assembly'
    return {**row, 'status': status, 'release': lock['release'], 'hf_revision': lock['hf_revision'],
            'files': len(planned['files']), 'present_files': local,
            'size_bytes': sum(e['size_bytes'] for e in planned['files'].values()),
            'unique_size_bytes': sum(e['size_bytes'] for e in objects.values()),
            'download_bytes': sum(e['size_bytes'] for e in needed.values()),
            'receipt_bound': receipt_bound}


def parser():
    result = argparse.ArgumentParser(prog='caeoj data', description=__doc__)
    commands = result.add_subparsers(dest='command', required=True)
    for command in ('list', 'lock', 'fetch', 'verify'):
        p = commands.add_parser(command)
        p.add_argument('--root', type=Path, help='Repository root (also discovered from cwd)')
        p.add_argument('--config', type=Path, help='User data source TOML')
        p.add_argument('--cache-dir', type=Path)
        selection = p.add_mutually_exclusive_group()
        selection.add_argument('--task', '--problem', dest='tasks', action='append', help='Task slug or stable ID; repeatable')
        selection.add_argument('--chapter')
        if command != 'lock':
            p.add_argument('--kind', action='append', choices=['all', *locks.KINDS])
        if command in ('lock', 'fetch'):
            p.add_argument('--source', help='Configured local/SCP/HF source name')
            p.add_argument('--source-dir', type=Path, help='Use a repository-shaped local pool')
            p.add_argument('--update', action='store_true', help='Replace reviewed metadata or differing managed payloads')
        if command == 'lock':
            p.add_argument('--revision', help='HF branch/tag/commit; only this command resolves a moving revision')
        elif command == 'fetch':
            p.add_argument('--dry-run', action='store_true', help='Offline plan; no downloads or writes')
            p.add_argument('--retries', type=int, default=3)
        elif command == 'verify':
            p.add_argument('--strict', action='store_true')
    p = commands.add_parser('source')
    p.add_argument('action', choices=['list'])
    p.add_argument('--config', type=Path)
    return result


def run(args):
    config = sources.configuration(args.config)
    if args.command == 'source':
        return {'sources': config.get('sources', {}), 'default_source': config.get('default_source', 'hf')}, 0
    root = project_root(args.root)
    if args.command in ('lock', 'fetch') and not (args.tasks or args.chapter):
        raise pool.PoolError('Choose --task or --chapter before preparing data')
    if args.command == 'fetch' and not 1 <= args.retries <= 10:
        raise pool.PoolError('--retries must be between 1 and 10')
    if args.command != 'lock':
        locks.selected_kinds(args.kind)
    selected = tasks(root, args.tasks, args.chapter)
    cache = cache_root(root, args, config)
    reports, failures = [], []
    for task in selected:
        try:
            if args.command == 'list' or (args.command == 'fetch' and args.dry_run):
                report = inventory(task, args.kind, cache)
                if args.command == 'fetch' and report['status'] in ('unregistered', 'unlocked', 'incomplete'):
                    report['actionable'] = False
                    failures.append({'task': task.name, 'error': 'Data is not published and locked'})
                reports.append(report)
                continue
            value = pool.manifest(task/'data-manifest.json')
            if args.command == 'lock':
                source = source_configuration(args, config)
                with discovery_store(value, source, args.revision, cache) as store:
                    lock = locks.create(value, store)
                path = task/locks.LOCK
                if path.exists() and pool.checked_json(path) != lock and not args.update:
                    raise pool.PoolError('Data lock differs; review before using --update')
                # Validate before publishing the generated file.
                pool.write_json(path, lock)
                reports.append({'task': task.name, 'lock': str(path), 'status': lock['status'],
                                'release': lock['release'], 'hf_revision': lock['hf_revision']})
                if lock['status'] != 'published':
                    failures.append({'task': task.name, 'error': 'Selected data contains incomplete groups'})
                continue
            lock = locks.read(task, value)
            if args.command == 'verify':
                report = pool.verify(task, strict=args.strict, kinds=args.kind)
                reports.append({'task': task.name, **report})
                if not report['valid']:
                    failures.append({'task': task.name, 'error': '; '.join(report['errors'])})
                continue
            if locks.plan(task, value, lock, args.kind)['incomplete']:
                raise pool.PoolError('Data has not been completely published; regenerate and review the lock')
            before = inventory(task, args.kind, cache)
            print(json.dumps({'event': 'plan', **before}, ensure_ascii=False), file=sys.stderr)
            source = source_configuration(args, config)
            backend = sources.transport(source, value, lock, cache)
            with locks.metadata_store(value, lock) as metadata:
                planned = pool.plan(value, metadata, kinds=args.kind)
                store = sources.VerifiedStore(value, lock, metadata, planned, backend, cache, task, args.retries)
                result = pool.assemble(task, value, store, update=args.update, kinds=args.kind or ['all'])
                requested = pool.verify(task, strict=True, kinds=args.kind)
                after = inventory(task, ['all'], cache)
                complete = after['status'] == 'present'
                if complete:
                    pool.verify(task, strict=True)
                reports.append({'task': task.name, **result, 'complete': complete,
                                'requested_valid': requested['valid'], 'downloaded_files': store.downloaded})
        except (OSError, ValueError, RuntimeError, ImportError, KeyError, TypeError) as exc:
            message = str(exc)
            if isinstance(exc, FileNotFoundError):
                message = f'Missing data metadata or local file; run caeoj data list --task {task.name}'
            failures.append({'task': task.name, 'error': message,
                             'hint': f'caeoj data fetch --task {task.name}'})
    code = (1 if args.command == 'verify' and not args.strict else 2) if failures else 0
    return {'tasks': reports, 'failures': failures, 'valid': not failures}, code


def main(argv=None):
    p = parser()
    args = p.parse_args(argv)
    try:
        report, code = run(args)
    except (OSError, ValueError, ImportError, KeyError, TypeError) as exc:
        report, code = {'valid': False, 'error': str(exc)}, 2
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
