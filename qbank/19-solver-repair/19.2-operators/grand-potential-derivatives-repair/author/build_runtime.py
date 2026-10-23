"""Reproduce the genuine native base only on request; reuse its verified image otherwise."""
import argparse
import hashlib
import json
import shutil
import subprocess
import tarfile
from pathlib import Path

TASK=Path(__file__).resolve().parents[1]
DOCKER='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
NATIVE='caeoj-moose30236-prototype:base'
VERIFIED_NATIVE_ID='sha256:43029e45ecef50feb876bdb4897868cf36a88440eef5eeb8646c5d6fe324250e'


def inspect(image):
    return json.loads(subprocess.check_output([DOCKER,'image','inspect',image]))[0]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--dependencies',type=Path,required=True)
    parser.add_argument('--rebuild-native',action='store_true')
    args=parser.parse_args();args.work.mkdir(parents=True,exist_ok=False)
    if args.rebuild_native:
        native=args.work/'native';native.mkdir();source=native/'baseline-source';source.mkdir()
        closure=TASK/'public/moose-source.tar.gz'
        expected=json.loads((TASK/'author/data-evidence/source-closure.json').read_text())['closure_sha256']
        if hashlib.sha256(closure.read_bytes()).hexdigest()!=expected:raise ValueError('Changed source closure')
        with tarfile.open(closure) as archive:archive.extractall(source,filter='data')
        shutil.copyfile(TASK/'author/native-base.Dockerfile',native/'Dockerfile')
        subprocess.run([DOCKER,'build','--pull=false','--progress','plain','-t',NATIVE,str(native)],check=True)
    elif inspect(NATIVE)['Id']!=VERIFIED_NATIVE_ID:
        raise ValueError('Cached native base differs from actual verified build; explicitly reproduce and audit instead')
    context=args.work/'runtime';context.mkdir()
    shutil.copytree(TASK/'public',context/'driver',ignore=shutil.ignore_patterns('*.tar.gz','__pycache__'))
    dependencies=[]
    for group in ['wheels','rpms']:
        shutil.copytree(args.dependencies/group,context/group)
        dependencies.extend({'path':str(p.relative_to(args.dependencies)).replace('\\','/'),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted((args.dependencies/group).glob('*')) if p.is_file())
    shutil.copyfile(TASK/'author/runtime.Dockerfile',context/'Dockerfile')
    subprocess.run([DOCKER,'build','--pull=false','--progress','plain','-t','caeoj-moose30236-runtime:base',str(context)],check=True)
    record={'runtime_image_id':inspect('caeoj-moose30236-runtime:base')['Id'],'native_image_id':inspect(NATIVE)['Id'],
            'dockerfile_sha256':hashlib.sha256((context/'Dockerfile').read_bytes()).hexdigest(),'dependencies':dependencies}
    (TASK/'author/data-evidence/runtime.json').write_text(json.dumps(record,indent=2)+'\n',newline='\n')


if __name__=='__main__':main()
