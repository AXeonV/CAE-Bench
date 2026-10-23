"""Different documented Dedalus time integrator for the fixed KdV-Burgers check.

This verifies time integration independently of the author's SBDF2 history; it
is explicitly the same solver engine, not a second-solver cross-validation.
"""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
from spectral_queue import adapt
from catalog import WORK,IDS

def main():
    job=WORK/'independent-kdv-rk443';job.mkdir(parents=True,exist_ok=True)
    path=job/'solver.py';text=adapt(IDS[19],2,2).replace('d3.SBDF2','d3.RK443')
    path.write_text(text,encoding='utf-8');(job/'PDE_Benchmark/results/solution').mkdir(parents=True,exist_ok=True)
    record=dict(started_unix=time.time(),sha256=hashlib.sha256(text.encode()).hexdigest(),integrator='RK443',Nx=2048,dt=.000125)
    with (job/'stdout.log').open('w') as log:
        p=subprocess.Popen([sys.executable,str(path)],cwd=job,stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MPLBACKEND':'Agg'})
        record.update(pid=p.pid,status='running');(job/'process.json').write_text(json.dumps(record,indent=2))
        record.update(returncode=p.wait(),status='finished',wall_seconds=time.time()-record['started_unix'])
    (job/'process.json').write_text(json.dumps(record,indent=2));print(json.dumps(record),flush=True)
if __name__=='__main__':main()
