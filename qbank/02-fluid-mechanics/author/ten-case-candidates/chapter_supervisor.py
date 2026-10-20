"""Finite approved-plan dispatcher and compact inventory, never a PDE solver.

One-shot inspection is used by the half-hour heartbeat. A bounded persistent
process dispatches approved commands; native producers own resource leases.
Existing controller identities and live native mounts prevent duplicate starts.
Failures are reported, never automatically deleted or retried.
"""
import argparse
import collections
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from execution_report import GAPS
from native_closed_cavity import SOCKET, save
from titan_resources import capacity, identity


def read(path):
    return json.loads(path.read_text())


def active(meta):
    return identity(meta['pid']) == str(meta['starttime'])


def cpu():
    a = list(map(int, Path('/proc/stat').read_text().splitlines()[0].split()[1:]))
    time.sleep(1)
    b = list(map(int, Path('/proc/stat').read_text().splitlines()[0].split()[1:]))
    d = [y-x for x, y in zip(a[:8], b[:8])]
    return 100 * (sum(d)-d[3]-d[4]) / max(1, sum(d))


def inspect(root, snapshot):
    base = snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates'
    counts = collections.Counter(); pending = collections.defaultdict(list); issues = []
    for row in read(base/'index.json')['questions']:
        design = read(snapshot/row['path'])
        for e in design['proposed_cases']:
            path = root/'cases'/e['design_id']/'status.json'
            s = read(path) if path.exists() else {'status': 'held_unmatched_physics' if design['question'] in GAPS else 'pending_producer_adapter'}
            counts[s['status']] += 1
            if s['status'] == 'pending_producer_adapter':
                pending[design['question']].append(e['design_id'])
            elif s['status'] in ('needs_attention', 'native_iteration_limit'):
                issues.append({'design_id': e['design_id'], 'status': s['status'], 'error': s.get('error')})
    assert sum(counts.values()) == 630
    names, quota, available, memory = capacity(root)
    sample = subprocess.run(['docker', '--host', SOCKET, 'stats', '--no-stream', '--format', '{{.CPUPerc}}'], text=True, capture_output=True, timeout=30, check=True)
    used = sum(float(v.rstrip('%')) for v in sample.stdout.split()) / 100
    controllers = []
    for p in (root/'maintenance').glob('*.json'):
        try:
            j = read(p)
            if isinstance(j, dict) and {'pid', 'starttime'} <= j.keys() and active(j):
                controllers.append(p.name)
        except (ValueError, OSError, KeyError):
            continue
    report = {'at_unix': time.time(), 'counts': dict(counts), 'resources': {'host_cpu_percent': cpu(), 'docker_used_cores': round(used, 2), 'docker_percent_of_40': round(used/40*100, 1), 'accounted_quota_cores': quota, 'quota_headroom_cores': max(0, 40-quota), 'available_bytes': available, 'outer_cpu_limit_cores': 40, 'outer_memory_limit_gib': 52, **memory}, 'active_controllers': controllers, 'issues': issues, 'pending_adapter_cases': dict(pending), 'numerical_validation': 'not_performed', 'completion_claim': 'partial', 'scheduling_action': []}
    save(root/'maintenance/automation-handoff.json', report)
    return report


def dispatch(root, snapshot):
    plan_path = root/'maintenance/approved-queues.json'
    if not plan_path.exists():
        return []
    actions = []
    for q in read(plan_path)['queues']:
        marker = root/'maintenance'/q['marker']
        if marker.exists():
            actions.append({'queue': q['name'], 'action': 'active' if active(read(marker)) else 'ended_no_automatic_retry'})
            continue
        if any(active(read(root/'maintenance'/m)) for m in q.get('conflicting_controllers', []) if (root/'maintenance'/m).exists()):
            actions.append({'queue': q['name'], 'action': 'waiting_for_existing_controller'}); continue
        script = root/'scripts'/q['script']
        assert hashlib.sha256(script.read_bytes()).hexdigest() == q['script_sha256'], 'approved script changed; update plan explicitly'
        missing = [i for i in q['case_ids'] if not (root/'cases'/i/'status.json').exists()]
        if not missing:
            actions.append({'queue': q['name'], 'action': 'no_unstarted_cases'}); continue
        # Block orphaned live native jobs too: controller PID alone is insufficient.
        ids = subprocess.check_output(['docker', '--host', SOCKET, 'ps', '-q'], text=True).split()
        containers = json.loads(subprocess.check_output(['docker', '--host', SOCKET, 'inspect', *ids])) if ids else []
        live_mounts = {m['Source'] for c in containers for m in c['Mounts']}
        if any(str(root/'cases'/i) in live_mounts for i in missing):
            actions.append({'queue': q['name'], 'action': 'live_native_mount_blocks_launch'}); continue
        # capacity() asserts exact parent limits; producers lease CPU/memory before work.
        capacity(root)
        command = [sys.executable, str(script), '--root', str(root), '--snapshot', str(snapshot), '--workers', '40']
        with (root/'maintenance'/(q['name']+'.log')).open('a') as log:
            p = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True, env={**os.environ, 'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1'})
        save(marker, {'pid': p.pid, 'starttime': identity(p.pid), 'command': command, 'launched_unix': time.time(), 'approved_case_ids': q['case_ids']})
        actions.append({'queue': q['name'], 'action': 'launched', 'pid': p.pid, 'unstarted': len(missing)})
    # Only a reviewed conversion defect can be repaired automatically. Native
    # failures/iteration caps are excluded; the converter rechecks exit=0/mounts.
    for q in read(plan_path).get('conversion_repairs', []):
        status=root/'cases'/q['case_id']/'status.json'
        if not status.exists() or read(status).get('error') != "AssertionError('native node order')": continue
        marker=root/'maintenance'/q['marker']
        if marker.exists(): continue
        script=root/'scripts'/q['script']
        assert hashlib.sha256(script.read_bytes()).hexdigest()==q['script_sha256']
        capacity(root)
        command=[sys.executable,str(script),'--root',str(root),'--snapshot',str(snapshot),'--case-id',q['case_id']]
        with (root/'maintenance'/(q['marker']+'.log')).open('a') as log:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'})
        save(marker,{'pid':child.pid,'starttime':identity(child.pid),'command':command,'launched_unix':time.time()})
        actions.append({'case_id':q['case_id'],'action':'one_conversion_only_repair_launched','pid':child.pid})
    return actions


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--root', type=Path, required=True); ap.add_argument('--snapshot', type=Path, required=True); ap.add_argument('--serve', action='store_true'); ap.add_argument('--max-hours', type=float, default=168); args = ap.parse_args()
    lock = (args.root/'maintenance/supervisor.lock').open('a')
    if args.serve:
        try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: raise SystemExit('Persistent dispatcher already owns lock')
    deadline = time.monotonic()+args.max_hours*3600
    while True:
        # Different one-shot monitors cannot race with persistent dispatch.
        with (args.root/'maintenance/dispatch.lock').open('a') as gate:
            fcntl.flock(gate, fcntl.LOCK_EX)
            actions = dispatch(args.root, args.snapshot)
        report = inspect(args.root, args.snapshot); report['scheduling_action'] = actions
        save(args.root/'maintenance/automation-handoff.json', report)
        short = {k: report[k] for k in ('at_unix', 'counts', 'resources', 'scheduling_action')}
        short['issues'] = len(report['issues']); short['pending_adapter_questions'] = list(report['pending_adapter_cases'])
        save(args.root/'maintenance/automation-summary.json', short)
        with (args.root/'maintenance/automation-history.jsonl').open('a') as f:
            f.write(json.dumps(short)+'\n')
        print(json.dumps(short), flush=True)
        if not args.serve or time.monotonic() >= deadline: break
        time.sleep(60)


if __name__ == '__main__': main()
