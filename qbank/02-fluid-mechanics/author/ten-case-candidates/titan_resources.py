"""Bounded weighted CPU/memory reservations on Titan, not a daemon."""
import contextlib
import hashlib
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
        if identity(j['pid'])==j['starttime']:
            legacy=max(0,12-sum(c['HostConfig']['NanoCpus']/1e9 for c in running if c['Name'].lstrip('/').startswith('ch02elmer-')))
            # A reviewed, identity-bound certificate proves every original map
            # target already entered run(), whose first operation skips existing
            # status files. Recheck that none reverted to missing/preparing/queued.
            certificate=root/'maintenance/legacy-dispatch-settled.json'
            if certificate.exists():
                proof=json.loads(certificate.read_text());source=Path(proof['archived_source'])
                if proof['pid']==j['pid'] and str(proof['starttime'])==str(j['starttime']) and hashlib.sha256(source.read_bytes()).hexdigest()==proof['source_sha256']:
                    states=[json.loads((root/'cases'/i/'status.json').read_text()) for i in proof['original_target_ids']]
                    allowed={'unvalidated_candidate','native_iteration_limit','needs_attention','running'}
                    if all(v['status'] in allowed for v in states):
                        # Native tasks are counted above. Keep one CPU for each
                        # still-running original task outside an active container.
                        legacy=sum(v['status']=='running' and v.get('container') not in names for v in states)

    host=int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024
    outer=json.loads(subprocess.check_output(['docker','inspect','caeoj-solver-library-daemon']))[0]
    assert outer['HostConfig']['NanoCpus']==40*10**9 and outer['HostConfig']['Memory']==52*1024**3
    pid=outer['State']['Pid'];cg=next(l.split(':',2)[2].strip() for l in Path(f'/proc/{pid}/cgroup').read_text().splitlines() if l.startswith('0::'));parent=Path('/sys/fs/cgroup')/cg.lstrip('/');limits=[]
    for level in [parent,*parent.parents]:
        cap=level/'memory.max'
        if cap.exists() and cap.read_text().strip()!='max':
            stat=dict(line.split() for line in (level/'memory.stat').read_text().splitlines());working=int((level/'memory.current').read_text())-int(stat.get('inactive_file',0));limits.append(int(cap.read_text())-working)
    assert limits
    return names,used+legacy,min(host,*limits),{'host_available_bytes':host,'outer_available_working_set_bytes':min(limits),'running_quota_cores':used,'legacy_queue_reserved_cores':legacy,'running_memory_limit_bytes':sum(c['HostConfig']['Memory'] for c in running),'parallel_long_running':sum((c['Config'].get('Labels') or {}).get('ch02.workload')=='parallel_long' for c in running)}


@contextlib.contextmanager
def reservation(root,name,cpu=1,memory_limit_bytes=768*1024**2,workload='ordinary'):
    assert 0<cpu<=40 and 0<memory_limit_bytes<=65*1024**3
    if workload=='parallel_long':assert 8<=cpu<=16,'Long parallel solves require 8..16 native ranks/cores'
    directory=root/'maintenance/reservations';directory.mkdir(exist_ok=True);mine=directory/(name+'.json');lock=(directory/'lock').open('a');pid=os.getpid();start=identity(pid)
    while True:
        fcntl.flock(lock,fcntl.LOCK_EX)
        try:
            names,used,available,record=capacity(root);pending=0;pending_cpu=0;pending_memory=0;pending_long=0
            for p in directory.glob('*.json'):
                try:v=json.loads(p.read_text())
                except FileNotFoundError:continue
                if identity(v['pid'])==v['starttime'] and v['name'] not in names:
                    pending+=1;pending_cpu+=v.get('cpu',1);pending_memory+=v.get('memory_limit_bytes',768*1024**2);pending_long+=v.get('workload')=='parallel_long'
            long_ok=workload!='parallel_long' or record['parallel_long_running']+pending_long<4
            if long_ok and used+pending_cpu+cpu<=40 and available>8*1024**3+pending_memory+memory_limit_bytes and record['running_memory_limit_bytes']+pending_memory+memory_limit_bytes<=65*1024**3:
                save(mine,{'pid':pid,'starttime':start,'name':name,'at_unix':time.time(),'cpu':cpu,'memory_limit_bytes':memory_limit_bytes,'workload':workload})
                with (root/'maintenance/resource-scheduling.jsonl').open('a') as f:f.write(json.dumps({'name':name,'decision':'reserved_resources','requested_cpu':cpu,'requested_memory_bytes':memory_limit_bytes,'pending_reservations':pending,'pending_cpu':pending_cpu,**record,'at_unix':time.time()})+'\n')
                break
        finally:fcntl.flock(lock,fcntl.LOCK_UN)
        time.sleep(5)
    try:yield
    finally:
        fcntl.flock(lock,fcntl.LOCK_EX)
        try:mine.unlink(missing_ok=True)
        finally:fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
