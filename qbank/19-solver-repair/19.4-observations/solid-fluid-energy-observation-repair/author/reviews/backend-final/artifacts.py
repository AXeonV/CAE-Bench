import hashlib,json,tarfile,zipfile,posixpath,csv
from pathlib import Path
import h5py,numpy as np
R=Path(__file__).resolve().parents[3];T=R/'qbank/19-solver-repair/19.4-observations/solid-fluid-energy-observation-repair';E=T/'author/data-evidence';O=Path(__file__).parent
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def jr(p):return json.loads(p.read_text())
def rh(p):
 with h5py.File(p) as f:return {k:f[k][()] for k in f}
report={}
for stem in ['native','backend']:
 m=jr(E/f'{stem}-raw-manifest.json');p=E/m['archive'];assert sha(p)==m['archive_sha256'];expected={r['path']:r for r in m['files']};seen=set()
 with tarfile.open(p,'r|gz') as tf:
  for member in tf:
   if not member.isfile():continue
   data=tf.extractfile(member).read();x=expected[member.name];assert hashlib.sha256(data).hexdigest()==x['sha256'] and len(data)==x['bytes'];seen.add(member.name)
 assert seen==set(expected);report[stem+'_raw']={'files':len(seen),'sha256':sha(p)}
p=T/'public/moose-source.tar.gz';m=jr(E/'source-closure.json');assert sha(p)==m['closure_sha256'];expected={r['path']:r for r in m['files']};closure={}
with tarfile.open(p,'r|gz') as tf:
 for member in tf:
  assert member.isfile();data=tf.extractfile(member).read();x=expected[member.name];assert hashlib.sha256(data).hexdigest()==x['sha256'] and len(data)==x['bytes'];closure[member.name]=x['sha256']
assert set(closure)==set(expected)
archive=Path('C:/Users/Jim Zhou/.cache/caeoj-repair22/archived-source-downloads/moose-22074-baseline.tar.gz');assert sha(archive)==m['upstream_archive_sha256'];orig={};links={}
with tarfile.open(archive,'r|gz') as tf:
 for member in tf:
  name=member.name.partition('/')[2]
  if name in closure:
   if member.isfile():orig[name]=hashlib.sha256(tf.extractfile(member).read()).hexdigest()
   elif member.issym():links[name]=posixpath.normpath(posixpath.join(posixpath.dirname(name),member.linkname))
for name,x in expected.items():
 target=name;seen=set()
 while target in links:
  assert target not in seen;seen.add(target);target=links[target]
 assert orig.get(target)==closure[name],name
report['closure']={'files':len(closure),'archive_sha256':sha(archive),'closure_sha256':sha(p),'original_regular_files_checked':len(orig),'original_links_checked':len(links)}
zip_path=Path('C:/Users/Jim Zhou/.cache/caeoj-repair22/moose22074-dist-v1/solid-fluid-energy-observation-repair-agent.zip');assert sha(zip_path)=='307d4652af831c8ccaa15ba8ef509caa2d4786a7cbd56d89479510838537b0f2'
with zipfile.ZipFile(zip_path) as z:
 members=[x for x in z.namelist() if not x.endswith('/')];assert len(members)==43;assert not any('/author/' in x or '/cases/' in x or '/reference/' in x and '/samples/' not in x for x in members);report['public_zip']={'sha256':sha(zip_path),'members':members}
frozen=jr(E/'frozen-run.json');prep=R/'runs/harbor/tasks/solid-fluid-energy-observation-repair'
for name,x in frozen['prepared_files'].items():assert sha(prep/name)==x,name
report['frozen_files_checked']=len(frozen['prepared_files']);hf=jr(E/'hf-assembly.json');report['hf_assembly_keys']=list(hf);assert hf['revision']=='cadbdde490008f7709698216c5980c17bc6bdca9';assert jr(E/'hf-strict.json')['valid'];report['hf_receipt_files']=len(hf.get('files',{}))
for name,x in hf['files'].items():assert sha(T/name)==x['sha256'] and (T/name).stat().st_size==x['size_bytes'],name
native=[]
for c in sorted((T/'cases').iterdir()):
 d=R/'runs/authoring/repair-22/moose-22074-native-replay';text=(d/'defect'/c.name/'stderr.log').read_text()+(d/'defect'/c.name/'stdout.log').read_text();assert 'is not a registered object' in text or 'is not a registered type' in text or 'not registered' in text,text[-1500:]
 with (d/'reference'/c.name/'result.csv').open() as f:rows=list(csv.DictReader(f))
 actual=rh(T/'reference'/c.name/'reference.h5');mapping={'energy_solid':'energy_0','energy_fluid':'energy_1','advection_power':'advection','source_power':'source','robin_power':'convective_heat_transfer'}
 assert all(np.array_equal(actual[k].ravel(),[float(row[col]) for row in rows]) for k,col in mapping.items());native.append({'case':c.name,'raw_reference_csv_exact':True,'baseline_unknown_object':True,'native_input_sha256':sha(d/'reference'/c.name/'case.i')})
report['native_replays']=native
job=R/'runs/harbor/jobs/repair22-moose22074-harbor-oracle-v1';trial=next(x for x in job.iterdir() if x.is_dir());tr=jr(trial/'result.json');assert tr['exception_info'] is None;vr=jr(trial/'verifier/report.json');assert vr['score']==12 and vr['complete'] and vr['completed_cases']==vr['total_cases']==12
results=[]
for c in sorted((T/'cases').iterdir()):
 a=rh(T/'reference'/c.name/'reference.h5');b=rh(trial/'verifier'/c.name/'result.h5');assert set(a)==set(b);assert all(np.array_equal(a[k],b[k]) for k in a),c.name;ex=jr(trial/'verifier'/c.name/'execution.json');results.append({'case':c.name,'all_7_arrays_bitwise_numeric_equal':True,'execution':ex})
base=jr(trial/'verifier/build/baseline-report.json');candidate=jr(trial/'verifier/build/report.json');health=jr(trial/'verifier/build/baseline-probe-report.json');assert base['status']==candidate['status']=='built' and health['status']=='ready';assert len(candidate['removed_build_artifacts'])==4
report['official']={'trial':trial.name,'exception_info':tr['exception_info'],'cases':results,'baseline_build_seconds':base['elapsed_seconds'],'candidate_build_seconds':candidate['elapsed_seconds'],'health':health,'score':vr['score'],'total':vr['total_cases'],'trial_result_sha256':sha(trial/'result.json'),'job_result_sha256':sha(job/'result.json')}
(O/'artifacts.json').write_text(json.dumps(report,indent=2)+'\n');print('ARTIFACTS_PASS',report['closure'],report['frozen_files_checked'])
