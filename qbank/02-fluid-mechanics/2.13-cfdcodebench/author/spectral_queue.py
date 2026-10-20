"""Audited adapters of the pinned Dedalus reference producers.

Changes: final-step clipping, explicit authorized shear projection, independent
spatial/time refinements, native spectral output (no source linear interpolation).
Original programs are retained separately. All subprocesses remain local.
"""
from __future__ import annotations
import concurrent.futures as cf
import argparse
import hashlib, json, os, subprocess, sys, time
from pathlib import Path
from catalog import WORK, IDS

PROJECTION = '''
# Authorized continuous initialization: periodic Helmholtz projection.
_U = np.array(u['g'], copy=True)
_kx = 2*np.pi*np.fft.fftfreq(_U.shape[1], d=Lx/_U.shape[1])[:,None]
_kz = 2*np.pi*np.fft.fftfreq(_U.shape[2], d=Lz/_U.shape[2])[None,:]
_hat = np.fft.fft2(_U, axes=(-2,-1))
_k2 = _kx**2+_kz**2
_dot = _kx*_hat[0]+_kz*_hat[1]
_phi = np.divide(_dot,_k2,out=np.zeros_like(_dot),where=_k2!=0)
_hat[0] -= _kx*_phi
_hat[1] -= _kz*_phi
u['g'] = np.fft.ifft2(_hat, axes=(-2,-1)).real
'''

def adapt(task, level, temporal):
    source = WORK/'upstream/CFDCodeBench/PDE_Benchmark/solution'/f'{task}.py'
    text = source.read_text(encoding='utf-8')
    factor = [0.5,1,2][level]
    if task == IDS[19]:
        text = text.replace('Nx = 1024', f'Nx = {int(1024*factor)}')
        text = text.replace('timestep = 5e-4', f'timestep = {5e-4/(max(1,factor)*temporal)}')
        text = text.replace('solver.step(timestep)', 'solver.step(min(timestep, stop_sim_time-solver.sim_time))')
        text = text[:text.index('# Plot')]+"\nu.change_scales(1)\nnp.savez('native.npz', x=dist.local_grid(xbasis).ravel(), u=u['g'].copy(), time=solver.sim_time)\n"
    elif task in (IDS[20],IDS[21]):
        nx,nz = (256,64) if task==IDS[20] else (128,256)
        text = text.replace(f'Nx, Nz = {nx}, {nz}',f'Nx, Nz = {int(nx*factor)}, {int(nz*factor)}')
        # Same refinement CFL, plus explicit independent temporal check.
        maxdt = .125 if task==IDS[20] else .01
        text = text.replace(f'max_timestep = {"0.125" if task==IDS[20] else "1e-2"}',f'max_timestep = {maxdt/(max(1,factor)*temporal)}')
        text = text.replace('safety=0.5', f'safety={.5/temporal}').replace('safety=0.2', f'safety={.2/temporal}')
        text = text.replace('solver.step(timestep)', 'solver.step(min(timestep, stop_sim_time-solver.sim_time))')
        if task==IDS[21]: text=text.replace('# Analysis',PROJECTION+'\n# Analysis',1)
        text = text[:text.index('##########################################################################')]
        fields = "u=u['g'][0].copy(), w=u['g'][1].copy(), b=b['g'].copy(), p=p['g'].copy()" if task==IDS[20] else "u=u['g'][0].copy(), w=u['g'][1].copy(), s=s['g'].copy(), p=p['g'].copy()"
        text += "\nu.change_scales(1)\np.change_scales(1)\n" + ("b.change_scales(1)\n" if task==IDS[20] else "s.change_scales(1)\n")
        text += f"np.savez('native.npz', x=dist.local_grid(xbasis).ravel(), z=dist.local_grid(zbasis).ravel(), time=solver.sim_time, {fields})\n"
    else:
        text = text.replace('Nr = 64', f'Nr = {int(64*factor)}')
        text = text.replace('ncc_cutoff = 1e-3','ncc_cutoff = 1e-12')
    return text

def run(job):
    task,level,temporal=job
    directory=WORK/'spectral'/task/f'L{level}-dt{temporal}'
    record_path=directory/'process.json'
    if record_path.exists() and json.loads(record_path.read_text()).get('returncode')==0: return
    path=directory/'PDE_Benchmark/solution'/f'{task}.py'
    path.parent.mkdir(parents=True,exist_ok=True)
    (directory/'PDE_Benchmark/results/solution').mkdir(parents=True,exist_ok=True)
    text=adapt(task,level,temporal);path.write_text(text,encoding='utf-8')
    record=dict(task=task,level=level,temporal_factor=temporal,started_unix=time.time(),
                adapter_sha256=hashlib.sha256(text.encode()).hexdigest(),status='running')
    env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MPLBACKEND':'Agg'}
    with (directory/'stdout.log').open('w') as log:
        process=subprocess.Popen([sys.executable,str(path)],cwd=directory,env=env,stdout=log,stderr=subprocess.STDOUT)
        record['pid']=process.pid;record_path.write_text(json.dumps(record,indent=2))
        try: record['returncode']=process.wait(timeout=7200)
        except subprocess.TimeoutExpired:
            process.terminate();process.wait();record.update(returncode=process.returncode,timeout_seconds=7200)
    record.update(status='finished',wall_seconds=time.time()-record['started_unix'])
    record_path.write_text(json.dumps(record,indent=2))
    print(json.dumps(record),flush=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--only',nargs='*',type=int)
    parser.add_argument('--workers',type=int,default=2);args=parser.parse_args()
    tasks=[IDS[i-1] for i in (20,21,22,23,24)]
    # Cheap mode/elliptic jobs first, then start the long fine evolution early.
    jobs=[(t,l,d) for t in tasks[::-1] for l,d in ((0,1),(1,1),(2,1),(2,2))]
    if args.only:jobs=[job for job in jobs if IDS.index(job[0])+1 in args.only]
    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool: list(pool.map(run,jobs))

if __name__=='__main__':main()
