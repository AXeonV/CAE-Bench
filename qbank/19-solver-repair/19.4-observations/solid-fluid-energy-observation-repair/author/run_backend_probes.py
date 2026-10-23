"""Serial real probes in disposable fixed-image containers; retain all raw logs."""
import hashlib
import json
from pathlib import Path
import subprocess
import time

TASK=Path(__file__).resolve().parents[1]
ROOT=TASK.parents[3]
DOCKER='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
DEST=Path('C:/Users/Jim Zhou/.cache/caeoj-repair22/moose22074-backend-probes-v1')


def main():
    DEST.mkdir(parents=True,exist_ok=False)
    image=json.loads(subprocess.check_output([DOCKER,'image','inspect','caeoj-moose22074-verifier:v1']))[0]['Id']
    report={'image_id':image,'resources':{'cpus':4,'memory_bytes':4294967296,'network':'none'},
            'probe_script_sha256':hashlib.sha256((TASK/'author/backend_probe.py').read_bytes()).hexdigest(),
            'modes':[],'complete':False}
    for mode in ['valid','syntax','compiler','baseline-runtime','baseline-sdk','extra','symlink','oversize']:
        name='moose22074-backend-'+mode
        directory=DEST/mode;directory.mkdir()
        command=[DOCKER,'run','--name',name,'--network','none','--cpus','4','--memory','4g',
                 '--mount',f'type=bind,source={TASK/"author/generated"},target=/probe,readonly',
                 '--mount',f'type=bind,source={TASK/"author/backend_probe.py"},target=/probe_backend.py,readonly',
                 '--entrypoint','/usr/local/bin/python',image,'/probe_backend.py',mode]
        started=time.monotonic()
        try:
            result=subprocess.run(command,capture_output=True,text=True,timeout=1200)
            (directory/'stdout.log').write_text(result.stdout,newline='\n');(directory/'stderr.log').write_text(result.stderr,newline='\n')
            copied=subprocess.run([DOCKER,'cp',name+':/logs/verifier',str(directory/'verifier')],capture_output=True,text=True,timeout=60)
            if result.returncode:raise RuntimeError((mode,result.returncode,result.stdout[-2000:],result.stderr[-2000:]))
            item=json.loads(result.stdout.strip().splitlines()[-1]);assert item['passed']
            item.update(seconds=time.monotonic()-started,raw_directory=str(directory),log_copy_returncode=copied.returncode)
            report['modes'].append(item)
            (TASK/'author/data-evidence/backend-probes.json').write_text(json.dumps(report,indent=2)+'\n',newline='\n')
            print(mode,'passed',item['seconds'],flush=True)
        finally:subprocess.run([DOCKER,'rm','-f',name],capture_output=True,timeout=60)
    report['complete']=True
    (TASK/'author/data-evidence/backend-probes.json').write_text(json.dumps(report,indent=2)+'\n',newline='\n')


if __name__=='__main__':main()
