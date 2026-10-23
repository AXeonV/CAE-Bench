"""Read-only independent audit. No solver invocation or compiler execution."""
from pathlib import Path
import copy, hashlib, importlib.util, json, math, shutil, tarfile, tempfile, zipfile
import numpy as np
import h5py
from caeoj.sdk import load_problem, load_result, write_result
from caeoj.case_grading import grade_case
from caeoj.validation import ContractError, read_mesh

ROOT=Path(__file__).resolve().parents[3]
T=ROOT/'qbank/19-solver-repair/19.6-waves/cylindrical-field-pml-repair'
D=ROOT/'work/repair-22/meep-2338/dataset'
O=Path(__file__).parent
E=T/'author/data-evidence'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
spec=importlib.util.spec_from_file_location('audit_cyl',T/'extension/caeoj_task_ext/cylindrical.py');ext=importlib.util.module_from_spec(spec);spec.loader.exec_module(ext)
report={'cases':[],'samples':[],'variants':[],'grades':[],'source':{},'oracle':[]}
materials={}
def bind(p):materials[str(p.relative_to(ROOT))]=sha(p)

# Freeze every inspected task file and original raw native evidence, excluding transient pyc.
for p in T.rglob('*'):
 if p.is_file() and '__pycache__' not in str(p):bind(p)
z=ROOT/'dist/cylindrical-field-pml-repair-agent.zip';bind(z)
assert sha(z)=='acac8a89d2b02b4aa1a753fcdd2354b836c2af0af1cb21748973ed41564e0027'
with zipfile.ZipFile(z) as archive:
 report['zip_members']=archive.namelist()
 assert not any('/author/' in n or '/cases/' in n or '/generated/' in n for n in archive.namelist())

for kind,paths in [('cases', sorted((T/'cases').glob('*/problem.json'))),('samples', sorted((T/'samples').glob('*/input/problem.json')))]:
 for path in paths:
  p=load_problem(path);errs=[];ext.check(p,errs);assert not errs,errs
  a=p.arrays;m=p.manifest;v={k:x['value'] for k,x in m['physics']['parameters'].items()}
  ref=T/'reference'/path.parent.name if kind=='cases' else path.parent.parent/'reference'
  out=load_result(p,ref/'reference.h5')
  assert set(a)=={'face_ids','probe_ids','probe_coordinates','times'}
  assert np.array_equal(a['face_ids'],np.array([11,17,23],dtype=np.int64))
  assert a['probe_coordinates'].shape==(1,2) and a['probe_coordinates'].dtype==np.float64
  expected_point=np.array([[(2*v['resolution']+1)*(.5/v['resolution']),.5/v['resolution']]])
  assert np.array_equal(a['probe_coordinates'],expected_point)
  mesh=read_mesh(path.parent/'surfaces.msh',geometry=True)
  mesh_expected={1:(0.,float(v['half_height']),0.),2:(float(v['radius']),float(v['half_height']),0.),3:(float(v['radius']),-float(v['half_height']),0.),4:(0.,-float(v['half_height']),0.)}
  assert set(mesh['node_coordinates'])==set(mesh_expected) and all(np.array_equal(mesh['node_coordinates'][k],v) for k,v in mesh_expected.items())
  assert {k:r for k,r in mesh['connectivity'].items() if r[0]!=15}=={11:(1,(1,2)),17:(1,(2,3)),23:(1,(3,4))}
  assert grade_case(path,ref/'reference.h5',ref/'grading.json')['score']==1
  assert set(out)=={'face_ids','probe_ids','times','spectral_flux','observed_dft','time_step','window_end'}
  row={'name':path.parent.name if kind=='cases' else path.parent.parent.name,'parameters':v,'input_arrays':{k:{'dtype':str(x.dtype),'shape':list(x.shape),'values':x.tolist()} for k,x in a.items()},'mesh_elements':{k:r for k,r in mesh['connectivity'].items()},'output_arrays':{k:{'dtype':str(x.dtype),'shape':list(x.shape),'finite':bool(np.isfinite(x).all())} for k,x in out.items()}}
  if kind=='cases':
   rawdir=D/'replay/reference'/path.parent.name
   for name in ['trace.csv','payload.txt','stdout.json','stderr.log']:bind(rawdir/name)
   # Accumulate six complex DTFTs with explicit E/H phase, independently of author's evaluate().
   trace=np.loadtxt(rawdir/'trace.csv',delimiter=',',skiprows=1);n=2160*v['resolution'];dt=.5/v['resolution']
   assert trace.shape==(n,13) and np.isfinite(trace).all()
   np.testing.assert_allclose(trace[:,0],np.arange(1,n+1)*dt,rtol=0,atol=1e-12)
   calculated=[]
   for c in range(6):
    samples=trace[:,1+2*c]+1j*trace[:,2+2*c]
    clock=trace[:,0]-(dt/2 if c>=3 else 0)
    calculated.append(dt/math.sqrt(2*math.pi)*np.dot(np.exp(2j*math.pi*clock),samples))
   calculated=np.asarray(calculated);native=out['observed_dft'].ravel()[::2]+1j*out['observed_dft'].ravel()[1::2]
   delta=np.abs(np.array([[q.real,q.imag] for q in calculated]).ravel()-out['observed_dft'].ravel())
   assert np.all(delta<=1e-10+1e-8*np.abs(out['observed_dft'].ravel()))
   raw=json.loads((rawdir/'stdout.json').read_text());np.testing.assert_array_equal(out['spectral_flux'].ravel(),raw['flux']);np.testing.assert_array_equal(out['observed_dft'].reshape(6,2),raw['fields'])
   assert out['time_step'].item()==dt and out['window_end'].item()==1080 and np.all(out['spectral_flux']>0)
   # Derivative dyadic retarded Green tensor: E=i*k*(I+gradgrad/k^2)G*q, H=gradG cross q.
   xyz=np.r_[expected_point[0,0],0.,expected_point[0,1]];r=np.linalg.norm(xyz);nhat=xyz/r;k=2*math.pi
   q=math.pi*v['source_amplitude']*50/(4*v['resolution'])*np.array([1,1j*v['mode'],0])
   G=np.exp(1j*k*r)/(4*math.pi*r);gp=(1j*k-1/r)*G;gpp=(-k*k-2j*k/r+2/r**2)*G
   hessian_q=(gp/r)*q+(gpp-gp/r)*nhat*np.dot(nhat,q)
   green=np.r_[1j*k*(G*q+hessian_q/k**2),gp*np.cross(nhat,q)]
   green_err=np.abs(native-green)/np.abs(green)
   # Direct polar integration of 1+cos(theta)^2 over caps and complementary side.
   c=v['half_height']/math.hypot(v['radius'],v['half_height'])
   cap=((1+1/3)-(c+c**3/3))/(8/3)
   p0=(k*k/(3*math.pi))*abs(q[0])**2
   continuum=p0*np.array([cap,1-2*cap,cap]);flux=out['spectral_flux'].ravel()
   assert max(green_err)<.05 and max(abs(flux/continuum-1))<.15
   row.update(trace_steps=n,dtft_max_abs=float(delta.max()),dtft_components=calculated.tolist(),green_max_relative=float(max(green_err)),green_components=[[x.real,x.imag] for x in green],P0=p0,continuum_flux=continuum.tolist(),native_absolute_flux=flux.tolist(),surface_relative=(flux/continuum-1).tolist())
   row['dtft_components']=[[x.real,x.imag] for x in calculated]
   bindings=json.loads((E/'formal-oracle/output-bindings.json').read_text());job=ROOT/Path(bindings['job'])
   actuals=list(job.rglob(path.parent.name+'/result.h5'))
   if not actuals:actuals=[f for f in job.rglob('result.h5') if path.parent.name in str(f)]
   assert len(actuals)==1,(path,actuals)
   actual=load_result(p,actuals[0]);assert set(actual)==set(out)
   assert all(np.array_equal(actual[k],out[k]) and actual[k].dtype==out[k].dtype for k in out)
   bind(actuals[0]);report['oracle'].append({'case':path.parent.name,'actual':str(actuals[0]),'sha256':sha(actuals[0]),'all_7_arrays_bitwise_equal':True})
  else:
   assert grade_case(path,path.parent.parent/'output/result.h5',ref/'grading.json')['score']==1
  report[kind].append(row)

# Actual source archive and upstream head: independent hash join against all 700 entries.
manifest=json.loads((E/'baseline-tree.json').read_text())
def tree(p):
 with tarfile.open(p) as tar:
  return {'/'.join(x.name.split('/')[1:]):tar.extractfile(x).read() for x in tar.getmembers() if x.isfile()}
base=tree(T/'public/meep-source.tar.gz');fixed=tree(ROOT/'work/repair-22/meep-2338/fixed.tar.gz')
assert len(base)==700 and set(base)==set(manifest)
assert all(hashlib.sha256(data).hexdigest()==manifest[k] for k,data in base.items())
changed=[k for k in base if base[k]!=fixed[k]];assert sorted(changed)==['python/tests/test_ldos.py','src/step_db.cpp']
assert (T/'author/generated/step_db.cpp').read_bytes()==fixed['src/step_db.cpp']
report['source']={'original_files':700,'all_archive_hashes_match':True,'upstream_changes':changed,'producer_only_replacement':'src/step_db.cpp','reference_source_sha256':sha(T/'author/generated/step_db.cpp')}

# Declarative legal/illegal cases independently chosen from DATA, including combinations absent from real data.
original=load_problem(T/'samples/01/input/problem.json')
with tempfile.TemporaryDirectory() as temp:
 td=Path(temp);shutil.copyfile(original.path.parent/'surfaces.msh',td/'surfaces.msh')
 variants=[('amplitude-positive-lower',True,'source_amplitude',.25),('amplitude-negative-upper',True,'source_amplitude',-1),('amplitude-negative-integer',True,'source_amplitude',-1),('amplitude-low',False,'source_amplitude',.249999),('amplitude-high',False,'source_amplitude',1.000001),('amplitude-bool',False,'source_amplitude',True),('integer-float',False,'resolution',30.),('integer-bool',False,'radial_pml',True),('zero-mode',False,'mode',0),('outside-radius',False,'radius',4),('outside-halfheight',False,'half_height',3),('axialPML-two',True,'axial_pml',2),('radialPML-two',True,'radial_pml',2),('mode-positive',True,'mode',1)]
 for name,expected,key,value in variants:
  m=copy.deepcopy(original.manifest);m['physics']['parameters'][key]['value']=value
  (td/'problem.json').write_text(json.dumps(m));shutil.copyfile(original.path.parent/'input.h5',td/'input.h5');accepted=True
  try:p=load_problem(td/'problem.json');errors=[];ext.check(p,errors);accepted=not errors
  except ContractError:accepted=False
  assert accepted==expected,(name,accepted)
  report['variants'].append({'name':name,'accepted':accepted})
 # SDK must copy only IDs/times; mutations must fail structure even when values otherwise exact.
 ref=T/'samples/01/reference';valid=load_result(original,ref/'reference.h5');fields={k:valid[k].copy() for k in original.manifest['outputs']}
 write_result(td/'sdk.h5',original,fields)
 with h5py.File(td/'sdk.h5') as h:assert set(h)==set(valid)
 for field in fields:
  atol,rtol={'spectral_flux':(1e-9,1e-8),'observed_dft':(1e-10,1e-8),'time_step':(1e-12,1e-12),'window_end':(1e-10,1e-12)}[field]
  value=float(valid[field].flat[0]);tol=atol+rtol*abs(value)
  for factor in [.999,1.001]:
   data={k:v.copy() for k,v in fields.items()};data[field].flat[0]=value+factor*tol;write_result(td/'grade.h5',original,data)
   result=grade_case(original.path,td/'grade.h5',ref/'grading.json');assert result['score']==(1 if factor<1 else 0)
   report['grades'].append({'field':field,'factor':factor,'actual_error':abs(data[field].flat[0]-value),'limit':tol,'score':result['score'],'status':result['status']})
 for name in ['extra-key','missing-field','wrong-dtype','wrong-shape','wrong-IDs','nonfinite','bottom-sign','complex-swapped','mean-flux']:
  shutil.copyfile(ref/'reference.h5',td/'bad.h5')
  with h5py.File(td/'bad.h5','r+') as h:
   if name=='extra-key':h['probe_coordinates']=original.arrays['probe_coordinates']
   elif name=='missing-field':del h['observed_dft']
   elif name=='wrong-dtype':x=h['time_step'][()].astype('float32');del h['time_step'];h['time_step']=x
   elif name=='wrong-shape':x=h['observed_dft'][()].ravel();del h['observed_dft'];h['observed_dft']=x
   elif name=='wrong-IDs':h['face_ids'][...]=[11,17,24]
   elif name=='nonfinite':h['time_step'][...]=np.nan
   elif name=='bottom-sign':h['spectral_flux'][0,2,0]*=-1
   elif name=='complex-swapped':h['observed_dft'][...]=h['observed_dft'][()][...,::-1]
   else:h['spectral_flux'][...]=h['spectral_flux'][()]/np.sum(h['spectral_flux'][()])
  result=grade_case(original.path,td/'bad.h5',ref/'grading.json');assert result['score']==0
  report['grades'].append({'variant':name,'status':result['status'],'score':result['score']})
 # Corrupted reference must raise infrastructure, not be converted into candidate score 0.
 shutil.copyfile(ref/'reference.h5',td/'reference.h5');(td/'grading.json').write_bytes((ref/'grading.json').read_bytes())
 with h5py.File(td/'reference.h5','r+') as h:del h['time_step']
 try:
  bad=grade_case(original.path,td/'sdk.h5',td/'grading.json')
  assert bad['score'] is None and bad['status']=='evaluation_error',bad
  report['bad_reference']=bad
 except Exception as e:report['bad_reference']={'exception':type(e).__name__,'message':str(e)}

dump(O/'actual-evidence.json',report);dump(O/'materials-sha256.json',materials)
print(json.dumps({'cases':len(report['cases']),'samples':len(report['samples']),'max_dtft_abs':max(r['dtft_max_abs'] for r in report['cases']),'oracle':len(report['oracle']),'variants':len(report['variants']),'grading':len(report['grades']),'source':report['source']},indent=2))
