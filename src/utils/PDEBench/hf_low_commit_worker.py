# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["huggingface_hub==1.33.0", "httpx>=0.28,<1", "numpy>=2,<3", "h5py>=3.13,<4", "gmsh==4.15.2", "jsonschema==4.26.0", "fsspec[http]>=2025.3"]
# ///
"""Bounded two-commit archive workers, with actual HTTP pacing and cloud recovery."""
import argparse
import base64
import copy
from email.utils import parsedate_to_datetime
import gc
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time
import zipfile

RUNTIME_ZIP = ''
ARCHIVE_SOURCE = ''
COORD_SOURCE = ''
PLAN = ''


def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def validate_recovery_plan(plan):
    coverage={file:set(rows) for file,rows in plan['baseline_coverage'].items()}
    if sum(map(len,coverage.values()))!=plan['completed_source_rows']:raise ValueError('Baseline coverage differs')
    if {w['worker'] for w in plan['workers']}!=set(range(1,6)):raise ValueError('Expected five workers')
    for assignment in plan['workers']:
        if sum(x['count'] for x in assignment['batches'])!=assignment['source_rows']:raise ValueError('Assignment total differs')
        for b in assignment['batches']:
            rows=set(range(b['first'],b['first']+b['count']))
            if not 1<=b['count']<=1000 or min(rows)<0 or max(rows)>=10000 or coverage[b['file']]&rows:
                raise ValueError('Invalid/overlapping recovery range')
            coverage[b['file']]|=rows
    if len(coverage)!=25 or any(rows!=set(range(10000)) for rows in coverage.values()):raise ValueError('Incomplete source coverage')


def prove_unpublished_regeneration(old, fresh):
    """An absent, unaccepted bundle may be re-serialized, never rebound in place.

    Byte identities of HDF5 containers need not reproduce across runtimes. Bind
    the exact source and JSON plus every recorded array digest before allowing
    a fresh candidate; the normal full remote consumption still follows.
    """
    if any(old['recipe'][key] != fresh['recipe'][key] for key in
           ('kind', 'family', 'sources', 'first', 'per_file', 'count', 'worker_sha256')):
        raise ValueError('Unpublished regeneration changed pinned source recipe')
    before, after = old['selection'], fresh['selection']
    if (any(before.get(k) != after.get(k) for k in ('task_id', 'repository', 'samples'))
            or set(before['cases']) != set(after['cases'])):
        raise ValueError('Unpublished regeneration changed task or source row names')
    old_records = old['producer_report']['records']
    new_records = fresh['producer_report']['records']
    if len(old_records) != old['recipe']['count'] or len(new_records) != len(old_records):
        raise ValueError('Unpublished regeneration missing source rows')
    def semantic(record):
        required = {'local_id', 'source_file', 'sample_index', 'fields',
            'source_coordinates_sha256', 'mapped_coordinates_sha256', 'valid_times_sha256',
            'input_files', 'unused_trailing_time_coordinates', 'frames', 'reference_recomputed'}
        if not required <= record.keys() or record['reference_recomputed'] is not False:
            raise ValueError('Unpublished regeneration lacks array evidence')
        result = copy.deepcopy(record)
        result.pop('reference_sha256')
        if set(result['input_files']) != {'source.json', 'problem.json', 'input.h5'}:
            raise ValueError('Unexpected unpublished input inventory')
        result['input_files'].pop('input.h5')
        if not result['fields'] or any(not {'source', 'mapped_float64', 'original_dtype', 'shape'} <= x.keys()
                                     for x in result['fields'].values()):
            raise ValueError('Unpublished regeneration lacks field evidence')
        return result
    old_by_name = {r['local_id']: semantic(r) for r in old_records}
    new_by_name = {r['local_id']: semantic(r) for r in new_records}
    if (set(old_by_name) != set(before['cases']) or set(new_by_name) != set(after['cases'])
            or len(old_by_name) != len(old_records) or old_by_name != new_by_name):
        different = next((name for name in sorted(set(old_by_name) | set(new_by_name))
                          if old_by_name.get(name) != new_by_name.get(name)), 'row inventory')
        a, b = old_by_name.get(different, {}), new_by_name.get(different, {})
        changes = {k: {'old': a.get(k), 'fresh': b.get(k)} for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)}
        raise ValueError('Unpublished regeneration changed source arrays, coordinates, times or input JSON: '+
                         json.dumps({'row': different, 'changed_evidence': changes}, sort_keys=True))
    old_raw = {r['local_id']: r for r in old_records}
    new_raw = {r['local_id']: r for r in new_records}
    return {'all_rows': len(old_records), 'pinned_source_recipe_equal': True,
        'source_and_mapped_array_hashes_equal': True, 'input_json_hashes_equal': True,
        'input_container_hash_changes': sum(old_raw[n]['input_files']['input.h5'] != new_raw[n]['input_files']['input.h5'] for n in old_raw),
        'reference_container_hash_changes': sum(old_raw[n]['reference_sha256'] != new_raw[n]['reference_sha256'] for n in old_raw),
        'changed_case_ids': sum(before['cases'][n]['case_id'] != after['cases'][n]['case_id'] for n in old_raw),
        'changed_descriptor_bindings': sum(before['cases'][n]['case'] != after['cases'][n]['case'] for n in old_raw),
        'old_selection_sha256': hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest(),
        'fresh_selection_sha256': hashlib.sha256(json.dumps(after, sort_keys=True).encode()).hexdigest(),
        'old_candidate_was_never_published_or_accepted': True,
        'full_remote_consumption_still_required': True}


class BatchTransaction:
    """Bind prepared publication and verified progress in exactly two commits."""
    def __init__(self,api,pool,publisher,args,state,assignment,item,plan_sha,gate,started):
        self.api=api;self.pool=pool;self.publisher=publisher;self.args=args;self.progress=state
        self.assignment=assignment;self.item=item;self.plan_sha=plan_sha;self.gate=gate;self.started=started
        self.pending=None;self.saved_result=None;self.expected_selection=None;self.expected_checkpoint=None;self.replaces_unpublished=None

    def name(self,checkpoint):return self.args.prefix+'/batches/'+checkpoint['batch_key']+'.json'

    def operations(self,checkpoint,progress):
        from huggingface_hub import CommitOperationAdd
        progress['commit_policy']=self.gate.snapshot()
        return [CommitOperationAdd(path_in_repo=self.name(checkpoint),path_or_fileobj=self.pool.encoded(checkpoint)),
            CommitOperationAdd(path_in_repo=self.args.prefix+'/report.json',path_or_fileobj=self.pool.encoded(progress))]

    def save(self,args,checkpoint):
        if checkpoint['status'] in ('planned','prepared'):
            if checkpoint['status']=='prepared' and self.expected_checkpoint is not None:
                checkpoint['unpublished_regeneration_proof']=prove_unpublished_regeneration(self.expected_checkpoint,checkpoint)
                checkpoint['replaces_unpublished_prepared']=self.replaces_unpublished
            elif checkpoint['status']=='prepared' and self.expected_selection is not None:
                for key in ('task_id','repository','cases','samples'):
                    if checkpoint['selection'].get(key)!=self.expected_selection.get(key):
                        raise ValueError('Regenerated unpublished source changed logical case/descriptor binding')
                checkpoint['replaces_unpublished_prepared']=self.replaces_unpublished
            self.pending=copy.deepcopy(checkpoint)
            return 'local-prepared-not-published'
        if checkpoint['status']!='verified' or self.pending is None:raise ValueError('Unexpected transaction transition')
        if checkpoint['selection']!=self.pending['selection'] or checkpoint['transport_sha256']!=self.pending['transport_sha256']:
            raise ValueError('Immutable prepared binding changed')
        result={'family':self.item['family'],'source_file':self.item['file'],'first':self.item['first'],
            'cases':checkpoint['verified_cases'],'source_files':1,'elapsed_seconds':checkpoint['elapsed_seconds'],
            'pool_revision':checkpoint['pool_revision'],'batch_key':checkpoint['batch_key'],
            'upload_seconds':checkpoint.get('upload_seconds',0.),'remote_consume_seconds':checkpoint.get('remote_consume_seconds',0.),
            'reference_recomputed':False}
        progress={**self.progress,'batches':self.progress['batches']+[result],
            'verified_cases':self.progress['verified_cases']+result['cases'],
            'elapsed_seconds':time.monotonic()-self.started}
        progress.pop('current_batch',None)
        progress['status']='worker_completed' if len(progress['batches'])==len(self.assignment['batches']) else 'running'
        head=self.api.repo_info(args.repo_id,repo_type='dataset',revision=args.revision).sha
        commit=self.api.create_commit(repo_id=args.repo_id,repo_type='dataset',revision=args.revision,parent_commit=head,
            operations=self.operations(checkpoint,progress),commit_message='Verify archive batch and cumulative source coverage')
        self.progress.clear();self.progress.update(progress);self.saved_result=result
        return commit.oid

    def upload(self,directory,*,revision='main',update=False):
        if revision!=self.args.revision or update or self.pending is None or self.pending['status']!='prepared':
            raise ValueError('Unexpected batch publication')
        progress={**self.progress,'status':'prepared','current_batch':self.item,
            'elapsed_seconds':time.monotonic()-self.started}
        receipt=self.publisher(directory,revision=revision,atomic=True,
            extra_operations=self.operations(self.pending,progress))
        return receipt


def recover_prepared(prepared,args,report,runtime,root,transaction,archive):
    """Restore the exact previously bound physical bundle inside HF, without repacking."""
    from huggingface_hub import hf_hub_download
    from caeoj_tools import data_pool as pool
    began=time.monotonic()
    state=pool.checked_json(hf_hub_download(args.repo_id,prepared['state_path'],repo_type='dataset',revision=prepared['branch_revision']))
    if state['status']!='prepared' or state['recipe']['first']!=args.batch_start or state['recipe']['count']!=args.per_file:
        raise ValueError('Prepared source span/binding changed')
    recipe=state['recipe']
    records=state['producer_report']['records']
    expected={(args.source_file,i) for i in range(args.batch_start,args.batch_start+args.per_file)}
    if (state['batch_key']!=prepared['batch_key'] or recipe['family']!=prepared['family']
        or recipe['sources'][0]['file']!=args.source_file or len(records)!=args.per_file
        or {(r['source_file'],r['sample_index']) for r in records}!=expected
        or any(r['reference_recomputed'] for r in records) or len(state['selection']['cases'])!=args.per_file):
        raise ValueError('Prepared checkpoint source provenance differs')
    family=prepared['family'];prefix=archive.BASE+'/'+archive.TASKS[family][1]
    batch=state['transport_sha256'];remote=prefix+'/pool/batches/'+batch
    physical=root/'physical';physical.mkdir(parents=True)
    transport_path=hf_hub_download(args.repo_id,remote+'/transport.json',repo_type='dataset',revision=prepared['branch_revision'])
    if pool.digest(transport_path)!=state['transport_sha256']:raise ValueError('Frozen prepared transport differs')
    catalog=pool.checked_json(transport_path)
    assets=[e[k]['path'] for e in catalog['shards'] for k in ('archive','locator')]+['index.json','selection.json','transport.json']
    for name in assets:
        source=hf_hub_download(args.repo_id,remote+'/'+pool.relative(name),repo_type='dataset',revision=prepared['branch_revision'])
        target=physical/pool.relative(name);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    if pool.manifest(physical/'selection.json')!=state['selection']:raise ValueError('Prepared selection differs')
    state={**state,'recovered_prepared_from':{'revision':prepared['branch_revision'],'path':prepared['state_path']}}
    transaction.save(args,state)
    upload_started=time.monotonic();receipt=transaction.upload(physical,revision=args.revision)
    upload_seconds=time.monotonic()-upload_started
    consume_started=time.monotonic();count=archive.consume(args,state,receipt['revision'],root/'consumed')
    state.update(status='verified',pool_revision=receipt['revision'],verified_cases=count,upload_receipt=receipt,
        last_job_id=os.environ['JOB_ID'],elapsed_seconds=time.monotonic()-began,
        upload_seconds=upload_seconds,remote_consume_seconds=time.monotonic()-consume_started)
    transaction.save(args,state)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--worker',required=True,type=int);args=parser.parse_args()
    if not os.environ.get('JOB_ID') or not all((PLAN,RUNTIME_ZIP,ARCHIVE_SOURCE,COORD_SOURCE)):raise ValueError('Cloud budget launcher required')
    plan_bytes=base64.b64decode(PLAN);plan=json.loads(plan_bytes);plan_sha=hashlib.sha256(plan_bytes).hexdigest();validate_recovery_plan(plan)
    assignment=next(w for w in plan['workers'] if w['worker']==args.worker)
    started=time.monotonic();deadline=started+assignment['hard_timeout_seconds']
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('Bounded cloud worker deadline')))
    signal.alarm(assignment['hard_timeout_seconds']-300)
    os.environ.update(HF_HOME='/tmp/archive-hf',HF_HUB_CACHE='/tmp/archive-hf/hub',HF_XET_CHUNK_CACHE_SIZE_BYTES='0',HF_HUB_DISABLE_PROGRESS_BARS='1')
    runtime=Path('/tmp/archive-runtime');runtime.mkdir()
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(RUNTIME_ZIP))) as archive_zip:
        for entry in archive_zip.infolist():
            if not (runtime/entry.filename).resolve().is_relative_to(runtime.resolve()):raise ValueError('Unsafe runtime path')
        archive_zip.extractall(runtime)
    libraries=json.loads((runtime/'support/gmsh-system-packages.json').read_text())
    subprocess.run(['apt-get','update','-qq'],check=True,timeout=120)
    subprocess.run(['apt-get','install','-y','-qq','--no-install-recommends',*libraries],check=True,timeout=120)
    subprocess.run(['uv','pip','install','--python',sys.executable,'--no-deps',str(runtime)],check=True,timeout=120)
    sys.path.insert(0,str(runtime/'support'))
    archive_source=base64.b64decode(ARCHIVE_SOURCE).decode()
    archive_source=re.sub(r'^RUNTIME_ZIP = .*$',lambda _:'RUNTIME_ZIP = '+repr(RUNTIME_ZIP),archive_source,flags=re.MULTILINE)
    (runtime/'hf_archive_migrate.py').write_text(archive_source)
    (runtime/'hf_parallel_archive.py').write_bytes(base64.b64decode(COORD_SOURCE))
    archive=load_module('archive_worker',runtime/'hf_archive_migrate.py');coordinator=load_module('parallel_coordinator',runtime/'hf_parallel_archive.py')
    coordinator.PREFIX=plan['progress_prefix']
    from huggingface_hub import HfApi,hf_hub_download,CommitOperationAdd
    from huggingface_hub.utils import get_session
    from caeoj_tools import data_pool as pool
    from caeoj_tools.data_pool_shards import publish
    import hf_migrate
    from hf_commit_gateway import CommitGateway
    api=HfApi();actual=api.inspect_job(job_id=os.environ['JOB_ID'])
    price=next(h for h in api.list_jobs_hardware() if h.name=='cpu-basic')
    if actual.flavor!='cpu-basic' or price.unit_label!='minute' or not 0<price.unit_cost_micro_usd<=167:raise ValueError('Hardware/price differs')
    response=get_session().get(f'{api.endpoint}/api/jobs/jimzhouzzy2006/{actual.id}',headers=api._build_hf_headers());response.raise_for_status()
    gate=CommitGateway(args.worker,plan['repository'],parsedate_to_datetime(response.headers['date']).timestamp()+.5,deadline)
    gate.install();api._commit_gateway=gate
    report=pool.checked_json(hf_hub_download(plan['repository'],'migration-trials/pdebench/2026-10-18/source-probe/report.json',repo_type='dataset',revision=plan['source_revision']))
    state={'status':'running','worker':args.worker,'job_id':os.environ['JOB_ID'],'plan_sha256':plan_sha,
        'verified_cases':0,'target_cases':assignment['source_rows'],'batches':[],'formal_selection_changed':False}
    prefix=plan['progress_prefix']+'/w'+str(args.worker)
    def persist():
        state.update(elapsed_seconds=time.monotonic()-started,commit_policy=gate.snapshot())
        head=api.repo_info(plan['repository'],repo_type='dataset',revision=assignment['branch']).sha
        return api.create_commit(repo_id=plan['repository'],repo_type='dataset',revision=assignment['branch'],parent_commit=head,
            operations=[CommitOperationAdd(path_in_repo=prefix+'/report.json',path_or_fileobj=pool.encoded(state))],
            commit_message='Record worker terminal or finalization state').oid
    try:
        for item in assignment['batches']:
            if time.monotonic()+1800>deadline-900:raise TimeoutError('Not enough runtime for another source span')
            if shutil.disk_usage('/tmp').free<20*1024**3:raise RuntimeError('Insufficient scratch headroom')
            worker_args=argparse.Namespace(repo_id=plan['repository'],revision=assignment['branch'],prefix=prefix,
                source_file=item['file'],batch_start=item['first'],per_file=item['count'])
            root=Path('/tmp/archive-production-batch');root.mkdir()
            transaction=BatchTransaction(api,pool,publish,worker_args,state,assignment,item,plan_sha,gate,started)
            original_save=hf_migrate.save;original_upload=pool.upload
            hf_migrate.save=transaction.save;pool.upload=transaction.upload
            try:
                prepared=next((p for p in plan['quarantined_prepared_batches'] if (p['file'],p['first'],p['count'])==(item['file'],item['first'],item['count'])),None)
                if prepared and prepared.get('recovery_mode')=='regenerate_unpublished':
                    old=pool.checked_json(hf_hub_download(plan['repository'],prepared['state_path'],repo_type='dataset',revision=prepared['branch_revision']))
                    transaction.expected_checkpoint=old
                    transaction.replaces_unpublished={'revision':prepared['branch_revision'],'checkpoint':prepared['state_path'],
                        'reason':'Frozen batch folder and all case bindings were proven absent; retain old candidate and prove exact source/JSON/array identity before fresh publication'}
                    archive.run_family(worker_args,report,runtime,item['family'],root)
                elif prepared:recover_prepared(prepared,worker_args,report,runtime,root,transaction,archive)
                else:archive.run_family(worker_args,report,runtime,item['family'],root)
            finally:hf_migrate.save=original_save;pool.upload=original_upload
            if transaction.saved_result is None:raise ValueError('Batch ended without a durable verified transaction')
            print(json.dumps({'phase':'batch_verified','worker':args.worker,'verified_cases':state['verified_cases'],
                'source_file':item['file'],'first':item['first'],'count':item['count']}),flush=True)
            shutil.rmtree(root);gc.collect()
            for cache in ('/tmp/archive-hf','/tmp/caeoj-shards','/tmp/caeoj-index-reads'):shutil.rmtree(cache,ignore_errors=True)
        coordinator.check_worker(state,assignment,plan_sha)
        if args.worker==plan['finalizer_worker']:
            state['final']=coordinator.finalize(api,pool,archive,plan,plan_sha,state,persist,deadline)
            state['status']='completed';persist()
        signal.alarm(0)
    except Exception as exc:
        print(json.dumps({'phase':'worker_error','worker':args.worker,'error':str(exc)[-2000:]}),flush=True)
        # Do not spend an hour trying to report a failure through the same quota.
        # The API terminal state and last durable batch/checkpoint remain authoritative.
        raise


if __name__=='__main__':main()
