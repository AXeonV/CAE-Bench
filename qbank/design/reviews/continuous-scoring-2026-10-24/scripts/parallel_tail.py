"""Independent local task assembly; the large first 15 stay with pack.py."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path('D:/Code/CAE-Bench-OJ');WORK=ROOT/'runs/continuous-scoring'
plan=json.loads((ROOT/'runs/uniform-samples/plan.json').read_text(encoding='utf-8'))
tasks=plan['tasks'][15:]
assert len(tasks)==67
env=dict(os.environ,TEMP=str(WORK/'temp'),TMP=str(WORK/'temp'))
def one(task):
    slug=task['task']
    with (WORK/('pack-'+slug+'.log')).open('w',encoding='utf-8') as log:
        result=subprocess.run([sys.executable,'-X','utf8',str(WORK/'pack.py'),'--task',slug],env=env,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:raise RuntimeError(slug+' assembly failed; see its log')
    return slug
with ThreadPoolExecutor(max_workers=3) as executor:
    for future in as_completed([executor.submit(one,t) for t in tasks]):
        print('Independent task ready:',future.result(),flush=True)
print('All67 tail tasks strictly assembled',flush=True)
