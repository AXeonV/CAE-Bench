"""Repackage one stopped, successful native run using coordinate node identity.

No solver rerun or numerical verification. Previous public payload is archived.
"""
import argparse
import fcntl
import json
from pathlib import Path
import shutil
import subprocess
import time
import numpy as np
from native_closed_cavity import SOCKET, save, digest
from native_elmer_incompressible import package
from titan_resources import reservation


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int,default=1);args=ap.parse_args()
    proof=json.loads((args.root/'maintenance/elmer-node-order-conversion-handoff.json').read_text());job=args.root/'cases'/proof['design_id']
    with (job/'conversion.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        state=json.loads((job/'status.json').read_text())
        if state['status']=='unvalidated_candidate':return
        assert state.get('error')=="AssertionError('native node order')"
        native=json.loads(subprocess.check_output(['docker','--host',SOCKET,'inspect',proof['native_container']]))[0]
        assert not native['State']['Running'] and native['State']['ExitCode']==0
        assert any(m['Source']==str(job) for m in native['Mounts'])
        e=json.loads((job/'design.json').read_text())
        design=next(args.snapshot.glob('qbank/02-fluid-mechanics/*/'+e['task']+'/author/chapter02-ten-20261020/design.json'))
        frozen=json.loads(design.read_text());match=next(z for z in frozen['proposed_cases'] if z['design_id']==e['design_id'])
        assert match['detailed_spec']==e['detailed_spec'], 'Frozen physical/observation design differs'
        g=json.loads((design.parents[1]/'grading-template.json').read_text())
        archive=args.root/'maintenance/adapter-attempts'/(job.name+'-node-order-conversion-'+str(time.time_ns()));archive.mkdir()
        shutil.copy2(job/'status.json',archive/'status.json')
        for name in ('input','reference'):
            if (job/name).exists():shutil.copytree(job/name,archive/name)
        with reservation(args.root,'ch02-convert-node-order-'+str(time.time_ns())):
            m=dict(np.load(job/'adapter-data.npz'));groups=m.pop('groups');result=package(job,e,m,groups)
            save(job/'reference/grading.json',g)
            conversion={'at_unix':time.time(),'previous_payload':str(archive),'script_sha256':digest(Path(__file__)),'conversion_script_sha256':digest(Path(__file__).with_name('native_elmer_incompressible.py')),'native_container':native['Id'],'native_exit_code':0,'native_solver_rerun':False,'numerical_validation':False,**result}
            save(job/'conversion-repair.json',conversion)
            state.update(result,status='unvalidated_candidate',conversion_script_sha256=conversion['conversion_script_sha256'],ended_unix=time.time());state.pop('error',None)
            save(job/'status.json',state);save(args.root/'maintenance/elmer-node-order-conversion-summary.json',conversion)


if __name__=='__main__':main()
