"""Reproduce pinned native dependencies/build only on explicit request; otherwise verify cached native identity."""
import argparse,hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
TASK=Path(__file__).resolve().parents[1];DOCKER='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
NATIVE='caeoj-moose22074-prototype:pinned2022';NATIVE_ID='sha256:19dace486df01a36eb210364d76469885a45fead71ee5f390439be0df8a7f2ff'
def inspect(name):return json.loads(subprocess.check_output([DOCKER,'image','inspect',name]))[0]['Id']
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--work',type=Path,required=True);ap.add_argument('--dependencies',type=Path,required=True,help='Verified old-deps archive directory with all pinned dependency tarballs');ap.add_argument('--rpms',type=Path,required=True);ap.add_argument('--rebuild-native',action='store_true');args=ap.parse_args();args.work.mkdir(parents=True,exist_ok=False)
 if args.rebuild_native:
  dep=args.work/'dependencies';dep.mkdir()
  for item in json.loads((TASK/'author/data-evidence/pinned-dependency-archives.json').read_text()):
   path=args.dependencies/(item['label']+'.tar.gz');assert hashlib.file_digest(path.open('rb'),'sha256').hexdigest()==item['sha256'];shutil.copyfile(path,dep/path.name)
  shutil.copyfile(TASK/'author/dependencies.Dockerfile',dep/'Dockerfile');subprocess.run([DOCKER,'build','--pull=false','--progress=plain','-t','caeoj-moose22074-dependencies:pinned2022',str(dep)],check=True)
  native=args.work/'native';(native/'baseline-source').mkdir(parents=True);closure=TASK/'public/moose-source.tar.gz';assert hashlib.file_digest(closure.open('rb'),'sha256').hexdigest()==json.loads((TASK/'author/data-evidence/source-closure.json').read_text())['closure_sha256']
  with tarfile.open(closure) as archive:archive.extractall(native/'baseline-source',filter='data')
  shutil.copyfile(TASK/'author/native-base.Dockerfile',native/'Dockerfile');subprocess.run([DOCKER,'build','--pull=false','--progress=plain','-t',NATIVE,str(native)],check=True)
 else:assert inspect(NATIVE)==NATIVE_ID
 expected=json.loads((TASK/'author/data-evidence/runtime-images.json').read_text())['images']['caeoj-moose30236-runtime:base'];assert inspect('caeoj-moose30236-runtime:base')==expected
 ctx=args.work/'runtime';(ctx/'driver').mkdir(parents=True);shutil.copyfile(TASK/'author/CMakeLists.txt',ctx/'driver/CMakeLists.txt');shutil.copytree(args.rpms,ctx/'rpms');shutil.copyfile(TASK/'author/runtime.Dockerfile',ctx/'Dockerfile');subprocess.run([DOCKER,'build','--network=none','--pull=false','--progress=plain','-t','caeoj-moose22074-runtime:base',str(ctx)],check=True)
 print(json.dumps({'runtime_image_id':inspect('caeoj-moose22074-runtime:base'),'native_image_id':inspect(NATIVE)}))
if __name__=='__main__':main()
