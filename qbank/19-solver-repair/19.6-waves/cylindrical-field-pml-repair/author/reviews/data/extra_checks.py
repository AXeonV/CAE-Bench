from pathlib import Path
import copy,hashlib,importlib.util,json,math,shutil,tempfile
import numpy as np,h5py
from caeoj.sdk import load_problem,load_result,write_result
from caeoj.case_grading import grade_case
from caeoj.storage import write_hdf5
from caeoj.validation import ContractError
R=Path(__file__).resolve().parents[3];T=R/'qbank/19-solver-repair/19.6-waves/cylindrical-field-pml-repair';O=Path(__file__).parent;original=load_problem(T/'samples/01/input/problem.json')
s=importlib.util.spec_from_file_location('contract',T/'extension/caeoj_task_ext/cylindrical.py');ext=importlib.util.module_from_spec(s);s.loader.exec_module(ext)
report={'declarations':[],'float_boundaries':[],'source_math':[]}
mutations=[('res40-canonical',True,lambda m,a:(m['physics']['parameters']['resolution'].update(value=40),a.update(probe_coordinates=np.array([[(2*40+1)*(.5/40),.5/40]])))),('extra-parameter',False,lambda m,a:m['physics']['parameters'].update(extra={'value':1,'unit':'1'})),('parameter-unit',False,lambda m,a:m['physics']['parameters']['mode'].update(unit='m')),('conditions',False,lambda m,a:m.update(conditions=[{'role':'source','variable':'E','location':'field_probe','operator':'assign','data':{'value':{'value':1,'unit':'1'}}}])),('location-coordinate',False,lambda m,a:a['probe_coordinates'].__iadd__(1e-10)),('static-label',False,lambda m,a:a['times'].__iadd__(1)),('face-order',False,lambda m,a:a.update(face_ids=a['face_ids'][::-1].copy())),('probe-ID',False,lambda m,a:a.update(probe_ids=np.array([8],dtype=np.int64))),('extra-array',False,lambda m,a:a.update(unused=np.array([1.]))),('output-components',False,lambda m,a:m['outputs']['observed_dft']['components'].reverse()),('output-sampling',False,lambda m,a:m['outputs']['observed_dft'].update(sampling={'space':'uniform','time':'constant','extrapolation':'forbid'})),('flux-point',False,lambda m,a:m['outputs']['spectral_flux'].update(value_kind='point')),('output-unit',False,lambda m,a:m['outputs']['observed_dft'].update(unit='V/m')),('output-quantity',False,lambda m,a:m['outputs']['observed_dft'].update(quantity='electric_field'))]
with tempfile.TemporaryDirectory() as tmp:
 d=Path(tmp);mesh=(original.path.parent/'surfaces.msh').read_text()
 for name,expected,mutate in mutations:
  (d/'surfaces.msh').write_text(mesh);m=copy.deepcopy(original.manifest);a={k:v.copy() for k,v in original.arrays.items()};mutate(m,a);(d/'problem.json').write_text(json.dumps(m));write_hdf5(d/'input.h5',a)
  try:p=load_problem(d/'problem.json');errors=[];ext.check(p,errors);accepted=not errors
  except ContractError:accepted=False
  assert accepted==expected,(name,accepted);report['declarations'].append({'variant':name,'accepted':accepted})
 # The optional type15 branch: zero point elements legal; duplicate node point element illegal.
 for name,expected,text in [('no-point-elements',True,mesh.replace('2 7 11 1004','1 3 11 23').replace('0 10 15 4\n1001 1 \n1002 2 \n1003 3 \n1004 4 \n','')),('duplicate-point',False,mesh.replace('2 7 11 1004','2 8 11 1005').replace('0 10 15 4','0 10 15 5').replace('1004 4 \n','1004 4 \n1005 4 \n')),('reversed-line',False,mesh.replace('11 1 2','11 2 1'))]:
  (d/'surfaces.msh').write_text(text);(d/'problem.json').write_text(json.dumps(original.manifest));write_hdf5(d/'input.h5',original.arrays)
  try:p=load_problem(d/'problem.json');errors=[];ext.check(p,errors);accepted=not errors
  except ContractError:accepted=False
  assert accepted==expected,(name,accepted);report['declarations'].append({'variant':name,'accepted':accepted})
 ref=T/'samples/01/reference';valid=load_result(original,ref/'reference.h5');fields={k:valid[k].copy() for k in original.manifest['outputs']}
 for key,(atol,rtol) in {'spectral_flux':(1e-9,1e-8),'observed_dft':(1e-10,1e-8),'time_step':(1e-12,1e-12),'window_end':(1e-10,1e-12)}.items():
  val=fields[key].flat[0];threshold=atol+rtol*abs(val);candidate=val+threshold
  for direction in [-np.inf,np.inf]:
   x=np.nextafter(candidate,direction);data={k:v.copy() for k,v in fields.items()};data[key].flat[0]=x;write_result(d/'result.h5',original,data);g=grade_case(original.path,d/'result.h5',ref/'grading.json');expected=int(abs(x-val)<=threshold);assert g['score']==expected,(key,x,g)
   report['float_boundaries'].append({'field':key,'nextafter_direction':str(direction),'actual_error':float(abs(x-val)),'threshold':float(threshold),'score':g['score']})
 # Parse DATA's standalone JSON locations fragment as JSON, and match the live instances.
 text=(T/'DATA.md').read_text(encoding='utf8');fragment=text.split('```json\n')[1].split('```')[0];assert json.loads(fragment)==original.manifest['locations'];report['DATA_JSON_fragment_matches_locations']=True

# Source dipole differentiated in the Fourier domain: Jhat(fc)=tau, positive phase and no-half flux.
for resolution in [30,40]:
 dt=.5/resolution;t=np.arange(0,1000+dt/2,dt);dipole=1j/(2*math.pi)*np.exp(-(t-500)**2/(2*50**2))*np.exp(-2j*math.pi*(t-500));phat=np.trapezoid(dipole*np.exp(2j*math.pi*t),dx=dt)/math.sqrt(2*math.pi);jhat=-2j*math.pi*phat
 assert abs(jhat-50)<1e-10
 report['source_math'].append({'resolution':resolution,'Jhat_real':jhat.real,'Jhat_imag':jhat.imag,'radial_moment':1/(4*resolution),'P0':math.pi**3*50**2/(12*resolution**2)})
coarse=json.loads((R/'work/repair-22/meep-2338/narrow-prototype-replay.json').read_text());fine=json.loads((R/'work/repair-22/meep-2338/extra-prototype-replay.json').read_text())
report['coarse_fine_raw_sha256']={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [R/'work/repair-22/meep-2338/narrow-prototype-replay.json',R/'work/repair-22/meep-2338/extra-prototype-replay.json']}
def flux_record(rows,res):
 for row in rows:
  raw=json.loads(row.get('stdout','{}'))
  if row.get('kind')=='fixed' and row.get('m')==-1 and raw.get('R')==3 and raw.get('Z')==2 and raw.get('resolution')==res:return np.asarray(raw['flux'])
 raise AssertionError('coarse/fine record missing')
f30=flux_record(coarse,30);f40=flux_record(fine,40);c=2/math.sqrt(13);cap=(4-3*c-c**3)/8
report['coarse_fine']=[{'resolution':res,'native_total':float(sum(f)),'total_relative_error':float(abs(sum(f)/(math.pi**3*50**2/(12*res**2))-1)),'cap_fraction_error':float(abs(f[0]/sum(f)-cap))} for res,f in [(30,f30),(40,f40)]]
assert report['coarse_fine'][1]['total_relative_error']<report['coarse_fine'][0]['total_relative_error'] and report['coarse_fine'][1]['cap_fraction_error']<report['coarse_fine'][0]['cap_fraction_error']
snapshot=R/'work/repair-22/meep-2338/hf-fixed-cache/datasets--jimzhouzzy2006--CAE-Bench-OJ/snapshots/7abc5ec8686026548ae4abdfeb4530a33ccd8332'/T.relative_to(R)
manifest=json.loads((T/'data-manifest.json').read_text());report['fixed_HF_case_descriptors']=[]
for name,selection in manifest['cases'].items():
 desc=snapshot/selection['case']['path'];assert hashlib.sha256(desc.read_bytes()).hexdigest()==selection['case']['sha256'];row=json.loads(desc.read_text());assert row['input']['complete'] and row['reference']['complete']
 for rel,identity in row['files'].items():
  actual=T/'cases'/name/Path(rel).name if rel.startswith('input/') else T/'reference'/name/Path(rel).name
  assert actual.stat().st_size==identity['size_bytes'] and hashlib.sha256(actual.read_bytes()).hexdigest()==identity['sha256']
 report['fixed_HF_case_descriptors'].append({'case':name,'descriptor_sha256':selection['case']['sha256'],'all_five_native_files_match_HF':True})
report['baseline_scores']=[]
for path in sorted((T/'cases').glob('*/problem.json')):
 base=R/'work/repair-22/meep-2338/dataset/replay/defect'/path.parent.name/'result.h5';g=grade_case(path,base,T/'reference'/path.parent.name/'grading.json')
 report['baseline_scores'].append({'case':path.parent.name,'score':g['score'],'status':g['status'],'actual_sha256':hashlib.sha256(base.read_bytes()).hexdigest()})
assert sum(x['score'] for x in report['baseline_scores'])==2
with h5py.File(T/'reference/01-negative-mode-public/reference.h5') as h1,h5py.File(T/'reference/02-positive-mode-public/reference.h5') as h2:
 x=h1['observed_dft'][()].reshape(6,2);y=h2['observed_dft'][()].reshape(6,2);assert np.array_equal(x,y*np.array([1,-1,1,-1,1,-1])[:,None]);assert np.array_equal(h1['spectral_flux'][()],h2['spectral_flux'][()]);report['mode_parity_exact']=True
(O/'extra-evidence.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps({'declarations':len(report['declarations']),'neighbor_boundary_checks':len(report['float_boundaries']),'coarse_fine':report['coarse_fine']},indent=2))
