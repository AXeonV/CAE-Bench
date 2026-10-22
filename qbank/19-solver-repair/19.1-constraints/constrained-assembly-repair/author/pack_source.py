"""Create a deterministic, minimal buildable upstream source asset and hash it."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import tarfile

TASK = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True,
                        help='The source/ directory of the successfully prepared build context')
    args = parser.parse_args()
    destination = TASK / 'public/chrono-source.tar.gz'
    destination.parent.mkdir(exist_ok=True)
    with destination.open('wb') as raw, gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode='w') as archive:
            for path in sorted(args.source.rglob('*')):
                if not path.is_file():
                    continue
                if path.is_symlink():
                    raise ValueError('Source links are not allowed')
                info = archive.gettarinfo(str(path), path.relative_to(args.source).as_posix())
                info.uid = info.gid = info.mtime = 0
                info.uname = info.gname = ''
                info.mode = 0o644
                with path.open('rb') as stream:
                    archive.addfile(info, stream)
            info = tarfile.TarInfo('data')
            info.type = tarfile.DIRTYPE
            info.mode = 0o755
            archive.addfile(info)
    record = {'version': 1, 'files': []}
    for path in sorted((TASK / 'public').glob('*')):
        if path.is_file():
            record['files'].append({'path': path.relative_to(TASK).as_posix(),
                                    'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    (TASK / 'public-materials.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'source_bytes': destination.stat().st_size, **record}))


if __name__ == '__main__':
    main()
