"""Fetch and pin the actual upstream source; never use a moving branch."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile
import urllib.request

BASE = 'c6acd4e5a199f56052ba74b8e9d735a2157ba613'
FIX = '23c679076915d893ccd949fd0f8a2af0fc906982'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    records = []
    for role, sha in [('base', BASE), ('upstream-fix', FIX)]:
        url = f'https://codeload.github.com/projectchrono/chrono/tar.gz/{sha}'
        target = args.output / f'{role}.tar.gz'
        if not target.exists():
            partial = target.with_suffix('.partial')
            with urllib.request.urlopen(url, timeout=120) as source, partial.open('wb') as output:
                while block := source.read(1024 * 1024):
                    output.write(block)
            partial.replace(target)
        destination = args.output / role
        if not destination.exists():
            with tarfile.open(target) as archive:
                members = archive.getmembers()
                prefix = f'chrono-{sha}/'
                destination.mkdir()
                for item in members:
                    if not item.name.startswith(prefix):
                        if item.name == prefix[:-1]:
                            continue
                        raise ValueError('Unexpected archive prefix: ' + item.name)
                    relative = item.name[len(prefix):]
                    if not relative:
                        continue
                    item.name = relative
                    archive.extract(item, destination, filter='data')
        records.append({'role': role, 'commit': sha, 'url': url,
                        'archive_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                        'archive_bytes': target.stat().st_size})
    (args.output / 'sources.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(records))


if __name__ == '__main__':
    main()
