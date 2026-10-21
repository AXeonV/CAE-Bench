"""Finite closed, fully wet, zero-friction native bathymetry f-wave queue."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import traceback
from native_pyclaw_closed_flat import IMAGE,prepare as closed_prepare,convert
from native_lowmach import sample
import copy
import h5py
import numpy as np
from native_closed_cavity import SOCKET,save,digest
from titan_resources import reservation


CASE='ch02-2-9-2-07-cross_waves'

def prepare(job,e,allow_bed=True):
    assert e['design_id']==CASE
    spec=e['detailed_spec'];boundary=spec['boundaries'][1]
    assert boundary['selection']=='x=0' and boundary['operator']=='water_reservoir'
    assert boundary['data']['depth']['expression']=='1+.05*P'
    assert boundary['data']['velocity']['expression']==[0.,0.]
    private=copy.deepcopy(e)
    private['detailed_spec']['boundaries']=spec['boundaries'][:1]
    m,ids=closed_prepare(job,private,True)
    x,c,b=m['x'],m['c'],m['b']
    inlet=np.all(np.isclose(x[b,0],0.),axis=1)
    assert inlet.any() and (~inlet).any()
    end=spec['time_interval_s'][1]
    times=np.array([0.,.1*end,.4*end,.6*end,end])
    vals=np.array([sample('1+.05*P',np.zeros((1,2)),float(t),spec).reshape(-1)[0] for t in times])
    assert np.allclose(vals,[1.,1.05,1.05,1.,1.])
    problem=json.loads((job/'input/problem.json').read_text())
    problem['locations']['reservoir']={'kind':'mesh','mesh':'main','entity':'element','dimension':1,'ids':'reservoir'}
    problem['time_axes']['reservoir_history']='reservoir_history'
    problem['fields']['reservoir_depth']={'array':'reservoir_depth','quantity':'depth','location':'reservoir','time_axis':'reservoir_history','dtype':'float64','kind':'scalar','component_shape':[1],'components':['value'],'unit':'m','value_kind':'point','sampling':{'space':'piecewise_constant','time':'linear','extrapolation':'forbid'}}
    problem['conditions'].append({'role':'boundary','variable':'water','operator':'water_reservoir','location':'reservoir','data':{'depth':{'field':'reservoir_depth'},'velocity':{'value':[0.,0.],'unit':'m/s'}}})
    save(job/'input/problem.json',problem)
    with h5py.File(job/'input/input.h5','a') as f:
        del f['wall'];f['wall']=np.flatnonzero(~inlet).astype(np.int64)+len(c)+1
        f['reservoir']=np.flatnonzero(inlet).astype(np.int64)+len(c)+1
        f['reservoir_history']=times
        f['reservoir_depth']=np.broadcast_to(vals[:,None,None],(len(times),int(inlet.sum()),1))
    raw=dict(np.load(job/'native-input.npz'));raw.update(reservoir_times=times,reservoir_depth=vals)
    np.savez(job/'native-input.npz',**raw)
    save(job/'reservoir-adapter.json',{'physical_boundary':'Exterior h(t), u=0; same bed on both sides. Ghost state only; native Riemann kernel applies sign-split fluctuations at x=0. Interior boundary cells are evolved, not overwritten. Tangential exterior and initial velocity both zero.','source':'https://github.com/clawpack/riemann/blob/v5.9.0/src/rpn2_shallow_bathymetry_fwave.f90','scope':'single finite case; no friction, holes or drying','native_input_sha256':digest(job/'native-input.npz'),'numerical_validation':False})
    from shallow_reservoir_fields import normalize
    normalize(job)
    return m,ids


def run(root,e,g):
    job=root/'cases'/e['design_id'];status=job/'status.json'
    if status.exists():return json.loads(status.read_text())
    job.mkdir();save(job/'design.json',e);state={'design_id':e['design_id'],'status':'queued'};save(status,state);name='ch02reservoir-'+hashlib.sha256(e['design_id'].encode()).hexdigest()[:12]+'-'+str(time.time_ns())[-9:]
    try:
        with reservation(root,name):
            m,ids=prepare(job,e,True);runtime=Path(__file__).with_name('pyclaw_reservoir_runtime.py');shutil.copy2(runtime,job/runtime.name)
            cmd=['docker','--host',SOCKET,'run','--name',name,'--network','none','--cpus','1','--memory','768m','--user',f'{os.getuid()}:{os.getgid()}','-e','OMP_NUM_THREADS=1','-e','OPENBLAS_NUM_THREADS=1','-v',f'{job}:/work','-w','/work',IMAGE,'python',runtime.name]
            record={'producer':'unmodified Clawpack/PyClaw 5.9.0 Classic 2D shallow_bathymetry_fwave_2D','image':IMAGE,'source_url':'https://github.com/clawpack/clawpack/tree/v5.9.0','script_sha256':digest(Path(__file__)),'conversion_script_sha256':digest(Path(__file__).with_name('native_pyclaw_closed_flat.py')),'native_configuration_script_sha256':digest(runtime),'command':cmd,'start_unix':time.time(),'native_dry_tolerance':1e-10,'native_sea_level':0.,'physical_scope':'Fully wet, zero drag; x=0 external reservoir ghost state, other boundaries reflective; native f-wave wave splitting. No accuracy validation.','numerical_validation':False};save(job/'execution.json',record);state.update(status='running',container=name);save(status,state)
            with (job/'solver.log').open('w') as log:cp=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
            assert cp.returncode==0,f'native exit {cp.returncode}'
            record['binary_sha256']=json.loads((job/'native-runtime.json').read_text())['riemann_binary_sha256'];save(job/'execution.json',record)
            result=convert(job,e,m,ids);result['mapping']=result['mapping'].replace('HLLE','bathymetry f-wave').replace('zero drag/flat bed','zero drag/P1 bed mapped to exact native cell averages');result['mapping']=result['mapping'].replace('reflective walls','x=0 reservoir Riemann interface and other walls');state.update(result);save(job/'reference/grading.json',g);state['status']='unvalidated_candidate'
    except Exception as ex:state.update(status='needs_attention',error=repr(ex),traceback=traceback.format_exc())
    state['ended_unix']=time.time();save(status,state);return state


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int,default=5);args=ap.parse_args()
    p=next(args.snapshot.glob('qbank/02-fluid-mechanics/*/fully-wet-transient/author/chapter02-ten-20261020/design.json'));freeze=json.loads((args.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text());assert digest(p)==freeze['designs'][p.relative_to(args.snapshot).as_posix()];d=json.loads(p.read_text());tasks=[]
    e=next(e for e in d['proposed_cases'] if e['design_id']==CASE)
    g=json.loads((p.parents[1]/'grading-template.json').read_text())
    states=[run(args.root,{**e,'task':d['task'],'model':d['model']},g)]
    save(args.root/'maintenance/pyclaw-reservoir-summary.json',states)


if __name__=='__main__':main()
