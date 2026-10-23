"""Read-only final backend binding; does not prepare or launch an Oracle."""
from pathlib import Path
import hashlib,json,subprocess,tarfile,zipfile
import h5py,numpy as np
ROOT=Path(__file__).resolve().parents[3];TASK=ROOT/'qbank/19-solver-repair/19.6-waves/parallel-pml-reduction-repair';OUT=Path(__file__).parent
PREP=ROOT/'runs/harbor/tasks/parallel-pml-reduction-repair';WORK=ROOT/'work/repair-22/specfem-661'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
state=json.loads((ROOT/'runs/authoring/repair-22/repair22-specfem661-oracle-v3.json').read_text())
assert state['phase']=='completed'
for name,digest in state['task_sha256'].items():assert sha(PREP/name)==digest,name
assert sha(PREP/'tests/judge.py')=='5595500ff6c8612f4682f4eda0cdc6521c5af94343dcba6c825bb3555141180f'
assert sha(PREP/'tests/agent.zip')=='9cd9a7479aaa7973194bfd5099e97fbc60f40c8133cddcce8b2e7552f54c3f39'
job=ROOT/'runs/harbor/jobs/repair22-specfem661-oracle-v3';trials=list(job.glob('*/result.json'));assert len(trials)==1
terminal=json.loads(trials[0].read_text());assert terminal['exception_info'] is None
verifier=trials[0].parent/'verifier';report=json.loads((verifier/'report.json').read_text())
assert report['complete'] and report['score']==report['completed_cases']==report['total_cases']==8 and report['reward']==1
rows=[]
for row in report['cases']:
    actual=verifier/row['case']/'result.h5';reference=TASK/'reference'/row['case']/'reference.h5'
    with h5py.File(actual) as f,h5py.File(reference) as r:
        assert set(f)==set(r)
        for k in f:assert np.array_equal(f[k][:],r[k][:]),(row['case'],k)
    rows.append({'case':row['case'],'status':row['status'],'score':row['score'],'all_arrays_equal':True,'actual_sha256':sha(actual),'reference_sha256':sha(reference)})
probes=[]
for mode in ['valid','syntax','extra','symlink','compiler','baseline-runtime','runtime-timeout']:
    path=WORK/'probe-evidence-v3'/(mode+'.stdout.json');r=json.loads(path.read_text());assert r['passed'] and r['mode']==mode
    probes.append({'mode':mode,'sha256':sha(path),'result':r})
valid=probes[0]['result'];assert valid['binding']['uid']==1000 and valid['binding']['network']=='denied'
assert valid['cpu_max'].strip()=='400000 100000' and valid['memory_max'].strip()=='4294967296'
assert len(valid['build']['built_artifacts_sha256'])==2
timeout=probes[-1]['result'];assert timeout['actual_fortran_timeout'] and timeout['all_absent_including_zombies'] and timeout['unrelated_same_uid_sentinel_survived'] and len(timeout['rank_pids'])==3
build={p.name:json.loads(p.read_text()) for p in (verifier/'build').glob('*report.json')}
assert build['report.json']['sources_sha256']['get_MPI.F90']==sha(TASK/'author/generated/get_MPI.F90')
assert build['report.json']['built_artifacts_sha256']==valid['build']['built_artifacts_sha256']
assert build['baseline-report.json']['status']=='built' and build['baseline-probe-report.json']['status']=='ready'
source_files={}
with tarfile.open(TASK/'public/specfem-source.tar.gz') as tf:
    for member in tf:
        name=member.name.split('/',1)[-1]
        if member.isfile() and name.startswith('src/'):
            source_files[name]=hashlib.sha256(tf.extractfile(member).read()).hexdigest()
# Read all archive src files inside production/runtime images, no solver invocation.
code="""from pathlib import Path
import hashlib,json
root=Path('/opt/specfem-repair-build/upstream')
expected=json.loads(Path('/audit/expected-sources.json').read_text())
differences={}
for name,want in expected.items():
 actual=hashlib.sha256((root/name).read_bytes()).hexdigest()
 if actual!=want:differences[name]=actual
print(json.dumps({'source_files_checked':len(expected),'differences':differences,'artifact_sha256':{name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in ['obj/get_MPI.spec.o','bin/xspecfem2D']}}))
"""
(OUT/'expected-sources.json').write_text(json.dumps(source_files,indent=2));images={}
for image in ['caeoj-specfem661-runtime:base','caeoj-specfem661-reference:production']:
    cmd=['docker','run','--rm','--network','none','-v',str(OUT)+':/audit:ro',image,'python','-c',code]
    p=subprocess.run(cmd,text=True,capture_output=True,check=True);r=json.loads(p.stdout)
    if image.endswith(':base'):assert not r['differences'],r
    else:
        assert r['differences']=={'src/specfem2D/get_MPI.F90':sha(TASK/'author/generated/get_MPI.F90')},r
        assert {str('/opt/specfem-repair-build/upstream/'+k):v for k,v in r['artifact_sha256'].items()}==build['report.json']['built_artifacts_sha256']
    images[image]=r
with zipfile.ZipFile(PREP/'tests/agent.zip') as z:
    members=z.namelist()
    assert len(members)==44
    assert not any('/author/' in n or '/cases/' in n or n.startswith('tests/') for n in members)
    assert all('/reference/' not in n or '/samples/' in n for n in members)
    zipsha={n:hashlib.sha256(z.read(n)).hexdigest() for n in members if not n.endswith('/')}
corners=[]
from caeoj.sdk import load_problem,load_result
for folder in ['resource-corner','resource-sh']:
    d=WORK/folder;q=load_problem(d/'problem.json');out=load_result(q,d/'result.h5');a=q.arrays
    assert len(a['cell_ids'])==6000 and len(a['times'])==6400 and len(a['source_ids'])==2 and len(a['probe_ids'])==8
    assert q.manifest['physics']['parameters']['processes']['value']==4
    for x in list(a.values())+list(out.values()):assert np.isfinite(x).all()
    resource=json.loads((d/'resource.json').read_text());assert resource['exit_code']==0 and resource['elapsed_seconds']<210
    corners.append({'folder':folder,'resource':resource,'input_sha256':sha(d/'input.h5'),'output_sha256':sha(d/'result.h5')})
result={'oracle_v3':rows,'terminal':terminal,'snapshot_sha256':sha(ROOT/'runs/authoring/repair-22/repair22-specfem661-oracle-v3.json'),'build':build,'probes':probes,'images':images,'archive_members_sha256':zipsha,'resource_corners':corners,'prepared_sha256':state['task_sha256']}
(OUT/'actualchecks.json').write_text(json.dumps(result,indent=2));print('v3 all8 returned arrays; seven probes; actual source trees; 2 build artifacts; archive/resource bindings passed')
