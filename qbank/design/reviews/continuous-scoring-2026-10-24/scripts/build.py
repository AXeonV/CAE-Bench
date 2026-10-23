import hashlib
import json
from pathlib import Path
import shutil
import time
from caeoj_tools import data_pool as pool
from caeoj_tools.release import build

ROOT=Path('D:/Code/CAE-Bench-OJ')
WORK=ROOT/'runs/continuous-scoring'
plan=json.loads((WORK/'plan.json').read_text(encoding='utf-8'))
public=json.loads((WORK/'public-plan.json').read_text(encoding='utf-8'))
for task, published in zip(plan['tasks'],public['tasks']):
    assert task['task']==published['task']
    task.update(public_archive=published['public_archive'],public_archive_sha256=published['public_archive_sha256'])
    source=WORK/'publish-stage'/task['task_path'];target=WORK/'stage'/task['task_path']
    for name in ('instruction.md','DATA.md','judge-config.json','harbor/task.toml'):
        if (source/name).is_file():
            dst=target/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/name,dst)
    for name in ('instruction.md','DATA.md'):
        assert (ROOT/task['task_path']/name).read_bytes()==(target/name).read_bytes()
pool.write_json(WORK/'plan.json',plan)
target=ROOT/'runs/releases'/plan['release_id']
state=json.loads((WORK/'state.json').read_text(encoding='utf-8'))
state.update(stage='building',build_started_unix=time.time(),target=str(target))
pool.write_json(WORK/'state.json',state)
catalog=build(WORK/'plan.json',target)
state.update(stage='built_pending_independent_consumption',built_unix=time.time(),
             tasks=len(catalog['tasks']),cases=sum(len(t['cases']) for t in catalog['tasks']),
             samples=sum(len(t['samples']) for t in catalog['tasks']))
pool.write_json(WORK/'state.json',state)
print(json.dumps(state,ensure_ascii=False),flush=True)
