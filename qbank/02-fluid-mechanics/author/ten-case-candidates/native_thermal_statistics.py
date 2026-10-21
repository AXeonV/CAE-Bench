"""Direct native transient NS/heat samples, followed by prescribed statistics.

No RANS variables, synthesized fluctuations or new PDE implementation.
Resolution adequacy for DNS, temporal accuracy and statistical uncertainty
are NOT verified; these are candidate direct-simulation results only.
"""
import argparse
import copy
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import traceback
import h5py
import numpy as np
import native_lowmach as base
from native_closed_cavity import SOCKET, save, digest
from native_gas_film import IMAGE, COMMIT
from titan_resources import reservation


def sample_view(e):
    v=copy.deepcopy(e);s=v['detailed_spec'];p={k:q['value'] for k,q in s['parameters'].items()};assert s['analysis_kind']=='discrete_statistics';s['analysis_kind']='transient'
    n=round((p['statistics_end']-p['statistics_start'])/p['statistics_step']);times=p['statistics_start']+np.arange(n+1)*p['statistics_step']
    indices=times/s['time_interval_s'][1]*1000;assert np.allclose(indices,np.round(indices),atol=1e-9,rtol=0) and min(indices)>=1 and max(indices)<=1000
    s['output_times_s']=times.tolist();return v


def convert(job,e,view,data,native_frames=None):
    base.convert(job,view,data,native_frames=native_frames)
    path=job/'reference/reference.h5';samples=job/'native-sample-reference.h5';path.rename(samples)
    with h5py.File(samples,'r') as f:cells=f['cells'][...];u=f['velocity'][...];p=f['pressure'][...];T=f['temperature'][...];times=f['requested'][...]
    um=u.mean(axis=0);tm=T.mean(axis=0);du=u-um;dt=T-tm;count=len(times)
    values={'velocity':um[None],'pressure':p.mean(axis=0)[None],'temperature':tm[None],'velocity_covariance':(np.einsum('sni,snj->nij',du,du)/count)[None],'temperature_variance':np.mean(dt**2,axis=0)[None],'turbulent_heat_flux':np.mean(du*dt,axis=0)[None]}
    endpoint=np.array(e['detailed_spec']['output_times_s'],dtype=float);assert endpoint.shape==(1,) and np.isclose(endpoint[0],times[-1])
    with h5py.File(path,'w') as f:
        f['cells']=cells;f['requested']=endpoint
        for q,a in values.items():assert np.isfinite(a).all();f[q]=a
    problem_path=job/'input/problem.json';problem=json.loads(problem_path.read_text())
    with h5py.File(job/'input/input.h5','r+') as f:del f['requested'];f['requested']=endpoint
    for q,unit,kind,shape,components in [('velocity_covariance','m2/s2','tensor',[3,3],[a+b for a in 'xyz' for b in 'xyz']),('temperature_variance','K2','scalar',[1],['value']),('turbulent_heat_flux','K.m/s','vector',[3],list('xyz'))]:
        descriptor=dict(problem['outputs']['temperature']);descriptor.update(array=q,quantity=q,unit=unit,kind=kind,component_shape=shape,components=components);problem['outputs'][q]=descriptor
    save(problem_path,problem)
    record={'reference_sha256':digest(path),'frames':1,'statistical_sample_count':count,'sample_times':times.tolist(),'instantaneous_sample_sha256':digest(samples),'mapping':'Unmodified Elmer direct transient FlowSolver + HeatSolver, variable molecular properties, Boussinesq acceleration and molecular Friction Heat. Actual native P1 simplex averages are sampled at the exact prescribed times. Population moments use equal weights after spatial averaging. Pressure gauge imposed per sample. No Reynolds-model variance or synthetic perturbation.','limitation':'Direct unsteady candidate; spatial/time resolution adequacy for DNS and statistical uncertainty unverified. Stabilized P1 discretization may be underresolved; no DNS accuracy certification.','numerical_validation':False}
    save(job/'statistics-production.json',record);return record


def run(root,e,g,direct_retry=False):
    job=root/'cases'/e['design_id'];status=job/'status.json'
    if status.exists():return json.loads(status.read_text())
    job.mkdir(parents=True);save(job/'design.json',e);state={'design_id':e['design_id'],'status':'queued'};save(status,state);name='ch02thermalstats-'+hashlib.sha256(e['design_id'].encode()).hexdigest()[:12]+'-'+str(time.time_ns())[-9:]
    try:
        with reservation(root,name):
            state['status']='preparing';save(status,state);view=sample_view(e);save(job/'native-sampling-view.json',view);data=base.prepare(job,view)
            if direct_retry:
                sif=job/'native/case.sif';text=sif.read_text();assert text.count('Linear System Solver = Iterative')==2
                sif.write_text(text.replace('Linear System Solver = Iterative','Linear System Solver = Direct\nLinear System Direct Method = UMFPACK'))
                save(job/'linear-repair.json',{'reason':'Native IterSolve STOP 1: too many linear iterations with BiCGStabL/ILU1','new_native_linear_solver':'UMFPACK','physical_changes':False,'grid_time_step_or_tolerance_changes':False,'attempts':1})
            cmd=['docker','--host',SOCKET,'run','--name',name,'--network','none','--cpus','1','--memory','768m','--user',f'{os.getuid()}:{os.getgid()}','-e','OMP_NUM_THREADS=1','-e','OPENBLAS_NUM_THREADS=1','-v',f'{job.resolve()}:/work','-w','/work/native',IMAGE,'ElmerSolver','case.sif']
            save(job/'execution.json',{'producer':'unmodified Elmer direct transient FlowSolver + HeatSolver; sampled statistics','image':IMAGE,'source_commit':COMMIT,'source_url':f'https://github.com/ElmerCSC/elmerfem/tree/{COMMIT}/fem/src/modules','script_sha256':digest(Path(__file__)),'conversion_script_sha256':digest(Path(base.__file__)),'command':cmd,'start_unix':time.time(),'linear_configuration':'UMFPACK one-shot repair' if direct_retry else 'BiCGStabL/ILU1', 'native_closure':'Direct unsteady equations, no RANS or explicit SGS model; resolution adequacy unverified','numerical_validation':False});state.update(status='running',container=name);save(status,state)
            with (job/'solver.log').open('w') as log:cp=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
            assert cp.returncode==0,f'Elmer exit {cp.returncode}'
            state.update(convert(job,e,view,data));save(job/'reference/grading.json',g);state['status']='unvalidated_candidate'
    except Exception as ex:state.update(status='needs_attention',error=repr(ex),traceback=traceback.format_exc())
    state['ended_unix']=time.time();save(status,state);return state


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int,default=40);args=ap.parse_args();freeze=json.loads((args.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text());tasks=[]
    for p in args.snapshot.glob('qbank/02-fluid-mechanics/*/thermal-statistics-3d/author/chapter02-ten-20261020/design.json'):
        assert digest(p)==freeze['designs'][p.relative_to(args.snapshot).as_posix()];d=json.loads(p.read_text())
        for e in d['proposed_cases']:tasks.append(({**e,'task':d['task'],'model':d['model']},json.loads((p.parents[1]/'grading-template.json').read_text())))
    assert len(tasks)==10
    with ProcessPoolExecutor(max_workers=min(args.workers,len(tasks))) as pool:states=list(pool.map(run,[args.root]*len(tasks),[e for e,g in tasks],[g for e,g in tasks]))
    save(args.root/'maintenance/thermal-statistics-summary.json',states)


if __name__=='__main__':main()
