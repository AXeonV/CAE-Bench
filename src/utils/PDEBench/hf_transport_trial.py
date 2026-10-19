# /// script
# requires-python = ">=3.11"
# dependencies = ["huggingface_hub>=1.0,<2", "numpy>=2,<3", "h5py>=3.13,<4", "gmsh==4.15.2", "jsonschema==4.26.0", "requests>=2.32,<3", "fsspec[http]>=2025.3"]
# ///
"""Cloud trial: source initial states -> exact transport references -> HF pool.

The launcher embeds only the explicitly inventoried runtime and public contract.
No original numeric answer is relabeled as the exact continuous solution.
"""
import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import zipfile


RUNTIME_ZIP = ''  # Filled in a staging copy by hf_trial_launch.py, never credentials.
TASK_REL = 'qbank/01-prescribed-pdes/1.3-scalar-transport/linear-periodic-transport-1d'


def translated_averages(initial, times, speed):
    import numpy as np
    initial = np.asarray(initial, dtype=np.float64).reshape(-1)
    shifts = np.asarray(times, dtype=np.float64) * speed * len(initial)
    integers = np.floor(shifts).astype(np.int64)
    fractions = shifts - integers
    rows = [(1-f)*np.roll(initial, int(k)) + f*np.roll(initial, int(k)+1)
            for k, f in zip(integers, fractions)]
    return np.asarray(rows)[..., None]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-id', required=True)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--prefix', required=True)
    parser.add_argument('--source-revision', required=True)
    parser.add_argument('--source-prefix', required=True)
    parser.add_argument('--preflight', action='store_true', help='Bounded shard/recovery/1000-case experiment')
    parser.add_argument('--readiness',action='store_true')
    parser.add_argument('--resume',action='store_true')
    parser.add_argument('--migrate',action='store_true')
    parser.add_argument('--source-file')
    parser.add_argument('--batch-start',type=int,default=0)
    parser.add_argument('--batch-count',type=int,default=1000)
    args = parser.parse_args(argv)
    if not os.environ.get('JOB_ID') or not RUNTIME_ZIP:
        parser.error('Only the budgeted HF launcher may run this data worker')
    import h5py
    import numpy as np
    from huggingface_hub import HfApi, hf_hub_download

    started = time.monotonic()
    runtime = Path('/tmp/caeoj-runtime')
    runtime.mkdir()
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(RUNTIME_ZIP))) as z:
        for entry in z.infolist():
            if not (runtime/entry.filename).resolve().is_relative_to(runtime.resolve()):
                raise ValueError('Unsafe runtime path')
        z.extractall(runtime)
    # Reuse the established Harbor image's runtime libraries (no separate list).
    libraries = json.loads((runtime/'support/gmsh-system-packages.json').read_text())
    subprocess.run(['apt-get', 'update', '-qq'], check=True, timeout=120)
    subprocess.run(['apt-get', 'install', '-y', '-qq', '--no-install-recommends', *libraries], check=True, timeout=120)
    subprocess.run([sys.executable, '-m', 'pip', '--version'], stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, check=False)
    # uv environments need not contain pip. Install the public runtime non-editably.
    subprocess.run(['uv', 'pip', 'install', '--python', sys.executable, '--no-deps', str(runtime)],
                   check=True, timeout=120)
    sys.path.insert(0, str(runtime/'support'))
    os.chdir('/tmp')
    from caeoj.sdk import load_problem, load_result, write_result
    from caeoj.storage import write_hdf5
    from caeoj.case_grading import direct_config, grade_case
    from caeoj_tools import data_pool as pool
    from utils.PDEBench.conversion import make_mesh, advection_average

    if args.readiness:
        from hf_readiness import run
        return run(args,runtime)

    report_path = hf_hub_download(args.repo_id, args.source_prefix+'/report.json',
                                  revision=args.source_revision, repo_type='dataset')
    source_report = json.loads(Path(report_path).read_text())
    sources = [s for s in source_report['sources'] if s['family']=='advection']
    if len(sources) != 8 or any(s['status']!='source_subset_extracted' for s in sources):
        raise ValueError('Eight complete advection source subsets required')
    if args.preflight:
        from hf_preflight import prepare_source
        sources = prepare_source(args, source_report, runtime)
    if args.migrate:
        from hf_migrate import prepare
        args.task_rel=TASK_REL
        sources=prepare(args,source_report,runtime)
        if sources is None:return 0
    task = runtime/TASK_REL
    generated = Path('/tmp/transport-generated')
    generated.mkdir()
    for name in ('instruction.md', 'DATA.md'):
        shutil.copyfile(task/name, generated/name)
    policy = json.loads((task/'author/grading-template.json').read_text())
    report = {'job_id': os.environ['JOB_ID'], 'source_revision': args.source_revision,
              'source_prefix': args.source_prefix, 'records': [],
              'reference_producer': 'Periodic translation formula, integrated over each original cell',
              'formula_source': 'https://arxiv.org/html/2210.07182v2#S4.SS1',
              'adaptation': 'Published initial numbers define a new piecewise-constant initial condition; archived later frames are diagnostics only.',
              'precision_target': {'atol': 1e-6, 'rtol': 1e-6},
              'formal_selection_changed': False, 'agent_benchmark_run': False,
              'limitations': ['The alternate integral is an independent implementation of the same formula, not an independent physical experiment.',
                             'No solver execution under the declared CPU/memory/time limits has been certified.',
                             'Burgers and compressible subsets have not been promoted to usable cases.']}
    mesh = Path('/tmp/transport-mesh.msh')
    ids, _ = make_mesh(mesh, (1024,), ((0., 1.),))
    reference_errors = []
    for source in sources:
        subset_name = args.source_prefix+'/advection/'+source['file']+'.subset.h5'
        subset_path = source.get('local_subset') or hf_hub_download(args.repo_id, subset_name, revision=args.source_revision, repo_type='dataset')
        if pool.digest(Path(subset_path)) != source['subset_sha256']:
            raise ValueError('Subset does not match bound source report')
        speed = float(source['attrs']['beta'])
        if speed not in (.1,.2,.4,.7,1.,2.,4.,7.):
            raise ValueError('Unexpected advection speed')
        with h5py.File(subset_path, 'r') as subset:
            times = np.asarray(subset['t-coordinate'], dtype=np.float64)
            coordinates = subset['x-coordinate'][:]
            if not np.array_equal(coordinates, (np.arange(1024)+.5)/1024):
                raise ValueError('Coordinates do not coincide with original cell centers')
            if not 1 <= len(times) <= 201 or times[0] != 0 or times[-1] > 2 or not np.all(np.diff(times)>0):
                raise ValueError('Output times outside the new contract')
            for row, source_index in enumerate(subset['source_indices'][:]):
                case_start = time.monotonic()
                name = f'{len(report["records"])+1:03d}'
                input_dir = generated/'cases'/name
                ref_dir = generated/'reference'/name
                input_dir.mkdir(parents=True); ref_dir.mkdir(parents=True)
                shutil.copyfile(mesh, input_dir/'mesh.msh')
                initial = np.asarray(subset['tensor'][row, 0], dtype=np.float64)
                if not np.isfinite(initial).all() or np.max(abs(initial)) > 1000:
                    raise ValueError('Initial condition outside public scope')
                def field(array, axis):
                    return {'array': array, 'quantity': 'state', 'location': 'domain',
                            'time_axis': axis, 'dtype': 'float64', 'kind': 'scalar',
                            'component_shape': [1], 'components': ['value'], 'unit': '1', 'value_kind': 'average'}
                problem = {'task':'linear-periodic-transport-1d', 'spatial_dimension':1,
                           'data_file':'input.h5','geometries':{},'meshes':{'main':{'file':'mesh.msh'}},
                           'locations':{'domain':{'kind':'mesh','mesh':'main','entity':'element','dimension':1,
                                                 'ids':'cell_ids','physical_group':{'dimension':1,'tag':1}}},
                           'time_axes':{'initial':'initial_times','output':'times'},
                           'fields':{'initial_state':field('initial_state','initial')},
                           'outputs':{'state':field('state','output')},
                           'physics':{'model':'linear_periodic_transport_1d','parameters':{'velocity':{'value':speed,'unit':'m/s'}}},
                           'conditions':[{'role':'initial','variable':'state','location':'domain','operator':'assign',
                                          'data':{'value':{'field':'initial_state'}}},
                                         {'role':'boundary','variable':'state','location':'domain','operator':'periodic',
                                          'data':{'period_x':{'value':1,'unit':'m'}}}]}
                pool.write_json(input_dir/'problem.json', problem)
                write_hdf5(input_dir/'input.h5', {'cell_ids':ids,'initial_times':np.array([0.]),
                                                'times':times,'initial_state':initial[None,:,None]})
                loaded = load_problem(input_dir/'problem.json')
                exact = translated_averages(initial, times, speed)
                alternate = advection_average(initial, times, speed)
                discrepancy = float(np.max(abs(exact-alternate)))
                if discrepancy > 1e-9 or not np.array_equal(exact[0,:,0], initial):
                    raise ValueError('Exact-reference implementation disagreement')
                if np.max(abs(exact.mean(axis=1)-initial.mean())) > 1e-10:
                    raise ValueError('Exact-reference mass check failed')
                reference_errors.append(discrepancy)
                write_result(ref_dir/'reference.h5', loaded, {'state':exact})
                pool.write_json(ref_dir/'grading.json', direct_config(policy))
                if grade_case(input_dir/'problem.json', ref_dir/'reference.h5', ref_dir/'grading.json')['status']!='accepted':
                    raise ValueError('Reference failed real grading')
                incorrect = exact.copy(); incorrect[-1, 0, 0] += .01
                bad = Path('/tmp/transport-incorrect.h5')
                write_result(bad, loaded, {'state':incorrect})
                if grade_case(input_dir/'problem.json', bad, ref_dir/'grading.json')['status']!='wrong_answer':
                    raise ValueError('Discriminating wrong-output check failed')
                input_files = {p.name:pool.digest(p) for p in input_dir.iterdir()}
                certificate = {'source_repository':source['repo_id'], 'source_file':source['file'],
                               'source_sha256':source['source_lfs_sha256'],
                               'sample_index':int(source_index), 'input_files':input_files,
                               'contract_sha256':hashlib.sha256((task/'instruction.md').read_bytes()+(task/'DATA.md').read_bytes()).hexdigest(),
                               'source_revision':source['revision']}
                pool.write_json(ref_dir/'certificate.json', certificate)
                archived = np.asarray(subset['tensor'][row], dtype=np.float64)[...,None]
                report['records'].append({'local_id':name, 'source_file':source['file'],
                                          'source_index':int(source_index),'source_revision':source['revision'],
                                          'source_lfs_sha256':source['source_lfs_sha256'],
                                          'input_files':input_files, 'reference_sha256':pool.digest(ref_dir/'reference.h5'),
                                          'alternate_integral_max_abs':discrepancy,
                                          'archived_snapshot_difference_max_abs':float(np.max(abs(exact-archived))),
                                          'construction_and_checks_seconds':time.monotonic()-case_start})
                if not args.preflight or len(report['records']) % 100 == 0:
                    print(json.dumps({'case':name,'status':'contract_and_reference_checked'}), flush=True)
    value = {'schema_version':4,'task_id':'caeoj-000005',
             'repository':{'repo_id':args.repo_id,'repo_type':'dataset','path':TASK_REL},
             'pool':{'index':'pool/index.json'},'cases':{},'samples':{}}
    bundle = Path('/tmp/transport-bundle')
    pool.pack(generated, bundle, value)
    if args.migrate:
        from hf_migrate import finish
        return finish(args,bundle,report)
    if args.preflight:
        from hf_preflight import finish_preflight
        return finish_preflight(args, source_report, runtime, generated, bundle, report, started)
    choice = pool.manifest(bundle/'selection.json')
    local_check = Path('/tmp/transport-local-check'); local_check.mkdir()
    pool.write_json(local_check/'data-manifest.json',choice)
    pool.assemble(local_check,choice,pool.LocalStore(bundle/'repository'))
    pool.verify(local_check,strict=True)
    uploaded = pool.upload(bundle, revision=args.revision)
    remote_check = Path('/tmp/transport-remote-check'); remote_check.mkdir()
    pool.write_json(remote_check/'data-manifest.json',choice)
    store = pool.HubStore(args.repo_id, revision=uploaded['revision'], cache_dir='/tmp/transport-pool-cache')
    pool.assemble(remote_check,choice,store)
    pool.verify(remote_check,strict=True)
    for directory in sorted((remote_check/'cases').iterdir()):
        ref = remote_check/'reference'/directory.name
        if grade_case(directory/'problem.json',ref/'reference.h5',ref/'grading.json')['status']!='accepted':
            raise ValueError('Remote case failed grading')
    report.update(status='trial_cases_uploaded_and_verified',cases=len(report['records']),
                  pool_revision=uploaded['revision'],uploaded_files=uploaded['uploaded_files'],
                  maximum_reference_implementation_difference=max(reference_errors),
                  elapsed_seconds=time.monotonic()-started)
    # Publish only author reports/contracts here; data_pool owns pool uploads.
    artifacts = Path('/tmp/transport-reports');artifacts.mkdir()
    pool.write_json(artifacts/'report.json',report)
    shutil.copyfile(bundle/'selection.json',artifacts/'validation-selection.json')
    shutil.copyfile(task/'instruction.md',artifacts/'instruction.md')
    shutil.copyfile(task/'DATA.md',artifacts/'DATA.md')
    api = HfApi()
    commit = api.upload_folder(repo_id=args.repo_id,repo_type='dataset',revision=args.revision,
                              folder_path=artifacts,path_in_repo=args.prefix,
                              commit_message='Record independently defined transport trial and pool validation')
    print(json.dumps({'status':report['status'],'cases':report['cases'],'pool_revision':uploaded['revision'],
                      'report_revision':commit.oid,'elapsed_seconds':report['elapsed_seconds']}),flush=True)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
