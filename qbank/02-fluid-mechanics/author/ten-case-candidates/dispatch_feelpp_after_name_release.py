"""One reviewed dispatch after Docker name conflict, never a solver retry loop."""
import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0,str(Path(__file__).parent/'feelpp-transient2d-bundle-v2'))
from finish_feelpp_powerlaw import finish
from native_closed_cavity import SOCKET,save
from titan_resources import reservation

CASES=['ch02-2-1-6-01-power_law_channel','ch02-2-1-6-06-power_law_traction']


def run(root,snapshot,case):
    job=root/'cases'/case;status=json.loads((job/'status.json').read_text());execution=json.loads((job/'execution.json').read_text())
    assert status['status']=='needs_attention' and status['native_exit_code']==125
    log=job/'native-solver.log';assert 'container name' in log.read_text() and 'already in use' in log.read_text()
    model=json.loads((job/'native/cfd.json').read_text());assert model['InitialConditions']['fluid']['velocity']['Expression']['initial_zero']['expr']=='{0,0}'
    assert subprocess.run(['docker','--host',SOCKET,'inspect',status['container']],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode!=0
    assert execution['native_ranks']==8 and '-np 8 ' in execution['command'][-1]
    save(job/'name-conflict-status.json',status);save(job/'name-conflict-execution.json',execution);log.rename(job/'name-conflict-docker.log')
    with reservation(root,status['container'],cpu=8,memory_limit_bytes=8*1024**3,workload='parallel_long'):
        status.update(status='running',dispatch_recovery='Verified stopped conflicting container renamed; no previous solver started for this prepared input',native_exit_code=None)
        execution.update(start_unix=time.time(),dispatch_recovery='One approved name-release dispatch; same immutable image/config/command, prior metadata retained')
        save(job/'status.json',status);save(job/'execution.json',execution)
        try:
            with log.open('w') as out:result=subprocess.run(execution['command'],stdout=out,stderr=subprocess.STDOUT,timeout=14460)
            status.update(status='native_raw_complete_pending_package' if result.returncode==0 else 'needs_attention',native_exit_code=result.returncode)
        except Exception as ex:status.update(status='needs_attention',error=repr(ex))
        current=json.loads((job/'status.json').read_text())
        if current['status']=='stopped_runtime_limit':return
        status['finished_unix']=time.time();save(job/'status.json',status)
    if status['status']=='native_raw_complete_pending_package':
        try:finish(root,snapshot,case_id=case)
        except Exception as ex:
            status['packaging_error']=repr(ex);save(job/'status.json',status)


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--snapshot',type=Path,required=True);p.add_argument('--workers',type=int);a=p.parse_args()
    with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(lambda case:run(a.root,a.snapshot,case),CASES))


if __name__=='__main__':main()
