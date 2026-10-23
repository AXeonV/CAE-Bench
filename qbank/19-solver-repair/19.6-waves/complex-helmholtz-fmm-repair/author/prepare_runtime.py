"""Prepare exact source assets and reproducible native/reference build contexts."""
from pathlib import Path
import argparse,hashlib,json,shutil,tarfile,urllib.request

TASK=Path(__file__).resolve().parents[1]
BASE='84345ee9ee314c85750f045c7ad38090f5ea5f26'
FIXED='2a353ef7cf73883fd761b400691dfb82cd7f614f'
ARCHIVES={
 'base':('https://codeload.github.com/bempp/bempp-cl/tar.gz/'+BASE,'c565f0caf31d5895c411a852f0c9deba4e73870e64d318dcc38a925d23e6e15f'),
 'fixed':('https://codeload.github.com/bempp/bempp-cl/tar.gz/'+FIXED,'cce9fd520ac783392c5128741211840334b3d293fd9ba6c350b8b84574bc22f2'),
 'exafmm-v0.1.0':('https://codeload.github.com/exafmm/exafmm-t/tar.gz/refs/tags/v0.1.0','87670c9ebd23fddd805848dd1846981bc76f8a454864b6a893a0a0c14c85a12c')}
FILES=('exafmm.py','fmm_assembler.py','helpers.py')


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(work):
    work.mkdir(parents=True,exist_ok=True);evidence={}
    for kind,(url,sha) in ARCHIVES.items():
        path=work/(kind+'.tar.gz')
        if not path.exists():urllib.request.urlretrieve(url,path)
        if digest(path)!=sha:raise ValueError('Pinned archive mismatch: '+kind)
        with tarfile.open(path) as archive:
            if any(m.issym() or m.islnk() for m in archive):raise ValueError('Unexpected source link')
            manifest={m.name.split('/',1)[1]:hashlib.sha256(archive.extractfile(m).read()).hexdigest() for m in archive if m.isfile()}
        evidence[kind]={'url':url,'sha256':sha,'files':len(manifest),'manifest':manifest}
    context=work/'production-context';context.mkdir(exist_ok=True)
    for src,dst in [(work/'base.tar.gz',context/'bempp.tar.gz'),(work/'exafmm-v0.1.0.tar.gz',context/'exafmm.tar.gz'),(TASK/'author/runtime.Dockerfile',context/'Dockerfile'),(TASK/'public/CMakeLists.txt',context/'CMakeLists.txt'),(TASK/'public/driver.py',context/'driver.py'),(work/'base.tar.gz',TASK/'public/bempp-source.tar.gz'),(work/'exafmm-v0.1.0.tar.gz',TASK/'public/exafmm-source.tar.gz')]:shutil.copyfile(src,dst)
    wheels=work/'offline-wheels'
    if not list(wheels.glob('*.whl')):raise ValueError('Pinned Linux CPython3.11 SDK wheelhouse required')
    shutil.copytree(wheels,context/'offline-wheels',dirs_exist_ok=True)
    evidence['sdk_wheels']={p.name:digest(p) for p in wheels.glob('*.whl')}
    reference=work/'production-reference-context';reference.mkdir(exist_ok=True)
    oracle=TASK/'author/generated';oracle.mkdir(exist_ok=True)
    with tarfile.open(work/'fixed.tar.gz') as archive:
        for name in FILES:
            member=next(m for m in archive if m.name.endswith('/bempp/api/fmm/'+name))
            raw=archive.extractfile(member).read();(oracle/name).write_bytes(raw);(reference/name).write_bytes(raw)
    (reference/'Dockerfile').write_text('FROM caeoj-bempp20-runtime:base\nCOPY exafmm.py fmm_assembler.py helpers.py /opt/upstream/bempp-cl-'+BASE+'/bempp/api/fmm/\nRUN /opt/bempp-env/bin/python -m compileall -q -f --invalidation-mode checked-hash /opt/upstream/bempp-cl-'+BASE+'/bempp/api/fmm\n',encoding='utf-8')
    dest=TASK/'author/data-evidence';dest.mkdir(exist_ok=True)
    (dest/'source-archives.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'context':str(context),'reference_context':str(reference),'original_files':evidence['base']['files'],'native_files':evidence['exafmm-v0.1.0']['files']}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);prepare(p.parse_args().work)
