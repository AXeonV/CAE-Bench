"""One bounded repair of the original native trial's known averaging syntax.

Wait for the active container to end. Never interrupt it or retry other errors.
"""
import argparse
import json
import shutil
import subprocess
import time
from pathlib import Path
from native_closed_cavity import SOCKET, save
from native_sparta import run


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);args=ap.parse_args();cid='ch02-2-10-4-01-pressure_duct';job=args.root/'cases'/cid;deadline=time.monotonic()+24*3600
    while time.monotonic()<deadline:
        state=json.loads((job/'status.json').read_text())
        if state['status'] not in ('running','queued','preparing'):break
        time.sleep(60)
    else:raise RuntimeError('bounded wait expired; active trial left untouched')
    if state['status']!='needs_attention':return
    log=(job/'solver.log').read_text()
    assert 'Could not find fix ave/grid group ID' in log, 'unexpected failure; no automatic retry'
    obj=json.loads(subprocess.check_output(['docker','--host',SOCKET,'inspect',state['container']]))[0]
    assert not obj['State']['Running'] and any(m['Source']==str(job.resolve()) for m in obj['Mounts'])
    dest=args.root/'maintenance/adapter-attempts'/(cid+'-averaging-syntax-'+str(time.time_ns()));shutil.move(job,dest)
    for p in args.snapshot.glob('qbank/02-fluid-mechanics/*/*/author/chapter02-ten-20261020/design.json'):
        r=json.loads(p.read_text())
        for e in r['proposed_cases']:
            if e['design_id']==cid:
                g=json.loads((p.parents[1]/'grading-template.json').read_text());result=run(args.root,{**e,'task':r['task'],'model':r['model']},g);save(args.root/'maintenance/sparta-trial-repair-summary.json',result);return
    raise RuntimeError('frozen trial not found')


if __name__=='__main__':main()
