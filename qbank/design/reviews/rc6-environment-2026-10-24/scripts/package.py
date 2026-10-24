"""Package the entire verified RC6 directory as one reconstructable ZIP."""
import hashlib,json,shutil,time,zipfile
from pathlib import Path
from caeoj_tools.release import verify
ROOT=Path('D:/Code/CAE-Bench-OJ');WORK=ROOT/'runs/releases/rc6-authoring'
release=ROOT/'runs/releases/caeoj-qbank-20261024-rc6';verify(release)
target=release.with_suffix('.zip');started=time.time()
with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_STORED,allowZip64=True) as archive:
    for path in sorted(release.rglob('*')):
        if not path.is_file():continue
        info=zipfile.ZipInfo(release.name+'/'+path.relative_to(release).as_posix(),(2026,10,24,0,0,0));info.external_attr=0o100644<<16
        with path.open('rb') as source,archive.open(info,'w',force_zip64=True) as output:shutil.copyfileobj(source,output,1024*1024)
with target.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
checks=json.loads((release/'SHA256SUMS.json').read_text(encoding='utf-8'))['files']
checks['SHA256SUMS.json']={'size_bytes':(release/'SHA256SUMS.json').stat().st_size,
    'sha256':hashlib.sha256((release/'SHA256SUMS.json').read_bytes()).hexdigest()}
with zipfile.ZipFile(target) as archive:
    assert set(archive.namelist())=={release.name+'/'+name for name in checks}
    for name,expected in checks.items():
        with archive.open(release.name+'/'+name) as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
        assert actual==expected['sha256']
        assert archive.getinfo(release.name+'/'+name).file_size==expected['size_bytes']
result={'status':'passed','archive':str(target),'bytes':target.stat().st_size,'sha256':digest,
        'verified_members':len(checks),'elapsed_seconds':time.time()-started}
(WORK/'delivery.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result),flush=True)
