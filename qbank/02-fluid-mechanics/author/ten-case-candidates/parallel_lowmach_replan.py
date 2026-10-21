"""Finite reviewed native MPI replans; preserve each stopped serial attempt."""
import argparse
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import traceback
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial import cKDTree
import native_lowmach as base
from native_closed_cavity import SOCKET,save,digest
from titan_resources import reservation
CASE='ch02-2-2-4-02-natural_convection'

def merge_frame(pvtu,x):
    totals={};count=np.zeros(len(x));tree=cKDTree(x)
    for piece in ET.parse(pvtu).findall('.//Piece'):
        p=pvtu.parent/piece.get('Source');t=ET.parse(p);pos=np.fromstring(t.find('.//Points/DataArray').text,sep=' ').reshape(-1,3)[:,:x.shape[1]];dist,ids=tree.query(pos);assert dist.max()<1e-8
        np.add.at(count,ids,1)
        for a in t.findall('.//PointData/DataArray'):
            key=a.get('Name').lower()
            if key not in ('velocity','pressure','temperature'):continue
            v=np.fromstring(a.text,sep=' ').reshape(len(pos),-1)
            if key not in totals:totals[key]=np.zeros((len(x),v.shape[1]))
            np.add.at(totals[key],ids,v)
    assert np.all(count>0) and set(totals)=={'velocity','pressure','temperature'}
    return {k:v/count[:,None] for k,v in totals.items()}

def run_one(r,approval,cores):
    case=approval['case_id'];assert cores in (8,16);assert int(os.environ['CH02_SOLVE_BUDGET_SECONDS'])<=7100
    archive=Path(approval['archive']);assert digest(archive/'native/case.sif')==approval['original_sif_sha256']
    image=json.loads((r/'maintenance/elmer-mpi-native-stage/stage.json').read_text());assert image['status']=='native_mpi_ready_pending_parallel_case_adapter';image=image['image']
    e=json.loads((archive/'design.json').read_text());s=e['detailed_spec'];assert e['design_id']==case and s['analysis_kind']=='transient';j=r/'cases'/case;assert not j.exists();j.mkdir();save(j/'design.json',e);state={'design_id':case,'status':'queued'};save(j/'status.json',state);name='ch02lowmach-mpi-'+str(time.time_ns())[-9:]
    try:
        with reservation(r,name,cpu=cores,memory_limit_bytes=8*1024**3,workload='parallel_long'):
            n=j/'native';n.mkdir();shutil.copytree(archive/'native/mesh',n/'mesh',ignore=shutil.ignore_patterns('partitioning.*'));shutil.copy2(archive/'adapter-data.npz',j/'adapter-data.npz')
            z=np.load(j/'adapter-data.npz');m={k:z[k] for k in z.files if k not in ['mech','thermal','joint','hist','sources']};data=(m,z['mech'],z['thermal'],z['hist'],z['sources'])
            end=s['time_interval_s'][1];knots=sorted(set([0.,.1*end,.4*end,.6*end,end,*s['output_times_s']]));intervals=[math.ceil((b-a)/.01-1e-10) for a,b in zip(knots,knots[1:])];sizes=[(b-a)/n for a,b,n in zip(knots,knots[1:],intervals)];times=[]
            for lo,hi,num in zip(knots,knots[1:],intervals):times.extend(np.linspace(lo,hi,num+1)[1:].tolist())
            text=(archive/'native/case.sif').read_text();text=re.sub(r'Timestep Intervals\(1\) = 1000',f'Timestep Intervals({len(intervals)}) = '+' '.join(map(str,intervals)),text);text=re.sub(r'Timestep Sizes\(1\) = [^\n]+',f'Timestep Sizes({len(sizes)}) = '+' '.join(format(v,'.17g') for v in sizes),text);text=text.replace('Output Intervals(1) = 1',f'Output Intervals({len(sizes)}) = '+' '.join('1' for _ in sizes))
            text=text.replace('Steady State Max Iterations = 20','Steady State Max Iterations = 10').replace('Steady State Convergence Tolerance = 1e-8','Steady State Convergence Tolerance = 1e-6').replace('Nonlinear System Max Iterations = 30','Nonlinear System Max Iterations = 20').replace('Nonlinear System Convergence Tolerance = 1e-8','Nonlinear System Convergence Tolerance = 1e-6').replace('Nonlinear System Convergence Tolerance = 1e-9','Nonlinear System Convergence Tolerance = 1e-6').replace('Nonlinear System Newton After Iterations = 1000000','Nonlinear System Newton After Iterations = 3').replace('Linear System Convergence Tolerance = 1e-10','Linear System Convergence Tolerance = 1e-8').replace('Linear System Convergence Tolerance = 1e-11','Linear System Convergence Tolerance = 1e-8')
            (n/'case.sif').write_text(text);save(j/'parallel-numerical-plan.json',{'cores':cores,'native_time_steps':len(times),'time_knots':knots,'native_frame_times':times,'production_tolerances':'Nonlinear/coupled1e-6,linear1e-8; Newton after3; no accuracy certificate','wall_budget_seconds':7100,'basis':approval['numerical_plan_basis'],'physical_change':False,'original_sif_sha256':approval['original_sif_sha256']})
            shell=f'cd /work/native && /opt/elmer-mpi/bin/ElmerGrid 2 2 mesh -metis {cores} > /work/partition.log 2>&1 && mpirun -np {cores} /opt/elmer-mpi/bin/ElmerSolver_mpi case.sif'
            cmd=['docker','--host',SOCKET,'run','--name',name,'--network','none','--cpus',str(cores),'--memory','8g','--label','ch02.workload=parallel_long','--user',f'{os.getuid()}:{os.getgid()}','-e','HOME=/tmp','-e','OMP_NUM_THREADS=1','-e','OPENBLAS_NUM_THREADS=1','-e','ELMER_HOME=/opt/elmer-mpi','-e','LD_LIBRARY_PATH=/opt/elmer-mpi/lib/elmersolver:/opt/elmer-mpi/lib:/usr/lib/x86_64-linux-gnu','-v',f'{j}:/work',image,'bash','-c',shell]
            save(j/'execution.json',{'image':image,'command':cmd,'start_unix':time.time(),'script_sha256':digest(Path(__file__)),'conversion_sha256':digest(Path(base.__file__)),'native_ranks':cores,'workload':'parallel_long','solver_budget_seconds':7100,'source_commit':'a19504ac53ec222e3355e182b08f2ff280c2203a','reviewed_replan':str(r/'maintenance/parallel-lowmach-batch-approval.json'),'numerical_validation':False});state.update(status='running',container=name);save(j/'status.json',state)
            with (j/'solver.log').open('w') as log:cp=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
            assert cp.returncode==0,f'Native MPI exit{cp.returncode}'
            logtext=(j/'solver.log').read_text(errors='replace')
            if re.search(r'NAVIER-STOKES ITERATION\s+20\b|Coupled system iteration:\s+10\b',logtext):
                state.update(status='native_iteration_limit',reason='Native configured iteration ceiling reached; conservatively retain raw results without candidate packaging.');save(j/'status.json',state);return
            files=sorted(n.rglob('solution*.pvtu'));assert len(files)==len(times),(len(files),len(times));frames={}
            for t in s['output_times_s']:
                k=int(np.argmin(np.abs(np.array(times)-t)));assert abs(times[k]-t)<1e-12;frames[round(float(t),12)]=merge_frame(files[k],m['x'])
            state.update(base.convert(j,e,data,native_frames=frames));save(j/'reference/grading.json',json.loads((archive/'grading-template.json').read_text()) if (archive/'grading-template.json').exists() else approval['grading']);state.update(status='unvalidated_candidate',mpi_ranks=cores,native_steps=len(times))
    except Exception as ex:state.update(status='needs_attention',error=repr(ex),traceback=traceback.format_exc())
    state['ended_unix']=time.time();save(j/'status.json',state)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int,default=1);a=ap.parse_args()
    approval=json.loads((a.root/'maintenance/parallel-lowmach-replan-approval.json').read_text());approval['case_id']=CASE
    approval['numerical_plan_basis']='Initial reviewed8-rank case with same mesh and physics, ~100steps, 7100s guard; no accuracy certificate.'
    run_one(a.root,approval,int(os.environ['CH02_LONG_SOLVER_CORES']))
if __name__=='__main__':main()
