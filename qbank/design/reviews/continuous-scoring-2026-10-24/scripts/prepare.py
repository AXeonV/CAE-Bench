"""Prepare RC4 assets without altering its immutable files or identities."""
import json
import os
from pathlib import Path
import shutil
import time

from caeoj_tools import data_pool as pool
from caeoj_tools.continuous_scoring import convert_grading

ROOT = Path('D:/Code/CAE-Bench-OJ')
WORK = ROOT / 'runs/continuous-scoring'
PLAN = json.loads((ROOT/'runs/uniform-samples/plan.json').read_text(encoding='utf-8'))
records = []

def immutable_copy(source, target):
    # References/inputs remain read-only through this process. Grading is the
    # only file rewritten, so give it a separate physical copy first.
    if Path(source).name == 'grading.json':
        return shutil.copyfile(source, target)
    os.link(source, target)
    return target

for task in PLAN['tasks']:
    original = Path(task['source_root'])/task['task_path']
    prepared = WORK/'prepared'/task['task']
    before = pool.manifest(original/'data-manifest.json')
    if prepared.exists():
        raise RuntimeError('Use a fresh preparation directory: '+str(prepared))
    for prefix in ('cases','reference','samples'):
        shutil.copytree(original/prefix, prepared/prefix, copy_function=immutable_copy)
    revised = []
    if not task['chapter'].startswith('00-'):
        for slot in before['cases']:
            path = prepared/'reference'/slot/'grading.json'
            old = json.loads(path.read_text(encoding='utf-8'))
            new = convert_grading(old)
            pool.write_json(path, new)
            revised.append({'case':slot, 'previous':old, 'current':new,
                            'previous_sha256':pool.digest(original/'reference'/slot/'grading.json'),
                            'current_sha256':pool.digest(path)})
    for slot in before['samples']:
        marker = prepared/'samples'/slot/'example.json'
        if marker.exists():
            assert json.loads(marker.read_text(encoding='utf-8')) == {'kind':'format'}
        else:
            pool.write_json(marker, {'kind':'format'})
    receipt = json.loads((original/'.data-assembly.json').read_text(encoding='utf-8'))
    unchanged = {key:value for key,value in receipt['files'].items()
                 if not (revised and key.startswith('reference/') and key.endswith('/grading.json'))}
    record = {'task':task['task'], 'chapter':task['chapter'], 'case_count':len(before['cases']),
              'sample_count':len(before['samples']), 'revised_grading':revised,
              'original_root':str(original), 'unchanged_assets':unchanged,
              'prepared':str(prepared), 'hf_uploaded':False}
    records.append(record)
    pool.write_json(WORK/'preparation.json', records)
    print(task['task'],len(revised),'grading configurations prepared',flush=True)
assert len(records)==82
assert sum(len(r['revised_grading']) for r in records)==630
print('Prepared 82 tasks; 630 numerical grading configurations changed; 17 infrastructure cases unchanged',flush=True)
