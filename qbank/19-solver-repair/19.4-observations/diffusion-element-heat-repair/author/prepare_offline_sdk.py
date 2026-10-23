"""Reuse a local SDK dependency image when package indexes are unreachable.

Only installed dependencies are copied from that image, never its private tests,
reference data, submission, logs, or source tree. Build tools are pure Python
distributions repacked with the standard wheel tool and recorded by digest.
"""
import argparse
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys

TASK=Path(__file__).resolve().parents[1]


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--build-tools-site',type=Path,required=True)
    parser.add_argument('--sdk-image',required=True)
    parser.add_argument('--docker',default='docker')
    args=parser.parse_args()
    work=args.work
    work.mkdir(parents=True,exist_ok=True)
    report={'method':'offline SDK dependency cache, not a physics reference producer','packages':{}}
    for package in ['setuptools','wheel']:
        dist=next(d for d in metadata.distributions(path=[str(args.build_tools_site)])
                  if d.metadata['Name'].lower()==package)
        stage=work/('repack-'+package)
        if stage.exists():
            raise ValueError('Use an empty work directory; preserve previous repack evidence')
        stage.mkdir()
        wheel_metadata=dist.read_text('WHEEL')
        if 'Tag: py3-none-any' not in wheel_metadata:
            raise ValueError('Only platform-independent build tool distributions may be repacked')
        for file in dist.files:
            if '..' in file.parts or '__pycache__' in file.parts or str(file).endswith('.pyc'):
                continue
            source=args.build_tools_site/file
            if source.is_file():
                target=stage/file
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(source,target)
        wheels=work/'wheels'
        wheels.mkdir(exist_ok=True)
        subprocess.run([sys.executable,'-m','wheel','pack',str(stage),'--dest-dir',str(wheels)],check=True)
        report['packages'][package]={'version':dist.version,'origin':'installed pure Python distribution; repacked, not downloaded wheel bytes'}
    shutil.copyfile(TASK/'public/driver.py',work/'driver.py')
    sdk=json.loads(subprocess.check_output([args.docker,'image','inspect',args.sdk_image]))[0]['Id']
    alias='caeoj-sdk-dependencies:'+sdk.split(':')[-1][:16]
    subprocess.run([args.docker,'tag',sdk,alias],check=True)
    report['sdk_cache_image_id']=sdk
    report['solver_base_image_id']=json.loads(subprocess.check_output([args.docker,'image','inspect','caeoj-pybamm5859-core:base']))[0]['Id']
    report['wheels_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in wheels.glob('*.whl')}
    (work/'Dockerfile').write_text('''ARG SDK_IMAGE
FROM ${SDK_IMAGE} AS sdk
FROM caeoj-pybamm5859-core:base
COPY --from=sdk /usr/local/lib/python3.14/site-packages/ /usr/local/lib/python3.14/site-packages/
COPY --from=sdk /usr/local/lib/libgmsh.so.4.15 /usr/local/lib/libgmsh.so.4.15
COPY wheels /opt/offline-wheels
COPY driver.py /opt/repair-driver/driver.py
ENV PIP_NO_INDEX=1 PIP_FIND_LINKS=/opt/offline-wheels
RUN python -c "import pybamm, numpy, h5py, jsonschema, gmsh; assert hasattr(gmsh.lib, 'gmshInitialize'); print(pybamm.__file__, numpy.__version__)"
''',encoding='utf-8')
    subprocess.run([args.docker,'build','--pull=false','--progress','plain','--build-arg','SDK_IMAGE='+alias,
                    '-t','caeoj-pybamm5859-core:offline-sdk',str(work)],check=True)
    report['result_image_id']=json.loads(subprocess.check_output([args.docker,'image','inspect','caeoj-pybamm5859-core:offline-sdk']))[0]['Id']
    (TASK/'author/data-evidence/offline-sdk.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
