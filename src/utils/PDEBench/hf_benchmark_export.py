# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["huggingface_hub>=1.0,<2", "numpy>=2,<3", "h5py>=3.13,<4", "gmsh==4.15.2", "jsonschema==4.26.0"]
# ///
"""Extract explicitly selected migrated cases in HF; return only a small ZIP."""
import argparse,base64,hashlib,io,json,os,signal,subprocess,sys,zipfile
from pathlib import Path

RUNTIME_ZIP = ''
EXPORT_PLAN = ''


def main():
    parser=argparse.ArgumentParser()
    for key in ('repo-id','revision','prefix','source-revision','source-prefix'):
        parser.add_argument('--'+key,required=True)
    args=parser.parse_args()
    if not os.environ.get('JOB_ID') or not RUNTIME_ZIP or not EXPORT_PLAN:
        parser.error('Budgeted HF-only export required')
    signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(TimeoutError('Export deadline')))
    signal.alarm(480)
    runtime=Path('/tmp/export-runtime');runtime.mkdir()
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(RUNTIME_ZIP))) as archive:
        for entry in archive.infolist():
            if not (runtime/entry.filename).resolve().is_relative_to(runtime):raise ValueError('Unsafe runtime')
        archive.extractall(runtime)
    libraries=json.loads((runtime/'support/gmsh-system-packages.json').read_text())
    subprocess.run(['apt-get','update','-qq'],check=True,timeout=120)
    subprocess.run(['apt-get','install','-y','-qq','--no-install-recommends',*libraries],check=True,timeout=120)
    subprocess.run(['uv','pip','install','--python',sys.executable,'--no-deps',str(runtime)],check=True,timeout=120)
    from caeoj_tools import data_pool as pool
    from huggingface_hub import HfApi,CommitOperationAdd
    plan=json.loads(base64.b64decode(EXPORT_PLAN));root=Path('/tmp/exported-cases');root.mkdir()
    if set(plan)!={'advection','burgers','compressible'} or any(len(v['cases'])!=3 or v['samples'] for v in plan.values()):
        raise ValueError('Export exactly nine selected cases')
    for family,choice in plan.items():
        target=root/family
        pool.write_json(target/'data-manifest.json',choice)
        pool.assemble(target,choice,pool.HubStore(args.repo_id,args.source_revision,cache_dir='/tmp/export-cache'))
        pool.verify(target,strict=True)
    payload=Path('/tmp/nine-cases.zip')
    with zipfile.ZipFile(payload,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as archive:
        for path in sorted(root.rglob('*')):
            if path.is_file() and not any(x.startswith('.') for x in path.relative_to(root).parts):
                archive.write(path,path.relative_to(root).as_posix())
    report={'job_id':os.environ['JOB_ID'],'cases':9,'source_revision':args.source_revision,
        'plan_sha256':hashlib.sha256(base64.b64decode(EXPORT_PLAN)).hexdigest(),
        'zip_sha256':pool.digest(payload),'zip_bytes':payload.stat().st_size,
        'reference_recomputed':False,'formal_selection_changed':False}
    api=HfApi();head=api.repo_info(args.repo_id,repo_type='dataset',revision=args.revision).sha
    commit=api.create_commit(repo_id=args.repo_id,repo_type='dataset',revision=args.revision,parent_commit=head,
        operations=[CommitOperationAdd(path_in_repo=args.prefix+'/nine-cases.zip',path_or_fileobj=payload),
                    CommitOperationAdd(path_in_repo=args.prefix+'/report.json',path_or_fileobj=pool.encoded(report))],
        commit_message='Export nine explicitly selected migrated cases for local benchmark')
    print(json.dumps({**report,'revision':commit.oid}),flush=True)


if __name__=='__main__':main()
