"""Verify the two real archives and extract only genuine upstream repair files."""
import argparse,hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
TASK=Path(__file__).resolve().parents[1]
BASE='85e107771808a4b89e4b4514007512f48c1c121b'
HEAD='2828d4d92cac52c5666ca18351b6d64f4feefb09'
ARCHIVES={'source':('796b8ecc813382251c26a2830c461ac9c6be3cda4f7aae6d2409ba9ff7ac7fdb',BASE),'fixed':('c170de1cacd61a980f257be2cf3f52275908db86c1082172173d73c2023528eb',HEAD)}
REPLACEMENTS=['step_db.cpp']
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
 if changed!={'src/step_db.cpp','python/tests/test_ldos.py'}:raise ValueError('Unexpected upstream diff scope')
 shutil.copyfile(work/'source.tar.gz',TASK/'public/meep-source.tar.gz');generated=TASK/'author/generated';generated.mkdir(exist_ok=True)
 for n in REPLACEMENTS:shutil.copyfile(work/'fixed'/('meep-'+HEAD)/'src'/n,generated/n)
 record={'repository':'https://github.com/NanoComp/meep','issue':2338,'pull_request':2382,'baseline':BASE,'head':HEAD,'merge':'d370f1aa603c5f9f74eae2690952e7a3b3d3cb0d','archive_sha256':ARCHIVES['source'][0],'files':len(trees['source']),'baseline_tree_sha256':hashlib.sha256(json.dumps(trees['source'],sort_keys=True).encode()).hexdigest(),'changed_files':sorted(changed),'reference_kind':'genuine upstream step_db.cpp replacement; upstream Python test excluded from solver; no author physics changes'}
 (TASK/'author/data-evidence/source.json').write_text(json.dumps(record,indent=2)+'\n');(TASK/'author/data-evidence/baseline-tree.json').write_text(json.dumps(trees['source'],indent=2,sort_keys=True)+'\n')
 return work
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',required=True,type=Path);p.add_argument('--proxy');a=p.parse_args();prepare(a.work,a.proxy)
