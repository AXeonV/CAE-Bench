"""Verify the two real archives and extract only genuine upstream repair files."""
import argparse,hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
TASK=Path(__file__).resolve().parents[1]
BASE='ccb3c372dc34ca75ce01f99c2b50e0e89ad0a203'
HEAD='50118dbc8e54ac022e9e17400f43cc56e5bac560'
ARCHIVES={'source':('5474945f0aad427c203971cbbeea5294a4617f8b6f7e4a385b35f300c5b612d0',BASE),'fixed':('71c7fee994aca443f9e62a1d67b390300a2ba17058fbe4f62384a3b018b710f8',HEAD)}
REPLACEMENTS=['dft.cpp','fields.cpp','structure.cpp','meep.hpp']
def prepare(work,proxy=None):
 work=Path(work);work.mkdir(parents=True,exist_ok=True);trees={}
 for name,(sha,commit) in ARCHIVES.items():
  archive=work/(name+'.tar.gz')
  if not archive.exists():
   cmd=['curl','--fail','--silent','--show-error','--location','--retry','2','--max-time','180']
   if proxy:cmd+=['--proxy',proxy]
   subprocess.run(cmd+['https://codeload.github.com/NanoComp/meep/tar.gz/'+commit,'-o',str(archive)],check=True)
  if hashlib.sha256(archive.read_bytes()).hexdigest()!=sha:raise ValueError('Pinned archive changed')
  dest=work/name;root=dest/('meep-'+commit)
  with tarfile.open(archive) as tar:
   members={m.name.split('/',1)[1]:m for m in tar if m.isfile()}
   if not root.exists():tar.extractall(dest,filter='data')
   mapping={key:hashlib.sha256(tar.extractfile(member).read()).hexdigest() for key,member in members.items()}
  if any(not (root/n).is_file() or hashlib.sha256((root/n).read_bytes()).hexdigest()!=v for n,v in mapping.items()):raise ValueError('Source cache changed')
  trees[name]=mapping
 changed={n for n in trees['source'].keys()|trees['fixed'].keys() if trees['source'].get(n)!=trees['fixed'].get(n)}
 if changed!={'src/'+n for n in REPLACEMENTS}:raise ValueError('Unexpected upstream diff scope')
 shutil.copyfile(work/'source.tar.gz',TASK/'public/meep-source.tar.gz');generated=TASK/'author/generated';generated.mkdir(exist_ok=True)
 for n in REPLACEMENTS:shutil.copyfile(work/'fixed'/('meep-'+HEAD)/'src'/n,generated/n)
 record={'repository':'https://github.com/NanoComp/meep','issue':2408,'pull_request':2413,'baseline':BASE,'head':HEAD,'merge':'a6a11920f98ee478a81f9d1f42d8946908b54fd6','archive_sha256':ARCHIVES['source'][0],'files':len(trees['source']),'baseline_tree_sha256':hashlib.sha256(json.dumps(trees['source'],sort_keys=True).encode()).hexdigest(),'changed_files':sorted(changed),'reference_kind':'complete four genuine upstream implementation/header replacements; no author physics changes'}
 (TASK/'author/data-evidence/source.json').write_text(json.dumps(record,indent=2)+'\n');(TASK/'author/data-evidence/baseline-tree.json').write_text(json.dumps(trees['source'],indent=2,sort_keys=True)+'\n')
 return work
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',required=True,type=Path);p.add_argument('--proxy');a=p.parse_args();prepare(a.work,a.proxy)
