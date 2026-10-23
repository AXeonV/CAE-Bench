"""Verify the full pristine source and prepare the real reference rebuild."""
from pathlib import Path
import argparse,hashlib,json,subprocess,shutil
Q=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--docker',default='docker');a=p.parse_args()
    source=json.loads((Q/'author/data-evidence/source.json').read_text());assert hashlib.sha256((Q/'public/su2-source.tar.gz').read_bytes()).hexdigest()==source['source_archive_sha256']
    config=json.loads((Q/'harbor/source-repair.json').read_text());expected=json.loads((Q/'author/data-evidence/source-manifest.json').read_text())
    script="import pathlib,json,hashlib,sys;root=pathlib.Path('/opt/su2-source');expected=json.load(sys.stdin);bad=[n for n,h in expected.items() if not (root/n).is_file() or hashlib.sha256((root/n).read_bytes()).hexdigest()!=h];print(json.dumps({'checked_files':len(expected),'mismatches':bad}));sys.exit(bool(bad))"
    r=subprocess.run([a.docker,'run','--rm','-i','--network','none',config['base_image'],'python','-c',script],input=json.dumps(expected),text=True,capture_output=True,check=True)
    (Q/'author/data-evidence/pristine-trusted-runtime.json').write_text(r.stdout)
    context=a.output/'reference-context';context.mkdir(parents=True,exist_ok=True);lines=['FROM '+config['base_image']]
    for row in config['replacements']:
        shutil.copyfile(Q/'author/generated'/row['submission'],context/row['submission']);lines.append('COPY '+row['submission']+' '+row['target'])
    lines.append('RUN rm -f '+' '.join(config['rebuild_files'])+' && cmake --build '+config['build_directory']+' --target '+config['build_target']+' --parallel 4 && chmod -R go-w /opt/su2-source /opt/su2-build /opt/repair-driver')
    (context/'Dockerfile').write_text('\n'.join(lines)+'\n');print(context)
