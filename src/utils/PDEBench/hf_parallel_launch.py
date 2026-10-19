"""Atomically reserve and submit the approved five-way migration exactly once."""
import argparse
import base64
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import tempfile

ROOT=Path(__file__).resolve().parents[3]
PLAN_PATH=ROOT/'qbank/design/reviews/pdebench-parallel-20261019/plan.json'
LEDGER=ROOT/'runs/pdebench-cloud-trial/budget.json'


def module(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


def terminal_observation_bound(raw, server_date, rate):
    """Bound a confirmed terminal job by its later server response timestamp."""
    if raw['status']['stage'] not in ('CANCELED','CANCELLED','COMPLETED','ERROR'):
        raise ValueError('Job is not terminal')
    expose, ssh = raw.get('expose'), raw.get('ssh')
    expose_off = expose == [] or (isinstance(expose,dict) and expose == {'ports':[]})
    ssh_off = ssh is False or (isinstance(ssh,dict) and ssh == {'enabled':False})
    if raw.get('flavor')!='cpu-basic' or not expose_off or not ssh_off:
        raise ValueError('Unexpected hardware or chargeable access')
    if not isinstance(rate,int) or not 0<rate<=167:raise ValueError('Invalid captured price')
    created=datetime.fromisoformat(raw['createdAt'].replace('Z','+00:00'))
    observed=parsedate_to_datetime(server_date)
    seconds=(observed-created).total_seconds()
    if seconds<0:raise ValueError('Server observation predates creation')
    return round((math.ceil(seconds/60)+1)*rate/1_000_000,6)


def replace_assignment(source, name, value):
    updated,n=re.subn(r'^'+name+r' = .*$',lambda _:name+' = '+repr(value),source,flags=re.MULTILINE)
    if n!=1:raise ValueError('Unexpected payload assignment '+name)
    return updated


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--submit',action='store_true');args=parser.parse_args()
    from huggingface_hub import HfApi,get_token,hf_hub_download
    from huggingface_hub.utils import get_session
    helper=module('hf_trial_launch'); worker=module('hf_parallel_archive'); old=module('hf_migrate')
    plan=json.loads(PLAN_PATH.read_text());api=HfApi()
    owner=api.whoami()['name']
    if plan['repository']!=owner+'/CAE-Bench-OJ':raise ValueError('Wrong authenticated owner')
    frozen=json.loads(Path(hf_hub_download(plan['repository'],
        'migration-trials/pdebench/2026-10-18/full-archive/full-report.json',repo_type='dataset',revision=plan['frozen_base_revision'])).read_text())
    worker.validate_plan(plan,frozen)
    raw_archive=Path(__file__).with_name('hf_archive_migrate.py').read_bytes()
    if hashlib.sha256(raw_archive).hexdigest()!=frozen['recipe']['worker_sha256']:
        raise ValueError('Frozen archive implementation changed')
    runtime=helper.runtime_payload(ROOT)
    if old.runtime_identity(runtime)!=frozen['recipe']['runtime_contents_sha256']:
        raise ValueError('Frozen runtime contents changed')
    plan['frozen_runtime_contents_sha256']=old.runtime_identity(runtime)
    # This execution contract is frozen before any job is reserved/submitted.
    plan['execution']={'coordinator_sha256':hashlib.sha256(Path(__file__).with_name('hf_parallel_archive.py').read_bytes()).hexdigest(),
        'archive_worker_sha256':hashlib.sha256(raw_archive).hexdigest(),'no_paid_retries':True}
    plan_bytes=(json.dumps(plan,indent=2)+'\n').encode();plan_sha=hashlib.sha256(plan_bytes).hexdigest()
    hardware=next(h for h in api.list_jobs_hardware() if h.name=='cpu-basic')
    if hardware.unit_label!='minute' or not 0<hardware.unit_cost_micro_usd<=167:raise ValueError('CPU Basic price differs')
    reserve=round((600+10)*hardware.unit_cost_micro_usd/1_000_000,6)
    if not args.submit:
        print(json.dumps({'workers':5,'plan_sha256':plan_sha,'each_reservation_usd':reserve,'submit':False}));return
    token=get_token()
    if not token:raise ValueError('Missing HF authentication')
    lock=LEDGER.with_suffix('.lock');fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(fd)
    try:
        ledger=json.loads(LEDGER.read_text())
        if ledger['budget_usd']!=1:raise ValueError('Unexpected cumulative budget')
        if any(a.get('phase')=='archive-parallel' or a.get('status')=='submission_pending' for a in ledger['attempts']):
            raise ValueError('Parallel jobs already reserved or submission unresolved; inspect, never resubmit')
        old_id='6ad4dbdac6628814522749be'
        response=get_session().get(f'{api.endpoint}/api/jobs/{owner}/{old_id}',headers=api._build_hf_headers());response.raise_for_status()
        raw=response.json()
        if raw['status']['stage'] not in ('CANCELED','CANCELLED'):raise ValueError('Old writer is not canceled')
        original=next(a for a in ledger['attempts'] if a.get('job_id')==old_id)
        bound=terminal_observation_bound(raw,response.headers['date'],original['hardware_unit_cost_micro_usd'])
        original.update(status=raw['status']['stage'].lower(),api_lifecycle_cost_upper_bound_usd=bound,
            terminal_observation={'server_date':response.headers['date'],'api_created_at':raw['createdAt'],
                'stage':raw['status']['stage'],'method':'authenticated terminal response upper bound; not invoice'})
        mismatch=next(a for a in ledger['attempts'] if a.get('job_id')=='6ad4a7da5ccb47ba0f7c3968')
        mismatch['original_maximum_reserved_compute_usd']=mismatch['maximum_reserved_compute_usd']
        mismatch['maximum_reserved_compute_usd']=max(.02,mismatch['maximum_reserved_compute_usd'])
        mismatch['reservation_reason']='Historical observed CPU Upgrade; retain upgraded timeout plus startup margin'
        occupation=sum(helper.effective_reservation(a) for a in ledger['attempts'])
        if occupation+5*reserve>1:raise ValueError('Five reservations exceed cumulative USD 1')
        if any(j.status.stage in ('RUNNING','STARTING','PENDING') and j.id==old_id for j in api.list_jobs()):
            raise ValueError('Old writer still active')
        repo=plan['repository'];base=plan['frozen_base_revision']
        branches={r.name:r.target_commit for r in api.list_repo_refs(repo,repo_type='dataset').branches}
        for branch in [w['branch'] for w in plan['workers']]+[plan['final_branch']]:
            if branch in branches and branches[branch]!=base:raise ValueError('Destination branch changed: '+branch)
            api.create_branch(repo,repo_type='dataset',branch=branch,revision=base,exist_ok=True)
        PLAN_PATH.write_bytes(plan_bytes)
        stage=Path(__file__).with_name('hf_parallel_archive.py').read_text()
        for name,value in [('RUNTIME_ZIP',runtime),('ARCHIVE_SOURCE',base64.b64encode(raw_archive).decode()),('PLAN',base64.b64encode(plan_bytes).decode())]:
            stage=replace_assignment(stage,name,value)
        script_sha=hashlib.sha256(stage.encode()).hexdigest()
        new=[]
        for assignment in plan['workers']:
            attempt={'phase':'archive-parallel','worker':assignment['worker'],'status':'reserved',
                'hardware':'cpu-basic','hardware_unit_cost_micro_usd':hardware.unit_cost_micro_usd,
                'timeout_seconds':36000,'maximum_reserved_compute_usd':reserve,'repo_id':repo,
                'revision':assignment['branch'],'prefix':worker.PREFIX+'/w'+str(assignment['worker']),
                'plan_sha256':plan_sha,'submitted_script_sha256':script_sha,'source_rows':assignment['source_rows'],
                'created_at':datetime.now(timezone.utc).isoformat()}
            new.append(attempt)
        ledger['attempts'].extend(new)
        def save():
            temp=LEDGER.with_suffix('.parallel.tmp');temp.write_text(json.dumps(ledger,indent=2)+'\n');temp.replace(LEDGER)
        save()
        evidence=PLAN_PATH.parent/'launch.json'
        def receipt():evidence.write_text(json.dumps({'plan_sha256':plan_sha,'jobs':new,
            'cumulative_budget_occupation_usd':sum(helper.effective_reservation(a) for a in ledger['attempts']),
            'invoice_verified':False},indent=2)+'\n')
        receipt()
        with tempfile.TemporaryDirectory(prefix='caeoj-five-job-code-') as tmp:
            staged=Path(tmp)/'hf_parallel_archive.py';staged.write_text(stage)
            for attempt in new:
                attempt['status']='submission_pending';save();receipt()
                job=api.run_uv_job(str(staged),flavor='cpu-basic',timeout=36000,
                    script_args=['--worker',str(attempt['worker'])],secrets={'HF_TOKEN':token},
                    name='caeoj-pdebench-parallel-w'+str(attempt['worker']),
                    labels={'caeoj-purpose':'pdebench-parallel','budget-usd':'1','worker':str(attempt['worker'])})
                attempt.update(status='submitted',job_id=job.id,job_url=job.url);save();receipt()
                actual=api.inspect_job(job_id=job.id)
                attempt['observed_hardware']=actual.flavor
                if actual.flavor!='cpu-basic':
                    api.cancel_job(job_id=job.id);attempt['status']='canceled_hardware_mismatch';save();receipt()
                    raise RuntimeError('Wrong actual hardware; canceled; no further submissions')
                save();receipt()
                print(json.dumps({'worker':attempt['worker'],'job_id':job.id,'hardware':actual.flavor}),flush=True)
        print(evidence.read_text())
    finally:lock.unlink(missing_ok=True)


if __name__=='__main__':main()
