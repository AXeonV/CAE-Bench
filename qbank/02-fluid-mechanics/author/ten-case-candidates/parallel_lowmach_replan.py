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
        p=pvtu.parent/piece.get('Source');t=ET.parse(p);pos=np.fromstring(t.find('.//Points/DataArray').text,sep=' ').reshape(-1,3)[:,:x.shape[1]];dist,nearest=tree.query(pos,k=2);assert np.all(dist[:,0]<1e-7*max(1.,np.abs(x).max())) and np.all(dist[:,1]>10*dist[:,0]), 'native node order';ids=nearest[:,0]
        np.add.at(count,ids,1)
        for a in t.findall('.//PointData/DataArray'):
            key=a.get('Name').lower()
            if key not in ('velocity','pressure','temperature','kinetic energy','kinetic dissipation'):continue
            v=np.fromstring(a.text,sep=' ').reshape(len(pos),-1)
            if key not in totals:totals[key]=np.zeros((len(x),v.shape[1]))
            np.add.at(totals[key],ids,v)
    assert np.all(count>0) and {'velocity','pressure','temperature'}.issubset(totals)
    return {k:v/count[:,None] for k,v in totals.items()}

def run_one(r,approval,cores):
    case=approval['case_id'];assert cores in (8,16);assert int(os.environ['CH02_SOLVE_BUDGET_SECONDS'])<=14300
    archive=Path(approval['archive']);assert digest(archive/'native/case.sif')==approval['original_sif_sha256']
    image=json.loads((r/'maintenance/elmer-mpi-native-stage/stage.json').read_text());assert image['status']=='native_mpi_ready_pending_parallel_case_adapter';image=image['image']
    e=json.loads((archive/'design.json').read_text());view=e
    if approval.get('converter')=='thermal_statistics':
        from native_thermal_statistics import sample_view
        view=sample_view(e)
    s=view['detailed_spec'];assert e['design_id']==case and s['analysis_kind']=='transient';j=r/'cases'/case;assert not j.exists();j.mkdir();save(j/'design.json',e);state={'design_id':case,'status':'queued'};save(j/'status.json',state);name='ch02lowmach-mpi-'+str(time.time_ns())[-9:]
    try:
        with reservation(r,name,cpu=cores,memory_limit_bytes=8*1024**3,workload='parallel_long'):
            n=j/'native';n.mkdir();
            if (archive/'native-closure.json').exists():shutil.copy2(archive/'native-closure.json',j/'native-closure.json')
            if approval.get('nonuniform_initial'):
                for filename in ('initial-ke-input.npz','initial-ke-mapping.json'):shutil.copy2(archive/filename,j/filename)
                shutil.copy2(archive/'native/initial-ke.dat',n/'initial-ke.dat')
                shutil.copy2(Path(__file__).with_name('InitialKE_MPI.F90'),n/'InitialKE_MPI.F90')
            shutil.copytree(archive/'native/mesh',n/'mesh',ignore=shutil.ignore_patterns('partitioning.*'));shutil.copy2(archive/'adapter-data.npz',j/'adapter-data.npz')
            z=np.load(j/'adapter-data.npz');m={k:z[k] for k in z.files if k not in ['mech','thermal','joint','hist','sources']};data=(m,z['mech'],z['thermal'],z['hist'],z['sources'])
            end=s['time_interval_s'][1];knots=sorted(set([0.,.1*end,.4*end,.6*end,end,*s['output_times_s']]));intervals=[math.ceil((b-a)/.01-1e-10) for a,b in zip(knots,knots[1:])];sizes=[(b-a)/n for a,b,n in zip(knots,knots[1:],intervals)];times=[]
            for lo,hi,num in zip(knots,knots[1:],intervals):times.extend(np.linspace(lo,hi,num+1)[1:].tolist())
            text=(archive/'native/case.sif').read_text()
            if approval.get('converter')=='thermal_statistics':
                text=text.replace('Linear System Solver = Direct','Linear System Solver = Iterative').replace('Linear System Direct Method = UMFPACK','! Native MPI BiCGStabL/ILU1; serial UMFPACK removed')
                save(j/'native-sampling-view.json',view)
            text=re.sub(r'Timestep Intervals\(1\) = 1000',f'Timestep Intervals({len(intervals)}) = '+' '.join(map(str,intervals)),text);text=re.sub(r'Timestep Sizes\(1\) = [^\n]+',f'Timestep Sizes({len(sizes)}) = '+' '.join(format(v,'.17g') for v in sizes),text);text=text.replace('Output Intervals(1) = 1',f'Output Intervals({len(sizes)}) = '+' '.join('1' for _ in sizes))
            coupled_max=int(approval.get('coupled_max_iterations',10));assert 10<=coupled_max<=30
            nonlinear_max=int(approval.get('nonlinear_max_iterations',20));assert 20<=nonlinear_max<=40
            text=text.replace('Steady State Max Iterations = 20',f'Steady State Max Iterations = {coupled_max}').replace('Steady State Convergence Tolerance = 1e-8','Steady State Convergence Tolerance = 1e-6').replace('Nonlinear System Max Iterations = 30',f'Nonlinear System Max Iterations = {nonlinear_max}').replace('Nonlinear System Convergence Tolerance = 1e-8','Nonlinear System Convergence Tolerance = 1e-6').replace('Nonlinear System Convergence Tolerance = 1e-9','Nonlinear System Convergence Tolerance = 1e-6').replace('Nonlinear System Newton After Iterations = 1000000','Nonlinear System Newton After Iterations = 3').replace('Linear System Convergence Tolerance = 1e-10','Linear System Convergence Tolerance = 1e-8').replace('Linear System Convergence Tolerance = 1e-11','Linear System Convergence Tolerance = 1e-8')
            (n/'case.sif').write_text(text);save(j/'parallel-numerical-plan.json',{'cores':cores,'coupled_max_iterations':coupled_max,'nonlinear_max_iterations':nonlinear_max,'native_time_steps':len(times),'time_knots':knots,'native_frame_times':times,'production_tolerances':'Nonlinear/coupled1e-6,linear1e-8; Newton after3; no accuracy certificate','wall_budget_seconds':int(os.environ['CH02_SOLVE_BUDGET_SECONDS']),'basis':approval['numerical_plan_basis'],'physical_change':False,'original_sif_sha256':approval['original_sif_sha256']})
            shell=f'cd /work/native && /opt/elmer-mpi/bin/ElmerGrid 2 2 mesh -metis {cores} > /work/partition.log 2>&1 && mpirun -np {cores} /opt/elmer-mpi/bin/ElmerSolver_mpi case.sif'
            if approval.get('nonuniform_initial'):
                shell=shell.replace('cd /work/native && ', 'cd /work/native && /opt/elmer-mpi/bin/elmerf90 -shared InitialKE_MPI.F90 -o CAEInitialFields.so > /work/initial-ke-build.log 2>&1 && ',1)
            cmd=['docker','--host',SOCKET,'run','--name',name,'--network','none','--cpus',str(cores),'--memory','8g','--label','ch02.workload=parallel_long','--user',f'{os.getuid()}:{os.getgid()}','-e','HOME=/tmp','-e','OMP_NUM_THREADS=1','-e','OPENBLAS_NUM_THREADS=1','-e','ELMER_HOME=/opt/elmer-mpi','-e','LD_LIBRARY_PATH=/opt/elmer-mpi/lib/elmersolver:/opt/elmer-mpi/lib:/usr/lib/x86_64-linux-gnu','-v',f'{j}:/work',image,'bash','-c',shell]
            save(j/'execution.json',{'image':image,'command':cmd,'start_unix':time.time(),'script_sha256':digest(Path(__file__)),'conversion_sha256':digest(Path(base.__file__)),'native_ranks':cores,'workload':'parallel_long','solver_budget_seconds':int(os.environ['CH02_SOLVE_BUDGET_SECONDS']),'source_commit':'a19504ac53ec222e3355e182b08f2ff280c2203a','reviewed_replan':approval.get('approval_file',str(r/'maintenance/parallel-lowmach-batch-approval.json')),'numerical_validation':False});state.update(status='running',container=name);save(j/'status.json',state)
            with (j/'solver.log').open('w') as log:cp=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
            assert cp.returncode==0,f'Native MPI exit{cp.returncode}'
            logtext=(j/'solver.log').read_text(errors='replace')
            from native_coupled_completion import assess
            termination=assess(j);save(j/'native-termination.json',termination)
            if not termination['native_coupled_termination_complete']:
                state.update(status='native_iteration_limit',reason='One or more steps lack final converged native coupled termination.');save(j/'status.json',state);return
            files=sorted(n.rglob('solution*.pvtu'));assert len(files)==len(times),(len(files),len(times));frames={}
            for t in s['output_times_s']:
                k=int(np.argmin(np.abs(np.array(times)-t)));assert abs(times[k]-t)<1e-12;frames[round(float(t),12)]=merge_frame(files[k],m['x'])
            converter=base
            if approval.get('converter')=='thermal_urans':
                import native_thermal_rans as converter
            if approval.get('converter')=='thermal_statistics':
                import native_thermal_statistics as statistics
                result=statistics.convert(j,e,view,data,native_frames=frames)
            else:result=converter.convert(j,e,data,native_frames=frames)
            state.update(result);save(j/'reference/grading.json',json.loads((archive/'grading-template.json').read_text()) if (archive/'grading-template.json').exists() else approval['grading']);state.update(status='unvalidated_candidate',mpi_ranks=cores,native_steps=len(times))
    except Exception as ex:state.update(status='needs_attention',error=repr(ex),traceback=traceback.format_exc())
    state['ended_unix']=time.time();save(j/'status.json',state)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int,default=1);a=ap.parse_args()
    approval=json.loads((a.root/'maintenance/parallel-lowmach-replan-approval.json').read_text());approval['case_id']=CASE
    approval['numerical_plan_basis']='Initial reviewed8-rank case with same mesh and physics, ~100steps, 7100s guard; no accuracy certificate.'
    run_one(a.root,approval,int(os.environ['CH02_LONG_SOLVER_CORES']))
if __name__=='__main__':main()
