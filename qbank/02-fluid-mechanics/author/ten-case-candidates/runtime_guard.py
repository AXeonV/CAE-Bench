"""User-authorized wall-clock stops for case solvers, not build containers."""
import argparse
import concurrent.futures
import datetime
import fcntl
import json
from pathlib import Path
import subprocess
import time
from native_closed_cavity import SOCKET,save

def docker(*args,timeout=60):
    return subprocess.check_output(['docker','--host',SOCKET,*args],text=True,timeout=timeout)

def enforce(root):
    policy=json.loads((root/'maintenance/runtime-policy.json').read_text());now=time.time();targets=[];skipped=[]
    for status in (root/'cases').glob('*/status.json'):
        s=json.loads(status.read_text());receipt=status.parent/'runtime-stop-receipt.json'
        if receipt.exists():
            old=json.loads(receipt.read_text())
            if old.get('stopped') and s.get('container')==old['container_name'] and s.get('status') not in ('unvalidated_candidate','stopped_runtime_limit'):
                s.update(status='stopped_runtime_limit',runtime_stop=old['reason'],runtime_receipt=receipt.name);save(status,s)
        if s.get('status')!='running' or not s.get('container'):continue
        try:c=json.loads(docker('inspect',s['container']))[0]
        except (subprocess.SubprocessError,json.JSONDecodeError):continue
        if not c['State']['Running'] or c['State']['Pid']<=0:continue
        if not any(m['Source']==str(status.parent) and m['Destination']=='/work' for m in c['Mounts']):
            skipped.append({'case_id':s['design_id'],'reason':'actual mount mismatch'});continue
        execution=json.loads((status.parent/'execution.json').read_text())
        if execution.get('image') not in (c['Config']['Image'],c['Image']):
            skipped.append({'case_id':s['design_id'],'reason':'actual image mismatch'});continue
        started=datetime.datetime.fromisoformat(c['State']['StartedAt'].replace('Z','+00:00')).timestamp()
        threshold=policy['new_stop_after_seconds'] if started>=policy['effective_unix'] else policy['existing_hard_limit_seconds']
        if now-started<threshold:continue
        targets.append((status,s,c,started,'new_two_hour_budget' if started>=policy['effective_unix'] else 'existing_over_four_hours'))
    def stop(target):
        status,s,c,started,reason=target;j=status.parent
        # Immutable container ID + unchanged StartedAt/mount identity, never old PID alone.
        actual=json.loads(docker('inspect',c['Id']))[0]
        if not actual['State']['Running'] or actual['State']['StartedAt']!=c['State']['StartedAt']:return {'case_id':s['design_id'],'action':'already_ended_no_signal'}
        rec={'requested_unix':time.time(),'case_id':s['design_id'],'container_id':c['Id'],'container_name':s['container'],'native_state_before':actual['State'],'mounts':actual['Mounts'],'elapsed_seconds':time.time()-started,'reason':reason,'prior_status':s,'stopped':False,'preserve':'All mesh, input, raw outputs, logs and original execution records stay in place. No automatic restart.'};save(j/'runtime-stop-receipt.json',rec)
        try:
            docker('stop','--time','30',c['Id'],timeout=50)
            after=json.loads(docker('inspect',c['Id']))[0];rec.update(stopped=not after['State']['Running'],native_state_after=after['State'],ended_unix=time.time())
        except subprocess.SubprocessError as ex:rec['error']=repr(ex)
        save(j/'runtime-stop-receipt.json',rec)
        if rec['stopped']:
            latest=json.loads(status.read_text());latest.update(status='stopped_runtime_limit',runtime_stop=reason,runtime_receipt='runtime-stop-receipt.json');save(status,latest)
        return {'case_id':s['design_id'],'action':'stopped_runtime_limit' if rec['stopped'] else 'stop_needs_attention','elapsed_hours':round(rec['elapsed_seconds']/3600,2)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=40) as pool:actions=list(pool.map(stop,targets))
    out={'at_unix':time.time(),'policy':policy,'actions':actions,'identity_skips':skipped,'scope':'Only identity-verified case solver mounts; build/import/staging containers excluded.'};save(root/'maintenance/runtime-guard-summary.json',out)
    if actions:
        with (root/'maintenance/runtime-guard-history.jsonl').open('a') as f:f.write(json.dumps(out)+'\n')
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--serve',action='store_true');ap.add_argument('--deadline-unix',type=float,required=True);a=ap.parse_args()
    with (a.root/'maintenance/runtime-guard.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        while True:
            try:
                out=enforce(a.root)
                if out['actions'] or not a.serve:print(json.dumps(out),flush=True)
            except Exception as ex:
                save(a.root/'maintenance/runtime-guard-error.json',{'at_unix':time.time(),'error':repr(ex)});raise
            if not a.serve or time.time()>=a.deadline_unix:break
            time.sleep(15)
if __name__=='__main__':main()
