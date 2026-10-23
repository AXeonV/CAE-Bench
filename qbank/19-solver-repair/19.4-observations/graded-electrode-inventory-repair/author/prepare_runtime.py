"""Prepare pinned real PyBaMM source and minimal inventory repair images."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import urllib.request
TASK=Path(__file__).resolve().parents[1]
COMMITS={'base':'07d642caa864aecb5032d241cd70e3f36958535e','fixed':'bd572504ebf6619e14d4e0f26d4809ee407fd685'}
HASHES={'base':'74950ed6b598c219dbc266e6cee8203a44a2af199f1d0700ccb8b8cada0f0441','fixed':'d2e146e1e80ff02cdacb73a633ec30c64f0ff667224a71f5c3e244fb3a9f8e88'}
SUBDIR=Path('packages/pybamm/src/pybamm/expression_tree')


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(work,wheel_dir):
    spec=importlib.util.spec_from_file_location('pybamm_archive_verifier',TASK.parent/'diffusion-element-heat-repair/author/prepare_runtime.py')
    verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)
    evidence={'repository':'https://github.com/pybamm-team/PyBaMM','issue':'https://github.com/pybamm-team/PyBaMM/issues/5810','pull':'https://github.com/pybamm-team/PyBaMM/pull/5813','archives':{}}
    work.mkdir(parents=True,exist_ok=True)
    for kind,commit in COMMITS.items():
        archive=work/(kind+'.tar.gz');url=f'https://codeload.github.com/pybamm-team/PyBaMM/tar.gz/{commit}'
        if not archive.exists():urllib.request.urlretrieve(url,archive)
        if digest(archive)!=HASHES[kind]:raise ValueError('Pinned archive hash mismatch: '+kind)
        root=work/kind
        if not root.exists():
            root.mkdir()
            with tarfile.open(archive) as source:
                prefix=source.getmembers()[0].name+'/'
                for member in source.getmembers():
                    if member.name.startswith(prefix) and member.isfile():
                        member.name=member.name[len(prefix):]
                        source.extract(member,root,filter='data')
        evidence['archives'][kind]={'commit':commit,'url':url,'sha256':digest(archive),'tree_manifest_sha256':verifier.verify_tree(archive,root)}
    context=work/'context';context.mkdir(exist_ok=True)
    if not (context/'source').exists():shutil.copytree(work/'base',context/'source')
    verifier.verify_tree(work/'base.tar.gz',context/'source')
    for origin,name in [(TASK/'author/runtime.Dockerfile','Dockerfile'),(TASK/'public/CMakeLists.txt','CMakeLists.txt'),(TASK/'public/driver.py','driver.py')]:shutil.copyfile(origin,context/name)
    wheels=context/'build-wheels';wheels.mkdir(exist_ok=True)
    expected=json.loads((TASK/'author/data-evidence/build-wheels.json').read_text('utf-8'))['wheels']
    for item in expected:
        origin=wheel_dir/item['file']
        if not origin.exists() or digest(origin)!=item['sha256']:raise ValueError('Missing or changed wheel '+item['file'])
        shutil.copyfile(origin,wheels/origin.name)
    original=(work/'base'/SUBDIR/'averages.py').read_text('utf-8');fixed=(work/'fixed'/SUBDIR/'averages.py').read_text('utf-8')
    def section(text):
        start=text.index('def _is_independent_of(');end=text.index('\n\nclass _BaseAverage',start);return start,end
    start,end=section(original);first,last=section(fixed)
    minimal=original[:start]+fixed[first:last]+original[end:]
    oracle=TASK/'author/generated';oracle.mkdir(exist_ok=True);(oracle/'averages.py').write_text(minimal,encoding='utf-8',newline='\n')
    evidence['applied_fix']={'path':str(SUBDIR/'averages.py'),'subset':'Only _is_independent_of function; division rules remain baseline','sha256':digest(oracle/'averages.py')}
    reference=work/'reference-context';reference.mkdir(exist_ok=True);shutil.copyfile(oracle/'averages.py',reference/'averages.py')
    (reference/'Dockerfile').write_text('FROM caeoj-pybamm5813-core:base\nCOPY averages.py /opt/pybamm-build/source/'+SUBDIR.as_posix()+'/averages.py\nRUN rm -f /opt/pybamm-build/source/'+SUBDIR.as_posix()+'/__pycache__/averages.cpython-314.pyc && cmake --build /opt/pybamm-build --target repair_sources\n',encoding='utf-8')
    shutil.copyfile(work/'base.tar.gz',TASK/'public/pybamm-source.tar.gz')
    (TASK/'public-materials.json').write_text(json.dumps({'version':1,'files':[{'path':'public/'+p.name,'sha256':digest(p)} for p in sorted((TASK/'public').iterdir()) if p.is_file()]},indent=2)+'\n',encoding='utf-8')
    evidence['version_metadata_note']='Archive installation reports0.0.0; identity is pinned by commit, archive, and source manifest.'
    (TASK/'author/data-evidence/source.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    return context,reference


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--work',type=Path,required=True);parser.add_argument('--wheel-dir',type=Path,required=True);parser.add_argument('--build',action='store_true');parser.add_argument('--docker',default='docker');args=parser.parse_args()
    context,reference=prepare(args.work,args.wheel_dir)
    if args.build:
        subprocess.run([args.docker,'build','--network','none','-t','caeoj-pybamm5813-core:base',str(context)],check=True)
        subprocess.run([args.docker,'build','--network','none','-t','caeoj-pybamm5813-reference:fixed',str(reference)],check=True)
