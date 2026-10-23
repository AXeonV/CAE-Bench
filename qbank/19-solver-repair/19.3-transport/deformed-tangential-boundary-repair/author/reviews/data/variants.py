import sys,json,copy
from pathlib import Path
import numpy as np,h5py
ROOT=Path(__file__).resolve().parents[3];TASK=ROOT/'qbank/19-solver-repair/19.3-transport/deformed-tangential-boundary-repair';OUT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(TASK/'extension'))
from caeoj.sdk import load_problem
from caeoj.case_grading import grade_case
from caeoj.validation import check_result
from caeoj_task_ext.deformed_tangential import check
report={'input':{},'output':{},'grading':{}}
def inp(name,base,fn,expected):
 p=copy.deepcopy(base);fn(p);errors=[];check(p,errors);actual=not errors
 assert actual==expected,(name,errors);report['input'][name]={'valid':actual,'expected':expected}
def param(k,value):return lambda p:p.manifest['physics']['parameters'][k].update(value=value)
parallel=load_problem(TASK/'cases/01-parallel-public/problem.json');three=load_problem(TASK/'cases/06-three-dimensional/problem.json');wedge=load_problem(TASK/'cases/09-wedge-negative/problem.json');ann=load_problem(TASK/'cases/02-annulus-public/problem.json')
for k,lo,hi in [('density',.1,10),('viscosity',.1,10),('temperature',200,1000)]:
 for val,ok in [(lo,True),(hi,True),(np.nextafter(lo,-np.inf),False),(np.nextafter(hi,np.inf),False)]:inp(k+'-'+str(val),parallel,param(k,float(val)),ok)
for name,p,fn,ok in [
 ('unknown-model',parallel,lambda x:x.manifest['physics'].update(model='deformed-unknown'),False),
 ('legacy-family',parallel,lambda x:x.manifest['physics']['parameters'].update(family={'value':0,'unit':'1'}),False),
 ('wrong-unit',parallel,lambda x:x.manifest['physics']['parameters']['viscosity'].update(unit='Pa'),False),
 ('2d-extra-depth',parallel,lambda x:x.manifest['physics']['parameters'].update(depth={'value':.5,'unit':'m'}),False),
 ('3d-missing-depth',three,lambda x:x.manifest['physics']['parameters'].pop('depth'),False),
 ('wedge-3d',wedge,lambda x:x.manifest.update(spatial_dimension=3),False),
 ('annulus-nonzero-end',ann,param('end_time',.1),False),
 ('annulus-nonzero-frame',ann,lambda x:x.arrays.update(times=np.array([.1])),False),
 ('nonintegral-steps',parallel,param('time_step',.3),False),
 ('refinement-float',parallel,param('refinement',3.),False),
 ('refinement-zero',parallel,param('refinement',0),False),
 ('3d-refinement3',three,param('refinement',3),False),
 ('annulus-refinement5',ann,param('refinement',5),False),
 ('wrong-time-frame',parallel,lambda x:x.arrays['times'].__setitem__(1,.26),False),
 ('point-outside',parallel,lambda x:x.arrays['probe_coordinates'].__setitem__((0,0),-.1),False),
 ('point-near-wall',parallel,lambda x:x.arrays['probe_coordinates'].__setitem__((0,0),1e-8),False),
 ('one-probe',parallel,lambda x:(x.arrays.update(probe_ids=x.arrays['probe_ids'][:1],probe_coordinates=x.arrays['probe_coordinates'][:1])),True),
 ('output-cell-average',parallel,lambda x:x.manifest['outputs']['pressure'].update(value_kind='average'),False),
 ('output-wrong-components',three,lambda x:x.manifest['outputs']['velocity'].update(components=['x','z','y']),False),
 ('extra-mesh',parallel,lambda x:x.manifest['meshes'].update(main={'file':'m.msh'}),False)]:inp(name,p,fn,ok)
fixture=OUT/'fixtures';fixture.mkdir(exist_ok=True)
for c in sorted((TASK/'cases').iterdir()):
 p=load_problem(c/'problem.json');g=TASK/'reference'/c.name/'grading.json'
 with h5py.File(g.parent/'reference.h5') as h:arr={k:h[k][:] for k in h}
 pol=json.loads(g.read_text())['checks'][0]['policy']['quantities'];result={}
 for k in ['velocity','pressure']:
  for factor in [.999,1.001]:
   a={kk:v.copy() for kk,v in arr.items()};ix=np.unravel_index(np.argmax(abs(a[k])),a[k].shape);rule=pol[k]['rule'];a[k][ix]+=factor*(rule['atol']+rule['rtol']*abs(a[k][ix]))
   out=fixture/'boundary.h5'
   with h5py.File(out,'w') as h:
    for kk,v in a.items():h[kk]=v
   score=grade_case(c/'problem.json',out,g);assert score['score']==int(factor<1),(c,k,factor,score)
   result[k+'-'+str(factor)]={'status':score['status'],'score':score['score'],'mutated_index':list(map(int,ix))}
 report['grading'][c.name]=result
 if c.name=='09-wedge-negative':
  for name,fn in [('missing-field',lambda a:a.pop('pressure')),('extra-field',lambda a:a.update(extra=np.array([0.]))),('float32',lambda a:a.update(velocity=a['velocity'].astype('float32'))),('nan',lambda a:a['velocity'].__setitem__((0,0,0),np.nan)),('wrong-id',lambda a:a['probe_ids'].__setitem__(0,0)),('wrong-time',lambda a:a['times'].__setitem__(0,-.1)),('flat-pressure',lambda a:a.update(pressure=a['pressure'].reshape(-1)))]:
   a={kk:v.copy() for kk,v in arr.items()};fn(a);out=fixture/'invalid.h5'
   with h5py.File(out,'w') as h:
    for kk,v in a.items():h[kk]=v
   score=grade_case(c/'problem.json',out,g);assert score['status']=='invalid_output' and score['score']==0,(name,score);report['output'][name]={'status':score['status'],'score':score['score']}
# Exact equality at zero reference, using binary-representable tolerances to isolate <=.
p=wedge;source=TASK/'reference/09-wedge-negative';g=json.loads((source/'grading.json').read_text());ref={k:v.copy() for k,v in arr.items()}
with h5py.File(source/'reference.h5') as h:ref={k:h[k][:] for k in h}
for k in ['velocity','pressure']:
 ref[k][:]=0
 g['checks'][0]['policy']['quantities'][k]['rule']['atol']=.125
 g['checks'][0]['policy']['quantities'][k]['rule']['rtol']=0
with h5py.File(fixture/'reference.h5','w') as h:
 for k,v in ref.items():h[k]=v
(fixture/'grading.json').write_text(json.dumps(g))
for v,expect in [(.125,1),(np.nextafter(.125,0.),1),(np.nextafter(.125,np.inf),0)]:
 a={k:x.copy() for k,x in ref.items()};a['velocity'][0,0,0]=v
 with h5py.File(fixture/'equality.h5','w') as h:
  for k,x in a.items():h[k]=x
 score=grade_case(TASK/'cases/09-wedge-negative/problem.json',fixture/'equality.h5',fixture/'grading.json');assert score['score']==expect,score
 report['grading']['equality-'+repr(v)]={'score':score['score'],'temporary_synthetic_reference':True}
(OUT/'variants.json').write_text(json.dumps(report,indent=2));print({k:len(v) for k,v in report.items()})
