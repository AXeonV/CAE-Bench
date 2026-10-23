"""Build an offline genuine Kratos core and seven-source beam component."""
import argparse,json,shutil,subprocess,tarfile
from pathlib import Path
TASK=Path(__file__).resolve().parents[1]
DOCKER='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);p.add_argument('--image',default='caeoj-kratos14657-runtime:base');args=p.parse_args()
    args.work.mkdir(parents=True,exist_ok=False)
    source=args.work/'source';source.mkdir()
    with tarfile.open(TASK/'public/kratos-source.tar.gz') as tar:tar.extractall(source,filter='data')
    shutil.copytree(TASK/'public',args.work/'driver',ignore=shutil.ignore_patterns('*.tar.gz','__pycache__'))
    shutil.copyfile(TASK/'author/runtime.Dockerfile',args.work/'Dockerfile')
    subprocess.run([DOCKER,'build','--pull=false','--progress','plain','-t',args.image,str(args.work)],check=True)
    image=json.loads(subprocess.check_output([DOCKER,'image','inspect',args.image]))[0]
    (TASK/'author/data-evidence/runtime.json').write_text(json.dumps({'image_id':image['Id'],'dockerfile':'author/runtime.Dockerfile','compiler':'Clang 19.1.7','source':'public/kratos-source.tar.gz'},indent=2)+'\n')
