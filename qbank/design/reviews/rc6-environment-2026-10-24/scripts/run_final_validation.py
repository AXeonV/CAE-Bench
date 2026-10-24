"""Validate the final fail-closed recipes without any solver/model execution."""
import json,os,subprocess,time
from pathlib import Path
ROOT=Path('D:/Code/CAE-Bench-OJ');WORK=ROOT/'runs/releases/rc6-authoring'
RELEASE=ROOT/'runs/releases/caeoj-qbank-20261024-rc6'
def run(arguments,name):
    with (WORK/(name+'.log')).open('w',encoding='utf-8') as output:
        subprocess.run(arguments,cwd=ROOT,stdout=output,stderr=subprocess.STDOUT,check=True)
python=ROOT/'.venv/Scripts/python.exe'
state={'phase':'building_final_runtime','pid':os.getpid(),'started_unix':time.time(),'model_calls':0,'score_corrections':0}
def save():(WORK/'execution-status.json').write_text(json.dumps(state,indent=2),encoding='utf-8')
try:
    save();run([str(python),'-X','utf8',str(RELEASE/'environment/build_runtime.py')],'runtime-build-final')
    state['phase']='validating_164_final_containers';save()
    run([str(python),'-X','utf8',str(RELEASE/'environment/check_tasks.py'),'--jobs','3',
         '--output',str(WORK/'environment-validation-final')],'environment-validation-final')
    state.update(phase='validated_pending_review',completed_unix=time.time());save()
except Exception as exc:
    state.update(phase='failed',error=repr(exc),completed_unix=time.time());save();raise
