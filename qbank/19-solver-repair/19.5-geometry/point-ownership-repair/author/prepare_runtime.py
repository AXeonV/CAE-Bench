"""Build actual full DOLFINx, determine true header closure and prepare repair images."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
from prepare_source import prepare,TASK,BASE

def build(args):
    prepare(args.work,args.proxy)
    upstream=args.work/'upstream-context';upstream.mkdir(exist_ok=True)
    for src,dst in [('author/upstream.Dockerfile','Dockerfile'),('author/SCOTCHConfig.cmake','SCOTCHConfig.cmake'),
      ('author/SCOTCHConfigVersion.cmake','SCOTCHConfigVersion.cmake')]:shutil.copyfile(TASK/src,upstream/dst)
    for src,dst in [('dolfinx.tar.gz','baseline.tar.gz'),('basix.tar.gz','basix.tar.gz'),('ffcx.tar.gz','ffcx.tar.gz')]:
        shutil.copyfile(args.work/src,upstream/dst)
    wrapper=args.work/'wrapper-context';wrapper.mkdir(exist_ok=True)
    for src,dst in [('author/wrapper.Dockerfile','Dockerfile'),('public/driver.cpp','driver.cpp'),('public/CMakeLists.txt','CMakeLists.txt')]:
        shutil.copyfile(TASK/src,wrapper/dst)
    runtime=args.work/'runtime-context';runtime.mkdir(exist_ok=True)
    shutil.copyfile(TASK/'author/runtime.Dockerfile',runtime/'Dockerfile')
    exists=subprocess.run([args.docker,'image','inspect','caeoj-dolfinx4450-prototype:base'],capture_output=True).returncode==0
    if not exists or args.rebuild_upstream:
        subprocess.run([args.docker,'build','-t','caeoj-dolfinx4450-prototype:base',str(upstream)],check=True)
    evidence=json.loads((TASK/'author/data-evidence/source.json').read_text())
    for record in evidence['sources']:
        name=record['repository'].rsplit('/',1)[1]+'-'+record['commit']
        code="from pathlib import Path;import json,hashlib;p=Path('/opt/upstream/"+name+"');d={q.relative_to(p).as_posix():hashlib.sha256(q.read_bytes()).hexdigest() for q in p.rglob('*') if q.is_file()};print(hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest())"
        actual=subprocess.check_output([args.docker,'run','--rm','--network','none','caeoj-dolfinx4450-prototype:base','python','-c',code],text=True).strip()
        if actual!=record['tree_manifest_sha256']:raise ValueError('Cached upstream image source is not pristine: '+name)
    for image,context in [('caeoj-dolfinx4450-wrapper:base',wrapper),('caeoj-dolfinx4450-core:base',runtime)]:
        subprocess.run([args.docker,'build','-t',image,str(context)],check=True)
    header='/opt/upstream/dolfinx-'+BASE+'/cpp/dolfinx/geometry/utils.h'
    directory='/opt/dolfinx-repair-build'
    code="""import subprocess,json
from pathlib import Path
root=Path(DIRECTORY);header=HEADER;current=None;closure=[]
for line in subprocess.check_output(['ninja','-C',str(root),'-t','deps'],text=True).splitlines():
 if line and not line.startswith(' '):current=line.split(': #deps',1)[0]
 elif line.strip()==header:
  path=root/current;assert path.is_file() and path.suffix=='.o';closure.append(str(path))
assert len(closure)>=7
closure+= [str(root/'lib/libdolfinx.so.0.12.0.0'),str(root/'bin/ownership_driver')]
assert all(Path(p).is_file() for p in closure)
print(json.dumps(closure))
""".replace('DIRECTORY',repr(directory)).replace('HEADER',repr(header))
    closure=json.loads(subprocess.check_output([args.docker,'run','--rm','--network','none','caeoj-dolfinx4450-core:base','python','-c',code],text=True))
    (TASK/'author/data-evidence/header-closure.json').write_text(json.dumps({'header':header,'rebuild_files':closure},indent=2)+'\n')
    reference=args.work/'reference-context';reference.mkdir(exist_ok=True)
    shutil.copyfile(TASK/'author/generated/utils.h',reference/'utils.h')
    dockerfile='FROM caeoj-dolfinx4450-core:base\nCOPY utils.h '+header+'\nRUN rm -f '+' '.join(closure)+' && cmake --build '+directory+' --target repair_sources --parallel 4\n'
    (reference/'Dockerfile').write_bytes(dockerfile.encode())
    subprocess.run([args.docker,'build','-t','caeoj-dolfinx4450-reference:fixed',str(reference)],check=True)
    return closure

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--proxy');parser.add_argument('--docker',default='docker');parser.add_argument('--rebuild-upstream',action='store_true')
    print(json.dumps(build(parser.parse_args()),indent=2))
