"""Create the reviewed low-commit recovery plan without submitting Jobs."""
import hashlib
import argparse
import json
from pathlib import Path
from datetime import datetime,timezone,timedelta
from email.utils import parsedate_to_datetime
from hf_commit_policy import planned_reservation_usd,measured_recovery_timeout_hours

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'qbank/design/reviews/pdebench-low-commit-20261019'


def main():
    global OUT
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path);args=parser.parse_args()
    if args.out:OUT=args.out.resolve()
    from huggingface_hub import hf_hub_download
    audit=json.loads((OUT/'audit.json').read_text())
    frozen=json.loads((ROOT/'qbank/design/reviews/pdebench-parallel-20261019/frozen-full-report.json').read_text())
    old_plan=json.loads((ROOT/'qbank/design/reviews/pdebench-parallel-20261019/plan.json').read_text())
    done={(b['source_file'],b['first'],b['cases']) for b in frozen['batches']}
    samples={f:[] for f in audit['family_verified_cases']}
    for branch in audit['branches']:
        prefix=audit.get('progress_prefix','migration-trials/pdebench/2026-10-19/parallel')+'/w'+str(branch['worker'])+'/report.json'
        try:progress=json.loads(Path(hf_hub_download(audit['repository'],prefix,repo_type='dataset',revision=branch['revision'])).read_text())
        except __import__('huggingface_hub').errors.EntryNotFoundError:progress={'batches':[]}
        for b in branch['verified_batches']:done.add((b['file'],b['first'],b['count']))
        for b in progress['batches']:samples[b['family']].append((b['cases'],b['elapsed_seconds']))
    serial={f:sum(b['elapsed_seconds'] for b in frozen['batches'] if b['family']==f)/sum(b['cases'] for b in frozen['batches'] if b['family']==f) for f in samples}
    rates={f:max(serial[f],sum(t for _,t in rows)/sum(n for n,_ in rows) if rows else 0) for f,rows in samples.items()}
    remaining=[]
    accepted={file:set(rows) for file,rows in audit['coverage'].items()}
    for i,b in enumerate(frozen['recipe']['plan']):
        rows=set(range(b['first'],b['first']+b['count']))
        if rows<=accepted[b['file']]:continue
        if rows&accepted[b['file']]:raise ValueError('Partly accepted source span needs explicit split')
        remaining.append(dict(b,original_batch_number=i))
    groups=[{'worker':i+1,'branch':f'pdebench-low-commit-20261019-w{i+1}','batches':[],'estimated_seconds':0.} for i in range(5)]
    for b in sorted(remaining,key=lambda x:(-max(x['count']*rates[x['family']],460),x['file'],x['first'])):
        target=min(groups,key=lambda g:(g['estimated_seconds'],len(g['batches']),g['worker']))
        weight=max(b['count']*rates[b['family']],460.)
        target['batches'].append(b);target['estimated_seconds']+=weight
    for g in groups:
        # Mix families instead of processing all scalar data before all CFD.
        byfamily={f:sorted((b for b in g['batches'] if b['family']==f),key=lambda b:(b['file'],b['first'])) for f in rates}
        interleaved=[]
        while any(byfamily.values()):
            for f in rates:
                if byfamily[f]:interleaved.append(byfamily[f].pop(0))
        g.update(batches=interleaved,source_rows=sum(b['count'] for b in g['batches']),
            family_rows={f:sum(b['count'] for b in g['batches'] if b['family']==f) for f in rates},
            estimated_hours=round(g['estimated_seconds']/3600,3),hard_timeout_seconds=43200)
    coverage={k:set(v) for k,v in audit['coverage'].items()}
    for g in groups:
        for b in g['batches']:
            rows=set(range(b['first'],b['first']+b['count']))
            if rows&coverage[b['file']]:raise ValueError('Recovery repeats accepted trajectories')
            coverage[b['file']]|=rows
    if len(coverage)!=25 or any(v!=set(range(10000)) for v in coverage.values()):raise ValueError('Recovery leaves source holes')
    for prepared in audit['quarantine']:
        owners=[g['worker'] for g in groups if any((b['file'],b['first'],b['count'])==(prepared['file'],prepared['first'],prepared['count']) for b in g['batches'])]
        if len(owners)!=1:raise ValueError('Prepared span lacks exactly one recovery owner')
        prepared['recovery_worker']=owners[0]
        prepared['recovery_policy']='Inspect frozen assets and complete cloud consumption before acceptance; preserve published binding; absent unpublished candidate needs exact source/JSON/array proof and full remote consumption'
    max_hours=max(g['estimated_hours'] for g in groups)
    timeout_hours=(12 if audit['verified_cases']==31096 else measured_recovery_timeout_hours(
        max_hours,max(len(g['batches']) for g in groups),audit['cumulative_budget_occupation_usd']))
    # A later small remainder should not reserve five full 12-hour machines.
    each,total=planned_reservation_usd(hours=timeout_hours,prior=audit['cumulative_budget_occupation_usd'])
    for g in groups:g['hard_timeout_seconds']=int(timeout_hours*3600)
    cold=max(parsedate_to_datetime(e['server_date']) for e in audit['old_jobs'])+timedelta(hours=1)
    receipt_path=OUT/'merge-receipt.json';receipt=json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
    finalizer=min(groups,key=lambda g:g['estimated_seconds'])['worker']
    work_hours=sum(g['estimated_seconds'] for g in groups)/3600
    measured_total_hours=work_hours+len(remaining)*115/3600+1.75+5*.25
    expected_occupation=audit['cumulative_budget_occupation_usd']+measured_total_hours*167*60/1_000_000
    result={'kind':'pdebench-low-commit-recovery-v1','status':'planned_not_launched','repository':audit['repository'],
        'consolidated_branch':receipt.get('destination_branch','pdebench-consolidated-20261019'),'consolidated_revision':receipt.get('final_revision'),
        'baseline_coverage':audit['coverage'],'source_revision':audit['source_revision'],'source_worker_sha256':old_plan['execution']['archive_worker_sha256'],
        'completed_source_rows':audit['verified_cases'],'family_completed':audit['family_verified_cases'],
        'remaining_source_rows':sum(g['source_rows'] for g in groups),'remaining_batches':len(remaining),
        'workers':groups,'rates_seconds_per_row':rates,'finalizer_worker':finalizer,
        'quarantined_prepared_batches':audit['quarantine'],'prepared_rows_already_in_remaining_total':sum(x['count'] for x in audit['quarantine']),
        'commit_policy':{'scope':'Every POST /api/datasets/<repo>/commit/<branch>, from every worker, failure handler and finalizer',
            'global_slot_seconds':46,'worker_slot_period_seconds':230,'nominal_repository_commits_per_hour':78.26,
            'maximum_scheduled_requests_per_rolling_hour':80,'slot_guard_seconds':3,'one_attempt_per_slot':True,
            'server_clock_required':True,'worker_ownership':'slot_number modulo 5 == worker_number - 1',
            'exclusive_finalizer_only_after_other_four_api_completed':True,'per_batch_target_commit_count':2,
            'no_git_commit_for_initial_planned_or_current_batch_progress':True,
            'first_commit':'Prevalidate local bundle, preupload blobs without repository commits, atomically publish immutable assets + hash partitions + roots + prepared checkpoint/progress at one fixed parent',
            'second_commit':'After full fixed-commit real remote consumption, atomically publish verified checkpoint + cumulative progress; only then count rows',
            'on_429':'Respect Retry-After/RateLimit reset; wait before using a new owned slot. Never immediate retry or terminate merely on an explicit quota rejection. Wait counts within hard runtime/budget.',
            'on_unknown_commit_outcome':'Inspect fixed recipe/checkpoint/asset hashes and exact branch head before deciding whether a retry is safe; unknown outcome stops, no blind replay',
            'critical':'Gate the actual commit HTTP request, including SDK/internal writes; pacing outer create_commit calls before slow LFS upload is insufficient',
            'earliest_launch_after_old_window_utc':cold.isoformat(),'startup':'Wait for old write quota to clear before paying for new Jobs; count consolidation writes in the first-hour allowance. New quota errors may move this earliest time later.'},
        'budget':{'cumulative_limit_usd':1,'prior_conservative_occupation_usd':audit['cumulative_budget_occupation_usd'],
            'known_terminal_lifecycle_upper_usd':audit['known_terminal_lifecycle_upper_usd'],
            'historical_unknown_reserves_usd':round(audit['cumulative_budget_occupation_usd']-audit['known_terminal_lifecycle_upper_usd'],6),
            'timeout_hours':timeout_hours,'per_job_plus_ten_minute_margin_reserve_usd':each,'all_five_reserve_usd':round(5*each,6),
            'cumulative_reservation_usd':total,'remaining_unallocated_usd':round(1-total,6),
            'timing_model_conservative_occupation_usd':round(expected_occupation,6),'forecast_includes_historical_unknown_holds':True,'forecast_is_not_a_billing_guarantee':True,'invoice_verified':False,'no_sixth_job_or_paid_retry':False,'autonomous_recovery_authorized':True},
        'estimated_data_work_hours':max_hours,
        'estimated_wall_hours_if_timings_hold':round(max_hours+max(len(g['batches']) for g in groups)*115/3600+1.75+.25,2),
        'measured_timeout_basis':{'producer_work_hours':max_hours,'maximum_batches':max(len(g['batches']) for g in groups),
            'additional_verified_commit_slot_wait_seconds_per_batch':115,'finalization_allowance_hours':1.75,
            'startup_allowance_hours':.25,'rounded_up_to_half_hour':True},
        'estimate_is_not_a_completion_guarantee':True,
        'monitor':{'automation_id':'pdebench-25','interval_minutes':30,'status':'ACTIVE','resume_only_after_explicit_start_and_new_id_registration':False,
            'normal_progress_quiet':True,'notify_on':['complete','job failure','429 cooldown or other anomaly','budget threshold','same batch two consecutive checks without progress'],
            'metrics':['verified rows by family/worker','current phase including intentional rate-limit waiting','actual commit POST count over rolling hour','next permitted slot and cooldown reset','worker durations and accumulated cost bounds']},
        'launch_gates':['User already authorized autonomous five-worker recovery inside cumulative USD 1; reconcile and register unique new cohort','Consolidated receipt completed with exact descriptor/blob identity and source coverage',
            'Replace seven-commit publisher/controller with the two-commit atomic protocol; freeze code and dependencies after tests',
            'Integrate tested slot policy at actual commit HTTP send; prove all paths, report writes and final merge obey it',
            'Offline fake-Hub integration: five-way concurrency, 429 reset, lost successful response, crash after prepared/verified, asset conflicts and preservation of earlier cases',
            'Check commit operation/size limits on real-shaped local metadata without a paid Job; split within the same paced policy if needed, recompute cost/ETA if more than two commits per batch',
            'Reconcile five prepared checkpoints without rewriting their bound assets; complete fresh remote consumption before accepting them',
            'No active old jobs; actual Basic price <=167 microUSD/min; atomically reserve all five against the current shared ledger',
            'Update monitor to the new five registered IDs; never reactivate the obsolete five-worker instructions'],
        'formal_selection_changed':False,'numerical_solver_run':False,'new_jobs_submitted':False,
        'validation':{'exact_full_coverage_rows':250000,'source_files':25,'missing_or_duplicate_rows':0},
        'created_at_utc':datetime.now(timezone.utc).isoformat()}
    (OUT/'plan.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['completed_source_rows','remaining_source_rows','remaining_batches','finalizer_worker','budget','commit_policy']},indent=2))
    for g in groups:print(g['worker'],len(g['batches']),g['source_rows'],g['family_rows'],g['estimated_hours'])


if __name__=='__main__':main()
