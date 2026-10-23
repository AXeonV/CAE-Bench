"""Independent final audit; public DATA formulas only, no author numerical imports."""
from pathlib import Path
import sys,json,hashlib,copy,csv,re,importlib.util
import numpy as np,h5py,mpmath as mp
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'src'))
TASK=ROOT/'qbank/19-solver-repair/19.2-operators/grand-potential-derivatives-repair'
OUT=Path(__file__).parent; mp.mp.dps=80
from caeoj.sdk import load_problem,load_result
from caeoj.case_grading import prepare_case
from caeoj.validation import check_result
spec=importlib.util.spec_from_file_location('review_contract',TASK/'extension/caeoj_task_ext/grand_potential.py');ext=importlib.util.module_from_spec(spec);spec.loader.exec_module(ext)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
M=lambda x:mp.mpf(float(x))
def checked(path):
 p=load_problem(path);errors=[];ext.check(p,errors);assert not errors,errors;return p
def arrays(path):
 with h5py.File(path) as f:return {k:f[k][()] for k in f}
def rule(name,p):
 if name.startswith(('void_response','solid_response')):return mp.mpf('1e-10')/(p['atomic_volume']*p[('void' if name.startswith('void') else 'solid')+'_energy_coefficient'])
 if 'number_density' in name:return mp.mpf('1e-6')
 if 'grand_potential' in name:return mp.mpf('1e-5')
 if name=='constraint_potential_jacobian':return mp.mpf('1e-8')
 if name.startswith('constraint_'):return mp.mpf('1e-11')
 return mp.mpf('1e-10')
def values(q,w,p):
 phi=q[0];eta=q[1:];h=mp.mpf(0) if phi<=0 else mp.mpf(1) if phi>=1 else 6*phi**5-15*phi**4+10*phi**3
 ceq=p['equilibrium_constant']+sum(p[f'equilibrium_linear_{i}']*eta[i] for i in range(4))
 ceq+=sum(p[f'equilibrium_hessian_{i}{j}']*eta[i]*eta[j]*(mp.mpf('.5') if i==j else 1) for i in range(4) for j in range(i,4))
 va=p['atomic_volume'];kv=p['void_energy_coefficient'];ks=p['solid_energy_coefficient']
 return [h,(1-h)*ceq,h/(va*kv),(1-h)/(va*ks),w/(va**2*kv)+1/va,w/(va**2*ks)+ceq/va,-w*w/(2*va**2*kv)-w/va,-w*w/(2*va**2*ks)-w*ceq/va]
def shifted(q,i,d):
 r=q.copy();r[i]+=d;return r
def independent(p,a):
 names=['void_minimum','solid_minimum','void_response','solid_response','void_number_density','solid_number_density','void_grand_potential','solid_grand_potential'];out={k:[] for k in names}
 for name in names[:4]:out[name+'_gradient']=[];out[name+'_hessian']=[]
 for name in ['constraint_residual','constraint_state_jacobian','constraint_potential_jacobian','constraint_concentration_jacobian']:out[name]=[]
 step=mp.mpf('1e-20');L=p['probe_length']
 for j in range(len(a['program_ids'])):
  q=[M(a['phi'][0,j,0]),*map(M,a['eta'][0,j])];w=M(a['potential'][0,j,0]);c=M(a['concentration'][0,j,0]);v=values(q,w,p)
  for k,name in enumerate(names):out[name].append([v[k]])
  for k,name in enumerate(names[:4]):
   f=lambda q:values(q,w,p)[k]
   out[name+'_gradient'].append([(f(shifted(q,i,step))-f(shifted(q,i,-step)))/(2*step) for i in range(5)])
   h=[]
   for i in range(5):
    for l in range(5):
     if i==l:h.append((f(shifted(q,i,step))-2*f(q)+f(shifted(q,i,-step)))/step**2)
     else:h.append(sum(si*sl*f(shifted(shifted(q,i,si*step),l,sl*step)) for si in [-1,1] for sl in [-1,1])/(4*step**2))
   out[name+'_hessian'].append(h)
  # Independent nodal interpolation and 2-point Gauss integration, then numeric perturbation.
  base=[q+[w,c],q+[w,c]]
  def residual(nodes):
   res=[mp.mpf(0),mp.mpf(0)]
   for x in [(1-1/mp.sqrt(3))/2,(1+1/mp.sqrt(3))/2]:
    N=[1-x,x];state=[sum(N[l]*nodes[l][k] for l in range(2)) for k in range(7)];vv=values(state[:5],state[5],p)
    force=state[6]-vv[0]-vv[1]-(vv[2]+vv[3])*state[5]
    for row in range(2):res[row]+=L/2*N[row]*force
   return res
  out['constraint_residual'].append(residual(base));matrix=[]
  for k in range(7):
   mat=[[0,0],[0,0]];delta=mp.mpf('1e-42') if k==5 else step
   for col in range(2):
    plus=copy.deepcopy(base);minus=copy.deepcopy(base);plus[col][k]+=delta;minus[col][k]-=delta
    rp=residual(plus);rm=residual(minus)
    for row in range(2):mat[row][col]=(rp[row]-rm[row])/(2*delta)
   matrix.append([x for row in mat for x in row])
  out['constraint_state_jacobian'].append(sum(matrix[:5],[]));out['constraint_potential_jacobian'].append(matrix[5]);out['constraint_concentration_jacobian'].append(matrix[6])
 return out
report={'precision_digits':80,'numeric_step':'1e-20','potential_step':'1e-42','cases':[],'samples':[],'variants':[],'sha256':{}}
def remember(path):report['sha256'][str(path.relative_to(ROOT)).replace('\\','/')]=sha(path)
paths=[*sorted((TASK/'cases').glob('*/problem.json')),*sorted((TASK/'samples').glob('*/input/problem.json'))]
for path in paths:
 sample='samples' in path.parts;name=path.parent.parent.name if sample else path.parent.name
 ref=path.parent.parent/'reference' if sample else TASK/'reference'/name
 prob=checked(path);a=prob.arrays;m=prob.manifest;p={k:M(v['value']) for k,v in m['physics']['parameters'].items()}
 assert m['geometries']==m['meshes']=={} and m['conditions']==[]
 r=load_result(prob,ref/'reference.h5');expected=independent(p,a);assert set(expected)==set(m['outputs']) and len(expected)==20
 plan=prepare_case(prob,ref/'grading.json');assert plan.evaluate(r)['score']==1
 policies=json.loads((ref/'grading.json').read_text())['checks'][0]['policy']['quantities']
 checks={};count=0
 for key,ev in expected.items():
  ar=r[key];assert ar.dtype==np.float64 and ar.shape==(1,len(a['program_ids']),len(ev[0]))
  rr=policies[m['outputs'][key]['quantity']]['rule'];assert np.isclose(rr['atol'],float(rule(key,p)),rtol=2e-16,atol=0) and rr['rtol']==1e-10
  assert rr['metric']=='pointwise' and rr['time']=='per_time' and rr['components']=='per_component'
  ratios=[abs(M(actual)-target)/(rule(key,p)+mp.mpf('1e-10')*abs(M(actual))) for actual,target in zip(ar.ravel(),sum(ev,[]))]
  worst=float(max(ratios));assert worst<=1,(name,key,worst);checks[key]=worst;count+=ar.size
 for key in ['program_ids','times']:assert np.array_equal(a[key],r[key]) and a[key].dtype==r[key].dtype
 entry={'name':name,'programs':len(a['program_ids']),'grain_count':int(p['grain_count']),'strict':int(p['strict_mass_conservation']),'variable_name_set':int(p['variable_name_set']),'scalar_values_checked':count,'max_tolerance_fraction':max(checks.values()),'outputs':checks}
 if sample:
  out=load_result(prob,path.parent.parent/'output/result.h5');assert all(np.array_equal(out[k],r[k]) for k in r);assert plan.evaluate(out)['score']==1
  remember(path.parent.parent/'output/result.h5')
 else:
  harbor=TASK/'author/data-evidence/harbor-oracle-v1/cases'/name/'result.h5';hr=arrays(harbor);assert plan.evaluate(hr)['score']==1
  entry['harbor_arrays_exact_to_reference']=all(np.array_equal(hr[k],r[k]) for k in r);remember(harbor)
 for asset in [path,path.parent/m['data_file'],ref/'reference.h5',ref/'grading.json']:remember(asset)
 report['samples' if sample else 'cases'].append(entry)
 print(name,entry['max_tolerance_fraction'],flush=True)
# DATA-selected input variants; check core plus task extension without modifying public tree.
original=checked(paths[0])
def variant(name,edit,valid):
 import tempfile
 m=copy.deepcopy(original.manifest);a={k:v.copy() for k,v in original.arrays.items()};edit(m,a)
 with tempfile.TemporaryDirectory(dir=OUT) as tmp:
  d=Path(tmp);(d/'problem.json').write_text(json.dumps(m));
  with h5py.File(d/m['data_file'],'w') as f:
   for k,v in a.items():f[k]=v
  try:checked(d/'problem.json');actual=True
  except Exception as e:actual=False
  assert actual==valid,(name,actual);report['variants'].append({'name':name,'expected_valid':valid,'actual_valid':actual})
variant('phi_clamped_both_bounds',lambda m,a:a['phi'].__setitem__((0,slice(0,2),0),[-.1,1.1]),True)
variant('temperature_extreme_bounds',lambda m,a:a['temperature'].__setitem__((0,slice(0,2),0),[250,2000]),True)
variant('renamed_nonstrict',lambda m,a:[m['physics']['parameters'][k].__setitem__('value',v) for k,v in [('strict_mass_conservation',0),('variable_name_set',1)]],True)
variant('phi_exceeds',lambda m,a:a['phi'].__setitem__((0,0,0),1.1000001),False)
variant('id_zero',lambda m,a:a['program_ids'].__setitem__(0,0),False)
variant('duplicate_ids',lambda m,a:a['program_ids'].__setitem__(1,a['program_ids'][0]),False)
variant('extra_hdf5_key',lambda m,a:a.__setitem__('unused',np.zeros(1)),False)
variant('wrong_units',lambda m,a:m['fields']['potential'].__setitem__('unit','eV'),False)
variant('missing_sampling',lambda m,a:m['fields']['phi'].pop('sampling'),False)
variant('inactive_eta_nonzero',lambda m,a:a['eta'].__setitem__((0,0,3),1e-8),False)
variant('inactive_cross_nonzero',lambda m,a:m['physics']['parameters']['equilibrium_hessian_03'].__setitem__('value',1e-8),False)
variant('fractional_grains',lambda m,a:m['physics']['parameters']['grain_count'].__setitem__('value',2.5),False)
variant('excess_potential',lambda m,a:a['potential'].__setitem__((0,0,0),1),False)
variant('nonzero_time',lambda m,a:a['times'].__setitem__(0,1),False)
variant('nan',lambda m,a:a['phi'].__setitem__((0,0,0),np.nan),False)
variant('float32',lambda m,a:a.__setitem__('phi',a['phi'].astype(np.float32)),False)
# Zero reference components permit exact float threshold equality and adjacent representable values.
pr=original;ref=TASK/'reference'/paths[0].parent.name;r=arrays(ref/'reference.h5');plan=prepare_case(pr,ref/'grading.json')
for key in ['void_minimum_gradient','solid_minimum_hessian','void_response_gradient','solid_response_hessian','constraint_state_jacobian']:
 idx=next(i for i in np.ndindex(r[key].shape) if r[key][i]==0);atol=json.loads((ref/'grading.json').read_text())['checks'][0]['policy']['quantities'][pr.manifest['outputs'][key]['quantity']]['rule']['atol']
 for label,val,score in [('inside',np.nextafter(atol,0),1),('equal',atol,1),('outside',np.nextafter(atol,np.inf),0)]:
  out={k:v.copy() for k,v in r.items()};out[key][idx]=val;actual=plan.evaluate(out)['score'];assert actual==score,(key,label,actual);report['variants'].append({'name':key+'_'+label,'expected_score':score,'actual_score':actual})
for name,edit in [('missing_output',lambda a:a.pop('void_minimum')),('extra_output',lambda a:a.__setitem__('extra',np.zeros(1))),('bad_ids',lambda a:a['program_ids'].__setitem__(0,1)),('nan_output',lambda a:a['solid_minimum'].__setitem__((0,0,0),np.nan))]:
 out={k:v.copy() for k,v in r.items()};edit(out);result=plan.evaluate(out);assert result['status']=='invalid_output' and result['score']==0;report['variants'].append({'name':name,'status':result['status']})
for key,decl in pr.manifest['outputs'].items():
 rr=json.loads((ref/'grading.json').read_text())['checks'][0]['policy']['quantities'][decl['quantity']]['rule'];idx=(0,0,0);tol=rr['atol']+rr['rtol']*abs(r[key][idx])
 for factor,expected in [(.5,1),(2,0)]:
  out={k:v.copy() for k,v in r.items()};out[key][idx]+=factor*tol;actual=plan.evaluate(out)['score'];assert actual==expected,(key,factor,actual);report['variants'].append({'name':key+'_tolerance_factor_'+str(factor),'expected_score':expected,'actual_score':actual})
for path in [TASK/'instruction.md',TASK/'DATA.md',ROOT/'docs/CONTRACT.md',Path(__file__)]:remember(path)
(OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS',len(report['cases']),len(report['samples']),len(report['variants']))
