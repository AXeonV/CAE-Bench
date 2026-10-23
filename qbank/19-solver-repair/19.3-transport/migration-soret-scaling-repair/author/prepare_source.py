"""Fetch fixed real source and replay the complete upstream two-hunk module patch."""
import argparse,hashlib,json,re,tarfile,urllib.request
from pathlib import Path
TASK=Path(__file__).resolve().parents[1]
ROOT=TASK.parents[3]
WORK=ROOT/'work/repair-22/elmer-870'
BASE='a3f108c8580efd649e84b35842cd92a06c834331'
HEAD='cd35f9d23145519973ed66c62661a0298105bf3a'
SOURCE=WORK/('elmerfem-'+BASE)
FILE='fem/src/modules/AdvectionDiffusion.F90'
ARCHIVE_SHA='4808a614f170e848180afaf9f75bda5ffd586b9be11b67b75c3c14782190ebfe'
FIXED_SHA='0f905d9e75ba747c546c849ad381883c8447c0c3a721fbf8ac282253bdd58dad'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def apply_patch(original,patch):
 lines=original.decode('utf-8').splitlines(True);patch=patch.splitlines();out=[];cursor=i=0
 while i<len(patch):
  if not patch[i].startswith('@@'):i+=1;continue
  m=re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))?',patch[i]);start=int(m.group(1))-1
  out+=lines[cursor:start];cursor=start;i+=1
  while i<len(patch) and not patch[i].startswith('@@'):
   row=patch[i];prefix=row[:1];value=row[1:]+'\n'
   if prefix in (' ','-'):
    if lines[cursor]!=value:raise ValueError('Upstream patch context mismatch')
    cursor+=1
   if prefix in (' ','+'):out.append(value)
   i+=1
 out+=lines[cursor:];return ''.join(out).encode('utf-8')
def main():
 p=argparse.ArgumentParser();p.add_argument('--proxy');a=p.parse_args();WORK.mkdir(parents=True,exist_ok=True)
 opener=urllib.request.build_opener(urllib.request.ProxyHandler({'https':a.proxy}) if a.proxy else urllib.request.ProxyHandler())
 def fetch(url,path):
  if not path.exists():
   with opener.open(url,timeout=180) as response:path.write_bytes(response.read())
 archive=WORK/'baseline.tar.gz';fetch('https://codeload.github.com/ElmerCSC/elmerfem/tar.gz/'+BASE,archive)
 if digest(archive)!=ARCHIVE_SHA:raise ValueError('Fixed source archive SHA mismatch')
 if not SOURCE.exists():
  with tarfile.open(archive) as t:t.extractall(WORK,filter='data')
 head=WORK/'upstream-head.F90';fetch('https://raw.githubusercontent.com/ElmerCSC/elmerfem/'+HEAD+'/'+FILE,head)
 fixed=apply_patch((SOURCE/FILE).read_bytes(),(TASK/'author/data-evidence/upstream.patch').read_text())
 if hashlib.sha256(fixed).hexdigest()!=FIXED_SHA or fixed!=head.read_bytes():raise ValueError('Mechanical complete upstream patch differs from actual pinned head')
 d=TASK/'author/generated';d.mkdir(exist_ok=True);(d/'AdvectionDiffusion.F90').write_bytes(fixed)
 record={'repository':'https://github.com/ElmerCSC/elmerfem','issue':870,'pull_request':872,'baseline':BASE,'head':HEAD,'merge':'15e4d8ff4e4340dab8707228e4a421b81c217c8e','archive_sha256':ARCHIVE_SHA,'source_file':FILE,'baseline_module_sha256':digest(SOURCE/FILE),'fixed_module_sha256':FIXED_SHA,'mechanical_patch_equals_actual_pinned_head':True,'head_git_blob_sha1':hashlib.sha1(f'blob {len(fixed)}\0'.encode()+fixed).hexdigest(),'patch_scope':'Both density corrections in the one true module; complete upstream code changes, tests excluded, no author source supplement.','corrections':'Source issue follow-up corrected scheme-dependent error numbers, temperature keyword spelling, old Ion Charge=z/rho workaround and Soret sign notes. References use independent closed forms and actual nodal output.'}
 (TASK/'author/data-evidence/source.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
if __name__=='__main__':main()
