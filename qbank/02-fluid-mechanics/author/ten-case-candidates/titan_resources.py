"""Bounded reservations for one-core producers on Titan, not a daemon."""
import contextlib
import fcntl
import json
import os
import subprocess
import time
from pathlib import Path
from native_closed_cavity import SOCKET,save


def identity(pid):
    try:
        fields=Path(f'/proc/{pid}/stat').read_text().split()
        return None if fields[2]=='Z' else fields[21]
    except FileNotFoundError:return None


def capacity(root):
    ids=subprocess.check_output(['docker','--host',SOCKET,'ps','-q'],text=True).split()
    running=json.loads(subprocess.check_output(['docker','--host',SOCKET,'inspect',*ids])) if ids else []
    names={c['Name'].lstrip('/') for c in running};used=sum(c['HostConfig']['NanoCpus']/1e9 for c in running)
    # The first bounded Elmer queue predates this reservation helper. Reserve
    # its full twelve-worker allotment until its controller actually exits.
    p=root/'maintenance/elmer-flow-queue.json';legacy=0
    if p.exists():
        j=json.loads(p.read_text())
        if identity(j['pid'])==j['starttime']:legacy=max(0,12-sum(c['HostConfig']['NanoCpus']/1e9 for c in running if c['Name'].lstrip('/').startswith('ch02elmer-')))
    host=int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024
    outer=json.loads(subprocess.check_output(['docker','inspect','caeoj-solver-library-daemon']))[0]
    assert outer['HostConfig']['NanoCpus']==40*10**9 and outer['HostConfig']['Memory']==52*1024**3
    pid=outer['State']['Pid'];cg=next(l.split(':',2)[2].strip() for l in Path(f'/proc/{pid}/cgroup').read_text().splitlines() if l.startswith('0::'));parent=Path('/sys/fs/cgroup')/cg.lstrip('/');limits=[]
    for level in [parent,*parent.parents]:
        cap=level/'memory.max'
        if cap.exists() and cap.read_text().strip()!='max':
            stat=dict(line.split() for line in (level/'memory.stat').read_text().splitlines());working=int((level/'memory.current').read_text())-int(stat.get('inactive_file',0));limits.append(int(cap.read_text())-working)
    assert limits
    return names,used+legacy,min(host,*limits),{'host_available_bytes':host,'outer_available_working_set_bytes':min(limits),'running_quota_cores':used,'legacy_queue_reserved_cores':legacy}


@contextlib.contextmanager
def reservation(root,name):
    directory=root/'maintenance/reservations';directory.mkdir(exist_ok=True);mine=directory/(name+'.json');lock=(directory/'lock').open('a');pid=os.getpid();start=identity(pid)
    while True:
        fcntl.flock(lock,fcntl.LOCK_EX)
        try:
            names,used,available,record=capacity(root);pending=0
            for p in directory.glob('*.json'):
                try:v=json.loads(p.read_text())
                except FileNotFoundError:continue
                if identity(v['pid'])==v['starttime'] and v['name'] not in names:pending+=1
            if used+pending+1<=40 and available>8*1024**3+(pending+1)*768*1024**2:
                save(mine,{'pid':pid,'starttime':start,'name':name,'at_unix':time.time(),'cpu':1,'memory_limit_bytes':768*1024**2})
                with (root/'maintenance/resource-scheduling.jsonl').open('a') as f:f.write(json.dumps({'name':name,'decision':'reserved_one_core','pending_reservations':pending,**record,'at_unix':time.time()})+'\n')
                break
        finally:fcntl.flock(lock,fcntl.LOCK_UN)
        time.sleep(5)
    try:yield
    finally:
        fcntl.flock(lock,fcntl.LOCK_EX)
        try:mine.unlink(missing_ok=True)
        finally:fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
