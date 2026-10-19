#!/usr/bin/env python3
"""Explicit DaRUS selection, bounded preparation, verification and assembly."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'src'))


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    commands = p.add_subparsers(dest='command', required=True)
    listing = commands.add_parser('list', help='Offline pinned source inventory')
    listing.add_argument('--task')
    plan = commands.add_parser('plan', help='Freeze explicit source selections without network')
    plan.add_argument('--spec', type=Path, required=True, help='JSON list of entries or {entries:[...]}')
    plan.add_argument('--output', type=Path, required=True)
    for name in ('inspect', 'prepare'):
        cmd = commands.add_parser(name)
        cmd.add_argument('--cache-root', type=Path, default=ROOT/'runs/pdebench-direct/cache')
        cmd.add_argument('--network-mb', type=float, default=64, help='Response body upper budget, decimal MB; headers/TLS excluded')
        cmd.add_argument('--disk-mb', type=float, default=2048)
        cmd.add_argument('--timeout', type=float, default=30)
        cmd.add_argument('--source-dir', type=Path, help='Optional full local source, size/MD5 verified')
        if name == 'inspect':
            cmd.add_argument('--task', required=True)
            cmd.add_argument('--source-id', required=True, type=int)
            cmd.add_argument('--index', type=int, default=0)
        else:
            cmd.add_argument('--selection', type=Path, required=True)
            cmd.add_argument('--workspace', type=Path, required=True)
    for name in ('verify', 'assemble'):
        cmd = commands.add_parser(name)
        cmd.add_argument('--selection', type=Path, required=True)
        cmd.add_argument('--workspace', type=Path, required=True)
    return p


def main(argv=None):
    p = parser(); args = p.parse_args(argv)
    from utils.PDEBench.selection import CATALOG, make_selection
    from utils.PDEBench.models import BY_TASK, MODELS, source_files
    catalog = json.loads(CATALOG.read_text())
    try:
        if args.command == 'list':
            models = [BY_TASK[args.task]] if args.task else MODELS
            result = {'dataset': catalog['dataset'], 'version': catalog['version'],
                      'tasks': [{'task': m.task, 'sources': source_files(m, catalog)} for m in models]}
        elif args.command == 'plan':
            spec = json.loads(args.spec.read_text())
            result = make_selection(spec['entries'] if isinstance(spec, dict) else spec)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n')
        else:
            from utils.PDEBench.pipeline import execute
            result = execute(args)
        print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
        return 2 if result.get('status') in ('blocked', 'failed') else 0
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        p.exit(1, f'PDEBench {args.command} failed: {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
