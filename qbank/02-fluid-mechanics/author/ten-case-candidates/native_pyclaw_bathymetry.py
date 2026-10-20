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
from native_pyclaw_closed_flat import IMAGE,prepare,convert
from native_closed_cavity import SOCKET,save,digest
from titan_resources import reservation


def run(root,e,g):
    job=root/'cases'/e['design_id'];status=job/'status.json'
    if status.exists():return json.loads(status.read_text())
    job.mkdir();save(job/'design.json',e);state={'design_id':e['design_id'],'status':'queued'};save(status,state);name='ch02fwave-'+hashlib.sha256(e['design_id'].encode()).hexdigest()[:12]+'-'+str(time.time_ns())[-9:]
    try:
        with reservation(root,name):
            m,ids=prepare(job,e,True);runtime=Path(__file__).with_name('pyclaw_bathymetry_runtime.py');shutil.copy2(runtime,job/runtime.name)
            cmd=['docker','--host',SOCKET,'run','--name',name,'--network','none','--cpus','1','--memory','768m','--user',f'{os.getuid()}:{os.getgid()}','-e','OMP_NUM_THREADS=1','-e','OPENBLAS_NUM_THREADS=1','-v',f'{job}:/work','-w','/work',IMAGE,'python',runtime.name]
            record={'producer':'unmodified Clawpack/PyClaw 5.9.0 Classic 2D shallow_bathymetry_fwave_2D','image':IMAGE,'source_url':'https://github.com/clawpack/clawpack/tree/v5.9.0','script_sha256':digest(Path(__file__)),'conversion_script_sha256':digest(Path(__file__).with_name('native_pyclaw_closed_flat.py')),'native_configuration_script_sha256':digest(runtime),'command':cmd,'start_unix':time.time(),'native_dry_tolerance':1e-10,'native_sea_level':0.,'physical_scope':'Fully wet, zero drag, reflective walls; native f-wave handles the bottom source. Dry handling unverified and not used as a wetting/drying reference.','numerical_validation':False};save(job/'execution.json',record);state.update(status='running',container=name);save(status,state)
            with (job/'solver.log').open('w') as log:cp=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
            assert cp.returncode==0,f'native exit {cp.returncode}'
            record['binary_sha256']=json.loads((job/'native-runtime.json').read_text())['riemann_binary_sha256'];save(job/'execution.json',record)
            result=convert(job,e,m,ids);result['mapping']=result['mapping'].replace('HLLE','bathymetry f-wave').replace('zero drag/flat bed','zero drag/P1 bed mapped to exact native cell averages');state.update(result);save(job/'reference/grading.json',g);state['status']='unvalidated_candidate'
    except Exception as ex:state.update(status='needs_attention',error=repr(ex),traceback=traceback.format_exc())
    state['ended_unix']=time.time();save(status,state);return state


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int,default=5);args=ap.parse_args()
    p=next(args.snapshot.glob('qbank/02-fluid-mechanics/*/fully-wet-transient/author/chapter02-ten-20261020/design.json'));freeze=json.loads((args.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text());assert digest(p)==freeze['designs'][p.relative_to(args.snapshot).as_posix()];d=json.loads(p.read_text());tasks=[]
    for e in d['proposed_cases']:
        s=e['detailed_spec']
        if e['design_id']=='ch02-2-9-2-01-gaussian_hump' or s['parameters']['drag_rate']['value']!=0 or s['geometry']['holes'] or s['geometry']['operation']!='box' or any(b['operator']!='water_wall' for b in s['boundaries']):continue
        tasks.append(({**e,'task':d['task'],'model':d['model']},json.loads((p.parents[1]/'grading-template.json').read_text())))
    assert len(tasks)==5
    with ProcessPoolExecutor(max_workers=min(args.workers,5)) as pool:states=list(pool.map(run,[args.root]*5,[e for e,g in tasks],[g for e,g in tasks]))
    save(args.root/'maintenance/pyclaw-bathymetry-summary.json',states)


if __name__=='__main__':main()
