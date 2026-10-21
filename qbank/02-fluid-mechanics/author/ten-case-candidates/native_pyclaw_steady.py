"""Finite fully-wet steady, zero-friction reservoir native PyClaw queue."""
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
import copy
import h5py
import numpy as np
from native_closed_cavity import SOCKET,save,digest
from titan_resources import reservation


def prepare(job,e,allow_bed=True):
    spec=e['detailed_spec'];boundaries=spec['boundaries']
    assert spec['analysis_kind']=='steady' and len(boundaries)==3
    assert [b['selection'] for b in boundaries[1:]]==['x=0','x=Lx']
    speed=float(boundaries[1]['data']['velocity']['expression'][0])
    for b in boundaries[1:]:
        assert b['operator']=='water_reservoir' and b['data']['depth_m']==1.
        assert b['data']['velocity']['expression']==[speed,0.]
    private=copy.deepcopy(e);ps=private['detailed_spec']
    ps['boundaries']=boundaries[:1]
    ps['initial']={'depth':{'expression':'1'},'velocity':{'expression':[0.,0.]}}
    m,ids=closed_prepare(job,private,True)
    x,c,b=m['x'],m['c'],m['b'];L=spec['geometry']['bounding_lengths']
    inlet=np.all(np.isclose(x[b,0],0.),axis=1);outlet=np.all(np.isclose(x[b,0],L[0]),axis=1)
    assert inlet.any() and outlet.any() and not (inlet&outlet).any()
    problem=json.loads((job/'input/problem.json').read_text())
    problem['conditions']=[a for a in problem['conditions'] if a['role']!='initial']
    problem['fields'].pop('depth0');problem['fields'].pop('velocity0')
    problem['time_axes'].pop('initial')
    for name,take in [('inlet',inlet),('outlet',outlet)]:
        problem['locations'][name]={'kind':'mesh','mesh':'main','entity':'element','dimension':1,'ids':name}
        problem['conditions'].append({'role':'boundary','variable':'water','operator':'water_reservoir','location':name,'data':{'depth':{'value':1.,'unit':'m'},'velocity':{'value':[speed,0.],'unit':'m/s'}}})
    save(job/'input/problem.json',problem)
    with h5py.File(job/'input/input.h5','a') as f:
        for key in ['wall','depth0','velocity0','initial']:del f[key]
        f['wall']=np.flatnonzero(~(inlet|outlet)).astype(np.int64)+len(c)+1
        f['inlet']=np.flatnonzero(inlet).astype(np.int64)+len(c)+1
        f['outlet']=np.flatnonzero(outlet).astype(np.int64)+len(c)+1
    raw=dict(np.load(job/'native-input.npz'));raw['q'][1]=raw['q'][0]*speed;raw['reservoir_speed']=speed
    np.savez(job/'native-input.npz',**raw)
    save(job/'input-transfer.json',{'method':'Exact clipping and affine integration of supplied public P1 bed onto native FV cells. Depth/momentum initial seed is private to the steady iteration; public steady input has no initial fields.','native_input_sha256':digest(job/'native-input.npz'),'numerical_validation':False})
    save(job/'steady-adapter.json',{'initialization':'Private native iteration seed h=1,u=(reservoir_speed,0), not a prescribed physical initial condition. No initial fields in public steady input.','boundary':'Both x faces are exterior-state Riemann interfaces; other faces impermeable. Native f-wave sign splitting, no interior overwrites.','stop':'Relative component state change per 1s <1e-8 for five consecutive windows; 1000-window cap. Not mesh/accuracy validation.','native_input_sha256':digest(job/'native-input.npz'),'numerical_validation':False})
    return m,ids


def run(root,e,g):
    job=root/'cases'/e['design_id'];status=job/'status.json'
    if status.exists():return json.loads(status.read_text())
    job.mkdir();save(job/'design.json',e);state={'design_id':e['design_id'],'status':'queued'};save(status,state);name='ch02steadywater-'+hashlib.sha256(e['design_id'].encode()).hexdigest()[:12]+'-'+str(time.time_ns())[-9:]
    try:
        with reservation(root,name):
            m,ids=prepare(job,e,True);runtime=Path(__file__).with_name('pyclaw_steady_runtime.py');shutil.copy2(runtime,job/runtime.name)
            cmd=['docker','--host',SOCKET,'run','--name',name,'--network','none','--cpus','1','--memory','768m','--user',f'{os.getuid()}:{os.getgid()}','-e','OMP_NUM_THREADS=1','-e','OPENBLAS_NUM_THREADS=1','-v',f'{job}:/work','-w','/work',IMAGE,'python',runtime.name]
            record={'producer':'unmodified Clawpack/PyClaw 5.9.0 Classic 2D shallow_bathymetry_fwave_2D','image':IMAGE,'source_url':'https://github.com/clawpack/clawpack/tree/v5.9.0','script_sha256':digest(Path(__file__)),'conversion_script_sha256':digest(Path(__file__).with_name('native_pyclaw_closed_flat.py')),'native_configuration_script_sha256':digest(runtime),'command':cmd,'start_unix':time.time(),'native_dry_tolerance':1e-10,'native_sea_level':0.,'physical_scope':'Steady fully wet, zero drag, exterior reservoirs at both x faces and reflective y walls. Finite convergence cap; no dry or accuracy claim.','numerical_validation':False};save(job/'execution.json',record);state.update(status='running',container=name);save(status,state)
            with (job/'solver.log').open('w') as log:cp=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
            assert cp.returncode==0,f'native exit {cp.returncode}'
            convergence=json.loads((job/'native-convergence.json').read_text())
            if not convergence['converged']:
                state.update(status='native_iteration_limit',ended_unix=time.time(),convergence_record='native-convergence.json');save(status,state);return state
            record['binary_sha256']=json.loads((job/'native-runtime.json').read_text())['riemann_binary_sha256'];save(job/'execution.json',record)
            result=convert(job,e,m,ids);result['mapping']=result['mapping'].replace('HLLE','bathymetry f-wave').replace('zero drag/flat bed','zero drag/P1 bed mapped to exact native cell averages');result['mapping']=result['mapping'].replace('reflective walls','two reservoir interfaces and y walls')+' Steady convergence record retained; requested time 0 labels the stationary field.';state.update(result);save(job/'reference/grading.json',g);state['status']='unvalidated_candidate'
    except Exception as ex:state.update(status='needs_attention',error=repr(ex),traceback=traceback.format_exc())
    state['ended_unix']=time.time();save(status,state);return state


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int,default=5);args=ap.parse_args()
    p=next(args.snapshot.glob('qbank/02-fluid-mechanics/*/fully-wet-steady/author/chapter02-ten-20261020/design.json'));freeze=json.loads((args.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text());assert digest(p)==freeze['designs'][p.relative_to(args.snapshot).as_posix()];d=json.loads(p.read_text());tasks=[]
    for e in d['proposed_cases']:
        s=e['detailed_spec']
        if s['parameters']['drag_rate']['value']!=0 or s['geometry']['holes'] or s['geometry']['operation']!='box':continue
        tasks.append(({**e,'task':d['task'],'model':d['model']},json.loads((p.parents[1]/'grading-template.json').read_text())))
    assert len(tasks)==5
    with ProcessPoolExecutor(max_workers=min(args.workers,5)) as pool:states=list(pool.map(run,[args.root]*5,[e for e,g in tasks],[g for e,g in tasks]))
    save(args.root/'maintenance/pyclaw-steady-summary.json',states)


if __name__=='__main__':main()
