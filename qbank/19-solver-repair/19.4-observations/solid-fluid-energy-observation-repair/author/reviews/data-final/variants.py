import copy,json,shutil
from pathlib import Path
import h5py,numpy as np
from caeoj.validation import validate_input,validate_output
from caeoj.case_grading import grade_case
R=Path(__file__).resolve().parents[3];T=R/'qbank/19-solver-repair/19.4-observations/solid-fluid-energy-observation-repair';O=Path(__file__).parent;D=O/'variants';D.mkdir(exist_ok=True)
cases=sorted((T/'cases').iterdir());records=[]
def rh(p):
 with h5py.File(p) as f:return {k:f[k][()] for k in f}
def wh(p,a):
 with h5py.File(p,'w') as f:
  for k,v in a.items():f[k]=v
def check(label,c,edit,valid):
 d=D/label;d.mkdir(exist_ok=True);m=json.loads((c/'problem.json').read_text());a=rh(c/'input.h5');edit(m,a);(d/'problem.json').write_text(json.dumps(m));wh(d/'input.h5',a);r=validate_input(d/'problem.json');assert r['valid']==valid,(label,r);records.append({'variant':label,'expected_valid':valid,'actual':r})
def param(k,v):return lambda m,a:m['physics']['parameters'][k].update(value=v)
check('valid-cartesian-bounds',cases[0],lambda m,a:(m['physics']['parameters']['nx'].update(value=8),a['temperature_coefficients'].fill(0),a['temperature_coefficients'].__setitem__((0,0,0),250)),True)
check('valid-transient-foursteps',cases[10],lambda m,a:(m['physics']['parameters']['dt'].update(value=.05),m['physics']['parameters']['step_count'].update(value=4),a.__setitem__('times',np.arange(5)*.05)),True)
check('nx-odd',cases[0],param('nx',5),False)
check('mesh-float-integer',cases[0],param('ny',2.0),False)
check('unit-not-equivalent',cases[0],lambda m,a:m['physics']['parameters']['density_fluid'].update(unit='g/cm3'),False)
check('missing-parameter',cases[0],lambda m,a:m['physics']['parameters'].pop('viscosity'),False)
check('unknown-parameter',cases[0],lambda m,a:m['physics']['parameters'].update(ghost={'value':1,'unit':'1'}),False)
check('sampling-missing',cases[0],lambda m,a:m['fields']['temperature_coefficients'].pop('sampling'),False)
check('rz-inactive-temperature',cases[4],lambda m,a:a['temperature_coefficients'].__setitem__((0,0,3),1),False)
check('rz-swirl',cases[4],lambda m,a:a['velocity_coefficients'].__setitem__((0,0,8),1),False)
check('coupled-unused-coefficients',cases[8],lambda m,a:a['temperature_coefficients'].__setitem__((0,0,0),300),False)
check('reynolds-over-bound',cases[8],lambda m,a:[m['physics']['parameters'][k].update(value=v) for k,v in [('density_fluid',20),('inlet_speed',1),('viscosity',.1)]],False)
check('zero-source',cases[8],lambda m,a:[m['physics']['parameters'][k].update(value=0) for k in ['source_constant','source_radial','source_axial']],False)
check('steady-nonzero-time',cases[8],param('dt',.1),False)
check('transient-missing-initial',cases[10],lambda m,a:a.__setitem__('times',a['times'][1:]),False)
check('transient-near-time',cases[10],lambda m,a:a['times'].__setitem__(1,a['times'][1]+1e-15),False)
check('initial-time-nonzero',cases[0],lambda m,a:a['initial_time'].__setitem__(0,1),False)
check('nonfinite-coefficient',cases[0],lambda m,a:a['temperature_coefficients'].__setitem__((0,0,0),np.nan),False)
c=cases[0];base=rh(T/'reference'/c.name/'reference.h5');p=c/'problem.json';gp=T/'reference'/c.name/'grading.json'
for label,edit,status in [('missing-support',lambda a:a.pop('times'),'invalid_output'),('extra-initial-support',lambda a:a.update(initial_time=np.array([0.])),'invalid_output'),('wrong-id',lambda a:a['experiment_ids'].__setitem__(0,2),'invalid_output'),('nan-output',lambda a:a['energy_solid'].fill(np.nan),'invalid_output'),('wrong-dtype',lambda a:a.update(energy_solid=a['energy_solid'].astype('float32')),'invalid_output'),('flatten-output',lambda a:a.update(energy_solid=a['energy_solid'].ravel()),'invalid_output')]:
 a=copy.deepcopy(base);edit(a);out=D/(label+'.h5');wh(out,a);r=grade_case(p,out,gp);assert r['status']==status,(label,r);records.append({'variant':label,'expected_status':status,'status':r['status']})
for key in ['energy_solid','energy_fluid','advection_power','source_power','robin_power']:
 for factor in [.999,1.001]:
  a=copy.deepcopy(base);v=a[key].flat[0];a[key].flat[0]=v+(1e-5+1e-9*abs(v))*factor;out=D/f'{key}-{factor}.h5';wh(out,a);r=grade_case(p,out,gp);expected=1 if factor<1 else 0;assert r['score']==expected,(key,factor,r);records.append({'variant':f'{key}-{factor}','score':r['score'],'actual_delta':float(a[key].flat[0]-v),'tolerance':1e-5+1e-9*abs(v)})
# Exact representable boundary for zero-reference Robin power.
a=copy.deepcopy(base);a['robin_power'].fill(1e-5);out=D/'threshold-equality.h5';wh(out,a);r=grade_case(p,out,gp);assert r['score']==1;records.append({'variant':'threshold-equality-zero-reference','score':r['score']})
(O/'variants.json').write_text(json.dumps(records,indent=2)+'\n');print('VARIANTS_PASS',len(records))
