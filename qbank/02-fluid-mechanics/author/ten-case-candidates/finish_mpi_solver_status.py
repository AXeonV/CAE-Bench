"""One bounded conversion-only repair of conservatively misclassified MPI jobs."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import time
import numpy as np
import native_lowmach
from native_closed_cavity import SOCKET,save,digest
from native_coupled_completion import assess
from parallel_lowmach_replan import merge_frame
from titan_resources import reservation

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);a=ap.parse_args();root=a.root;out=[]
    approvals=[]
    for name in ('parallel-lowmach-replan-approval.json','parallel-lowmach-batch-approval.json','parallel-urans-batch-approval.json','parallel-statistics-batch-approval.json'):
        v=json.loads((root/'maintenance'/name).read_text());approvals.extend(v['cases'] if 'cases' in v else [v])
    for p in sorted((root/'cases').glob('*/parallel-numerical-plan.json')):
        job=p.parent;state=json.loads((job/'status.json').read_text())
        if state['status']!='native_iteration_limit':continue
        report=assess(job);out.append({'case_id':job.name,**report})
        if not report['native_coupled_termination_complete']:continue
        execution=json.loads((job/'execution.json').read_text());c=json.loads(subprocess.check_output(['docker','--host',SOCKET,'inspect',state['container']]))[0]
        assert not c['State']['Running'] and c['State']['Pid']==0 and c['State']['ExitCode']==0 and c['Image']==execution['image']
        assert any(m['Source']==str(job) and m['Destination']=='/work' for m in c['Mounts'])
        approval=next(v for v in approvals if Path(v['archive']).name.startswith(job.name+'-serial'))
        archive=root/'maintenance/adapter-attempts'/(job.name+'-inner-cap-status');archive.mkdir(exist_ok=False);shutil.copy2(job/'status.json',archive/'status.json')
        for name in ('input','reference'):
            if (job/name).exists():shutil.copytree(job/name,archive/name)
        with reservation(root,'ch02-completion-convert-'+str(time.time_ns())):
            e=json.loads((job/'design.json').read_text());view=e
            if approval.get('converter')=='thermal_statistics':
                import native_thermal_statistics as converter
                view=converter.sample_view(e)
            elif approval.get('converter')=='thermal_urans':import native_thermal_rans as converter
            else:converter=native_lowmach
            z=np.load(job/'adapter-data.npz');m={k:z[k] for k in z.files if k not in ('mech','thermal','joint','hist','sources')};data=(m,z['mech'],z['thermal'],z['hist'],z['sources'])
            plan=json.loads(p.read_text());times=np.array(plan['native_frame_times']);files=sorted((job/'native').rglob('solution*.pvtu'));assert len(files)==len(times);frames={}
            for t in view['detailed_spec']['output_times_s']:
                i=int(np.argmin(abs(times-t)));assert abs(times[i]-t)<1e-12;frames[round(float(t),12)]=merge_frame(files[i],m['x'])
            result=converter.convert(job,e,view,data,native_frames=frames) if approval.get('converter')=='thermal_statistics' else converter.convert(job,e,data,native_frames=frames)
            save(job/'reference/grading.json',approval['grading']);save(job/'native-termination-status-repair.json',{'at_unix':time.time(),'prior_status':str(archive/'status.json'),'native_container_id':c['Id'],'solver_rerun':False,'numerical_validation':False,'repair_script_sha256':digest(Path(__file__)),**report})
            state.update(result,status='unvalidated_candidate',ended_unix=time.time());state.pop('reason',None);save(job/'status.json',state)
    save(root/'maintenance/native-coupled-status-repair-summary.json',{'at_unix':time.time(),'jobs':out,'solver_rerun':False,'numerical_validation':False})

if __name__=='__main__':main()
