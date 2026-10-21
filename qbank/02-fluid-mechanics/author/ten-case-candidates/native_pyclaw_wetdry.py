"""Finite closed zero-friction wet/dry native augmented Riemann queue."""
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
from native_pyclaw_closed_flat import IMAGE,prepare as closed_prepare,transfer
from native_lowmach import sample
from scipy.interpolate import RegularGridInterpolator
import copy
import h5py
import numpy as np
from native_closed_cavity import SOCKET,save,digest
from titan_resources import reservation


def prepare(job,e,allow_bed=True):
    spec=e['detailed_spec'];private=copy.deepcopy(e)
    private['detailed_spec']['initial']['depth']['expression']='1'
    m,ids=closed_prepare(job,private,True)
    h=sample(spec['initial']['depth']['expression'],m['x'],0.,spec)
    assert np.min(h)>=0. and np.max(h)>0.
    raw=dict(np.load(job/'native-input.npz'));raw['q'][0]=transfer(m['x'],m['c'],h,spec['geometry']['bounding_lengths'])
    np.savez(job/'native-input.npz',**raw)
    with h5py.File(job/'input/input.h5','a') as f:
        del f['depth0'];f['depth0']=h[None,:,None]
    save(job/'input-transfer.json',{'method':'Exact P1 public depth/bed integrals over clipped triangles onto native FV cells. Genuine zero-depth cells preserved, no depth floor or artificial water. Initial velocity zero.','native_input_sha256':digest(job/'native-input.npz'),'numerical_validation':False})
    return m,ids


def convert(job,e,m,ids):
    raw=np.load(job/'native-output.npz');times=raw['times'];assert np.array_equal(times,e['detailed_spec']['output_times_s']);points=m['x'][ids];hs=[];us=[];qs=[];volumes=[]
    for q in raw['q']:
        assert np.isfinite(q).all() and np.min(q[0])>=0.
        nodal=RegularGridInterpolator((raw['x'],raw['y']),np.moveaxis(q,0,-1),bounds_error=True)(points)
        h=nodal[:,0:1];flux=nodal[:,1:3];assert np.min(h)>=0.
        assert np.all(flux[h[:,0]==0]==0.),'Nonzero native reconstructed dry momentum'
        u=np.divide(flux,h,out=np.zeros_like(flux),where=h>0.)
        assert np.isfinite(u).all()
        hs.append(h);qs.append(flux);us.append(u);volumes.append([[q[0].sum()*np.prod(np.array(e['detailed_spec']['geometry']['bounding_lengths'])/q.shape[1:])]])
    ref=job/'reference';ref.mkdir()
    with h5py.File(ref/'reference.h5','w') as f:
        for key,a in {'observed':ids.astype(np.int64)+1,'integral':np.array([1],dtype=np.int64),'requested':times,'depth':hs,'velocity':us,'water_flux':qs,'water_volume':volumes}.items():f[key]=a
    return {'reference_sha256':digest(ref/'reference.h5'),'frames':len(times),'mapping':'Native PyClaw Classic 2D sw_aug_2D first order, native augmented wet/dry Riemann handling. Zero-friction closed rectangular geometry, actual P1 bed/depth integrals. Conservative native state bilinearly reconstructed at real public interior nodes; u=hu/h for positive h and exactly zero for h=0. No author depth clipping or added water. Water volume native FV integral. Spatial accuracy and wet/dry accuracy unverified.'}


def run(root,e,g):
    job=root/'cases'/e['design_id'];status=job/'status.json'
    if status.exists():return json.loads(status.read_text())
    job.mkdir();save(job/'design.json',e);state={'design_id':e['design_id'],'status':'queued'};save(status,state);name='ch02wetdry-'+hashlib.sha256(e['design_id'].encode()).hexdigest()[:12]+'-'+str(time.time_ns())[-9:]
    try:
        with reservation(root,name):
            m,ids=prepare(job,e,True);runtime=Path(__file__).with_name('pyclaw_wetdry_runtime.py');shutil.copy2(runtime,job/runtime.name)
            cmd=['docker','--host',SOCKET,'run','--name',name,'--network','none','--cpus','1','--memory','768m','--user',f'{os.getuid()}:{os.getgid()}','-e','OMP_NUM_THREADS=1','-e','OPENBLAS_NUM_THREADS=1','-v',f'{job}:/work','-w','/work',IMAGE,'python',runtime.name]
            record={'producer':'unmodified Clawpack/PyClaw 5.9.0 Classic 2D sw_aug_2D','image':IMAGE,'source_url':'https://github.com/clawpack/clawpack/tree/v5.9.0','script_sha256':digest(Path(__file__)),'conversion_script_sha256':digest(Path(__file__)),'native_configuration_script_sha256':digest(runtime),'command':cmd,'start_unix':time.time(),'native_dry_tolerance':1e-14,'native_order':1,'physical_scope':'Wetting/drying, zero drag, reflective walls; native augmented Riemann kernel handles dry states and bed source. First-order discretization; no accuracy certification.','numerical_validation':False};save(job/'execution.json',record);state.update(status='running',container=name);save(status,state)
            with (job/'solver.log').open('w') as log:cp=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
            assert cp.returncode==0,f'native exit {cp.returncode}'
            record['binary_sha256']=json.loads((job/'native-runtime.json').read_text())['riemann_binary_sha256'];save(job/'execution.json',record)
            result=convert(job,e,m,ids);state.update(result);save(job/'reference/grading.json',g);state['status']='unvalidated_candidate'
    except Exception as ex:state.update(status='needs_attention',error=repr(ex),traceback=traceback.format_exc())
    state['ended_unix']=time.time();save(status,state);return state


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int,default=5);args=ap.parse_args()
    p=next(args.snapshot.glob('qbank/02-fluid-mechanics/*/wetting-drying/author/chapter02-ten-20261020/design.json'));freeze=json.loads((args.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text());assert digest(p)==freeze['designs'][p.relative_to(args.snapshot).as_posix()];d=json.loads(p.read_text());tasks=[]
    for e in d['proposed_cases']:
        s=e['detailed_spec']
        if s['parameters']['drag_rate']['value']!=0 or s['geometry']['holes'] or s['geometry']['operation']!='box' or any(b['operator']!='water_wall' for b in s['boundaries']):continue
        tasks.append(({**e,'task':d['task'],'model':d['model']},json.loads((p.parents[1]/'grading-template.json').read_text())))
    assert len(tasks)==5
    with ProcessPoolExecutor(max_workers=min(args.workers,5)) as pool:states=list(pool.map(run,[args.root]*5,[e for e,g in tasks],[g for e,g in tasks]))
    save(args.root/'maintenance/pyclaw-wetdry-summary.json',states)


if __name__=='__main__':main()
