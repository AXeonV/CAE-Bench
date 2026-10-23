"""Build the genuine two-material OpenSees kernel without interpreter factories."""
import argparse,json,shutil,subprocess,tarfile
from pathlib import Path
TASK=Path(__file__).resolve().parents[1]
DOCKER='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);p.add_argument('--offline-wheels',type=Path,required=True);p.add_argument('--image',default='caeoj-opensees1817-runtime:base');args=p.parse_args()
    args.work.mkdir(parents=True,exist_ok=False)
    source=args.work/'source';source.mkdir()
    with tarfile.open(TASK/'public/opensees-source.tar.gz') as tar:tar.extractall(source,filter='data')
    shutil.copytree(TASK/'public',args.work/'driver',ignore=shutil.ignore_patterns('*.tar.gz','__pycache__'))
    shutil.copyfile(TASK/'author/runtime.Dockerfile',args.work/'Dockerfile')
    shutil.copytree(args.offline_wheels,args.work/'offline-wheels')
    subprocess.run([DOCKER,'build','--pull=false','--progress','plain','-t',args.image,str(args.work)],check=True)
    image=json.loads(subprocess.check_output([DOCKER,'image','inspect',args.image]))[0]
    (TASK/'author/data-evidence/runtime.json').write_text(json.dumps({'image_id':image['Id'],'dockerfile':'author/runtime.Dockerfile','compiler':'GCC 14.2.0','source':'public/opensees-source.tar.gz'},indent=2)+'\n')
