"""Archive the completed independent work directory and interrupted diagnostic pilots."""
from pathlib import Path
import hashlib,json,tarfile,shutil,sys
import h5py,numpy as np
from assess_openfoam import collect,sample,metrics
root=Path(sys.argv[1]).resolve();out=root/'compact-evidence';raw=root/'evidence';raw.mkdir(exist_ok=True)
assert len(list((root/'runs-final').glob('*/n32/execution.json')))==19
rows=collect(root/'source',root/'runs-final',root/'catalog.json',out)
assert all(r['accepted'] for r in rows)
shutil.copyfile(root/'producer.json',out/'producer.json')
name='lid-L-chamber';xy=np.array(json.loads((root/'runs-final'/name/'n32/translation.json').read_text())['probes'])
final,_=sample(root/'runs-final'/name/'n32',xy,1.,.1)
consistency={}
for folder in ('pilot-efficient','pilot-relative'):
    p=root/folder/name/'n32';e=json.loads((p/'execution.json').read_text());assert e['converged'] and e['solver']['returncode']==0
    values,path=sample(p,xy,1.,.1)
    consistency[folder]=dict(execution=e,configuration_sha256=hashlib.sha256((p/'system/fvSolution').read_bytes()).hexdigest(),sample_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        difference={q:dict(max_abs=float(np.max(np.abs(values[q]-final[q]))),max_tolerance_fraction=float(np.max(np.abs(values[q]-final[q])/(a+.01*np.abs(final[q]))))) for q,a in [('velocity',.001),('pressure',.1),('shear_rate',.01)]})
    assert max(v['max_tolerance_fraction'] for v in consistency[folder]['difference'].values())<.001
(out/'initialization-consistency.json').write_text(json.dumps(consistency,indent=2)+'\n')
def archive(name,paths):
    p=raw/name
    with tarfile.open(p,'w:gz',compresslevel=1) as tar:
        for path in paths:tar.add(root/path,arcname=str(path))
    # Reopen the actual archive, read every byte to check gzip/tar transport integrity.
    count=0
    with tarfile.open(p,'r:gz') as tar:
        for member in tar:
            if member.isfile():
                f=tar.extractfile(member)
                while f.read(1024*1024):pass
                count+=1
    return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size,files=count,all_members_read=True)
finalraw=archive('raw-final-runs.tar.gz',[Path('runs-final'),Path('source'),Path('producer.json'),Path('catalog.json'),Path('crosscheck_openfoam.py'),Path('assess_openfoam.py'),Path('capture_openfoam_producer.py')])
diagnostic=archive('diagnostic-runs.tar.gz',[Path(p) for p in ('runs','diagnostic-slow','pilot-fast','pilot-efficient','pilot-relative','pilot_fast.py','pilot_efficient.py','pilot_relative.py','interrupted-pilots.json','retired-slow.json')])
(out/'raw-results.json').write_text(json.dumps(dict(host='titan',final=finalraw,diagnostic=diagnostic,diagnostics_not_counted_as_final_runs=True),indent=2)+'\n')
with tarfile.open(root/'compact-evidence.tar.gz','w:gz') as tar:tar.add(out,arcname='.')
print(json.dumps(dict(cases=len(rows),accepted=sum(r['accepted'] for r in rows),archives=[finalraw,diagnostic])),flush=True)
