"""Authorized local recovery sequence; all paid writes stay in the gated launcher."""
import hashlib
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone
import subprocess

ROOT = Path('/Users/jimzhou/code/CAE-Bench-OJ')
OUT = Path(__file__).resolve().parent
REGISTRY = ROOT/'runs/pdebench-cloud-trial/low-commit-recovery-intent.json'
LAUNCH_INTENT = ROOT/'runs/pdebench-cloud-trial/low-commit-launch-intent.json'
LOCK = ROOT/'runs/pdebench-cloud-trial/low-commit-recovery.lock'
COHORT = 'r3'
LOG = ROOT/'qbank/design/reviews/pdebench-low-commit-20261019/runs/r3/launcher.log'
STATE = {'cohort': COHORT, 'pid': os.getpid(), 'process_group': os.getpgrp(), 'script': str(Path(__file__).resolve()),
    'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'out_directory': str(OUT), 'log': str(LOG), 'cumulative_budget_limit_usd': 1}

def record(phase, **extra):
    STATE.update(phase=phase, observed_at_utc=datetime.now(timezone.utc).isoformat(), **extra)
    tmp = REGISTRY.with_suffix('.tmp')
    tmp.write_text(json.dumps(STATE, indent=2)+'\n'); tmp.replace(REGISTRY)
    print(json.dumps({'local_recovery_phase': phase, **extra}), flush=True)

def release_lock():
    if LOCK.exists() and LOCK.read_text().strip() == str(os.getpid()):
        LOCK.unlink()

def main():
    audit = json.loads((OUT/'audit.json').read_text())
    if audit['status'] != 'audited_stopped' or audit['verified_cases'] != 124096:
        raise ValueError('Expected fixed stopped r2 audit missing')
    if (LOG.parent/'launch.json').exists():
        raise ValueError('r3 already registered; inspect unknown outcomes, never replay')
    env = dict(os.environ, PYTHONPATH=str(ROOT/'src'))
    commands = [
        ('consolidating', ['hf_partial_merge.py', '--out', str(OUT), '--destination', 'pdebench-consolidated-20261019-after-r2', '--apply']),
        ('checking_consolidated', ['hf_partial_check.py', '--out', str(OUT)]),
        ('planning', ['hf_recovery_plan.py', '--out', str(OUT)]),
        ('prepared_preflight', ['hf_prepared_preflight.py', '--out', str(OUT)]),
        ('checking_launch_gates', ['hf_low_commit_launch.py', '--cohort', COHORT, '--plan', str(OUT/'plan.json')]),
    ]
    for phase, args in commands:
        record(phase)
        subprocess.run([sys.executable, str(ROOT/'src/utils/PDEBench'/args[0]), *args[1:]],
                       cwd=ROOT, env=env, check=True)
    plan = json.loads((OUT/'plan.json').read_text())
    if (plan['budget']['cumulative_reservation_usd'] > 1
            or any(type(w['hard_timeout_seconds']) is not int for w in plan['workers'])):
        raise ValueError('Unapproved budget or non-integer timeout')
    args = [sys.executable, str(ROOT/'src/utils/PDEBench/hf_low_commit_launch.py'),
            '--cohort', COHORT, '--plan', str(OUT/'plan.json'), '--submit']
    intent = {'cohort': COHORT, 'pid': os.getpid(), 'command': args,
        'plan_path': str(OUT/'plan.json'), 'plan_sha256': hashlib.sha256((OUT/'plan.json').read_bytes()).hexdigest(),
        'launcher_log': str(LOG), 'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'earliest_paid_launch_utc': plan['commit_policy']['earliest_launch_after_old_window_utc'],
        'status': 'handing_to_authorized_launcher', 'current_may_still_reference_stopped_prior_cohort': True}
    tmp = LAUNCH_INTENT.with_suffix('.tmp'); tmp.write_text(json.dumps(intent, indent=2)+'\n'); tmp.replace(LAUNCH_INTENT)
    (ROOT/'runs/pdebench-cloud-trial/low-commit-launch.pid').write_text(str(os.getpid())+'\n')
    record('handed_to_launcher', expected_cumulative_reservation_usd=plan['budget']['cumulative_reservation_usd'])
    release_lock()
    os.execv(sys.executable, args)

if __name__ == '__main__':
    # Do not overwrite another live controller's intent on duplicate invocation.
    fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, 'w') as f:
        f.write(str(os.getpid())+'\n')
    try:
        main()
    except Exception as exc:
        record('failed', error=str(exc)[-2000:])
        raise
    finally:
        release_lock()
