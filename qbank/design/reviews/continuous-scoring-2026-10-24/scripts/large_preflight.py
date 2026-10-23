"""Measure the changed grader on a real large input before freezing RC limits."""
import json
from pathlib import Path
import subprocess
import sys
import time
import zipfile

ROOT=Path('D:/Code/CAE-Bench-OJ');WORK=ROOT/'runs/continuous-scoring'
slug='compressible-navier-stokes-3d';workspace=WORK/'large-public-workspace';installed=WORK/'large-installed'
workspace.mkdir()
with zipfile.ZipFile(WORK/'public'/(slug+'-agent.zip')) as archive:archive.extractall(workspace)
p=subprocess.run([sys.executable,'-m','pip','install','--no-deps','--no-build-isolation','--no-compile','--target',str(installed),str(workspace)],capture_output=True,text=True,timeout=180)
(WORK/'large-install.log').write_text(p.stdout+'\n'+p.stderr,encoding='utf-8');assert p.returncode==0
case=sorted((WORK/'prepared'/slug/'cases').iterdir())[0].name
code=r'''
import json,sys,time
from pathlib import Path
sys.path.insert(0,INSTALLED)
from caeoj.case_grading import grade_case
import caeoj
assert Path(caeoj.__file__).resolve().is_relative_to(Path(INSTALLED).resolve())
task=Path(PREPARED);slot=SLOT
started=time.monotonic()
result=grade_case(task/'cases'/slot/'problem.json',task/'reference'/slot/'reference.h5',task/'reference'/slot/'grading.json')
print(json.dumps({'task':SLUG,'case':slot,'score':result['score'],'status':result['status'],'seconds':time.monotonic()-started,'evaluation':result.get('evaluation_sha256'),'message':result.get('message')}))
'''
for key,value in [('INSTALLED',str(installed)),('PREPARED',str(WORK/'prepared'/slug)),('SLOT',case),('SLUG',slug)]:code=code.replace(key,repr(value))
p=subprocess.run([sys.executable,'-I','-X','utf8','-c',code],capture_output=True,text=True,timeout=240)
(WORK/'large-preflight.stderr.txt').write_text(p.stderr,encoding='utf-8')
assert p.returncode==0,p.stderr
result=json.loads(p.stdout);(WORK/'large-preflight.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
assert result['score']==1,result
print(json.dumps(result),flush=True)
