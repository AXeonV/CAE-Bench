"""One bounded local completion pipeline; no HF, titan, candidates or scheduling.

Wait only for existing authorized queues. It does not launch/restart solvers or
change their configurations. After terminal receipts it reconstructs completed
OpenFOAM fields, builds cases, audits numerics, and tests real installed CLI use.
Numerical failure/pending is reported explicitly and never promoted to readiness.
"""
import argparse,hashlib,json,os,subprocess,sys,time
from pathlib import Path
from catalog import WORK,SECTION,IDS

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def dependencies():
    entries=[]
    def add(job,file='native.npz'):entries.append((WORK/job,file))
    for i in (12,18):
        for l,d in ((0,1),(1,1),(2,1),(2,2)):add(f'cavity-p3/C{i:02}/L{l}-dt{d}')
    for task in (IDS[19],IDS[20],IDS[21],IDS[22],IDS[23]):
        for l,d in ((0,1),(1,1),(2,1),(2,2)):
            add(f'spectral/{task}/L{l}-dt{d}','PDE_Benchmark/results/solution/*.npy' if task in (IDS[22],IDS[23]) else 'native.npz')
    for n,p in ((64,96),(128,192),(256,384)):add(f'cylinder-openfoam/R{n}-P{p}')
    for i in (12,18):
        for n in (64,128):add(f'independent-cavity-openfoam/C{i:02}/N{n}')
    for l,d in ((0,1),(1,1),(2,1),(2,2)):add(f'cylinder-fem/L{l}-dt{d}')
    add('independent-kdv-rk443')
    return entries

def inspect(job,pattern):
    receipt=job/'process.json'
    if not receipt.exists():return 'pending'
    try:r=json.loads(receipt.read_text(encoding='utf-8'))
    except (OSError,ValueError):return 'pending'
    rc=r.get('returncode')
    if rc is None:return 'pending'
    if rc!=0:return 'failed'
    paths=list(job.glob(pattern))
    if not paths:return 'pending_export'
    if any(time.time()-p.stat().st_mtime<5 for p in paths):return 'pending_export'
    import numpy as np
    try:
        for p in paths:
            a=np.load(p)
            if hasattr(a,'files'):
                with a:
                    for name in a.files:_=a[name]
    except (OSError,ValueError,EOFError):return 'pending_export'
    return 'finished'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--wait-hours',type=float,default=24);args=ap.parse_args()
    lock=WORK/'completion-pipeline.lock'
    fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL)
    with os.fdopen(fd,'w') as f:json.dump(dict(pid=os.getpid(),started_unix=time.time()),f)
    status=WORK/'completion-pipeline.json';state=dict(pid=os.getpid(),started_unix=time.time(),phase='waiting')
    snapshot={p.name:sha(p) for p in (SECTION/'author').glob('*.py')}
    state['author_scripts_sha256']=snapshot
    def save():status.write_text(json.dumps(state,indent=2),encoding='utf-8')
    save()
    try:
        deadline=time.monotonic()+args.wait_hours*3600
        while True:
            results=[dict(job=p.relative_to(WORK).as_posix(),status=inspect(p,pat)) for p,pat in dependencies()]
            state['jobs']=results;state['last_checked_unix']=time.time();save()
            if all(r['status'] in ('finished','failed') for r in results):break
            if time.monotonic()>=deadline:
                state.update(phase='incomplete',reason='Bounded wait ended; active solves untouched');save();return
            time.sleep(30)
        changed=[name for name,digest in snapshot.items() if not (SECTION/'author'/name).exists() or sha(SECTION/'author'/name)!=digest]
        if changed:state.update(phase='needs_review',reason='Author scripts changed while waiting',changed=changed);save();return
        state['phase']='finalizing';save()
        # Only completed real fields are reconstructed. No solver is run here.
        from cylinder_openfoam import convert
        for n,p in ((64,96),(128,192),(256,384)):
            job=WORK/'cylinder-openfoam'/f'R{n}-P{p}'
            if inspect(job,'native.npz')=='finished':convert(job,n,p)
        for script in ('build_local.py','certify_local.py','verify_local_install.py'):
            with (WORK/('completion-'+script+'.log')).open('w',encoding='utf-8') as log:
                p=subprocess.run([sys.executable,str(SECTION/'author'/script)],cwd=WORK.parent.parent,stdout=log,stderr=subprocess.STDOUT)
            if p.returncode:state.update(phase='needs_review',failed_stage=script,returncode=p.returncode);save();return
        rows=json.loads((WORK/'certification.json').read_text(encoding='utf-8'))
        state.update(phase='ready_for_review',numerically_verified=sum(r['status']=='verified_with_stated_limits' for r in rows),not_verified=[dict(index=r['index'],status=r['status'],failed=r['failed'],missing=r['missing']) for r in rows if r['status']!='verified_with_stated_limits'],resource_status='provisional',formal_published=False)
        save()
    except Exception as error:
        state.update(phase='needs_review',error=repr(error));save();raise
    finally:
        state['ended_unix']=time.time();save();lock.unlink()
if __name__=='__main__':main()
