"""Create a portable text-only authoring snapshot, without reference payloads."""
import argparse
import gzip
import hashlib
import io
import json
import tarfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    index=json.loads((HERE/'index.json').read_text(encoding='utf8'))
    files=[p for p in HERE.iterdir() if p.suffix in ('.py','.md','.json')]
    for row in index['questions']:
        p=ROOT/row['path'];files.append(p);r=json.loads(p.read_text(encoding='utf8'))
        files.extend(ROOT/r['question_path']/name for name in ('instruction.md','DATA.md','author/grading-template.json'))
    files.append(ROOT/'docs/CONTRACT.md');files=sorted(set(files));args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('wb') as raw,gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0) as gz,tarfile.open(fileobj=gz,mode='w',format=tarfile.PAX_FORMAT) as tf:
        for p in files:
            data=p.read_text(encoding='utf8').encode();info=tarfile.TarInfo(p.relative_to(ROOT).as_posix());info.size=len(data);tf.addfile(info,io.BytesIO(data))
    print(json.dumps({'files':len(files),'bytes':args.output.stat().st_size,'sha256':hashlib.sha256(args.output.read_bytes()).hexdigest()}))

if __name__=='__main__':main()
