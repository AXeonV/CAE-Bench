"""Prepare pinned real PyBaMM source and minimal hysteresis heat repair images."""
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
COMMITS={'base':'273ccd4ec832efd9d5d783aa51a4421a4d8f70e4','fixed':'f04a1f8ed421fc4653071eaa089be9b85b0855de'}
HASHES={'base':'e1444287230c5c7536fddfb527faf73e21a56095d0582afd981b6d835713345f','fixed':'e861e5627d082eb076d11e498ae73810b85b1486f1858f6dcc8c01e1f33926ef'}
SUBDIR=Path('src/pybamm/models/submodels/thermal')


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(work):
    spec=importlib.util.spec_from_file_location('pybamm_archive_verifier',TASK.parent/'diffusion-element-heat-repair/author/prepare_runtime.py')
    verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)
    evidence={'repository':'https://github.com/pybamm-team/PyBaMM','issue':'https://github.com/pybamm-team/PyBaMM/issues/3867','pull':'https://github.com/pybamm-team/PyBaMM/pull/4893','archives':{}}
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
    oracle=TASK/'author/generated';oracle.mkdir(exist_ok=True)
    shutil.copyfile(work/'fixed'/SUBDIR/'base_thermal.py',oracle/'base_thermal.py')
    evidence['applied_fix']={'path':str(SUBDIR/'base_thermal.py'),'subset':'Only the real thermal/base_thermal.py; no OCP state or parameter API changes','sha256':digest(oracle/'base_thermal.py')}
    reference=work/'reference-context';reference.mkdir(exist_ok=True);shutil.copyfile(oracle/'base_thermal.py',reference/'base_thermal.py')
    (reference/'Dockerfile').write_text('FROM caeoj-pybamm3867-core:base\nCOPY base_thermal.py /opt/pybamm-build/source/'+SUBDIR.as_posix()+'/base_thermal.py\nRUN rm -f /opt/pybamm-build/source/'+SUBDIR.as_posix()+'/__pycache__/base_thermal.cpython-311.pyc && cmake --build /opt/pybamm-build --target repair_sources\n',encoding='utf-8')
    shutil.copyfile(work/'base.tar.gz',TASK/'public/pybamm-source.tar.gz')
    (TASK/'public-materials.json').write_text(json.dumps({'version':1,'files':[{'path':'public/'+p.name,'sha256':digest(p)} for p in sorted((TASK/'public').iterdir()) if p.is_file()]},indent=2)+'\n',encoding='utf-8')
    evidence['version_metadata_note']='Archive installation reports0.0.0; identity is pinned by commit, archive, and source manifest.'
    (TASK/'author/data-evidence/source.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    return context,reference


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--work',type=Path,required=True);parser.add_argument('--build',action='store_true');parser.add_argument('--docker',default='docker');args=parser.parse_args()
    context,reference=prepare(args.work)
    if args.build:
        subprocess.run([args.docker,'build','-t','caeoj-pybamm3867-core:base',str(context)],check=True)
        subprocess.run([args.docker,'build','--network','none','-t','caeoj-pybamm3867-reference:fixed',str(reference)],check=True)
