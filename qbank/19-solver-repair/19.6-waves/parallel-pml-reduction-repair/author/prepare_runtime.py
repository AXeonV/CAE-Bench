"""Reuse the completed real MPI build and install the standard task SDK assembly."""
import argparse,hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
from caeoj_tools.assembly import runtime_materials
TASK=Path(__file__).resolve().parents[1];ROOT=TASK.parents[3]
BASE='fa6e905bc5cd63487cc24f68233f5992830f8b6e';HEAD='4f4cd5f6acb0a77dcab4df113bd5f8838c4ec5c8'
ARCHIVE_SHA='3d3166ae70b4c34a34a39e3eafd6e447bd13b7b938b064090a96b4ff7930b198'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);p.add_argument('--build',action='store_true');a=p.parse_args()
    archive=TASK/'public/specfem-source.tar.gz'
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=ARCHIVE_SHA:raise ValueError('Pinned upstream source archive changed')
    tree={}
    with tarfile.open(archive) as tf:
        for member in tf:
            if member.isfile():tree[member.name.split('/',1)[1]]=hashlib.sha256(tf.extractfile(member).read()).hexdigest()
    fixed=(TASK/'author/generated/get_MPI.F90').read_bytes()
    if hashlib.sha1(b'blob '+str(len(fixed)).encode()+b'\0'+fixed).hexdigest()!='d843513239390f2bdc18046514b6d4efb2f36235':raise ValueError('PR660 replacement blob changed')
    evidence=TASK/'author/data-evidence';evidence.mkdir(exist_ok=True)
    (evidence/'source.json').write_text(json.dumps({'repository':'https://github.com/SPECFEM/specfem2d','issue':661,'pull_request':660,
        'baseline':BASE,'fixed':HEAD,'source_archive_sha256':ARCHIVE_SHA,'archive_regular_files':len(tree),
        'reference_replacement':'src/specfem2D/get_MPI.F90','replacement_git_blob':'d843513239390f2bdc18046514b6d4efb2f36235',
        'excluded_upstream_file':'src/specfem2D/setup_sources_receivers.F90','excluded_reason':'receiver debug output and serial unused-variable declaration; actual solver successfully runs without it'},indent=2))
    (evidence/'baseline-tree.json').write_text(json.dumps(tree,sort_keys=True,indent=2))
    context=a.work/'runtime-context';context.mkdir(parents=True,exist_ok=True)
    files,meta=runtime_materials({TASK.name:TASK},ROOT)
    for name,data in files.items():
        path=context/'sdk'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    shutil.copyfile(TASK/'public/CMakeLists.txt',context/'CMakeLists.txt')
    shutil.copyfile(TASK/'author/baseline_health.py',context/'baseline_health.py')
    dockerfile='''FROM caeoj-specfem661-prototype:mpi
RUN mkdir -p /opt/specfem-repair-build && mv /opt/specfem /opt/specfem-repair-build/upstream
COPY CMakeLists.txt /opt/specfem-cmake/CMakeLists.txt
COPY baseline_health.py /opt/specfem-baseline-health.py
RUN cmake -S /opt/specfem-cmake -B /opt/specfem-repair-build && cmake --build /opt/specfem-repair-build --target repair_sources
COPY sdk /opt/specfem-sdk
RUN python -m pip install --no-deps /opt/specfem-sdk && chmod -R go-w /opt/specfem-repair-build /opt/specfem-cmake /opt/specfem-sdk
WORKDIR /app
'''
    (context/'Dockerfile').write_bytes(dockerfile.encode())
    if a.build:subprocess.run(['docker','build','-t','caeoj-specfem661-runtime:base',str(context)],check=True)
    rebuild=['/opt/specfem-repair-build/upstream/obj/get_MPI.spec.o','/opt/specfem-repair-build/upstream/bin/xspecfem2D']
    runner='/app/qbank/19-solver-repair/19.6-waves/parallel-pml-reduction-repair/public/run_case.py'
    config={'version':1,'base_image':'caeoj-specfem661-runtime:base','replacements':[{'submission':'get_MPI.F90','target':'/opt/specfem-repair-build/upstream/src/specfem2D/get_MPI.F90'}],
        'build_directory':'/opt/specfem-repair-build','build_target':'repair_sources','rebuild_files':rebuild,'baseline_timeout_seconds':120,
        'build_timeout_seconds':120,'max_source_bytes':1048576,'runner':runner,'baseline_probe':['/usr/local/bin/python','/opt/specfem-baseline-health.py']}
    (TASK/'harbor/source-repair.json').write_text(json.dumps(config,indent=2))
    ref=a.work/'reference-context';ref.mkdir(exist_ok=True);shutil.copyfile(TASK/'author/generated/get_MPI.F90',ref/'get_MPI.F90')
    (ref/'Dockerfile').write_bytes(('FROM caeoj-specfem661-runtime:base\nCOPY get_MPI.F90 /opt/specfem-repair-build/upstream/src/specfem2D/get_MPI.F90\nRUN rm -f '+' '.join(rebuild)+' && cmake --build /opt/specfem-repair-build --target repair_sources\n').encode())
    if a.build:subprocess.run(['docker','build','-t','caeoj-specfem661-reference:production',str(ref)],check=True)
    print(meta['id'])
