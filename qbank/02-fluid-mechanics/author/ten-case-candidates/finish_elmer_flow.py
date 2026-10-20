"""One bounded postprocessor for the first queue, preserving live work."""
import argparse
import json
import shutil
import subprocess
import time
from pathlib import Path
import numpy as np
from native_closed_cavity import save,digest
from native_elmer_incompressible import package,run
from titan_resources import identity,reservation


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);args=ap.parse_args();root=args.root;controller=json.loads((root/'maintenance/elmer-flow-queue.json').read_text());deadline=time.monotonic()+24*3600
    while identity(controller['pid'])==controller['starttime']:
        if time.monotonic()>deadline:raise RuntimeError('24-hour bounded handoff reached; active controller was not interrupted')
        time.sleep(30)
    outcome=[]
    for p in (root/'cases').glob('ch02-2-1-*/status.json'):
        state=json.loads(p.read_text());job=p.parent
        if state['status']=='running':continue
        if not (job/'adapter-data.npz').exists():continue
        try:
            e=json.loads((job/'design.json').read_text());design=next(args.snapshot.glob('qbank/02-fluid-mechanics/*/'+e['task']+'/author/chapter02-ten-20261020/design.json'));g=json.loads((design.parents[1]/'grading-template.json').read_text());m=dict(np.load(job/'adapter-data.npz'));groups=m.pop('groups');state.update(package(job,e,m,groups));save(job/'reference/grading.json',g);state.update(status='unvalidated_candidate',conversion_script_sha256=digest(Path(__file__).with_name('native_elmer_incompressible.py')));state.pop('error',None);save(p,state);outcome.append({'id':job.name,'status':state['status']})
        except Exception as ex:outcome.append({'id':job.name,'error':repr(ex)})
    # Only the two audited pre-launch spelling failures are retried. No live
    # container, numerical failure, physical change or indefinite retry loop.
    for p in list((root/'cases').glob('ch02-2-1-*/status.json')):
        state=json.loads(p.read_text())
        if state.get('error')!="AssertionError('(0.1*sin(2*pi*Y),0[,0])')":continue
        assert 'container' not in state
        e=json.loads((p.parent/'design.json').read_text());design=next(args.snapshot.glob('qbank/02-fluid-mechanics/*/'+e['task']+'/author/chapter02-ten-20261020/design.json'));g=json.loads((design.parents[1]/'grading-template.json').read_text());archive=root/'maintenance/adapter-attempts'/(p.parent.name+'-source-expression-'+str(time.time_ns()));p.parent.rename(archive)
        result=run(root,e,g)
        outcome.append({'id':e['design_id'],'status':result['status']})
    save(root/'maintenance/elmer-flow-finalization.json',outcome)
    subprocess.run(['/home/zhouzhiyu/venvs/caeoj/bin/python',str(Path(__file__).with_name('execution_report.py')),'--root',str(root),'--snapshot',str(args.snapshot)],check=True)
    print(json.dumps({'finalization_records':len(outcome),'errors':[v for v in outcome if 'error' in v]}))


if __name__=='__main__':main()
