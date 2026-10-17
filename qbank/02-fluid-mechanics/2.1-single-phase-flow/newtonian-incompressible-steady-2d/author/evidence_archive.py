"""Pack, fetch and verify this task's non-consumer maintenance evidence.

This is not a case-pool extension. Downloads reuse the existing HubStore and
require an immutable commit; raw solver archives are retained without extraction.
"""
import argparse
import gzip
import json
import os
from pathlib import Path
import re
import shutil
import tarfile
import tempfile

from caeoj_tools import data_pool as pool

INDEX = Path(__file__).parent/'data-evidence/archive-index.json'
INVENTORY = '.evidence-inventory.json'
RECEIPT = '.evidence-receipt.json'


def entry(path):
    return dict(size_bytes=path.stat().st_size, sha256=pool.digest(path))


def check_file(path, expected):
    if not path.is_file() or path.is_symlink() or entry(path) != {
            k: expected[k] for k in ('size_bytes', 'sha256')}:
        raise ValueError(f'Evidence size/SHA-256 mismatch: {path}')


def inventory_files(manifest):
    if manifest.get('schema_version') != 1 or not manifest.get('files'):
        raise ValueError('Invalid evidence inventory')
    files = manifest['files']
    seen = set()
    for name, record in files.items():
        pool.relative(name)
        if name in (INVENTORY, RECEIPT) or name.startswith('raw/'):
            raise ValueError('Reserved evidence path')
        if name.casefold() in seen:
            raise ValueError('Case-insensitive evidence path collision')
        seen.add(name.casefold())
        if type(record.get('size_bytes')) is not int or record['size_bytes'] < 0:
            raise ValueError('Invalid evidence size')
        if not re.fullmatch('[a-f0-9]{64}', record.get('sha256', '')):
            raise ValueError('Invalid evidence digest')
    return files


def pack(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.is_relative_to(source):
        raise ValueError('Archive output must be outside its source')
    output.mkdir(parents=True, exist_ok=False)
    files = {}
    for path in sorted(source.rglob('*')):
        if path.is_symlink():
            raise ValueError('Evidence source must not contain links')
        if path.is_file():
            files[path.relative_to(source).as_posix()] = entry(path)
    inventory = dict(schema_version=1, files=files)
    inventory_files(inventory)
    pool.write_json(output/'inventory.json', inventory)
    archive = output/'verification-evidence.tar.gz'
    with archive.open('wb') as target, gzip.GzipFile(fileobj=target, mode='wb', mtime=0, filename='') as zipped:
        with tarfile.open(fileobj=zipped, mode='w|') as tar:
            for name in files:
                info = tar.gettarinfo(str(source/name), arcname=name)
                info.uid = info.gid = info.mtime = 0
                info.uname = info.gname = ''
                info.mode = 0o644
                info.pax_headers = {}
                with (source/name).open('rb') as stream:
                    tar.addfile(info, stream)
    return dict(archive=entry(archive), inventory=entry(output/'inventory.json'), files=len(files))


def read_index(path):
    value = json.loads(Path(path).read_text(encoding='utf-8'))
    if value.get('schema_version') != 1 or not re.fullmatch('[a-f0-9]{40}', value['repository']['revision']):
        raise ValueError('Evidence index requires a fixed 40-character HF commit')
    archives = value['archives']
    if sum(a['kind'] == 'tree' for a in archives) != 1:
        raise ValueError('Exactly one structured evidence archive is required')
    paths = set()
    for a in archives:
        pool.relative(a['path'])
        if a['kind'] not in ('tree', 'raw') or a['path'] in paths:
            raise ValueError('Invalid or repeated evidence archive')
        paths.add(a['path'])
        if a['kind'] == 'tree':
            pool.relative(a['inventory']['path'])
    raw_names = [Path(a['path']).name.casefold() for a in archives if a['kind'] == 'raw']
    if len(raw_names) != len(set(raw_names)):
        raise ValueError('Raw archive filename collision')
    return value


def unpack(archive, files, destination):
    seen = set()
    with tarfile.open(archive, 'r:gz') as tar:
        for member in tar:
            name = pool.relative(member.name)
            if not member.isfile() or name not in files or name in seen:
                raise ValueError(f'Unexpected/linked/duplicate archive member: {name}')
            if member.size != files[name]['size_bytes']:
                raise ValueError(f'Archive member size mismatch: {name}')
            seen.add(name)
            target = pool.within(destination, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            with tar.extractfile(member) as source, target.open('wb') as output:
                shutil.copyfileobj(source, output)
            check_file(target, files[name])
    if seen != set(files):
        raise ValueError('Evidence archive is incomplete')


def verify(index_path, destination):
    index_path, destination = Path(index_path), Path(destination)
    index = read_index(index_path)
    if destination.is_symlink() or not (destination/RECEIPT).is_file():
        raise ValueError('Destination must be a complete, unlinked evidence assembly')
    receipt = json.loads((destination/RECEIPT).read_text(encoding='utf-8'))
    if receipt['index_sha256'] != pool.digest(index_path) or receipt['revision'] != index['repository']['revision']:
        raise ValueError('Local evidence receipt does not match this fixed index')
    tree = next(a for a in index['archives'] if a['kind'] == 'tree')
    check_file(destination/INVENTORY, tree['inventory'])
    files = inventory_files(json.loads((destination/INVENTORY).read_text(encoding='utf-8')))
    for name, record in files.items():
        check_file(pool.within(destination, name), record)
    expected = set(files) | {INVENTORY, RECEIPT}
    if receipt['include_raw']:
        for a in index['archives']:
            if a['kind'] == 'raw':
                name = 'raw/'+Path(a['path']).name
                check_file(destination/name, a)
                expected.add(name)
    paths = list(destination.rglob('*'))
    if any(p.is_symlink() for p in paths):
        raise ValueError('Local evidence contains links')
    actual = {p.relative_to(destination).as_posix() for p in paths if p.is_file()}
    if actual != expected:
        raise ValueError('Local evidence contains missing or unknown files; nothing was overwritten')
    return dict(valid=True, revision=receipt['revision'], evidence_files=len(files), include_raw=receipt['include_raw'])


def fetch(index_path, destination, *, cache_dir=None, include_raw=False, store=None):
    index_path, destination = Path(index_path), Path(destination).absolute()
    index = read_index(index_path)
    if destination.exists():
        result = verify(index_path, destination)
        if result['include_raw'] != include_raw:
            raise ValueError('Use a new destination for a different raw-archive selection')
        return result
    repository = index['repository']
    store = store or pool.HubStore(repository['repo_id'], revision=repository['revision'], cache_dir=cache_dir)
    if 'release_manifest' in index:
        release_path = Path(store.get(index['release_manifest']['path']))
        check_file(release_path, index['release_manifest'])
        release = json.loads(release_path.read_text(encoding='utf-8'))
        for key in ('schema_version', 'case_commit', 'source_git_commit', 'evidence_files', 'archives'):
            if release[key] != index[key]:
                raise ValueError(f'Fixed release manifest differs from the Git index: {key}')
    tree = next(a for a in index['archives'] if a['kind'] == 'tree')
    manifest = Path(store.get(tree['inventory']['path']))
    check_file(manifest, tree['inventory'])
    files = inventory_files(json.loads(manifest.read_text(encoding='utf-8')))
    archive = Path(store.get(tree['path']))
    check_file(archive, tree)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.evidence-', dir=destination.parent) as temporary:
        stage = Path(temporary)/'payload'
        stage.mkdir()
        unpack(archive, files, stage)
        shutil.copyfile(manifest, stage/INVENTORY)
        for a in index['archives']:
            if include_raw and a['kind'] == 'raw':
                raw = Path(store.get(a['path']))
                check_file(raw, a)
                (stage/'raw').mkdir(exist_ok=True)
                shutil.copyfile(raw, stage/'raw'/Path(a['path']).name)
        pool.write_json(stage/RECEIPT, dict(schema_version=1, index_sha256=pool.digest(index_path),
                        revision=repository['revision'], include_raw=include_raw))
        verify(index_path, stage)
        os.replace(stage, destination)
    return verify(index_path, destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    packing = sub.add_parser('pack')
    packing.add_argument('source', type=Path)
    packing.add_argument('output', type=Path)
    for name in ('fetch', 'verify'):
        p = sub.add_parser(name)
        p.add_argument('--index', type=Path, default=INDEX)
        p.add_argument('--destination', type=Path, required=True)
        if name == 'fetch':
            p.add_argument('--cache-dir', type=Path)
            p.add_argument('--include-raw', action='store_true')
    args = parser.parse_args()
    if args.command == 'pack':
        result = pack(args.source, args.output)
    elif args.command == 'fetch':
        result = fetch(args.index, args.destination, cache_dir=args.cache_dir, include_raw=args.include_raw)
    else:
        result = verify(args.index, args.destination)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
