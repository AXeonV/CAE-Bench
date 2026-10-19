"""Freeze stopped branches and audit verified metadata; never read numerical assets."""
import hashlib
import argparse
import importlib.util
import json
import os
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'qbank/design/reviews/pdebench-low-commit-20261019'
BASE='qbank/01-prescribed-pdes/pdebench-archive'
TASKS={'advection':'pdebench-advection-1d','burgers':'pdebench-burgers-1d','compressible':'pdebench-compressible-1d'}


def read_module(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def main():
    global OUT
    parser=argparse.ArgumentParser();parser.add_argument('--cohort-plan',type=Path);parser.add_argument('--out',type=Path)
    args=parser.parse_args()
    if args.out:OUT=args.out.resolve()
    from huggingface_hub import HfApi,hf_hub_download
    from huggingface_hub.utils import get_session
    from caeoj_tools import data_pool as pool
    from caeoj_tools.data_pool_shards import PartitionStore
    api=HfApi();repo='jimzhouzzy2006/CAE-Bench-OJ'
    prior=json.loads((args.cohort_plan or ROOT/'qbank/design/reviews/pdebench-parallel-20261019/plan.json').read_text())
    ledger_path=ROOT/'runs/pdebench-cloud-trial/budget.json'
    lock=ledger_path.with_suffix('.lock');fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(fd)
    try:
        ledger=json.loads(ledger_path.read_text());helper=read_module('hf_trial_launch');helper.settle_completed(api,ledger)
        evidence=[]
        for a in ledger['attempts']:
            if args.cohort_plan:
                if a.get('phase')!='archive-low-commit' or a.get('cohort')!=prior['cohort']:continue
            elif a.get('phase')!='archive-parallel':continue
            if not a.get('job_id'):raise ValueError('Unknown or reserved submission must be reconciled first')
            response=get_session().get(f'{api.endpoint}/api/jobs/jimzhouzzy2006/{a["job_id"]}',headers=api._build_hf_headers());response.raise_for_status();raw=response.json()
            if raw['status']['stage'] not in ('COMPLETED','ERROR','CANCELED','CANCELLED'):raise ValueError('Writer still active')
            e={'job_id':a['job_id'],'worker':a['worker'],'status':raw['status']['stage'],'server_date':response.headers['date']}
            if 'api_lifecycle_cost_upper_bound_usd' not in a:
                bound=read_module('hf_parallel_launch').terminal_observation_bound(raw,response.headers['date'],a['hardware_unit_cost_micro_usd'])
                a.update(status=raw['status']['stage'].lower(),api_lifecycle_cost_upper_bound_usd=bound,
                    terminal_observation={'server_date':response.headers['date'],'api_created_at':raw['createdAt'],'stage':raw['status']['stage'],'method':'authenticated terminal response upper bound; not invoice'})
            e['lifecycle_upper_usd']=a['api_lifecycle_cost_upper_bound_usd'];evidence.append(e)
        tmp=ledger_path.with_suffix('.audit.tmp');tmp.write_text(json.dumps(ledger,indent=2)+'\n');tmp.replace(ledger_path)
    finally:lock.unlink(missing_ok=True)
    cache=(ROOT/'runs/pdebench-cloud-trial/partial-audit'/prior['cohort']) if args.cohort_plan else ROOT/'runs/pdebench-cloud-trial/partial-audit';cache.mkdir(parents=True,exist_ok=True)
    frozen=pool.checked_json(hf_hub_download(repo,'migration-trials/pdebench/2026-10-18/full-archive/full-report.json',repo_type='dataset',revision=prior['frozen_base_revision']))
    coverage=({file:set(rows) for file,rows in prior['baseline_coverage'].items()} if args.cohort_plan
        else {x['file']:set(range(16)) for x in frozen['recipe']['plan']})
    for b in frozen['batches']:coverage[b['source_file']].update(range(b['first'],b['first']+b['cases']))
    branches=[];quarantine=[];counts=dict(prior['family_completed']) if args.cohort_plan else {'advection':7016,'burgers':7080,'compressible':5000}
    for w in prior['workers']:
        head=api.repo_info(repo,repo_type='dataset',revision=w['branch']).sha
        prefix=(prior['progress_prefix']+'/w'+str(w['worker'])) if args.cohort_plan else f'migration-trials/pdebench/2026-10-19/parallel/w{w["worker"]}'
        exists=api.get_paths_info(repo,[prefix+'/batches'],repo_type='dataset',revision=head)
        paths=[f.path for f in api.list_repo_tree(repo,path_in_repo=prefix+'/batches',repo_type='dataset',revision=head)] if exists else []
        verified=[];selections={f:{} for f in TASKS}
        for name in paths:
            state=pool.checked_json(hf_hub_download(repo,name,repo_type='dataset',revision=head))
            recipe=state['recipe'];source=recipe['sources'][0]
            item={'worker':w['worker'],'branch_revision':head,'state_path':name,'batch_key':state['batch_key'],
                'status':state['status'],'family':recipe['family'],'file':source['file'],'first':recipe['first'],'count':recipe['count']}
            if state['status']!='verified':quarantine.append(item);continue
            records=state['producer_report']['records'];choice=state['selection'];n=state['verified_cases']
            expected={(item['file'],i) for i in range(item['first'],item['first']+item['count'])}
            actual={(r['source_file'],r['sample_index']) for r in records}
            if (len(records)!=n or len(choice['cases'])!=n or n!=item['count'] or actual!=expected
                    or any(r['reference_recomputed'] for r in records) or not state.get('upload_receipt')):
                raise ValueError('Verified checkpoint incomplete')
            for file,row in actual:
                if row in coverage[file]:raise ValueError('Repeated source trajectory')
                coverage[file].add(row)
            for binding in choice['cases'].values():
                cid=binding['case_id']
                if cid in selections[item['family']]:raise ValueError('Repeated case ID')
                selections[item['family']][cid]=binding['case']
            item.update(pool_revision=state['pool_revision'],verified_cases=n)
            verified.append(item);counts[item['family']]+=n
        refs={}
        for family,task in TASKS.items():
            if not selections[family]:continue
            prefix_task=BASE+'/'+task
            view=PartitionStore(pool.HubStore(repo,head),prefix_task,cache/('w'+str(w['worker']))/family)
            entries={}
            for cid,binding in selections[family].items():
                entry=view.lookup(cid)
                if entry is None or entry['sha256']!=binding['sha256'] or entry['path']!=binding['path']:
                    raise ValueError('Verified case missing from frozen branch root')
                if hashlib.sha256(pool.encoded(entry['descriptor'])).hexdigest()!=binding['sha256']:
                    raise ValueError('Embedded descriptor differs')
                entries[cid]=entry
            dest=cache/f'w{w["worker"]}-{family}.json';pool.write_json(dest,entries)
            refs[family]={'local_entries':str(dest),'case_count':len(entries),'sha256':pool.digest(dest)}
        branches.append({'worker':w['worker'],'branch':w['branch'],'revision':head,'verified_batches':verified,'entries':refs})
    if args.cohort_plan:
        existing={(x['file'],x['first'],x['count']) for x in quarantine}
        for old in prior.get('quarantined_prepared_batches',[]):
            identity=(old['file'],old['first'],old['count'])
            rows=set(range(old['first'],old['first']+old['count']))
            if rows<=coverage[old['file']] or identity in existing:continue
            quarantine.append(dict(old));existing.add(identity)
    # All source ranges are frozen, but prepared batches remain explicitly unaccepted.
    result={'status':'audited_stopped','repository':repo,'base_revision':prior['frozen_base_revision'],
        'source_revision':prior['source_revision'],'progress_prefix':prior.get('progress_prefix','migration-trials/pdebench/2026-10-19/parallel'),'old_jobs':evidence,'family_verified_cases':counts,
        'verified_cases':sum(counts.values()),'verified_new_batches':sum(len(b['verified_batches']) for b in branches),
        'branches':branches,'quarantine':quarantine,'coverage':{f:sorted(v) for f,v in coverage.items()},
        'cumulative_budget_occupation_usd':round(sum(helper.effective_reservation(a) for a in ledger['attempts']),6),
        'known_terminal_lifecycle_upper_usd':round(sum(a.get('api_lifecycle_cost_upper_bound_usd',0) for a in ledger['attempts']),6),
        'invoice_verified':False,'numerical_payload_downloaded':False,'observed_at_utc':datetime.now(timezone.utc).isoformat()}
    OUT.mkdir(exist_ok=True,parents=True);pool.write_json(OUT/'audit.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['branches','coverage']},indent=2))


if __name__=='__main__':main()
