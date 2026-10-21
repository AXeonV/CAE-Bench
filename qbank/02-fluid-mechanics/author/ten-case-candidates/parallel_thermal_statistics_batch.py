"""Dispatch only the finite individually approved MPI low-Mach cases."""
import argparse
import json
import os
from pathlib import Path
import parallel_lowmach_replan as producer
from parallel_lowmach_replan import run_one
from hashlib import sha256
def main():
    assert sha256(Path(producer.__file__).read_bytes()).hexdigest()=='d9880db6d9a0773e548be0596a6039959609981d88e5aff768dceec06f8a44b4'
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int,default=1);a=ap.parse_args()
    assert sha256(Path(producer.__file__).with_name('native_thermal_statistics.py').read_bytes()).hexdigest()=='5f88011caa67072164ea331eaa786609779611b6c57e9b1c3ee79b64dc50ccf5'
    assert sha256(Path(producer.__file__).with_name('InitialKE_MPI.F90').read_bytes()).hexdigest()=='cf130e49ad699f310b3a46aa7f60b2000c51b820ff5862cd0bd7e2195a571a2b'
    cores=int(os.environ['CH02_LONG_SOLVER_CORES']);assert cores in (8,16)
    approvals=json.loads((a.root/'maintenance/parallel-statistics-batch-approval.json').read_text())['cases']
    tasks=[e for e in approvals if e['cores']==cores and not (a.root/'cases'/e['case_id']/'status.json').exists()]
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=len(tasks) or 1) as pool:list(pool.map(lambda e:run_one(a.root,e,cores),tasks))
if __name__=='__main__':main()
