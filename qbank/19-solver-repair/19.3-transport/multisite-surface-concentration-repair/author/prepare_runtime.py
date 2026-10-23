"""Verify the complete pristine shared Cantera tree, then prepare baseline/reference contexts."""
import argparse,hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
Q=Path(__file__).resolve().parents[1]
ISSUE=1996
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--docker',default='docker');a=p.parse_args()
archive=Q/'public/cantera-source.tar.gz';source=json.loads((Q/'author/data-evidence/source.json').read_text());assert hashlib.sha256(archive.read_bytes()).hexdigest()==source['source_sha256'];expected={}
with tarfile.open(archive) as t:
 for m in t:
  if m.isfile():expected[m.name.split('/',1)[1]]=hashlib.sha256(t.extractfile(m).read()).hexdigest()
code="""from pathlib import Path
import hashlib,json,sys
root=Path('/opt/cantera-source');expected=json.load(sys.stdin)
assert all((root/n).is_file() and hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in expected.items())
print(len(expected))
"""
subprocess.run([a.docker,'run','--rm','--network','none','-i','caeoj-cantera1872-core:offline-sdk','python','-c',code],input=json.dumps(expected),text=True,check=True)
context=a.output/'context';context.mkdir(parents=True,exist_ok=True)
for n in ['driver.cpp','mechanism.yaml','CMakeLists.txt']:shutil.copyfile(Q/'public'/n,context/n)
shutil.copyfile(Q/'author/runtime.Dockerfile',context/'Dockerfile')
reference=a.output/'reference-context';reference.mkdir(parents=True,exist_ok=True);config=json.loads((Q/'harbor/source-repair.json').read_text());lines=[f'FROM caeoj-cantera{ISSUE}-core:base']
for row in config['replacements']:
 shutil.copyfile(Q/'author/generated'/row['submission'],reference/row['submission']);lines.append('COPY '+row['submission']+' '+row['target'])
lines.append('RUN rm -f '+' '.join(config['rebuild_files'])+' && cmake --build '+config['build_directory']+' --target repair_sources');(reference/'Dockerfile').write_text('\n'.join(lines)+'\n');print(context,reference)
