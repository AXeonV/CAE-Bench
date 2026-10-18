"""Retrieve and verify the immutable statement source, never case data."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[4]
CACHE = ROOT / 'runs/foambench-import'
INDEX = json.loads((Path(__file__).parent / 'source-index.json').read_text(encoding='utf-8'))


def source_path(kind):
    if kind not in INDEX['files']:
        raise ValueError(kind)
    return CACHE / Path(INDEX['files'][kind]['path']).name


def read_source(kind):
    raw = source_path(kind).read_bytes()
    expected = INDEX['files'][kind]['sha256']
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError(f'{kind}: immutable source SHA256 mismatch')
    return json.loads(raw)


def fetch():
    CACHE.mkdir(parents=True, exist_ok=True)
    for kind, entry in INDEX['files'].items():
        target = source_path(kind)
        if not target.exists():
            url = f"https://raw.githubusercontent.com/NLR-Theseus/cfdllmbench/{INDEX['revision']}/{entry['path']}"
            request = urllib.request.Request(url, headers={'User-Agent': 'CAE-Bench-OJ statement importer'})
            with urllib.request.urlopen(request, timeout=60) as response:
                raw = response.read()
            if hashlib.sha256(raw).hexdigest() != entry['sha256']:
                raise ValueError(f'{kind}: remote SHA256 mismatch; cache not written')
            target.write_bytes(raw)
        read_source(kind)
        print(f'{kind}: fixed revision and SHA256 verified')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch', action='store_true', help='Download missing fixed source files into ignored runs cache')
    args = parser.parse_args()
    if args.fetch:
        fetch()
    else:
        for kind in INDEX['files']:
            read_source(kind)
            print(f'{kind}: SHA256 verified')


if __name__ == '__main__':
    main()
