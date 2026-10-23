"""Verify original source closure and compiler header dependencies; prepare rebuild contexts."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
Q=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--docker',default='docker');a=p.parse_args()
source=json.loads((Q/'author/data-evidence/source.json').read_text());assert hashlib.sha256((Q/'public/lammps-source.tar.gz').read_bytes()).hexdigest()==source['source_archive_sha256']
expected=json.loads((Q/'author/data-evidence/source-manifest.json').read_text())
code="""from pathlib import Path
import hashlib,json,sys
root=Path('/opt/lammps-source');expected=json.load(sys.stdin)
assert all((root/n).is_file() and hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in expected.items())
deps=sorted(str(p) for p in Path('/opt/lammps-build').rglob('*.o.d') if 'pair_gran_hooke_history_kokkos.h' in p.read_text())
assert len(deps)==3,deps
print(json.dumps({'image':'caeoj-lammps4219-core:base','unmodified_source_files':len(expected),'full_source_sha_match':True,'header_dependency_files':deps}))
"""
r=subprocess.run([a.docker,'run','--rm','--network','none','-i','caeoj-lammps4219-core:base','python','-c',code],input=json.dumps(expected),text=True,capture_output=True,check=True)
(Q/'author/data-evidence/pristine-baseline.json').write_text(r.stdout)
context=a.output/'context';context.mkdir(parents=True,exist_ok=True);shutil.copyfile(Q/'public/lammps-source.tar.gz',context/'lammps-source.tar.gz');shutil.copyfile(Q/'author/runtime.Dockerfile',context/'Dockerfile')
reference=a.output/'reference-context';reference.mkdir(parents=True,exist_ok=True);config=json.loads((Q/'harbor/source-repair.json').read_text());lines=['FROM '+config['base_image']]
for row in config['replacements']:
    shutil.copyfile(Q/'author/generated'/row['submission'],reference/row['submission']);lines.append('COPY '+row['submission']+' '+row['target'])
lines.append('RUN rm -f '+' '.join(config['rebuild_files'])+' && cmake --build '+config['build_directory']+' --target '+config['build_target']+' --parallel 4')
(reference/'Dockerfile').write_text('\n'.join(lines)+'\n');print(context,reference)
