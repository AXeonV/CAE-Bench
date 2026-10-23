"""Pack the genuine upstream minimal build closure and mandatory copyright."""
import gzip,hashlib,json,tarfile
from prepare_source import TASK,SOURCE

def main():
    declaration=json.loads((TASK/'author/data-evidence/source-closure-plan.json').read_text())
    paths=sorted(set(declaration['files'])|{'COPYRIGHT'})
    target=TASK/'public/opensees-source.tar.gz';target.parent.mkdir(exist_ok=True)
    records=[]
    with target.open('wb') as raw, gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0,compresslevel=6) as compressed, tarfile.open(fileobj=compressed,mode='w') as tar:
        for rel in paths:
            source=SOURCE/rel
            info=tar.gettarinfo(str(source),arcname=rel);info.uid=info.gid=0;info.uname=info.gname='root';info.mode=0o644;info.mtime=0
            with source.open('rb') as stream:tar.addfile(info,stream)
            records.append({'file':rel,'sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
    (TASK/'author/data-evidence/source-closure.json').write_text(json.dumps({'files':records,'count':len(records),'archive_sha256':hashlib.sha256(target.read_bytes()).hexdigest()},indent=2)+'\n',encoding='utf-8',newline='\n')
    print(target,target.stat().st_size)
if __name__=='__main__':main()
