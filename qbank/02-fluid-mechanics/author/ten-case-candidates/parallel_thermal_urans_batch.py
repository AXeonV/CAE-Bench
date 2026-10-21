"""Dispatch only the finite individually approved MPI low-Mach cases."""
import argparse
import json
import os
from pathlib import Path
import parallel_lowmach_replan as producer
from parallel_lowmach_replan import run_one
from hashlib import sha256
def main():
    assert sha256(Path(producer.__file__).read_bytes()).hexdigest()=='d2b06cfdf3ac0fba49a0f6012818a25a9b5aba201089cc60158c3e9269a064ab'
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int,default=1);a=ap.parse_args()
    assert sha256(Path(producer.__file__).with_name('native_thermal_rans.py').read_bytes()).hexdigest()=='53ae1b232b9096d092f5da9d023250d9c15c6d03e10efe2581394bb44bc9e6ef'
    cores=int(os.environ['CH02_LONG_SOLVER_CORES']);assert cores in (8,16)
    approvals=json.loads((a.root/'maintenance/parallel-urans-batch-approval.json').read_text())['cases']
    tasks=[e for e in approvals if e['cores']==cores and not (a.root/'cases'/e['case_id']/'status.json').exists()]
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=len(tasks) or 1) as pool:list(pool.map(lambda e:run_one(a.root,e,cores),tasks))
if __name__=='__main__':main()
