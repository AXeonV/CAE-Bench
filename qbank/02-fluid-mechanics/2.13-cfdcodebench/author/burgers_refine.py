"""Exact-time/resolution adapter for the sourced CFDPython 2D Burgers producer."""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
from catalog import WORK,IDS

def main():
    original=(WORK/'upstream/CFDCodeBench/PDE_Benchmark/solution'/f'{IDS[5]}.py').read_text(encoding='utf-8')
    # Keep the author's updates, remove only visualization/output sections.
    prefix=original[:original.index('###(plot ICs)')]
    loop=original[original.index('for n in range(nt + 1)'):]
    loop=loop[:loop.index('fig = pyplot.figure')]
    for level,factor in ((0,1),(1,1),(2,1),(2,2)):
        size=81*2**level-(2**level-1);nt=480*4**level*factor
        text=prefix.replace('nx = 41',f'nx = {size}').replace('ny = 41',f'ny = {size}').replace('nt = 120',f'nt = {nt}')
        text=text.replace('dt = sigma * dx * dy / nu','dt = .027 / nt')
        text+=loop.replace('range(nt + 1)','range(nt)')
        text+="\nnumpy.savez('native.npz',x=x,y=y,u=u,v=v,time=nt*dt,dt=dt)\n"
        job=WORK/'burgers'/f'L{level}-dt{factor}';job.mkdir(parents=True,exist_ok=True)
        record=job/'process.json'
        if record.exists() and json.loads(record.read_text()).get('returncode')==0:continue
        path=job/'producer.py';path.write_text(text,encoding='utf-8');started=time.time()
        with (job/'stdout.log').open('w') as log:
            p=subprocess.Popen([sys.executable,str(path)],cwd=job,stdout=log,stderr=subprocess.STDOUT,
                env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MPLBACKEND':'Agg'})
            data=dict(pid=p.pid,started_unix=started,status='running',adapter_sha256=hashlib.sha256(text.encode()).hexdigest())
            record.write_text(json.dumps(data,indent=2));rc=p.wait()
        data.update(status='finished',returncode=rc,wall_seconds=time.time()-started)
        record.write_text(json.dumps(data,indent=2));print(json.dumps(data),flush=True)

if __name__=='__main__':main()
