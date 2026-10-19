# /// script
# requires-python = ">=3.11"
# dependencies = ["huggingface_hub>=1.0,<2", "numpy>=2,<3", "h5py>=3.13,<4", "fsspec[http]>=2025.3"]
# ///
"""Cloud-only source inspection; produces source subsets, never certified cases.

Run through hf_trial_launch.py. No legacy question or selection is consumed.
The output is author-side diagnostic material, outside the production pool.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import time


SOURCES = {
    'advection': ('pdebench/Advection', '33d90a245d98b8a250884eab613c6f9c26a13b68', 8),
    'burgers': ('pdebench/Burgers', '97bf5bb5315b9a083b4f9fc03e5c84d35286d52c', 12),
    'compressible': ('pdebench/1D-Compressible-Navier-Stokes',
                     'a6d507e6b7369ad80bd2f0e4ebbdf169c2eda903', 5),
}


def sample_indices(count, requested):
    if count < 1 or not 1 <= requested <= count:
        raise ValueError('Invalid source/sample count')
    # Stratifies source index only; it does not claim physical diversity.
    return sorted({i * (count - 1) // max(1, requested - 1) for i in range(requested)})


def valid_time_count(time_count, frames):
    if time_count not in (frames, frames + 1):
        raise ValueError('Unrecognized time/field length mismatch')
    return {'field_frames': frames, 'coordinate_entries': time_count,
            'unused_trailing_coordinates': time_count - frames,
            'interpretation': 'prefix association; generator semantics still require review'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-id', required=True)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--prefix', required=True)
    parser.add_argument('--per-file', type=int, default=10)
    args = parser.parse_args(argv)
    if not os.environ.get('JOB_ID'):
        parser.error('Remote array reads are restricted to HF Jobs (JOB_ID missing)')
    if not 1 <= args.per_file <= 100:
        parser.error('Probe is bounded to 1..100 records per source file')
    import fsspec
    import h5py
    import numpy as np
    from huggingface_hub import HfApi, hf_hub_url

    started = time.monotonic()
    api = HfApi()
    root = Path('/tmp/caeoj-source-probe')
    root.mkdir(exist_ok=True)
    report = {'version': 1, 'job_id': os.environ['JOB_ID'], 'sources': [],
              'status': 'running', 'per_file': args.per_file,
              'limitations': ['Source extraction, not question authoring or numerical certification.',
                             'Source subsets are author material, not candidate inputs.',
                             'No production pool or formal selection is changed.']}

    def persist():
        report['elapsed_seconds'] = time.monotonic() - started
        report['output_bytes'] = sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
        (root/'report.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
        api.upload_folder(repo_id=args.repo_id, repo_type='dataset', revision=args.revision,
                          folder_path=root, path_in_repo=args.prefix,
                          commit_message='Record bounded PDEBench source probe')

    def deadline(signum, frame):
        raise TimeoutError('Cloud probe reached its internal 50 minute deadline')

    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(50 * 60)
    try:
        for family, (repo, revision, expected_files) in SOURCES.items():
            files = [x for x in api.list_repo_tree(repo, repo_type='dataset', revision=revision)
                     if x.path.endswith('.hdf5')]
            if len(files) != expected_files:
                raise ValueError('Pinned source file count differs: '+repo)
            for item in sorted(files, key=lambda x: x.path):
                record = {'family': family, 'repo_id': repo, 'revision': revision,
                          'file': item.path, 'source_bytes': item.size,
                          'source_lfs_sha256': getattr(item.lfs, 'sha256', None),
                          'whole_source_checksum_verified': False, 'status': 'running'}
                report['sources'].append(record)
                output = root/family/(item.path+'.subset.h5')
                output.parent.mkdir(parents=True, exist_ok=True)
                try:
                    url = hf_hub_url(repo, item.path, repo_type='dataset', revision=revision)
                    # Mature HTTP range reader; no whole-file fallback allowed.
                    fs = fsspec.filesystem('http', client_kwargs={'trust_env': True})
                    with fs.open(url, 'rb', block_size=256*1024, cache_type='blockcache') as raw:
                        with h5py.File(raw, 'r') as source, h5py.File(output, 'w') as target:
                            keys = ['tensor'] if family != 'compressible' else ['density', 'Vx', 'pressure']
                            count, frames, nx = source[keys[0]].shape
                            selected = sample_indices(count, args.per_file)
                            record.update({'source_records': count, 'selected_indices': selected,
                                           'fields': {}, 'records': [],
                                           'attrs': {k: np.asarray(v).tolist() for k, v in source.attrs.items()}})
                            record['time_layout'] = valid_time_count(len(source['t-coordinate']), frames)
                            coords = np.asarray(source['x-coordinate'])
                            times = np.asarray(source['t-coordinate'][:frames])
                            if len(coords) != nx or not np.isfinite(coords).all() or not np.all(np.diff(coords)>0):
                                raise ValueError('Invalid source coordinates')
                            if not np.isfinite(times).all() or times[0] != 0 or not np.all(np.diff(times)>0):
                                raise ValueError('Invalid source time prefix')
                            target['x-coordinate'] = coords
                            target['t-coordinate'] = times
                            target['source_indices'] = np.asarray(selected, dtype=np.int64)
                            for key in keys:
                                field = source[key]
                                if field.shape != (count, frames, nx):
                                    raise ValueError('Source field shapes differ')
                                record['fields'][key] = {'shape': list(field.shape), 'dtype': str(field.dtype)}
                                target.create_dataset(key, shape=(len(selected), frames, nx), dtype=field.dtype,
                                                      chunks=(1, min(frames, 16), nx), compression='gzip',
                                                      compression_opts=1, shuffle=True)
                            for row, index in enumerate(selected):
                                metrics = {'source_index': index, 'fields': {}}
                                initial_hash = hashlib.sha256()
                                for key in keys:
                                    values = np.asarray(source[key][index])
                                    if not np.isfinite(values).all():
                                        raise ValueError('Nonfinite published field')
                                    target[key][row] = values
                                    initial_hash.update(key.encode())
                                    initial_hash.update(values[0].tobytes())
                                    metrics['fields'][key] = {'min': float(values.min()), 'max': float(values.max()),
                                                             'selected_payload_sha256': hashlib.sha256(values.tobytes()).hexdigest()}
                                metrics['initial_fingerprint'] = initial_hash.hexdigest()
                                record['records'].append(metrics)
                    with h5py.File(output, 'r') as reopened:
                        if reopened[keys[0]].shape[0] != len(selected):
                            raise ValueError('Subset read-back failed')
                    record.update(status='source_subset_extracted', subset_bytes=output.stat().st_size,
                                  subset_sha256=hashlib.sha256(output.read_bytes()).hexdigest())
                except Exception as exc:
                    output.unlink(missing_ok=True)
                    record.update(status='failed', error=type(exc).__name__+': '+str(exc).split('?')[0])
                print(json.dumps({k:record[k] for k in ('family','file','status')}, sort_keys=True), flush=True)
                persist()
        report['status'] = 'failed' if any(x['status']=='failed' for x in report['sources']) else 'source_probe_complete'
    except Exception as exc:
        report.update(status='failed', error=type(exc).__name__+': '+str(exc).split('?')[0])
    finally:
        signal.alarm(0)
        persist()
    return 0 if report['status']=='source_probe_complete' else 1


if __name__ == '__main__':
    raise SystemExit(main())
