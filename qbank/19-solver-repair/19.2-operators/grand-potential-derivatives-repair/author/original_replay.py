"""Replay the unchanged upstream two-step sintering regression; no physics claim from pass alone."""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

TASK=Path(__file__).resolve().parents[1]
ROOT=TASK.parents[3]
DOCKER='C:/Program Files/Docker/Docker/resources/bin/docker.exe'


def main():
    source=ROOT/'work/repair-22/moose-30236/baseline-source/modules/phase_field/test/tests/GrandPotentialPFM/SinteringParabolic.i'
    report={'input':'Exact original upstream SinteringParabolic.i, generated 17x10 mesh, original units/parameters and two BDF2 time steps; no CLI physics or output overrides.',
            'input_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'meaning':'Genuine original regression executes; not an independent morphology validation or exodiff-gold certification.', 'versions':[]}
    for version,image in [('baseline','caeoj-moose30236-prototype:base'),('exact-upstream','caeoj-moose30236-observer:upstream'),('author-complete','caeoj-moose30236-dof:complete')]:
        directory=ROOT/'runs/authoring/repair-22/moose-30236-original'/version
        directory.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,directory/source.name)
        image_id=json.loads(subprocess.check_output([DOCKER,'image','inspect',image]))[0]['Id']
        result=subprocess.run([DOCKER,'run','--rm','--network','none','--cpus','2','--memory','4g','--user','1000:1000','--mount',f'type=bind,source={directory.resolve()},target=/job','--workdir','/job','--entrypoint','/bin/bash',image_id,'-lc','source /environment && exec /opt/moose-source/modules/phase_field/phase_field-opt -i SinteringParabolic.i'],capture_output=True,text=True,timeout=180)
        (directory/'stdout.log').write_text(result.stdout,newline='\n');(directory/'stderr.log').write_text(result.stderr,newline='\n')
        artifacts=[{'name':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in directory.glob('*.e')]
        report['versions'].append({'version':version,'image_id':image_id,'returncode':result.returncode,'exodus_outputs':artifacts,'stdout_sha256':hashlib.sha256((directory/'stdout.log').read_bytes()).hexdigest()})
        print(version,result.returncode,len(artifacts),flush=True)
    report['passed_execution']=all(v['returncode']==0 and v['exodus_outputs'] for v in report['versions'])
    (TASK/'author/data-evidence/original-replay.json').write_text(json.dumps(report,indent=2)+'\n',newline='\n')
    if not report['passed_execution']:raise SystemExit(1)


if __name__=='__main__':main()
