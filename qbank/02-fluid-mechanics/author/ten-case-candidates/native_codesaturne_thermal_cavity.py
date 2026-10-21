"""One bounded stock Code_Saturne relaxation; raw completion is not a reference."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import traceback
from native_closed_cavity import SOCKET,save,digest
from titan_resources import reservation
IMAGE='sha256:e9cae326ea20d5903fdf819f21a58a3bfb179c8c194804724429a5c1979e40d9'
CASE='ch02-2-2-11-01-thermal_cavity'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int,default=1);args=ap.parse_args();r=args.root
    p=next(args.snapshot.glob('qbank/02-fluid-mechanics/*/newtonian-compressible-steady-3d/author/chapter02-ten-20261020/design.json'));frozen=json.loads((args.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text());assert digest(p)==frozen['designs'][p.relative_to(args.snapshot).as_posix()];d=json.loads(p.read_text());e=next(e for e in d['proposed_cases'] if e['design_id']==CASE)
    job=r/'cases'/CASE;assert not job.exists(),'Inspect existing attempt; never automatically repeat';job.mkdir();save(job/'design.json',{**e,'task':d['task'],'model':d['model']});state={'design_id':CASE,'status':'queued'};save(job/'status.json',state);name='ch02cs-cavity-'+str(time.time_ns())[-9:]
    try:
        with reservation(r,name):
            proto=r/'maintenance/code-saturne-case-adapter';n=job/'native';n.mkdir();shutil.copy2(proto/'mesh_input',n/'mesh_input');shutil.copy2(proto/'mesh-identity.npz',job/'mesh-identity.npz');shutil.copy2(proto/'public-mesh.msh',job/'public-mesh.msh')
            case=n/'study/cavity'
            for directory in ['DATA','SRC','RESU','SCRIPTS']:(case/directory).mkdir(parents=True,exist_ok=True)
            shutil.copy2(proto/'study/cavity/DATA/setup.xml',case/'DATA/setup.xml')
            for namefile in ['codesaturne_relaxation_setup.py','codesaturne_relaxation_observer.c','codesaturne_thermal_wall.f90']:shutil.copy2(Path(__file__).with_name(namefile),n/namefile)
            shutil.copy2(n/'codesaturne_relaxation_observer.c',case/'SRC/cs_user_extra_operations.c')
            shutil.copy2(n/'codesaturne_thermal_wall.f90',case/'SRC/cs_user_boundary_conditions.f90')
            save(n/'boundary-interface.json',{'scope':'Only prescribed wall temperature and zero heat flux via stock Fortran boundary callback; no PDE/state/closure edits.','sha256':digest(n/'codesaturne_thermal_wall.f90'),'source':'Code_Saturne6.0 installed cs_user_boundary_conditions.f90 and native cfxtcl.f90 temperature code5.','zone_ids':{'1':'hot_wall305K','2':'cold_wall295K','3':'adiabatic'}})
            code='cd /work/native && /usr/bin/python3 codesaturne_relaxation_setup.py && code_saturne run --case /work/native/study/cavity --param setup.xml --id candidate --nprocs 1'
            cmd=['docker','--host',SOCKET,'run','--name',name,'--network','none','--cpus','1','--memory','768m','--user',f'{os.getuid()}:{os.getgid()}','-e','USER=caeoj','-e','LOGNAME=caeoj','-e','HOME=/tmp','-e','OMP_NUM_THREADS=1','-e','PYTHONPATH=/usr/lib/python3/dist-packages/code_saturne','-v',str(job)+':/work',IMAGE,'bash','-c',code]
            save(job/'execution.json',{'producer':'Stock Code_Saturne6.0.2 compressible ideal-gas total energy, full native stress work. Native global-time adaptive relaxation, mean-density inventory monitored.','command':cmd,'image':IMAGE,'script_sha256':digest(Path(__file__)),'observer_sha256':digest(n/'codesaturne_relaxation_observer.c'),'setup_sha256':digest(n/'codesaturne_relaxation_setup.py'),'observer_scope':'Read-only field/output monitor plus native terminal-step request; no PDE/constitutive/state modification.','iteration_cap':5000,'stop':'After50 steps and1000s, relative state change<1e-8 and mass error<1e-6 for20 consecutive steps. These are production stops, not numerical validation.','numerical_validation':False});state.update(status='running',container=name);save(job/'status.json',state)
            with (job/'solver.log').open('w') as log:cp=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
            assert cp.returncode==0,f'Code_Saturne exit {cp.returncode}'
            stop=next((case/'RESU/candidate').rglob('caeoj-native-stop.json'));record=json.loads(stop.read_text());state.update(native_stop=record,native_result_directory=str(stop.parent.relative_to(job)));state['status']='native_complete_pending_conversion' if record['converged'] else 'native_iteration_limit'
    except Exception as ex:state.update(status='needs_attention',error=repr(ex),traceback=traceback.format_exc())
    state['ended_unix']=time.time();save(job/'status.json',state)

if __name__=='__main__':main()
