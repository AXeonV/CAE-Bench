# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["huggingface_hub>=1.0,<2", "numpy>=2,<3", "h5py>=3.13,<4", "gmsh==4.15.2", "jsonschema==4.26.0", "fsspec[http]>=2025.3"]
# ///
"""HF-only lossless archive-to-case pilot. Never runs a numerical solver."""
import argparse
import base64
import hashlib
import io
import json
import os
import re
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import zipfile

RUNTIME_ZIP = ''
TASKS = {
    'advection': ('caeoj-000006', 'pdebench-advection-1d'),
    'burgers': ('caeoj-000007', 'pdebench-burgers-1d'),
    'compressible': ('caeoj-000008', 'pdebench-compressible-1d'),
}
BASE = 'qbank/01-prescribed-pdes/pdebench-archive'


def array_sha(value):
    """Bind numeric values, dtype and shape independently of HDF5 layout."""
    import numpy as np
    array = np.ascontiguousarray(value)
    header = json.dumps([array.dtype.str, list(array.shape)], separators=(',', ':')).encode()
    return hashlib.sha256(header + b'\n' + array.tobytes()).hexdigest()


def native(value):
    import numpy as np
    if isinstance(value, bytes):
        return {'encoding': 'bytes-hex', 'value': value.hex()}
    if isinstance(value, np.ndarray):
        return native(value.tolist())
    if isinstance(value, np.generic):
        return native(value.item())
    if isinstance(value, (list, tuple)):
        return [native(x) for x in value]
    if isinstance(value, dict):
        return {str(k): native(v) for k, v in value.items()}
    return value


def field(key, axis):
    return {'array': key, 'quantity': key, 'location': 'samples', 'time_axis': axis,
            'dtype': 'float64', 'kind': 'scalar', 'component_shape': [1],
            'components': ['value'], 'unit': 'source_units_unspecified', 'value_kind': 'point'}


def build_case(generated, name, source, index, coordinates, raw_times, values, metadata):
    """Only reshape and exactly promote float32 to float64; no physical inference."""
    import numpy as np
    from caeoj.sdk import load_problem, load_result
    from caeoj.storage import write_hdf5
    from caeoj.case_grading import direct_config, grade_case
    from caeoj_tools import data_pool as pool
    fields = sorted(values)
    shapes = {tuple(value.shape) for value in values.values()}
    if len(shapes) != 1:
        raise ValueError('Source fields have different shapes')
    frames, nx = next(iter(shapes))
    x = np.asarray(coordinates, dtype=np.float64)
    raw_times = np.asarray(raw_times)
    times = np.asarray(raw_times[:frames], dtype=np.float64)
    if (len(x) != nx or len(times) != frames or not np.isfinite(x).all()
            or not np.isfinite(raw_times).all() or not np.all(np.diff(x) > 0)
            or not np.all(np.diff(times) > 0)):
        raise ValueError('Invalid source coordinate association')
    converted = {}
    for key, value in values.items():
        if value.dtype.kind != 'f' or value.dtype.itemsize not in (4, 8) or not np.isfinite(value).all():
            raise ValueError('Unsupported or nonfinite source field')
        converted[key] = np.asarray(value, dtype=np.float64)[..., None]
        if not np.array_equal(converted[key][..., 0].astype(value.dtype), value):
            raise ValueError('Lossy field conversion')
    inputs = generated/'cases'/name
    refs = generated/'reference'/name
    inputs.mkdir(parents=True); refs.mkdir(parents=True)
    task_id, task = TASKS[source['family']]
    problem = {'task': task, 'spatial_dimension': 1, 'data_file': 'input.h5',
        'geometries': {}, 'meshes': {},
        'locations': {'samples': {'kind': 'points', 'ids': 'point_ids', 'coordinates': 'coordinates'}},
        'time_axes': {'initial': 'initial_times', 'output': 'times'},
        'fields': {'initial_'+key: field('initial_'+key, 'initial') for key in fields},
        'outputs': {key: field(key, 'output') for key in fields},
        'physics': {'model': 'pdebench_archive_'+source['family'], 'parameters': {}},
        'conditions': []}
    # source.json is part of the input identity, preserving every source row even
    # when two archives have identical initial arrays. It contains no later fields.
    provenance = {'source_repository': source['repo_id'], 'source_revision': source['revision'],
        'source_file': source['file'], 'source_sha256': source['source_lfs_sha256'],
        'sample_index': int(index), 'family': source['family'], 'metadata': metadata,
        'field_mapping': {key: key for key in fields},
        'raw_time_coordinates': native(raw_times), 'field_frames': frames,
        'time_mapping': 'first field_frames coordinate entries, by archive index',
        'unused_trailing_time_coordinates': len(raw_times)-frames,
        'spatial_representation': 'ordered archive samples at supplied x coordinates; no reconstruction',
        'physical_sampling_and_units': 'preserved as supplied; unspecified information is not inferred',
        'reference_kind': 'PDEBench archived trajectory; no recomputation'}
    pool.write_json(inputs/'source.json', provenance)
    pool.write_json(inputs/'problem.json', problem)
    arrays = {'point_ids': np.arange(nx, dtype=np.int64), 'coordinates': x[:, None],
              'times': times, 'initial_times': times[:1]}
    arrays.update({'initial_'+key: value[:1] for key, value in converted.items()})
    write_hdf5(inputs/'input.h5', arrays, compression='gzip')
    loaded = load_problem(inputs/'problem.json')
    # Same standard result contract as write_result, with lossless gzip storage.
    from caeoj.validation import output_support, check_result, ContractError
    result = {key: loaded.arrays[key] for key in output_support(loaded)} | converted
    diagnostics = check_result(loaded, result)
    if not diagnostics['valid']:
        raise ContractError(diagnostics)
    write_hdf5(refs/'reference.h5', result, compression='gzip')
    policy = {'version': 1, 'fields': {key: {
        'metric': 'violation_fraction', 'time': 'per_time', 'components': 'joint',
        'count': 'spatial_points', 'atol': 0., 'rtol': 0., 'limit': 0.} for key in fields}}
    pool.write_json(refs/'grading.json', direct_config(policy))
    roundtrip = load_result(loaded, refs/'reference.h5')
    hashes = {}
    for key, original in values.items():
        recovered = roundtrip[key][..., 0].astype(original.dtype)
        if not np.array_equal(recovered, original):
            raise ValueError('Archive/reference roundtrip differs')
        if not np.array_equal(loaded.arrays['initial_'+key][0, :, 0], original[0]):
            raise ValueError('Archive/initial roundtrip differs')
        hashes[key] = {'source': array_sha(original), 'mapped_float64': array_sha(roundtrip[key]),
                       'original_dtype': original.dtype.str, 'shape': list(original.shape)}
    if grade_case(inputs/'problem.json', refs/'reference.h5', refs/'grading.json')['status'] != 'accepted':
        raise ValueError('Archive identity check failed')
    input_files = {path.name: pool.digest(path) for path in inputs.iterdir()}
    pool.write_json(refs/'certificate.json', {**{k: provenance[k] for k in (
        'source_repository', 'source_revision', 'source_file', 'source_sha256', 'sample_index')},
        'input_files': input_files, 'whole_source_checksum_verified': False,
        'source_field_payloads': hashes, 'numerical_certification_performed': False})
    return {'local_id': name, 'source_file': source['file'], 'sample_index': int(index),
        'fields': hashes, 'reference_sha256': pool.digest(refs/'reference.h5'),
        'source_coordinates_sha256': array_sha(coordinates),
        'mapped_coordinates_sha256': array_sha(arrays['coordinates']),
        'valid_times_sha256': array_sha(arrays['times']), 'input_files': input_files,
        'unused_trailing_time_coordinates': len(raw_times)-frames, 'frames': frames,
        'reference_recomputed': False}


def consume(args, state, revision, root):
    from caeoj_tools import data_pool as pool
    from caeoj.sdk import load_problem, load_result
    from caeoj.case_grading import grade_case
    choice = state['selection']
    pool.write_json(root/'data-manifest.json', choice)
    backing = pool.HubStore(args.repo_id, revision, cache_dir=str(root/'cache'))
    pool.assemble(root, choice, backing)
    pool.verify(root, strict=True)
    for record in state['producer_report']['records']:
        name = record['local_id']
        problem = load_problem(root/'cases'/name/'problem.json')
        ref = root/'reference'/name
        values = load_result(problem, ref/'reference.h5')
        for key, identity in record['fields'].items():
            if array_sha(values[key]) != identity['mapped_float64']:
                raise ValueError('Remote reference no longer matches source payload')
        if grade_case(root/'cases'/name/'problem.json', ref/'reference.h5', ref/'grading.json')['status'] != 'accepted':
            raise ValueError('Remote archive identity consumption failed')
    return len(choice['cases'])


def run_family(args, source_report, runtime, family, root):
    import numpy as np
    import h5py
    import fsspec
    from huggingface_hub import HfApi, hf_hub_url, hf_hub_download
    from caeoj_tools import data_pool as pool
    from hf_migrate import runtime_identity, save, validate_state
    started = time.monotonic()
    sources = [s for s in source_report['sources'] if s['family'] == family
               and (not getattr(args, 'source_file', None) or s['file'] == args.source_file)]
    if not sources:
        raise ValueError('No matching pinned source')
    task_id, task_name = TASKS[family]
    task_rel = BASE+'/'+task_name
    script, replacements = re.subn(r'^RUNTIME_ZIP = .*$', 'RUNTIME_ZIP = '+repr(''), Path(__file__).read_text(), flags=re.MULTILINE)
    if replacements != 1:
        raise ValueError('Cannot bind archive worker template')
    recipe = {'kind': 'pdebench-direct-archive-v1', 'family': family,
        'sources': [{k: s[k] for k in ('repo_id', 'revision', 'file', 'source_lfs_sha256')} for s in sources],
        'first': args.batch_start, 'per_file': args.per_file, 'count': args.per_file*len(sources),
        'worker_sha256': hashlib.sha256(script.encode()).hexdigest(),
        'runtime_contents_sha256': runtime_identity(RUNTIME_ZIP)}
    key = hashlib.sha256(pool.encoded(recipe)).hexdigest()
    api = HfApi()
    head = api.repo_info(args.repo_id, repo_type='dataset', revision=args.revision).sha
    state_name = args.prefix+'/batches/'+key+'.json'
    exists = api.get_paths_info(args.repo_id, [state_name], repo_type='dataset', revision=head)
    state = {'version': 1, 'batch_key': key, 'recipe': recipe, 'status': 'planned',
             'first_job_id': os.environ['JOB_ID']}
    if exists:
        state = pool.checked_json(hf_hub_download(args.repo_id, state_name, repo_type='dataset', revision=head))
        validate_state(state, key, recipe)
        if state['status'] == 'verified':
            count = consume(args, state, head, root/'replayed')
            return {'family': family, 'cases': count, 'replayed_without_source_read': True,
                    'state_revision': head, 'batch_key': key}
        if state['status'] == 'prepared':
            # Publication may have partially succeeded. Preserve its binding and
            # stop for inspection; do not create a different physical bundle.
            raise RuntimeError('Prepared batch exists; inspect publication before resuming')
    else:
        save(args, state)
    generated = root/'generated'
    generated.mkdir(parents=True)
    fs = fsspec.filesystem('http', client_kwargs={'trust_env': True})
    records, source_stats = [], []
    for ordinal, source in enumerate(sources):
        begin = time.monotonic()
        url = hf_hub_url(source['repo_id'], source['file'], repo_type='dataset', revision=source['revision'])
        with fs.open(url, 'rb', block_size=8*1024**2, cache_type='blockcache', cache_options={'maxblocks': 8}) as raw:
            with h5py.File(raw, 'r') as data:
                keys = sorted(source['fields'])
                for name in keys:
                    if list(data[name].shape) != source['fields'][name]['shape'] or str(data[name].dtype) != source['fields'][name]['dtype']:
                        raise ValueError('Pinned source field layout changed')
                x, times = data['x-coordinate'][:], data['t-coordinate'][:]
                metadata = {'file_attributes': native(dict(data.attrs)),
                    'dataset_attributes': {name: native(dict(data[name].attrs)) for name in keys+['x-coordinate', 't-coordinate']},
                    'source_field_layouts': source['fields'], 'source_probe_attributes': source['attrs'],
                    'filename': source['file'],
                    'parameter_resolution': 'raw attributes and filename both retained; conflicts are not silently resolved'}
                first, count = args.batch_start, args.per_file
                values = {name: data[name][first:first+count] for name in keys}
                for row in range(count):
                    name = f'{ordinal:02d}-{first+row:05d}'
                    records.append(build_case(generated, name, source, first+row, x, times,
                        {key: value[row] for key, value in values.items()}, metadata))
        source_stats.append({'file': source['file'], 'records': count,
            'elapsed_seconds': time.monotonic()-begin, 'whole_source_checksum_verified': False})
        print(json.dumps({'family': family, 'file': source['file'], 'converted': count}), flush=True)
    value = {'schema_version': 4, 'task_id': task_id,
        'repository': {'repo_id': args.repo_id, 'repo_type': 'dataset', 'path': task_rel},
        'pool': {'index': 'pool/index.json'}, 'cases': {}, 'samples': {}}
    bundle, physical = root/'bundle', root/'physical'
    pool.pack(generated, bundle, value)
    pool.shard_bundle(bundle, physical)
    report = {'family': family, 'records': records, 'sources': source_stats,
        'reference_recomputed': False, 'grading_scope': 'exact archive identity check only; formal evaluation tolerance not calibrated',
        'formal_selection_changed': False, 'agent_benchmark_run': False}
    state.update(status='prepared', selection=pool.manifest(bundle/'selection.json'),
        transport_sha256=pool.digest(physical/'transport.json'), producer_report=report)
    save(args, state)
    upload_started = time.monotonic()
    receipt = pool.upload(physical, revision=args.revision)
    upload_seconds = time.monotonic()-upload_started
    consume_started = time.monotonic()
    count = consume(args, state, receipt['revision'], root/'consumed')
    consume_seconds = time.monotonic()-consume_started
    state.update(status='verified', pool_revision=receipt['revision'], verified_cases=count,
        upload_receipt=receipt, last_job_id=os.environ['JOB_ID'], resumed_without_source_read=False,
        elapsed_seconds=time.monotonic()-started, upload_seconds=upload_seconds,
        remote_consume_seconds=consume_seconds)
    commit = save(args, state)
    summary = {'family': family, 'cases': count, 'source_files': len(sources),
        'elapsed_seconds': state['elapsed_seconds'], 'source_and_conversion_seconds': sum(s['elapsed_seconds'] for s in source_stats),
        'upload_seconds': upload_seconds, 'remote_consume_seconds': consume_seconds,
        'pool_revision': receipt['revision'], 'state_revision': commit, 'batch_key': key,
        'compressed_batch_bytes': sum(p.stat().st_size for p in physical.rglob('*') if p.is_file()),
        'reference_recomputed': False, 'replayed_without_source_read': False}
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('repo-id', 'revision', 'prefix', 'source-revision', 'source-prefix'):
        parser.add_argument('--'+name, required=True)
    parser.add_argument('--per-file', type=int, default=16)
    parser.add_argument('--batch-start', type=int, default=0)
    parser.add_argument('--full', action='store_true')
    parser.add_argument('--hard-timeout-seconds', type=int, default=1800)
    parser.add_argument('--baseline-revision')
    args = parser.parse_args(argv)
    if not os.environ.get('JOB_ID') or not RUNTIME_ZIP:
        parser.error('Only the budgeted HF launcher may run this array worker')
    if not 1 <= args.per_file <= 100 or not 0 <= args.batch_start <= 10000-args.per_file:
        parser.error('Invalid bounded archive pilot range')
    if args.full and (args.hard_timeout_seconds != 72*3600 or not args.baseline_revision):
        parser.error('Full migration requires its fixed baseline and 72h hard timeout')
    # Each batch deletes its cache; no accumulated TARs or Xet chunks on 50GB disk.
    os.environ.update(HF_HOME='/tmp/archive-hf', HF_HUB_CACHE='/tmp/archive-hf/hub',
        HF_XET_CHUNK_CACHE_SIZE_BYTES='0', HF_HUB_DISABLE_PROGRESS_BARS='1')
    started = time.monotonic()
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('Archive pilot deadline')))
    signal.alarm(args.hard_timeout_seconds-900 if args.full else 25*60)
    runtime = Path('/tmp/archive-runtime'); runtime.mkdir()
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(RUNTIME_ZIP))) as archive:
        for entry in archive.infolist():
            if not (runtime/entry.filename).resolve().is_relative_to(runtime.resolve()):
                raise ValueError('Unsafe runtime path')
        archive.extractall(runtime)
    libraries = json.loads((runtime/'support/gmsh-system-packages.json').read_text())
    subprocess.run(['apt-get', 'update', '-qq'], check=True, timeout=120)
    subprocess.run(['apt-get', 'install', '-y', '-qq', '--no-install-recommends', *libraries], check=True, timeout=120)
    subprocess.run(['uv', 'pip', 'install', '--python', sys.executable, '--no-deps', str(runtime)], check=True, timeout=120)
    sys.path.insert(0, str(runtime/'support'))
    from huggingface_hub import HfApi, hf_hub_download, CommitOperationAdd
    from caeoj_tools import data_pool as pool
    report = pool.checked_json(hf_hub_download(args.repo_id, args.source_prefix+'/report.json',
        repo_type='dataset', revision=args.source_revision))
    if len(report['sources']) != 25 or {f: sum(s['family'] == f for s in report['sources']) for f in TASKS} != {'advection': 8, 'burgers': 12, 'compressible': 5}:
        raise ValueError('Expected all 25 pinned source files')
    if args.full:
        return run_full(args, report, runtime, started)
    summary = {'job_id': os.environ['JOB_ID'], 'kind': 'pdebench-direct-archive-pilot-v1',
        'source_report_revision': args.source_revision, 'families': [], 'status': 'running',
        'formal_selection_changed': False, 'numerical_solver_run': False}
    api = HfApi()
    def persist():
        head = api.repo_info(args.repo_id, repo_type='dataset', revision=args.revision).sha
        return api.create_commit(repo_id=args.repo_id, repo_type='dataset', revision=args.revision,
            parent_commit=head, operations=[CommitOperationAdd(path_in_repo=args.prefix+'/report.json',
                path_or_fileobj=pool.encoded(summary))], commit_message='Record direct archive migration pilot').oid
    for family in TASKS:
        root = Path('/tmp/archive-'+family)
        root.mkdir()
        result = run_family(args, report, runtime, family, root)
        summary['families'].append(result)
        persist()
        shutil.rmtree(root)
    summary.update(status='completed', cases=sum(x['cases'] for x in summary['families']),
        elapsed_seconds=time.monotonic()-started)
    commit = persist()
    signal.alarm(0)
    print(json.dumps({'status': 'archive_pilot_completed', 'cases': summary['cases'], 'report_revision': commit}), flush=True)
    return 0


def full_plan(source_report):
    """The fixed pilot covers 0..15; these disjoint spans cover every other row."""
    result = []
    groups = {family: [s for s in source_report['sources'] if s['family'] == family] for family in TASKS}
    # Exercise each family's thousand-row path early, while retaining one writer.
    ordered = [groups[family][i] for i in range(max(map(len, groups.values())))
               for family in TASKS if i < len(groups[family])]
    for boundary in range(0, 10000, 1000):
        for source in ordered:
            if source.get('source_records') != 10000:
                raise ValueError('Expected exactly 10000 source rows')
            first = 16 if boundary == 0 else boundary
            result.append({'family': source['family'], 'file': source['file'],
                'first': first, 'count': min(boundary+1000, 10000)-first})
    if len(result) != 250 or sum(x['count'] for x in result) != 249600:
        raise ValueError('Full migration source accounting differs')
    return result


def remaining_time_allows_batch(elapsed, hard_timeout, prior_seconds=0.):
    # Leave publication/report headroom; never begin a batch near the deadline.
    return elapsed + max(1800., 2*prior_seconds) < hard_timeout-900


def verify_baseline(args, report):
    """Check all 400 fixed pilot descriptor bindings without downloading arrays."""
    from huggingface_hub import HfApi, hf_hub_download
    from caeoj_tools import data_pool as pool
    api = HfApi()
    prefix = 'migration-trials/pdebench/2026-10-18/direct-archive'
    pilot = pool.checked_json(hf_hub_download(args.repo_id, prefix+'/report.json',
        repo_type='dataset', revision=args.baseline_revision))
    if pilot.get('status') != 'completed' or pilot.get('cases') != 400 or pilot.get('numerical_solver_run') is not False:
        raise ValueError('Unverified archive baseline')
    expected = {(s['file'], i) for s in report['sources'] for i in range(16)}
    actual, baseline = set(), []
    head = api.repo_info(args.repo_id, repo_type='dataset', revision=args.revision).sha
    for family in pilot['families']:
        state = pool.checked_json(hf_hub_download(args.repo_id, prefix+'/batches/'+family['batch_key']+'.json',
            repo_type='dataset', revision=args.baseline_revision))
        if state.get('status') != 'verified' or state['recipe']['per_file'] != 16:
            raise ValueError('Baseline checkpoint not verified')
        choice = state['selection']
        view = pool.consumer_store(choice, pool.HubStore(args.repo_id, head))
        for binding in choice['cases'].values():
            current = view.lookup(binding['case_id'])
            if current is None or current['sha256'] != binding['case']['sha256']:
                raise ValueError('Baseline case changed or missing')
        records = state['producer_report']['records']
        if len(records) != state['verified_cases'] or len(records) != len(choice['cases']):
            raise ValueError('Baseline row count differs')
        for record in records:
            pair = (record['source_file'], record['sample_index'])
            if pair in actual or record['reference_recomputed']:
                raise ValueError('Baseline row repeated or recomputed')
            actual.add(pair)
        baseline.append({'family': family['family'], 'cases': len(records), 'batch_key': family['batch_key']})
    if actual != expected:
        raise ValueError('Baseline source rows differ')
    return baseline


def run_full(args, report, runtime, started):
    """One budget-reserved sequential cloud controller; checkpoints per source span."""
    import gc
    from huggingface_hub import HfApi, CommitOperationAdd, hf_hub_download
    from caeoj_tools import data_pool as pool
    from hf_migrate import runtime_identity
    api = HfApi()
    job = api.inspect_job(job_id=os.environ['JOB_ID'])
    hardware = next(x for x in api.list_jobs_hardware() if x.name == 'cpu-basic')
    if job.flavor != 'cpu-basic' or hardware.unit_label != 'minute' or not 0 < hardware.unit_cost_micro_usd <= 167:
        raise ValueError('Full worker CPU flavor or price differs')
    script, _ = re.subn(r'^RUNTIME_ZIP = .*$', 'RUNTIME_ZIP = '+repr(''), Path(__file__).read_text(), flags=re.MULTILINE)
    recipe = {'kind': 'pdebench-direct-archive-full-v1', 'source_revision': args.source_revision,
        'baseline_revision': args.baseline_revision, 'worker_sha256': hashlib.sha256(script.encode()).hexdigest(),
        'runtime_contents_sha256': runtime_identity(RUNTIME_ZIP), 'plan': full_plan(report)}
    recipe_sha = hashlib.sha256(pool.encoded(recipe)).hexdigest()
    name = args.prefix+'/full-report.json'
    head = api.repo_info(args.repo_id, repo_type='dataset', revision=args.revision).sha
    found = api.get_paths_info(args.repo_id, [name], repo_type='dataset', revision=head)
    if found:
        summary = pool.checked_json(hf_hub_download(args.repo_id, name, repo_type='dataset', revision=head))
        if summary.get('recipe_sha256') != recipe_sha:
            raise RuntimeError('Full migration recipe differs; inspect existing run')
    else:
        summary = {'kind': recipe['kind'], 'recipe_sha256': recipe_sha, 'recipe': recipe,
            'baseline': verify_baseline(args, report), 'baseline_cases': 400, 'target_cases': 250000,
            'batches': [], 'status': 'running', 'first_job_id': os.environ['JOB_ID'],
            'numerical_solver_run': False, 'formal_selection_changed': False}
    def persist():
        summary.update(last_job_id=os.environ['JOB_ID'], elapsed_seconds=time.monotonic()-started,
            verified_cases=400+sum(x['cases'] for x in summary['batches']))
        head = api.repo_info(args.repo_id, repo_type='dataset', revision=args.revision).sha
        return api.create_commit(repo_id=args.repo_id, repo_type='dataset', revision=args.revision,
            parent_commit=head, operations=[CommitOperationAdd(path_in_repo=name, path_or_fileobj=pool.encoded(summary))],
            commit_message='Checkpoint full archive migration progress').oid
    done = {(x['source_file'], x['first'], x['cases']) for x in summary['batches']}
    planned = {(x['file'], x['first'], x['count']) for x in recipe['plan']}
    if len(done) != len(summary['batches']) or not done <= planned:
        raise RuntimeError('Repeated completed batch')
    summary['status'] = 'running'
    summary.pop('error', None)
    persist()
    try:
        for number, item in enumerate(recipe['plan']):
            identity = (item['file'], item['first'], item['count'])
            if identity in done:
                continue
            previous = max((x.get('elapsed_seconds', 0.) for x in summary['batches']), default=0.)
            if not remaining_time_allows_batch(time.monotonic()-started, args.hard_timeout_seconds, previous):
                summary['status'] = 'stopped_at_time_budget'
                persist()
                return 0
            if shutil.disk_usage('/tmp').free < 20*1024**3:
                raise RuntimeError('Insufficient temporary disk before next batch')
            args.source_file, args.batch_start, args.per_file = item['file'], item['first'], item['count']
            root = Path('/tmp/archive-production-batch')
            root.mkdir()
            summary['current_batch'] = {'number': number, **item}
            persist()
            result = run_family(args, report, runtime, item['family'], root)
            summary['batches'].append({**result, 'source_file': item['file'], 'first': item['first']})
            done.add(identity)
            summary.pop('current_batch', None)
            persist()
            print(json.dumps({'status': 'full_batch_verified', 'batches': len(done),
                'verified_cases': summary['verified_cases'], 'target': 250000}), flush=True)
            shutil.rmtree(root)
            gc.collect()
            for cache in ('/tmp/archive-hf', '/tmp/caeoj-shards', '/tmp/caeoj-index-reads'):
                shutil.rmtree(cache, ignore_errors=True)
        counts = {}
        head = api.repo_info(args.repo_id, repo_type='dataset', revision=args.revision).sha
        for family, (_, task) in TASKS.items():
            root = pool.checked_json(hf_hub_download(args.repo_id, BASE+'/'+task+'/pool/index.json',
                repo_type='dataset', revision=head))
            counts[family] = root['case_count']
        if counts != {'advection': 80000, 'burgers': 120000, 'compressible': 50000}:
            raise RuntimeError('Final pool counts differ from source coverage')
        summary.update(status='completed', pool_counts=counts)
        persist()
        signal.alarm(0)
        return 0
    except Exception as exc:
        summary.update(status='error', error={'type': type(exc).__name__, 'message': str(exc)[:2000]})
        try:
            persist()
        except Exception:
            pass
        raise


if __name__ == '__main__':
    raise SystemExit(main())
