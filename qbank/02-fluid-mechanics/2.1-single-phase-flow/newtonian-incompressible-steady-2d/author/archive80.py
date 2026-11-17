"""Archive completed raw solver directories; keep an exact per-file inventory."""
from pathlib import Path
import argparse,concurrent.futures,hashlib,json,tarfile


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def archive(root,output,name,folders):
    files={};excluded=[];target=output/(name+'.tar.gz')
    with tarfile.open(target,'w:gz',compresslevel=6) as tar:
        paths=[p for folder in folders for p in (root/folder).rglob('*')]
        for p in sorted(paths):
            if p.is_symlink():
                if 'dynamicCode' not in p.parts:raise ValueError('Unexpected numerical payload link: '+str(p))
                excluded.append(dict(path=p.relative_to(root).as_posix(),reason='build-cache symlink; not numerical payload'));continue
            if not p.is_file():continue
            rel=p.relative_to(root).as_posix();files[rel]=dict(size_bytes=p.stat().st_size,sha256=digest(p));tar.add(p,arcname=rel,recursive=False)
    return dict(kind='raw',path=target.name,size_bytes=target.stat().st_size,sha256=digest(target),files=files,excluded=excluded)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('output',type=Path);p.add_argument('--extra',nargs='+');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        jobs=[('raw-extensions',a.extra)] if a.extra else [('raw-lethe',['runs']),('raw-openfoam',['openfoam'])]
        fs=[pool.submit(archive,a.root,a.output,name,folders) for name,folders in jobs]
        records=[f.result() for f in fs]
    inventory=a.root/'evidence/raw-inventory.json'
    if a.extra:
        old=json.loads(inventory.read_text());assert not {r['path'] for r in old}&{r['path'] for r in records};records=old+records
    inventory.write_text(json.dumps(records,indent=2)+'\n')
    print(json.dumps([{k:v for k,v in r.items() if k not in ('files','excluded')} for r in records]))
