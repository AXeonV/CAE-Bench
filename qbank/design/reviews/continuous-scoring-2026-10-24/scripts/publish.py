"""Freeze the final source closure and publish every selected task."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import time
from caeoj_tools import data_pool as pool

ROOT=Path('D:/Code/CAE-Bench-OJ')
WORK=ROOT/'runs/continuous-scoring'
STAGE=WORK/'publish-stage'
plan=json.loads((ROOT/'runs/uniform-samples/plan.json').read_text(encoding='utf-8'))
for name in ('src','qbank/extensions'):
    shutil.copytree(ROOT/name,STAGE/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.egg-info'))
for name in ('LICENSE','pyproject.toml','README.md','docs/CONTRACT.md','docs/GRADING.md'):
    dst=STAGE/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dst)
spec=importlib.util.spec_from_file_location('rc5_publisher',ROOT/'src/utils/publish_dist.py')
publisher=importlib.util.module_from_spec(spec);spec.loader.exec_module(publisher)
records=[]
for entry in plan['tasks']:
    source=ROOT/entry['task_path'];target=STAGE/entry['task_path']
    shutil.copytree(WORK/'prepared'/entry['task']/'samples',target/'samples',copy_function=os.link)
    # Publishing only consumes samples; use the original explicit format roles.
    original=Path(entry['source_root'])/entry['task_path']
    # Copy the genuine receipt plus unchanged sample data. samples_only strict
    # verification deliberately does not claim formal assembly in this root.
    for name in ('data-manifest.json','.data-assembly.json'):
        shutil.copyfile(original/name,target/name)
    for name in ('instruction.md','DATA.md','judge-config.json','harbor/task.toml','public-materials.json'):
        if (source/name).exists():
            dst=target/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/name,dst)
    for name in ('public','extension'):
        if (source/name).is_dir():shutil.copytree(source/name,target/name)
    result=publisher.publish(entry['task'],output=WORK/'public',root=STAGE)
    entry.update(public_archive=result['archive'],public_archive_sha256=result['sha256'])
    records.append({'task':entry['task'],**result})
    pool.write_json(WORK/'publication.json',records)
    print('Published',entry['task'],len(records),'/82',flush=True)
pool.write_json(WORK/'public-plan.json',plan)
