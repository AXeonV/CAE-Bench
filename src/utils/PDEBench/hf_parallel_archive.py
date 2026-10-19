# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["huggingface_hub>=1.0,<2", "numpy>=2,<3", "h5py>=3.13,<4", "gmsh==4.15.2", "jsonschema==4.26.0", "fsspec[http]>=2025.3"]
# ///
"""Five disjoint HF archive workers and a single immutable-index finalizer."""
import argparse
import base64
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
PLAN = ''
PREFIX = 'migration-trials/pdebench/2026-10-19/parallel'


def span(item):
    return item['file'], item['first'], item['count']


def validate_plan(plan, frozen):
    completed = {(b['source_file'], b['first'], b['cases']) for b in frozen['batches']}
    original = {span(x) for x in frozen['recipe']['plan']}
    assigned = [span(x) for w in plan['workers'] for x in w['batches']]
    if (len(completed) != len(frozen['batches']) or len(set(assigned)) != len(assigned)
            or completed & set(assigned) or completed | set(assigned) != original
            or len(plan['workers']) != 5 or {w['worker'] for w in plan['workers']} != set(range(1, 6))):
        raise ValueError('Overlapping, missing or changed source assignments')
    if sum(x[2] for x in assigned) + frozen['verified_cases'] != 250000:
        raise ValueError('Source total differs')
    for worker in plan['workers']:
        if sum(x['count'] for x in worker['batches']) != worker['source_rows']:
            raise ValueError('Worker row total differs')


def check_worker(report, assignment, plan_sha):
    if report.get('plan_sha256') != plan_sha or report.get('worker') != assignment['worker']:
        raise ValueError('Worker report plan binding differs')
    done = [(x['source_file'], x['first'], x['cases']) for x in report.get('batches', [])]
    if len(done) != len(set(done)) or set(done) != {span(x) for x in assignment['batches']}:
        raise ValueError('Worker source coverage differs')
    if report.get('verified_cases') != assignment['source_rows']:
        raise ValueError('Worker verified count differs')


def report_path(number):
    return f'{PREFIX}/w{number}/report.json'


def union_entries(current, incoming):
    """Preserve exact prior transport and descriptor bindings on overlaps."""
    result = dict(current)
    for cid, binding in incoming.items():
        if cid in result and result[cid] != binding:
            raise ValueError('Conflicting immutable case binding: '+cid)
        result[cid] = binding
    return result


def finalize(api, pool, archive, plan, plan_sha, own_report, persist, deadline):
    from huggingface_hub import CommitOperationAdd, CommitOperationCopy, hf_hub_download
    from caeoj_tools.data_pool_shards import PartitionStore, stage_plan
    repo = plan['repository']
    reports = []
    wait_until = min(deadline-900, time.monotonic()+7200)
    while True:
        reports = []
        pending = []
        for assignment in plan['workers']:
            rev = api.repo_info(repo, repo_type='dataset', revision=assignment['branch']).sha
            name = report_path(assignment['worker'])
            found = api.get_paths_info(repo, [name], repo_type='dataset', revision=rev)
            if not found:
                pending.append(assignment['worker']); continue
            report = pool.checked_json(hf_hub_download(repo, name, repo_type='dataset', revision=rev))
            if report.get('status') in ('error', 'stopped_at_time_budget'):
                raise RuntimeError('Peer worker stopped: '+str(assignment['worker']))
            if report.get('status') not in ('worker_completed', 'merging', 'completed'):
                pending.append(assignment['worker']); continue
            check_worker(report, assignment, plan_sha)
            reports.append((assignment, rev, report))
        if not pending:
            break
        if time.monotonic() >= wait_until:
            raise TimeoutError('Finalizer barrier deadline; pending workers '+str(pending))
        time.sleep(30)
    gateway = getattr(api, '_commit_gateway', None)
    if gateway:
        while True:
            stages=[api.inspect_job(job_id=r['job_id']).status.stage for a,v,r in reports
                    if a['worker']!=plan['finalizer_worker']]
            if all(stage=='COMPLETED' for stage in stages):break
            if any(stage in ('ERROR','CANCELED','CANCELLED') for stage in stages):
                raise RuntimeError('Peer failed before exclusive finalizer handoff')
            if time.monotonic()>deadline-1800:raise TimeoutError('Finalizer peer shutdown deadline')
            time.sleep(10)
        gateway.exclusive=True
    own_report['status'] = 'merging'; persist()
    dest = plan['final_branch']
    base = plan['frozen_base_revision']
    # Launcher creates the result branch once, before paid jobs start.
    head = api.repo_info(repo, repo_type='dataset', revision=dest).sha
    if head != base:
        raise RuntimeError('Final destination changed; inspect instead of overwriting')
    roots = {}
    metadata_operations = []
    frozen = pool.checked_json(hf_hub_download(repo,
        'migration-trials/pdebench/2026-10-18/full-archive/full-report.json', repo_type='dataset', revision=base))
    row_coverage = ({file:set(rows) for file,rows in plan['baseline_coverage'].items()}
        if 'baseline_coverage' in plan else {item['file']:set(range(16)) for item in frozen['recipe']['plan']})
    for b in frozen['batches']:
        row_coverage[b['source_file']].update(range(b['first'], b['first']+b['cases']))
    # Check every producer record, not merely report totals.
    for assignment, rev, report in reports:
        for batch in report['batches']:
            state_path = f"{PREFIX}/w{assignment['worker']}/batches/{batch['batch_key']}.json"
            state = pool.checked_json(hf_hub_download(repo, state_path, repo_type='dataset', revision=rev))
            records = state.get('producer_report', {}).get('records', [])
            if (state.get('status') != 'verified' or state.get('verified_cases') != batch['cases']
                    or len(records) != batch['cases'] or state.get('pool_revision') != batch['pool_revision']):
                raise ValueError('Unverified batch checkpoint')
            actual = set()
            for record in records:
                identity = record['source_file'], record['sample_index']
                if identity in actual or record['reference_recomputed']:
                    raise ValueError('Repeated/recomputed source record')
                actual.add(identity)
            expected = {(batch['source_file'], i) for i in range(batch['first'], batch['first']+batch['cases'])}
            if actual != expected or len(state['selection']['cases']) != len(actual):
                raise ValueError('Producer coverage differs from assigned span')
            rows = row_coverage[batch['source_file']]
            for _, i in actual:
                if i in rows: raise ValueError('Source row appears in multiple workers')
                rows.add(i)
    if len(row_coverage) != 25 or any(rows != set(range(10000)) for rows in row_coverage.values()):
        raise ValueError('Final source coverage incomplete')
    for family, (_, task) in archive.TASKS.items():
        prefix = archive.BASE+'/'+task
        backing = pool.HubStore(repo, base)
        view = PartitionStore(backing, prefix, Path('/tmp/merge-base')/family)
        partitions = {key: dict(view.partition(key)) for key in view.index['partitions']}
        # Only immutable batch assets are copied. Mutable root indexes are unioned.
        existing = {x.path: x for x in api.list_repo_tree(repo, path_in_repo=prefix+'/pool/batches',
            recursive=True, repo_type='dataset', revision=head) if hasattr(x, 'blob_id')}
        for assignment, rev, report in reports:
            src_view = PartitionStore(pool.HubStore(repo, rev), prefix,
                Path('/tmp/merge-source')/str(assignment['worker'])/family)
            for key in src_view.index['partitions']:
                incoming = src_view.partition(key)
                # Existing publisher merge planner enforces canonical case identity.
                groups = {}
                for cid, entry in incoming.items():
                    transport_key = json.dumps(entry['transport'], sort_keys=True)
                    groups.setdefault(transport_key, {})[cid] = entry
                for entries in groups.values():
                    transport = next(iter(entries.values()))['transport']
                    current = partitions.get(key, {})
                    # Reject even silent transport redirection on duplicates.
                    union_entries(current, entries)
                    staged, _ = stage_plan(view.index, entries, transport, lambda k: partitions.get(k, {}))
                    partitions.update(staged)
            src_view = None
            operations = []
            source_files = [x for x in api.list_repo_tree(repo, path_in_repo=prefix+'/pool/batches',
                recursive=True, repo_type='dataset', revision=rev) if hasattr(x, 'blob_id')]
            for file in source_files:
                old = existing.get(file.path)
                if old:
                    if old.blob_id != file.blob_id or old.size != file.size:
                        raise ValueError('Immutable destination asset differs')
                    continue
                operations.append(CommitOperationCopy(src_path_in_repo=file.path,
                    path_in_repo=file.path, src_revision=rev))
                existing[file.path] = file
            for start in range(0, len(operations), 40):
                head = api.create_commit(repo_id=repo, repo_type='dataset', revision=dest, parent_commit=head,
                    operations=operations[start:start+40], commit_message='Stage verified parallel archive assets').oid
            # Prove server copies preserve blob identity before any root publication.
            copied = operations
            for start in range(0, len(copied), 100):
                names = [op.path_in_repo for op in copied[start:start+100]]
                observed = {f.path:f for f in api.get_paths_info(repo, names, repo_type='dataset', revision=head)}
                if any(n not in observed or observed[n].blob_id != existing[n].blob_id
                       or observed[n].size != existing[n].size for n in names):
                    raise ValueError('Copied asset identity mismatch')
        merged = {**view.index, 'partitions':{}, 'case_count':sum(len(x) for x in partitions.values())}
        target = {'advection':80000, 'burgers':120000, 'compressible':50000}[family]
        if merged['case_count'] != target: raise ValueError('Final pool count differs')
        for key, entries in sorted(partitions.items()):
            for cid, binding in entries.items():
                if hashlib.sha256(pool.encoded(binding['descriptor'])).hexdigest() != binding['sha256']:
                    raise ValueError('Embedded descriptor identity mismatch')
                if binding['descriptor']['case_id'] != cid:
                    raise ValueError('Descriptor case ID mismatch')
            data = pool.encoded({'schema_version':1, 'cases':entries})
            digest = hashlib.sha256(data).hexdigest()
            binding = {'path':f'pool/partitions/{key}/{digest}.json', 'sha256':digest,
                'size_bytes':len(data), 'case_count':len(entries)}
            merged['partitions'][key] = binding
            metadata_operations.append(CommitOperationAdd(path_in_repo=prefix+'/'+binding['path'], path_or_fileobj=data))
        roots[prefix+'/pool/index.json'] = pool.encoded(merged)
        del partitions, view
        gc.collect()
    for start in range(0, len(metadata_operations), 8):
        head = api.create_commit(repo_id=repo, repo_type='dataset', revision=dest, parent_commit=head,
            operations=metadata_operations[start:start+8], commit_message='Stage unioned archive partitions').oid
    head = api.create_commit(repo_id=repo, repo_type='dataset', revision=dest, parent_commit=head,
        operations=[CommitOperationAdd(path_in_repo=n,path_or_fileobj=data) for n,data in roots.items()],
        commit_message='Atomically publish all three complete PDEBench pools').oid
    # Actual consumer check at the final revision: one real new case per family.
    checks = []
    for family in archive.TASKS:
        assignment, rev, report = next((a,v,r) for a,v,r in reports if any(b['family']==family for b in r['batches']))
        batch = next(b for b in report['batches'] if b['family']==family)
        state = pool.checked_json(hf_hub_download(repo,
            f"{PREFIX}/w{assignment['worker']}/batches/{batch['batch_key']}.json", repo_type='dataset', revision=rev))
        choice = dict(state['selection']); local_id = next(iter(choice['cases']))
        first = choice['cases'][local_id]
        choice.update(cases={local_id:first}, samples={})
        record = next(r for r in state['producer_report']['records'] if r['local_id']==local_id)
        check_root = Path('/tmp/final-consume')/family
        check_root.mkdir(parents=True)
        count = archive.consume(argparse.Namespace(repo_id=repo), {'selection':choice,'producer_report':{'records':[record]}}, head, check_root)
        checks.append({'family':family,'cases':count})
        shutil.rmtree(check_root)
    final = {'status':'completed', 'plan_sha256':plan_sha, 'verified_cases':250000,
        'source_files':25, 'coverage_per_file':{k:len(v) for k,v in row_coverage.items()},
        'pool_counts':{'advection':80000,'burgers':120000,'compressible':50000},
        'pool_revision':head, 'workers':[{'worker':a['worker'],'revision':v,'job_id':r['job_id']} for a,v,r in reports],
        'final_consumer_checks':checks, 'reference_recomputed':False, 'formal_selection_changed':False}
    final_name = PREFIX+'/final-report.json'
    commit = api.create_commit(repo_id=repo, repo_type='dataset', revision=dest, parent_commit=head,
        operations=[CommitOperationAdd(path_in_repo=final_name,path_or_fileobj=pool.encoded(final))],
        commit_message='Verify complete 250000-row parallel migration').oid
    return {'report_revision':commit, 'pool_revision':head, 'report_path':final_name}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--worker', type=int, required=True)
    args = parser.parse_args()
    if not os.environ.get('JOB_ID') or not all((RUNTIME_ZIP, ARCHIVE_SOURCE, PLAN)):
        raise ValueError('Cloud budget launcher required')
    plan_bytes = base64.b64decode(PLAN); plan = json.loads(plan_bytes)
    plan_sha = hashlib.sha256(plan_bytes).hexdigest()
    assignment = next(w for w in plan['workers'] if w['worker']==args.worker)
    started = time.monotonic(); deadline = started+assignment['hard_timeout_seconds']
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('Worker deadline')))
    signal.alarm(assignment['hard_timeout_seconds']-300)
    os.environ.update(HF_HOME='/tmp/archive-hf', HF_HUB_CACHE='/tmp/archive-hf/hub',
        HF_XET_CHUNK_CACHE_SIZE_BYTES='0', HF_HUB_DISABLE_PROGRESS_BARS='1')
    runtime = Path('/tmp/archive-runtime'); runtime.mkdir()
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(RUNTIME_ZIP))) as archive_zip:
        for entry in archive_zip.infolist():
            if not (runtime/entry.filename).resolve().is_relative_to(runtime.resolve()): raise ValueError('Unsafe runtime')
        archive_zip.extractall(runtime)
    packages = json.loads((runtime/'support/gmsh-system-packages.json').read_text())
    subprocess.run(['apt-get','update','-qq'],check=True,timeout=120)
    subprocess.run(['apt-get','install','-y','-qq','--no-install-recommends',*packages],check=True,timeout=120)
    subprocess.run(['uv','pip','install','--python',sys.executable,'--no-deps',str(runtime)],check=True,timeout=120)
    sys.path.insert(0,str(runtime/'support'))
    source = base64.b64decode(ARCHIVE_SOURCE).decode()
    source = re.sub(r'^RUNTIME_ZIP = .*$', lambda _: 'RUNTIME_ZIP = '+repr(RUNTIME_ZIP),source,flags=re.MULTILINE)
    code_path = runtime/'hf_archive_migrate.py'; code_path.write_text(source)
    spec=importlib.util.spec_from_file_location('archive_worker',code_path)
    archive=importlib.util.module_from_spec(spec);spec.loader.exec_module(archive)
    from huggingface_hub import HfApi, CommitOperationAdd, hf_hub_download
    from caeoj_tools import data_pool as pool
    from hf_migrate import runtime_identity
    if runtime_identity(RUNTIME_ZIP) != plan['frozen_runtime_contents_sha256']:
        raise ValueError('Runtime changed since original migration')
    api=HfApi(); actual=api.inspect_job(job_id=os.environ['JOB_ID'])
    hardware=next(h for h in api.list_jobs_hardware() if h.name=='cpu-basic')
    if actual.flavor!='cpu-basic' or hardware.unit_label!='minute' or not 0<hardware.unit_cost_micro_usd<=167:
        raise ValueError('Unexpected CPU hardware/price')
    repo=plan['repository']; branch=assignment['branch']
    frozen=pool.checked_json(hf_hub_download(repo,'migration-trials/pdebench/2026-10-18/full-archive/full-report.json',repo_type='dataset',revision=plan['frozen_base_revision']))
    validate_plan(plan,frozen)
    report=pool.checked_json(hf_hub_download(repo,'migration-trials/pdebench/2026-10-18/source-probe/report.json',repo_type='dataset',revision=plan['source_revision']))
    state={'status':'running','worker':args.worker,'job_id':os.environ['JOB_ID'],'plan_sha256':plan_sha,
        'batches':[],'verified_cases':0,'target_cases':assignment['source_rows'],'formal_selection_changed':False}
    def persist():
        state.update(elapsed_seconds=time.monotonic()-started,
            verified_cases=sum(x['cases'] for x in state['batches']))
        head=api.repo_info(repo,repo_type='dataset',revision=branch).sha
        return api.create_commit(repo_id=repo,repo_type='dataset',revision=branch,parent_commit=head,
            operations=[CommitOperationAdd(path_in_repo=report_path(args.worker),path_or_fileobj=pool.encoded(state))],
            commit_message='Checkpoint disjoint PDEBench worker').oid
    persist()
    try:
        for item in assignment['batches']:
            if time.monotonic()+1800>=deadline-900: raise TimeoutError('Insufficient time for another batch')
            if shutil.disk_usage('/tmp').free<20*1024**3: raise RuntimeError('Scratch disk headroom exhausted')
            state['current_batch']=item;persist()
            worker_args=argparse.Namespace(repo_id=repo,revision=branch,prefix=f'{PREFIX}/w{args.worker}',
                source_file=item['file'],batch_start=item['first'],per_file=item['count'])
            root=Path('/tmp/archive-production-batch');root.mkdir()
            result=archive.run_family(worker_args,report,runtime,item['family'],root)
            state['batches'].append({**result,'source_file':item['file'],'first':item['first']})
            state.pop('current_batch',None);persist()
            shutil.rmtree(root);gc.collect()
            for cache in ('/tmp/archive-hf','/tmp/caeoj-shards','/tmp/caeoj-index-reads'):
                shutil.rmtree(cache,ignore_errors=True)
        check_worker(state,assignment,plan_sha)
        state['status']='worker_completed';persist()
        if args.worker==plan['finalizer_worker']:
            state['final']=finalize(api,pool,archive,plan,plan_sha,state,persist,deadline)
            state['status']='completed';persist()
        signal.alarm(0)
        print(json.dumps({'status':state['status'],'verified_cases':state['verified_cases']}),flush=True)
    except Exception as exc:
        state.update(status='error',error={'type':type(exc).__name__,'message':str(exc)[:2000]})
        try:persist()
        except Exception:pass
        raise


if __name__=='__main__':main()
