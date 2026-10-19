"""Consolidate audited verified cases using server copies and pool index metadata.

No numerical payload is downloaded; the source branches remain untouched.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'qbank/design/reviews/pdebench-low-commit-20261019'
BASE='qbank/01-prescribed-pdes/pdebench-archive'
TASKS={'advection':'pdebench-advection-1d','burgers':'pdebench-burgers-1d','compressible':'pdebench-compressible-1d'}
DEST='pdebench-consolidated-20261019'


def validated_union(current,incoming):
    result=dict(current)
    for cid,entry in incoming.items():
        if cid in result and result[cid]!=entry:raise ValueError('Conflicting existing descriptor/transport '+cid)
        result[cid]=entry
    return result


def main():
    global OUT,DEST
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');parser.add_argument('--out',type=Path);parser.add_argument('--destination')
    args=parser.parse_args()
    if args.out:OUT=args.out.resolve()
    if args.destination:DEST=args.destination
    from huggingface_hub import HfApi,CommitOperationAdd,CommitOperationCopy
    from caeoj_tools import data_pool as pool
    from caeoj_tools.data_pool_shards import PartitionStore,stage_plan,bucket
    audit=json.loads((OUT/'audit.json').read_text());api=HfApi();repo=audit['repository'];base=audit['base_revision']
    for record in audit['old_jobs']:
        if api.inspect_job(job_id=record['job_id']).status.stage not in ('COMPLETED','ERROR','CANCELED','CANCELLED'):
            raise ValueError('Writer not stopped')
    cache=ROOT/'runs/pdebench-cloud-trial/partial-audit';index_ops=[];root_ops=[];copies=[];copy_sources={}
    dest_tree={x.path:x for x in api.list_repo_tree(repo,path_in_repo=BASE,recursive=True,repo_type='dataset',revision=base) if hasattr(x,'blob_id')}
    total=0
    for family,task in TASKS.items():
        prefix=BASE+'/'+task;view=PartitionStore(pool.HubStore(repo,base),prefix,cache/('base-'+family))
        partitions={k:dict(view.partition(k)) for k in view.index['partitions']};wanted={}
        for branch in audit['branches']:
            spec=branch['entries'].get(family)
            if not spec:continue
            path=Path(spec['local_entries'])
            if pool.digest(path)!=spec['sha256']:raise ValueError('Audited metadata changed')
            entries=pool.checked_json(path)
            groups={}
            for cid,entry in entries.items():
                groups.setdefault(json.dumps(entry['transport'],sort_keys=True),{})[cid]=entry
                transport=entry['transport']['path'];wanted.setdefault(branch['revision'],set()).add(prefix+'/'+transport.rsplit('/',1)[0])
            for group in groups.values():
                # Check full binding equality before reusing the standard merge planner.
                for cid,entry in group.items():validated_union({cid:partitions.get(bucket(cid),{}).get(cid)} if cid in partitions.get(bucket(cid),{}) else {},{cid:entry})
                staged,_=stage_plan(view.index,group,next(iter(group.values()))['transport'],lambda k:partitions.get(k,{}))
                partitions.update(staged)
        merged={**view.index,'partitions':{},'case_count':sum(len(x) for x in partitions.values())}
        if merged['case_count']!=audit['family_verified_cases'][family]:raise ValueError('Merged count differs')
        total+=merged['case_count']
        for key,entries in sorted(partitions.items()):
            data=pool.encoded({'schema_version':1,'cases':entries});sha=hashlib.sha256(data).hexdigest()
            binding={'path':f'pool/partitions/{key}/{sha}.json','sha256':sha,'size_bytes':len(data),'case_count':len(entries)}
            merged['partitions'][key]=binding
            if binding!=view.index['partitions'].get(key):index_ops.append(CommitOperationAdd(path_in_repo=prefix+'/'+binding['path'],path_or_fileobj=data))
        if merged!=view.index:root_ops.append(CommitOperationAdd(path_in_repo=prefix+'/pool/index.json',path_or_fileobj=pool.encoded(merged)))
        for rev,batches in wanted.items():
            for batch in sorted(batches):
                for file in api.list_repo_tree(repo,path_in_repo=batch,recursive=True,repo_type='dataset',revision=rev):
                    if not hasattr(file,'blob_id'):continue
                    if file.path in copy_sources:
                        if copy_sources[file.path]['blob_id']!=file.blob_id:raise ValueError('Source assets conflict')
                        continue
                    if file.path in dest_tree:
                        if dest_tree[file.path].blob_id!=file.blob_id:raise ValueError('Existing immutable asset conflict')
                        continue
                    if '.tar' in Path(file.path).name and not file.lfs:raise ValueError('Refuse local download of numerical TAR')
                    copy_sources[file.path]={'revision':rev,'blob_id':file.blob_id,'size':file.size,'lfs':bool(file.lfs)}
                    copies.append(CommitOperationCopy(src_path_in_repo=file.path,path_in_repo=file.path,src_revision=rev))
    if total!=audit['verified_cases']:raise ValueError('Total differs')
    summary={'destination_branch':DEST,'base_revision':base,'verified_cases':total,'family_verified_cases':audit['family_verified_cases'],
        'immutable_asset_copies':len(copies),'partition_writes':len(index_ops),'root_writes':len(root_ops),
        'expected_commits':(len(copies)+63)//64+(len(index_ops)+31)//32+1,
        'commit_interval_seconds':45,'numerical_payload_downloaded':False,'only_verified_checkpoints_accepted':True}
    pool.write_json(OUT/'merge-plan.json',summary);print(json.dumps(summary),flush=True)
    if not args.apply:return
    api.create_branch(repo,repo_type='dataset',branch=DEST,revision=base,exist_ok=True)
    head=api.repo_info(repo,repo_type='dataset',revision=DEST).sha
    receipt_path=OUT/'merge-receipt.json'
    receipt=json.loads(receipt_path.read_text()) if receipt_path.exists() else {**summary,'commits':[],'status':'staging'}
    if head!=base and not any(c['revision']==head for c in receipt['commits']):
        raise RuntimeError('Unknown destination change; inspect before resuming')
    completed={c['label'] for c in receipt['commits']}
    last=time.monotonic()
    def commit(label,operations):
        nonlocal head,last
        if label in completed:return
        while time.monotonic()-last<45:time.sleep(min(5,45-(time.monotonic()-last)))
        try:
            result=api.create_commit(repo_id=repo,repo_type='dataset',revision=DEST,parent_commit=head,
                operations=operations,commit_message=label)
        except Exception as exc:
            receipt.update(status='stopped_for_inspection',error=str(exc)[-2500:])
            pool.write_json(receipt_path,receipt)
            raise
        last=time.monotonic();head=result.oid
        receipt['commits'].append({'label':label,'revision':head,'observed_utc':datetime.now(timezone.utc).isoformat()})
        pool.write_json(receipt_path,receipt);print(json.dumps({'committed':label,'revision':head}),flush=True)
    for i in range(0,len(copies),64):commit('Stage verified prior batch assets '+str(i//64),copies[i:i+64])
    for i in range(0,len(index_ops),32):commit('Stage consolidated verified partitions '+str(i//32),index_ops[i:i+32])
    # Independently compare every copied asset at the accepted staging revision.
    for i in range(0,len(copy_sources),100):
        names=list(copy_sources)[i:i+100];files={f.path:f for f in api.get_paths_info(repo,names,repo_type='dataset',revision=head)}
        if any(n not in files or files[n].blob_id!=copy_sources[n]['blob_id'] or files[n].size!=copy_sources[n]['size'] for n in names):
            raise ValueError('Server-side copies differ from source bindings')
    report={**summary,'status':'consolidated_verified_checkpoints','source_branch_revisions':[{'worker':b['worker'],'revision':b['revision']} for b in audit['branches']],
        'quarantined_batches':audit['quarantine'],'validation_scope':'Prior full batch consumption receipts plus metadata/descriptor and copied-blob identity checks; no fresh numerical consumption',
        'invoice_verified':False,'formal_selection_changed':False}
    report_name='migration-trials/pdebench/2026-10-19/consolidated/report.json'
    commit('Atomically publish consolidated verified pools',root_ops+[CommitOperationAdd(path_in_repo=report_name,path_or_fileobj=pool.encoded(report))])
    backing=pool.HubStore(repo,head)
    for family,task in TASKS.items():
        view=PartitionStore(backing,BASE+'/'+task,cache/('final-'+family))
        if view.index['case_count']!=audit['family_verified_cases'][family]:raise ValueError('Published count differs')
        count=0
        for key in view.index['partitions']:
            for cid,entry in view.partition(key).items():
                if hashlib.sha256(pool.encoded(entry['descriptor'])).hexdigest()!=entry['sha256'] or entry['descriptor']['case_id']!=cid:
                    raise ValueError('Published descriptor invalid')
                count+=1
        if count!=audit['family_verified_cases'][family]:raise ValueError('Final membership count differs')
    receipt.update(status='completed',final_revision=head,report_path=report_name,verified_cases=total,
        validation_scope=report['validation_scope']);pool.write_json(receipt_path,receipt)
    print(json.dumps(receipt),flush=True)


if __name__=='__main__':main()
