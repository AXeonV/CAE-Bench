"""Bounded local producer subprocesses with immutable snapshots and PID checks."""
import hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path

def identity(pid):
    path=Path('/proc')/str(pid)/'stat'
    if not path.exists():return None
    text=path.read_text();parts=text[text.rfind(')')+2:].split()
    return dict(starttime=int(parts[19]),state=parts[0])

def run(job,script,arguments):
    job.mkdir(parents=True,exist_ok=True);record=job/'process.json'
    if record.exists():
        old=json.loads(record.read_text())
        if old.get('returncode')==0:return True
        pid=old.get('pid');current=identity(pid) if pid else None
        if current and current['state']!='Z':
            # Even legacy receipts without starttime must not cause an active
            # PID to be restarted just because the receipt looks old.
            raise RuntimeError('An existing PID needs inspection; refusing duplicate job: '+str(job))
        stamp=str(time.time_ns())
        for name in ('process.json','stdout.log'):
            path=job/name
            if path.exists():path.rename(job/(name+'.failed-'+stamp))
    snapshot=job/'producer-snapshot';snapshot.mkdir(exist_ok=True)
    sources={}
    for path in (script,Path(__file__),script.with_name('catalog.py')):
        data=path.read_bytes();(snapshot/path.name).write_bytes(data);sources[path.name]=hashlib.sha256(data).hexdigest()
    cmd=[sys.executable,str(script),*map(str,arguments)];started=time.time()
    timer=shutil.which('/usr/bin/time')
    command=[timer,'-v','-o',str(job/'resources.txt'),*cmd] if timer else cmd
    with (job/'stdout.log').open('w') as log:
        p=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'})
        data=dict(command=command,pid=p.pid,process_identity=identity(p.pid),started_unix=started,status='running',producer_sha256=sources)
        record.write_text(json.dumps(data,indent=2));rc=p.wait()
    data.update(returncode=rc,status='finished',wall_seconds=time.time()-started)
    record.write_text(json.dumps(data,indent=2));print(json.dumps(data),flush=True)
    return rc==0
