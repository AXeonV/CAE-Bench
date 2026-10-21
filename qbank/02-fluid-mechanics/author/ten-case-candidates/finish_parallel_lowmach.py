"""Bounded conversion of four successful native MPI runs; never launches a solver."""
import argparse
import fcntl
import json
from pathlib import Path
import re
import shutil
import subprocess
import time
import numpy as np
import native_lowmach as base
from parallel_lowmach_replan import merge_frame
from native_closed_cavity import SOCKET, save, digest
from titan_resources import reservation

def finish(root,job):
    with (job/'conversion.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        state=json.loads((job/'status.json').read_text())
        if state['status'] in ('unvalidated_candidate','native_iteration_limit','stopped_runtime_limit'):return True
        if state['status'] in ('running','queued','preparing'):return False
        assert state['status']=='needs_attention' and 'merge_frame' in state.get('traceback','')
        native=json.loads(subprocess.check_output(['docker','--host',SOCKET,'inspect',state['container']]))[0]
        assert not native['State']['Running'] and native['State']['Pid']==0 and native['State']['ExitCode']==0
        execution=json.loads((job/'execution.json').read_text());assert native['Image']==execution['image']
        assert any(m['Source']==str(job) and m['Destination']=='/work' for m in native['Mounts'])
        archive=root/'maintenance/adapter-attempts'/(job.name+'-mpi-coordinate-conversion');archive.mkdir(exist_ok=False)
        shutil.copy2(job/'status.json',archive/'status.json')
        for name in ('input','reference'):
            if (job/name).exists():shutil.copytree(job/name,archive/name)
        log=(job/'solver.log').read_text(errors='replace')
        if re.search(r'NAVIER-STOKES ITERATION\s+20\b|Coupled system iteration:\s+10\b',log):
            state.update(status='native_iteration_limit',reason='Native iteration ceiling reached; retain raw output without candidate claim.');save(job/'status.json',state);return True
        with reservation(root,'ch02-mpi-convert-'+str(time.time_ns())):
            e=json.loads((job/'design.json').read_text());z=np.load(job/'adapter-data.npz')
            m={k:z[k] for k in z.files if k not in ('mech','thermal','joint','hist','sources')};data=(m,z['mech'],z['thermal'],z['hist'],z['sources'])
            plan=json.loads((job/'parallel-numerical-plan.json').read_text());times=np.array(plan['native_frame_times']);files=sorted((job/'native').rglob('solution*.pvtu'));assert len(files)==len(times)
            frames={}
            for t in e['detailed_spec']['output_times_s']:
                k=int(np.argmin(abs(times-t)));assert abs(times[k]-t)<1e-12;frames[round(float(t),12)]=merge_frame(files[k],m['x'])
            result=base.convert(job,e,data,native_frames=frames)
            approvals=[json.loads((root/'maintenance/parallel-lowmach-replan-approval.json').read_text()),*json.loads((root/'maintenance/parallel-lowmach-batch-approval.json').read_text())['cases']]
            approval=next(a for a in approvals if Path(a['archive']).name.startswith(job.name+'-serial'))
            save(job/'reference/grading.json',approval['grading'])
            save(job/'conversion-repair.json',{'at_unix':time.time(),'native_container_id':native['Id'],'native_exit_code':0,'native_solver_rerun':False,'numerical_validation':False,'script_sha256':digest(Path(__file__)),'mapping_script_sha256':digest(Path(__file__).with_name('parallel_lowmach_replan.py')),'previous_status':str(archive/'status.json'),'reason':'VTU ASCII coordinate precision ~5e-8; nearest point within scale*1e-7 and >10x separation from second nearest. Exact original node identities retained.',**result})
            state.update(result,status='unvalidated_candidate',ended_unix=time.time());state.pop('error',None);state.pop('traceback',None);save(job/'status.json',state)
        return True

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);a=ap.parse_args()
    ids=['ch02-2-2-4-'+s for s in ('02-natural_convection','03-heated_lid','04-mixed_aiding','05-mixed_opposing')];deadline=time.time()+1800
    while ids and time.time()<deadline:
        ids=[case for case in ids if not finish(a.root,a.root/'cases'/case)]
        if ids:time.sleep(30)
    save(a.root/'maintenance/parallel-lowmach-conversion-summary.json',{'at_unix':time.time(),'remaining':ids,'solver_rerun':False})
if __name__=='__main__':main()
