"""Reserve an entire low-commit cohort and submit it once within cumulative USD 1."""
import argparse
import base64
from email.utils import parsedate_to_datetime
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import tempfile
import time
import zipfile

ROOT=Path(__file__).resolve().parents[3]
REVIEW=ROOT/'qbank/design/reviews/pdebench-low-commit-20261019'
LEDGER=ROOT/'runs/pdebench-cloud-trial/budget.json'
CURRENT=ROOT/'runs/pdebench-cloud-trial/low-commit-current.json'
CODE_FILES=['src/caeoj_tools/data_pool_shards.py','src/utils/PDEBench/hf_commit_policy.py',
    'src/utils/PDEBench/hf_commit_gateway.py','src/utils/PDEBench/hf_low_commit_worker.py',
    'src/utils/PDEBench/hf_parallel_archive.py','src/utils/PDEBench/hf_archive_migrate.py',
    'src/utils/PDEBench/hf_low_commit_launch.py','src/utils/PDEBench/hf_low_commit_status.py',
    'src/utils/PDEBench/hf_low_commit_readiness.py','tests/test_pdebench_low_commit.py',
    'tests/test_pdebench_recovery.py','tests/test_data_pool.py']


def load(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def inventory():return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in CODE_FILES}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--cohort',default='r1');parser.add_argument('--plan',type=Path,default=REVIEW/'plan.json')
    parser.add_argument('--submit',action='store_true');args=parser.parse_args()
    if not re.fullmatch('r[1-9][0-9]*',args.cohort):raise ValueError('Explicit recovery cohort rN required')
    from huggingface_hub import HfApi,get_token
    from huggingface_hub.utils import get_session
    api=HfApi();helper=load('hf_trial_launch');policy=load('hf_commit_policy');source_helper=load('hf_migrate')
    worker_module=load('hf_low_commit_worker');plan=json.loads(args.plan.read_text());repo=plan['repository']
    owner=api.whoami()['name']
    if repo!=owner+'/CAE-Bench-OJ':raise ValueError('Wrong HF owner')
    check=json.loads((args.plan.parent/'consolidated-check.json').read_text())
    if (not check['valid'] or check['fixed_revision']!=plan['consolidated_revision']
        or check['verified_cases']!=plan['completed_source_rows']):raise ValueError('Consolidated baseline not accepted')
    baseline=json.loads((args.plan.parent/'audit.json').read_text())['coverage']
    plan['baseline_coverage']=baseline
    plan['frozen_base_revision']=plan['consolidated_revision']
    if api.repo_info(repo,repo_type='dataset',revision=plan['consolidated_revision']).sha!=plan['consolidated_revision']:
        raise ValueError('Baseline commit missing')
    archive=Path(__file__).with_name('hf_archive_migrate.py').read_bytes()
    if hashlib.sha256(archive).hexdigest()!=plan['source_worker_sha256']:raise ValueError('Source conversion implementation changed')
    if plan['remaining_source_rows']<=0:raise ValueError('All sources available: consolidate/verify, do not submit empty Jobs')
    plan['cohort']=args.cohort;plan['progress_prefix']='migration-trials/pdebench/2026-10-19/low-commit/'+args.cohort
    plan['final_branch']='pdebench-low-commit-20261019-'+args.cohort
    for w in plan['workers']:w['branch']=plan['final_branch']+'-w'+str(w['worker'])
    plan['autonomous_recovery_authorized']=True
    plan['budget']['no_sixth_job_or_paid_retry']=False
    plan['budget']['recovery_rule']='Only after terminal settlement and exact re-audit; all additional cohorts remain inside cumulative USD 1'
    worker_module.validate_recovery_plan(plan)
    hardware=next(h for h in api.list_jobs_hardware() if h.name=='cpu-basic')
    if hardware.unit_label!='minute' or not 0<hardware.unit_cost_micro_usd<=167:raise ValueError('CPU Basic price differs')
    seconds=max(w['hard_timeout_seconds'] for w in plan['workers'])
    if not all(w['hard_timeout_seconds']==seconds for w in plan['workers']):raise ValueError('Cohort timeout ceilings differ')
    reserve,_=policy.planned_reservation_usd(rate_micro_usd=hardware.unit_cost_micro_usd,hours=seconds/3600,prior=0)
    runtime=helper.runtime_payload(ROOT)
    output=io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(runtime))) as src,zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as dest:
        for name in src.namelist():dest.writestr(name,src.read(name))
        for name in ['hf_commit_policy.py','hf_commit_gateway.py']:
            dest.write(Path(__file__).with_name(name),'support/'+name)
    runtime=base64.b64encode(output.getvalue()).decode()
    plan['execution']={'code_inventory':inventory(),'runtime_contents_sha256':source_helper.runtime_identity(runtime),
        'huggingface_hub_version':'1.33.0','python':'3.12','two_commit_publisher':True,'actual_commit_http_gate':True}
    readiness=ROOT/'runs/pdebench-cloud-trial/low-commit-readiness.json'
    if not readiness.exists():raise ValueError('Missing local integration readiness evidence')
    proof=json.loads(readiness.read_text())
    if not proof.get('passed') or proof.get('code_inventory')!=inventory():raise ValueError('Implementation changed after readiness checks')
    plan_bytes=(json.dumps(plan,indent=2)+'\n').encode();plan_sha=hashlib.sha256(plan_bytes).hexdigest()
    target=REVIEW/'runs'/args.cohort;target.mkdir(parents=True,exist_ok=True)
    if not args.submit:
        print(json.dumps({'cohort':args.cohort,'plan_sha256':plan_sha,'reserve_per_job_usd':reserve,'submit':False}));return
    if (target/'launch.json').exists():raise ValueError('Cohort already registered; never resubmit unknown outcomes')
    token=get_token()
    if not token:raise ValueError('Missing HF credentials')
    # Cold waiting happens locally before reservations or paid Job submission.
    response=get_session().get(api.endpoint+'/api/whoami-v2',headers=api._build_hf_headers());response.raise_for_status()
    now=parsedate_to_datetime(response.headers['date']).timestamp()+.5
    earliest=__import__('datetime').datetime.fromisoformat(plan['commit_policy']['earliest_launch_after_old_window_utc']).timestamp()
    left=max(0,earliest-now)
    if left:
        print(json.dumps({'phase':'unbilled_local_cooldown','seconds':round(left),'cohort':args.cohort}),flush=True)
        until=time.monotonic()+left
        while time.monotonic()<until:time.sleep(min(30,until-time.monotonic()))
    if inventory()!=plan['execution']['code_inventory']:
        raise ValueError('Code changed during unbilled wait; recheck readiness before any reservation/submission')
    lock=LEDGER.with_suffix('.lock');fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(fd)
    try:
        ledger=json.loads(LEDGER.read_text())
        if ledger['budget_usd']!=1:raise ValueError('Cumulative limit changed')
        if any(a.get('status') in ('reserved','submission_pending') for a in ledger['attempts']):
            raise ValueError('Resolve existing reserved/unknown submissions first')
        helper.settle_completed(api,ledger)
        for attempt in ledger['attempts']:
            if attempt.get('phase') in ('archive-full','archive-parallel','archive-low-commit') and attempt.get('job_id'):
                info=api.inspect_job(job_id=attempt['job_id'])
                if info.status.stage not in ('COMPLETED','ERROR','CANCELED','CANCELLED'):
                    raise ValueError('An older writer remains active')
                if attempt.get('cohort')==args.cohort:raise ValueError('Cohort was already submitted')
                if attempt.get('phase')=='archive-low-commit' and 'api_lifecycle_cost_upper_bound_usd' not in attempt:
                    raise ValueError('Prior cohort terminal budget requires settlement')
        occupation=sum(helper.effective_reservation(a) for a in ledger['attempts'])
        if occupation+5*reserve>1:raise ValueError('Five jobs exceed remaining cumulative budget; do not submit')
        plan['budget'].update(prior_conservative_occupation_usd=round(occupation,6),
            cumulative_reservation_usd=round(occupation+5*reserve,6))
        plan_bytes=(json.dumps(plan,indent=2)+'\n').encode();plan_sha=hashlib.sha256(plan_bytes).hexdigest()
        branches={b.name:b.target_commit for b in api.list_repo_refs(repo,repo_type='dataset').branches}
        for branch in [w['branch'] for w in plan['workers']]+[plan['final_branch']]:
            if branch in branches and branches[branch]!=plan['consolidated_revision']:raise ValueError('Destination changed')
            api.create_branch(repo,repo_type='dataset',branch=branch,revision=plan['consolidated_revision'],exist_ok=True)
        (target/'plan.json').write_bytes(plan_bytes)
        script=Path(__file__).with_name('hf_low_commit_worker.py').read_text()
        values={'RUNTIME_ZIP':runtime,'ARCHIVE_SOURCE':base64.b64encode(archive).decode(),
            'COORD_SOURCE':base64.b64encode(Path(__file__).with_name('hf_parallel_archive.py').read_bytes()).decode(),
            'PLAN':base64.b64encode(plan_bytes).decode()}
        replace=load('hf_parallel_launch').replace_assignment
        for name,value in values.items():script=replace(script,name,value)
        script_sha=hashlib.sha256(script.encode()).hexdigest()
        attempts=[{'phase':'archive-low-commit','cohort':args.cohort,'worker':w['worker'],'status':'reserved',
            'hardware':'cpu-basic','hardware_unit_cost_micro_usd':hardware.unit_cost_micro_usd,'timeout_seconds':seconds,
            'maximum_reserved_compute_usd':reserve,'repo_id':repo,'revision':w['branch'],
            'prefix':plan['progress_prefix']+'/w'+str(w['worker']),'source_rows':w['source_rows'],
            'plan_sha256':plan_sha,'submitted_script_sha256':script_sha} for w in plan['workers']]
        ledger['attempts'].extend(attempts)
        def save():
            tmp=LEDGER.with_suffix('.low-commit.tmp');tmp.write_text(json.dumps(ledger,indent=2)+'\n');tmp.replace(LEDGER)
            (target/'launch.json').write_text(json.dumps({'plan_sha256':plan_sha,'cohort':args.cohort,'jobs':attempts,
                'cumulative_budget_occupation_usd':sum(helper.effective_reservation(a) for a in ledger['attempts']),
                'invoice_verified':False},indent=2)+'\n')
            CURRENT.write_text(json.dumps({'cohort':args.cohort,'plan_path':str(target/'plan.json'),'launch_path':str(target/'launch.json')},indent=2)+'\n')
        save()
        with tempfile.TemporaryDirectory(prefix='caeoj-low-commit-') as tmp:
            staged=Path(tmp)/'hf_low_commit_worker.py';staged.write_text(script)
            for attempt in attempts:
                attempt['status']='submission_pending';save()
                job=api.run_uv_job(str(staged),flavor='cpu-basic',python='3.12',timeout=seconds,
                    script_args=['--worker',str(attempt['worker'])],secrets={'HF_TOKEN':token},
                    name='caeoj-pdebench-low-'+args.cohort+'-w'+str(attempt['worker']),
                    labels={'caeoj-purpose':'pdebench-low-commit','cohort':args.cohort,'budget-usd':'1'})
                attempt.update(status='submitted',job_id=job.id,job_url=job.url);save()
                actual=api.inspect_job(job_id=job.id)
                if actual.flavor!='cpu-basic':
                    api.cancel_job(job_id=job.id);attempt['status']='canceled_hardware_mismatch';save()
                    raise RuntimeError('Wrong actual hardware; stopped further submissions')
                attempt['observed_hardware']=actual.flavor;save()
                print(json.dumps({'worker':attempt['worker'],'job_id':job.id,'hardware':actual.flavor}),flush=True)
        print(json.dumps({'status':'five_submitted','cohort':args.cohort,'cumulative_reservation_usd':occupation+5*reserve}),flush=True)
    finally:lock.unlink(missing_ok=True)


if __name__=='__main__':main()
