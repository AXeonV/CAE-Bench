"""Build pinned actual preCICE, then trusted single-TU repair and minimal reference images."""
import argparse,json,shutil,subprocess
from pathlib import Path
from prepare_source import prepare,TASK

REBUILD=[
 '/opt/precice-repair-build/CMakeFiles/precice_repair.dir/opt/precice-upstream/precice-c2a06a65631e15a6622f5ecffae194f82ba0bae3/src/query/Index.cpp.o',
 '/opt/precice-repair-build/lib/libprecice.so.2.5.0',
 '/opt/precice-repair-build/CMakeFiles/projection_driver.dir/opt/precice-driver/driver.cpp.o',
 '/opt/precice-repair-build/bin/projection-driver']

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--work',required=True,type=Path);parser.add_argument('--proxy');parser.add_argument('--docker',default='docker');parser.add_argument('--build',action='store_true');parser.add_argument('--rebuild-upstream',action='store_true');args=parser.parse_args()
    root=prepare(args.work,args.proxy)
    upstream=args.work/'upstream-context';upstream.mkdir(exist_ok=True)
    shutil.copyfile(TASK/'author/upstream.Dockerfile',upstream/'Dockerfile');shutil.copyfile(args.work/'source.tar.gz',upstream/'source.tar.gz')
    runtime=args.work/'runtime-context';runtime.mkdir(exist_ok=True)
    for src,dst in [('author/runtime.Dockerfile','Dockerfile'),('public/driver.cpp','driver.cpp'),('public/CMakeLists.txt','CMakeLists.txt')]:shutil.copyfile(TASK/src,runtime/dst)
    reference=args.work/'reference-context';reference.mkdir(exist_ok=True);shutil.copyfile(TASK/'author/generated/Index.cpp',reference/'Index.cpp')
    target='/opt/precice-upstream/precice-c2a06a65631e15a6622f5ecffae194f82ba0bae3/src/query/Index.cpp'
    dockerfile='FROM caeoj-precice1304-core:base\nCOPY Index.cpp '+target+'\nRUN rm -f '+' '.join(REBUILD)+' && cmake --build /opt/precice-repair-build --target repair_sources --parallel 2\n'
    (reference/'Dockerfile').write_bytes(dockerfile.encode())
    if args.build:
        image='caeoj-precice1304-prototype:base'
        exists=subprocess.run([args.docker,'image','inspect',image],capture_output=True).returncode==0
        if not exists or args.rebuild_upstream:
            subprocess.run([args.docker,'build','-t',image,str(upstream)],check=True)
        import hashlib
        expected=json.loads((TASK/'author/data-evidence/source.json').read_text())['tree_manifest_sha256']
        code="from pathlib import Path;import json,hashlib;p=Path('/opt/precice-upstream/precice-c2a06a65631e15a6622f5ecffae194f82ba0bae3');d={q.relative_to(p).as_posix():hashlib.sha256(q.read_bytes()).hexdigest() for q in p.rglob('*') if q.is_file()};print(hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest())"
        actual=subprocess.check_output([args.docker,'run','--rm','--network','none',image,'python','-c',code],text=True).strip()
        if actual!=expected:raise ValueError('Cached upstream image source is not pristine pinned archive')
        for image,context in [('caeoj-precice1304-core:base',runtime),('caeoj-precice1304-reference:fixed',reference)]:
            subprocess.run([args.docker,'build','-t',image,str(context)],check=True)
