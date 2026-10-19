"""Inspect registered parallel Jobs and small progress JSON; no case payloads."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
DEFAULT_PLAN=ROOT/'qbank/design/reviews/pdebench-parallel-20261019/plan.json'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--settle-terminal',action='store_true')
    parser.add_argument('--output',type=Path,default=ROOT/'runs/pdebench-cloud-trial/parallel-status.json')
    args=parser.parse_args()
    from huggingface_hub import HfApi,hf_hub_download
    spec=importlib.util.spec_from_file_location('budget',Path(__file__).with_name('hf_trial_launch.py'))
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    ledger_path=ROOT/'runs/pdebench-cloud-trial/budget.json'
    ledger=json.loads(ledger_path.read_text());api=HfApi()
    if args.settle_terminal:
        lock=ledger_path.with_suffix('.lock');fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(fd)
        try:
            ledger=json.loads(ledger_path.read_text());helper.settle_completed(api,ledger)
            temp=ledger_path.with_suffix('.status.tmp');temp.write_text(json.dumps(ledger,indent=2)+'\n');temp.replace(ledger_path)
        finally:lock.unlink(missing_ok=True)
    plan_bytes=DEFAULT_PLAN.read_bytes();plan=json.loads(plan_bytes);plan_sha=hashlib.sha256(plan_bytes).hexdigest()
    previous=json.loads(args.output.read_text()) if args.output.exists() else {}
    previous_workers={w['worker']:w for w in previous.get('workers',[])}
    now=datetime.now(timezone.utc); repo=plan['repository'];workers=[];alerts=[]
    prefix='migration-trials/pdebench/2026-10-19/parallel'
    counts={'advection':7016,'burgers':7080,'compressible':5000}
    registered=[a for a in ledger['attempts'] if a.get('phase')=='archive-parallel']
    if len(registered)!=5:alerts.append('Expected five registered reservations; found '+str(len(registered)))
    for attempt in registered:
        if attempt['plan_sha256']!=plan_sha:raise ValueError('Registered plan SHA differs')
        number=attempt['worker']; report={};info=None
        if attempt.get('job_id'):info=api.inspect_job(job_id=attempt['job_id'])
        head=api.repo_info(repo,repo_type='dataset',revision=attempt['revision']).sha
        path=f'{prefix}/w{number}/report.json'
        found=api.get_paths_info(repo,[path],repo_type='dataset',revision=head)
        if found:
            if found[0].size>5*1024**2:raise ValueError('Progress JSON too large')
            report=json.loads(Path(hf_hub_download(repo,path,repo_type='dataset',revision=head)).read_text())
            if report.get('plan_sha256')!=plan_sha or report.get('job_id')!=attempt.get('job_id'):
                raise ValueError('Progress identity differs')
        assignment=next(w for w in plan['workers'] if w['worker']==number)
        batches=report.get('batches',[])
        allowed={(b['file'],b['first'],b['count']) for b in assignment['batches']}
        done=[(b['source_file'],b['first'],b['cases']) for b in batches]
        if len(done)!=len(set(done)) or not set(done)<=allowed:raise ValueError('Repeated/unassigned reported batch')
        for b in batches:counts[b['family']]+=b['cases']
        stage=info.status.stage if info else attempt['status']
        w={'worker':number,'job_id':attempt.get('job_id'),'job_status':stage,
            'job_message':info.status.message if info else None,
            'report_status':report.get('status','initializing'),'verified_cases':sum(b['cases'] for b in batches),
            'completed_batches':len(batches),'target_cases':assignment['source_rows'],
            'current_batch':report.get('current_batch'),'error':report.get('error'),
            'report_revision':head,'durations':vars(info.durations) if info and info.durations else None,
            'last_successful_batch':done[-1] if done else None,'stall_checks':0}
        prior=previous_workers.get(number,{})
        if (stage=='RUNNING' and w['report_status'] not in ('worker_completed','merging','completed')
                and prior.get('current_batch')==w['current_batch'] and prior.get('verified_cases')==w['verified_cases']):
            previous_at=previous.get('observed_at_utc')
            if previous_at and (now-datetime.fromisoformat(previous_at)).total_seconds()>=1200:
                w['stall_checks']=prior.get('stall_checks',0)+1
            else:w['stall_checks']=prior.get('stall_checks',0)
        if w['stall_checks']>=2:alerts.append(f'Worker {number}: same batch stalled on two checks')
        if stage in ('ERROR','CANCELED','CANCELLED') or w['report_status']=='error':alerts.append(f'Worker {number}: {stage}; {w["error"] or w["job_message"]}')
        if stage=='COMPLETED' and w['verified_cases']!=w['target_cases']:alerts.append(f'Worker {number}: terminal job lacks complete verified source coverage')
        workers.append(w)
    occupation=round(sum(helper.effective_reservation(a) for a in ledger['attempts']),6)
    if occupation>.95:alerts.append('Cumulative reserved budget approaching USD 1')
    final=None; final_head=api.repo_info(repo,repo_type='dataset',revision=plan['final_branch']).sha
    final_path=prefix+'/final-report.json'
    found=api.get_paths_info(repo,[final_path],repo_type='dataset',revision=final_head)
    if found:
        if found[0].size>1024**2:raise ValueError('Final JSON too large')
        final=json.loads(Path(hf_hub_download(repo,final_path,repo_type='dataset',revision=final_head)).read_text())
        if (final.get('status')!='completed' or final.get('plan_sha256')!=plan_sha
            or final.get('verified_cases')!=250000 or final.get('pool_counts')!={'advection':80000,'burgers':120000,'compressible':50000}
            or len(final.get('coverage_per_file',{}))!=25 or set(final['coverage_per_file'].values())!={10000}):
            raise ValueError('Final completion claims differ')
        # Independently check final roots at the fixed accepted pool revision.
        for family,task in [('advection','pdebench-advection-1d'),('burgers','pdebench-burgers-1d'),('compressible','pdebench-compressible-1d')]:
            index_path='qbank/01-prescribed-pdes/pdebench-archive/'+task+'/pool/index.json'
            root=json.loads(Path(hf_hub_download(repo,index_path,repo_type='dataset',revision=final['pool_revision'])).read_text())
            if root['case_count']!=final['pool_counts'][family]:raise ValueError('Final pool root count differs')
        if counts!=final['pool_counts']:raise ValueError('Worker source sums differ from final pools')
    finalizer=next((w for w in workers if w['worker']==plan['finalizer_worker']),{})
    if finalizer.get('job_status')=='COMPLETED' and not final:alerts.append('Finalizer exited without accepted final report')
    snapshot={'observed_at_utc':now.isoformat(),'status':'completed' if final else ('attention_required' if alerts else 'running'),
        'verified_cases':sum(counts.values()),'family_verified_cases':counts,'target_cases':250000,
        'completed_batches':19+sum(w['completed_batches'] for w in workers),'planned_batches':250,
        'workers':workers,'final_report_revision':final_head if final else None,'final_report':final,
        'cumulative_budget_occupation_usd':occupation,'budget_limit_usd':1,'alerts':alerts,
        'invoice_verified':False,'source_or_case_payload_downloaded':False}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(snapshot,indent=2)+'\n')
    print(json.dumps(snapshot,indent=2))


if __name__=='__main__':main()
