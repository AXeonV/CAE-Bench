"""Read-only current-cohort monitoring; metadata and bounded non-following logs only."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
CURRENT=ROOT/'runs/pdebench-cloud-trial/low-commit-current.json'


def module(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--settle-terminal',action='store_true')
    parser.add_argument('--output',type=Path,default=ROOT/'runs/pdebench-cloud-trial/low-commit-status.json')
    parser.add_argument('--logs',action='store_true',help='Read last 20 currently available logs per registered Job; never follow')
    args=parser.parse_args()
    from huggingface_hub import HfApi,hf_hub_download
    from huggingface_hub.utils import get_session
    if not CURRENT.exists():
        print(json.dumps({'status':'not_registered','jobs_submitted':False}));return
    current=json.loads(CURRENT.read_text());plan_bytes=Path(current['plan_path']).read_bytes();plan=json.loads(plan_bytes)
    plan_sha=hashlib.sha256(plan_bytes).hexdigest();repo=plan['repository'];api=HfApi()
    ledger_path=ROOT/'runs/pdebench-cloud-trial/budget.json';ledger=json.loads(ledger_path.read_text());helper=module('hf_trial_launch')
    if args.settle_terminal:
        lock=ledger_path.with_suffix('.lock')
        try:fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        except FileExistsError:
            print(json.dumps({'status':'launcher_or_settlement_holds_lock','cohort':current['cohort']}));return
        os.close(fd)
        try:
            ledger=json.loads(ledger_path.read_text());helper.settle_completed(api,ledger)
            for a in ledger['attempts']:
                if a.get('phase')!='archive-low-commit' or not a.get('job_id') or 'api_lifecycle_cost_upper_bound_usd' in a:continue
                response=get_session().get(f'{api.endpoint}/api/jobs/jimzhouzzy2006/{a["job_id"]}',headers=api._build_hf_headers());response.raise_for_status();raw=response.json()
                if raw['status']['stage'] not in ('COMPLETED','ERROR','CANCELED','CANCELLED'):continue
                bound=module('hf_parallel_launch').terminal_observation_bound(raw,response.headers['date'],a['hardware_unit_cost_micro_usd'])
                a.update(status=raw['status']['stage'].lower(),api_lifecycle_cost_upper_bound_usd=bound,
                    terminal_observation={'server_date':response.headers['date'],'created_at':raw['createdAt'],'stage':raw['status']['stage'],'method':'authenticated terminal observation; not invoice'})
            temp=ledger_path.with_suffix('.low-status.tmp');temp.write_text(json.dumps(ledger,indent=2)+'\n');temp.replace(ledger_path)
        finally:lock.unlink(missing_ok=True)
    attempts=[a for a in ledger['attempts'] if a.get('phase')=='archive-low-commit' and a.get('cohort')==current['cohort']]
    now=datetime.now(timezone.utc);old=json.loads(args.output.read_text()) if args.output.exists() else {}
    prior={w['worker']:w for w in old.get('workers',[]) if old.get('cohort')==current['cohort']}
    counts=dict(plan['family_completed']);workers=[];alerts=[]
    def logs(a):
        events=[]
        if args.logs and a.get('job_id'):
            for line in api.fetch_job_logs(job_id=a['job_id'],follow=False,tail=20):
                try:value=json.loads(line)
                except (ValueError,TypeError):continue
                if isinstance(value,dict) and value.get('phase') in ('commit_post','rate_limited_wait','batch_verified','worker_error'):events.append(value)
        return a['worker'],events
    with ThreadPoolExecutor(max_workers=5) as executor:
        events_by_worker=dict(executor.map(logs,attempts))
    for a in attempts:
        assignment=next(w for w in plan['workers'] if w['worker']==a['worker']);report={};info=None
        if a.get('job_id'):info=api.inspect_job(job_id=a['job_id'])
        head=api.repo_info(repo,repo_type='dataset',revision=a['revision']).sha
        path=a['prefix']+'/report.json';found=api.get_paths_info(repo,[path],repo_type='dataset',revision=head)
        if found:
            if found[0].size>5*1024**2:raise ValueError('Unexpected report size')
            report=json.loads(Path(hf_hub_download(repo,path,repo_type='dataset',revision=head)).read_text())
            if report['plan_sha256']!=plan_sha or report['job_id']!=a.get('job_id'):raise ValueError('Progress identity differs')
        done=[(b['source_file'],b['first'],b['cases']) for b in report.get('batches',[])]
        allowed={(b['file'],b['first'],b['count']) for b in assignment['batches']}
        if len(done)!=len(set(done)) or not set(done)<=allowed:raise ValueError('Repeated or unassigned source coverage')
        for b in report.get('batches',[]):counts[b['family']]+=b['cases']
        stage=info.status.stage if info else a['status'];events=events_by_worker.get(a['worker'],[])
        cooldown=max([e.get('until_server_time',0) for e in events]+[report.get('commit_policy',{}).get('cooldown_until_server_time',0)])
        phase='quota_cooldown' if cooldown>now.timestamp() else report.get('status','initializing')
        w={'worker':a['worker'],'job_id':a.get('job_id'),'job_status':stage,'job_message':info.status.message if info else None,
            'phase':phase,'verified_cases':sum(b['cases'] for b in report.get('batches',[])),
            'target_cases':assignment['source_rows'],'completed_batches':len(done),'current_batch':report.get('current_batch'),
            'report_revision':head,'last_verified_span':done[-1] if done else None,
            'durations':vars(info.durations) if info and info.durations else None,
            'cooldown_until_server_time':cooldown,'recent_control_events':events,'stall_checks':0}
        previous=prior.get(a['worker'],{})
        if stage in ('ERROR','CANCELED','CANCELLED'):alerts.append(f'Worker {a["worker"]} terminal {stage}')
        if phase=='quota_cooldown' and cooldown>previous.get('cooldown_until_server_time',0):alerts.append(f'Worker {a["worker"]} received quota cooldown')
        if (stage=='RUNNING' and phase not in ('quota_cooldown','worker_completed','merging','completed')
            and previous.get('current_batch')==w['current_batch'] and previous.get('verified_cases')==w['verified_cases']):
            if old.get('observed_at_utc') and (now-datetime.fromisoformat(old['observed_at_utc'])).total_seconds()>=1200:
                w['stall_checks']=previous.get('stall_checks',0)+1
            else:w['stall_checks']=previous.get('stall_checks',0)
        if w['stall_checks']>=2:alerts.append(f'Worker {a["worker"]} unchanged for two scheduled checks')
        if stage=='COMPLETED' and w['verified_cases']!=assignment['source_rows']:alerts.append(f'Worker {a["worker"]} exited without complete assigned coverage')
        workers.append(w)
    final=None;final_head=api.repo_info(repo,repo_type='dataset',revision=plan['final_branch']).sha
    path=plan['progress_prefix']+'/final-report.json';found=api.get_paths_info(repo,[path],repo_type='dataset',revision=final_head)
    if found:
        if found[0].size>1024**2:raise ValueError('Final report unexpectedly large')
        final=json.loads(Path(hf_hub_download(repo,path,repo_type='dataset',revision=final_head)).read_text())
        if (final.get('status')!='completed' or final['plan_sha256']!=plan_sha or final['verified_cases']!=250000
            or final['pool_counts']!={'advection':80000,'burgers':120000,'compressible':50000}
            or len(final['coverage_per_file'])!=25 or set(final['coverage_per_file'].values())!={10000}
            or counts!=final['pool_counts']):raise ValueError('Final completion claims mismatch')
        for family,task in [('advection','pdebench-advection-1d'),('burgers','pdebench-burgers-1d'),('compressible','pdebench-compressible-1d')]:
            root_path='qbank/01-prescribed-pdes/pdebench-archive/'+task+'/pool/index.json'
            root=json.loads(Path(hf_hub_download(repo,root_path,repo_type='dataset',revision=final['pool_revision'])).read_text())
            if root['case_count']!=counts[family]:raise ValueError('Accepted final root count differs')
    terminal=all(w['job_status'] in ('COMPLETED','ERROR','CANCELED','CANCELLED') for w in workers) and len(workers)==5
    finalizer=next((w for w in workers if w['worker']==plan['finalizer_worker']),{})
    if finalizer.get('job_status')=='COMPLETED' and not final:alerts.append('Finalizer exited without final accepted report')
    occupation=round(sum(helper.effective_reservation(a) for a in ledger['attempts']),6)
    if occupation>.95:alerts.append('Cumulative budget occupation near USD 1')
    snapshot={'observed_at_utc':now.isoformat(),'cohort':current['cohort'],
        'status':'completed' if final and terminal else ('attention_required' if alerts else 'running'),
        'verified_cases':sum(counts.values()),'family_verified_cases':counts,'target_cases':250000,'workers':workers,
        'all_jobs_terminal':terminal,'final_report':final,'final_report_revision':final_head if final else None,
        'cumulative_budget_occupation_usd':occupation,'known_terminal_lifecycle_upper_usd':round(sum(a.get('api_lifecycle_cost_upper_bound_usd',0) for a in ledger['attempts']),6),
        'budget_limit_usd':1,'alerts':alerts,'invoice_verified':False,'numerical_payload_downloaded':False}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(snapshot,indent=2)+'\n');print(json.dumps(snapshot,indent=2))


if __name__=='__main__':main()
