"""CLI for author-side data pools; also registered under caeoj-maint data."""
import argparse
import json
import tempfile
import shutil
from pathlib import Path

from . import data_pool as pool
from .author import PROJECT_ROOT
from .task_paths import task_directory


def configure(parser):
    commands = parser.add_subparsers(dest='data_command', required=True)
    pack = commands.add_parser('pack', help='Stage generated directories as a reusable pool')
    pack.add_argument('--task', required=True)
    pack.add_argument('--source', type=Path, help='Generated task directory; defaults to the canonical task')
    pack.add_argument('--output', type=Path, required=True, help='Empty staging bundle directory')
    pack.add_argument('--task-id', help='Required for tasks without a data manifest')
    pack.add_argument('--repo-id', default='jimzhouzzy2006/CAE-Bench-OJ')
    pack.add_argument('--shard-mib',type=int,help='Pack immutable TAR transport, target MiB per shard')
    upload = commands.add_parser('upload', help='Validate and atomically merge a bundle into HF')
    upload.add_argument('--bundle', type=Path, required=True)
    upload.add_argument('--update', action='store_true')
    upload.add_argument('--revision', default='main')
    for command in ('select', 'fetch', 'assemble', 'verify'):
        p = commands.add_parser(command)
        p.add_argument('--task', required=True)
        p.add_argument('--manifest', type=Path, help='Selection path; defaults to the task data-manifest.json')
        if command != 'verify':
            p.add_argument('--source-dir', type=Path, help='Offline repository-shaped pool tree')
            p.add_argument('--revision', default='main')
            p.add_argument('--cache-dir', type=Path)
        if command == 'select':
            p.add_argument('--case', action='append', default=[], help='[local-name=]case-id; repeatable')
            p.add_argument('--sample', action='append', default=[], help='[local-name=]case-id; repeatable')
            p.add_argument('--output', type=Path, help='Write a separate selection instead of replacing the manifest')
            p.add_argument('--allow-incomplete', action='store_true', help='Development selection only; strict consumption still refuses incomplete data')
        elif command in ('fetch', 'assemble'):
            p.add_argument('--cases', nargs='*', help='Only these local case names; empty means no cases')
            p.add_argument('--samples', nargs='*', help='Only these local sample names; empty means no samples')
            if command == 'assemble':
                p.add_argument('--update', action='store_true')
        else:
            p.add_argument('--strict', action='store_true')
            p.add_argument('--samples-only', action='store_true')
    for command in commands.choices.values():
        command.add_argument('--root',type=Path,default=PROJECT_ROOT,help='Author workspace root (also supports non-editable installations)')


def _run(args):
    if args.data_command == 'upload':
        return pool.upload(args.bundle, update=args.update, revision=args.revision)
    root=args.root.resolve()
    task = task_directory(args.task, root)
    selection = getattr(args, 'manifest', None) or task/'data-manifest.json'
    if args.data_command == 'pack':
        if selection.exists():
            value = pool.manifest(selection)
            if args.task_id and args.task_id != value['task_id']:
                raise pool.PoolError('Cannot reassign an existing task ID during pack')
        else:
            if not args.task_id:
                raise pool.PoolError('New tasks require an explicitly assigned --task-id')
            for path in (root/'qbank').glob('**/data-manifest.json'):
                if pool.checked_json(path).get('task_id') == args.task_id:
                    raise pool.PoolError('Task ID already assigned: ' + args.task_id)
            value = {'schema_version': 4, 'task_id': args.task_id,
                     'repository': {'repo_id': args.repo_id, 'repo_type': 'dataset',
                                    'path': task.relative_to(root).as_posix()}}
        if args.shard_mib is not None:
            if not 1<=args.shard_mib<=512:raise pool.PoolError('--shard-mib must be 1..512')
            with tempfile.TemporaryDirectory(prefix='caeoj-pack-') as tmp:
                raw=Path(tmp)/'raw'
                pool.pack(args.source or task,raw,value)
                catalog=pool.shard_bundle(raw,args.output,target_bytes=args.shard_mib*1024**2)
                if (raw/'evidence').exists():shutil.copytree(raw/'evidence',args.output/'evidence')
                return {'bundle':str(args.output),'cases':catalog['case_count'],'shards':len(catalog['shards'])}
        return pool.pack(args.source or task, args.output, value)
    if args.data_command == 'verify':
        if selection != task/'data-manifest.json':
            raise pool.PoolError('Verify consumes the canonical manifest bound by the assembly receipt')
        return pool.verify(task, strict=args.strict, samples_only=args.samples_only)
    value = pool.manifest(selection)
    store = pool.LocalStore(args.source_dir) if args.source_dir else pool.HubStore(
        value['repository']['repo_id'], args.revision, args.cache_dir)
    if args.data_command == 'select':
        if not args.case and not args.sample:
            raise pool.PoolError('Select at least one --case or --sample')
        result = pool.select(value, store, args.case, args.sample, allow_incomplete=args.allow_incomplete)
        destination = args.output or selection
        pool.write_json(destination, result)
        return {'selection': str(destination), 'revision': store.revision,
                'cases': len(result['cases']), 'samples': len(result['samples'])}
    options = {'cases': args.cases, 'samples': args.samples}
    if args.data_command == 'fetch':
        result = pool.fetch(value, store, **options)
        return {k: result[k] for k in ('revision', 'scope', 'incomplete', 'overlaps', 'public_cases')} | {
            'files': len(result['files']), 'complete': not result['incomplete']}
    if selection != task/'data-manifest.json':
        raise pool.PoolError('Install the reviewed selection at task/data-manifest.json before assembly')
    return pool.assemble(task, value, store, update=args.update, **options)


def run(args):
    try:
        return _run(args)
    except (KeyError, TypeError) as exc:
        raise pool.PoolError(f'Invalid pool metadata: {exc}') from exc
    except Exception as exc:
        if type(exc).__module__.startswith(('huggingface_hub', 'httpx')):
            raise pool.PoolError(f'HF request failed: {exc}') from exc
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    configure(parser)
    args = parser.parse_args(argv)
    try:
        result = run(args)
    except (OSError, ValueError, KeyError, ImportError) as exc:
        parser.exit(2, f'Data pool error: {exc}\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get('valid', True) else 1


if __name__ == '__main__':
    raise SystemExit(main())
