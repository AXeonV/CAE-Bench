"""Verify the public ZIP installs and runs independently in the baseline image."""
import hashlib,json,subprocess
from pathlib import Path
TASK=Path(__file__).resolve().parents[1];ROOT=TASK.parents[3]
DOCKER='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
CODE=r'''
import json,os,pathlib,subprocess,sys,zipfile
with zipfile.ZipFile('/payload/agent.zip') as z:z.extractall('/tmp/public')
subprocess.run([sys.executable,'-m','pip','install','--no-cache-dir','/tmp/public'],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
os.chdir('/tmp')
import caeoj
from caeoj.case_grading import grade_case
root=pathlib.Path('/tmp/public/qbank/19-solver-repair/19.3-transport/migration-soret-scaling-repair');scores={}
for sample in ['01','02']:
    d=root/'samples'/sample;output=pathlib.Path('/tmp')/('baseline-sample-'+sample+'.h5')
    subprocess.run([sys.executable,str(root/'public/run_case.py'),'--input',str(d/'input/problem.json'),'--output',str(output)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    scores[sample]=grade_case(d/'input/problem.json',output,d/'reference/grading.json')['score']
assert scores=={'01':0,'02':0},scores
print(json.dumps({'installed_module':caeoj.__file__,'baseline_sample_scores':scores,'network':'none','meaning':'The original defective solver runs from the independently installed public ZIP; both transport/unit defects are observable. Oracle validation separately supplies the repaired implementation.'}))
'''
if __name__=='__main__':
    directory=ROOT/'dist';command=[DOCKER,'run','--rm','--network','none','--cpus','4','--memory','4g','--mount',f'type=bind,source={(directory/"migration-soret-scaling-repair-agent.zip").resolve()},target=/payload/agent.zip,readonly','caeoj-elmer870-runtime:base','python','-c',CODE]
    run=subprocess.run(command,capture_output=True,text=True,timeout=120)
    if run.returncode:raise RuntimeError(run.stderr)
    value=json.loads(run.stdout);value['archive_sha256']=hashlib.sha256((directory/'migration-soret-scaling-repair-agent.zip').read_bytes()).hexdigest();(TASK/'author/data-evidence/public-install.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))
