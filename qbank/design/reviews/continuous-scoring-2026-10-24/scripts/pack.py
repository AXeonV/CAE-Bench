"""Rebind changed grading with the existing pool and assembly implementation."""
import json
import os
from pathlib import Path
import shutil
import sys
import time
from caeoj_tools import data_pool as pool

ROOT = Path('D:/Code/CAE-Bench-OJ')
WORK = ROOT/'runs/continuous-scoring'
STAGE = WORK/'stage'
plan = json.loads((ROOT/'runs/uniform-samples/plan.json').read_text(encoding='utf-8'))
records = json.loads((WORK/'preparation.json').read_text(encoding='utf-8'))
only=sys.argv[sys.argv.index('--task')+1] if '--task' in sys.argv else None
state_path=WORK/'task-state'/(only+'.json') if only else WORK/'state.json'
state_path.parent.mkdir(exist_ok=True)
state=json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else {'started_unix':time.time(),'tasks':[]}
state.update(pid=os.getpid(),stage='packing',resumed_unix=time.time(),temporary_directory=os.environ.get('TEMP'))
completed={row['task'] for row in state['tasks']}
def save(): pool.write_json(state_path,state)
save()
def copy_immutable(source,target):
    if Path(target).exists():
        assert pool.identity(source)==pool.identity(target)
    else:os.link(source,target)
    return target
for entry, original_record in zip(plan['tasks'],records):
    assert entry['task']==original_record['task']
    if only and entry['task']!=only:continue
    if entry['task'] in completed:
        entry['source_root']=str(STAGE)
        if original_record['revised_grading']:
            entry['limitations'].append('RC5 continuous 5%-10% max-NRMSE grading; inherited scale floors are explicit migration choices, not numerical calibration. Input/reference arrays unchanged; local descriptor revision not uploaded to HF.')
        continue
    old = Path(original_record['original_root'])
    before=pool.manifest(old/'data-manifest.json')
    prepared=Path(original_record['prepared'])
    target=STAGE/entry['task_path']
    target.mkdir(parents=True,exist_ok=True)
    # These immutable payloads are hardlinked to avoid duplicating large local
    # HDF5 files. Only newly created grading files differ from RC4.
    for prefix in ('cases','reference','samples'):
        shutil.copytree(prepared/prefix,target/prefix,copy_function=copy_immutable,dirs_exist_ok=True)
    if original_record['revised_grading']:
        bundle=WORK/'pools'/entry['task']
        if not (bundle/'selection.json').exists():
            if bundle.exists() and any(bundle.iterdir()):
                raise RuntimeError('Incomplete pool needs a new isolated retry path: '+str(bundle))
            pool.pack(prepared,bundle,before)
        pool.validate_bundle(bundle)
        packed=pool.manifest(bundle/'selection.json')
        for role in ('cases','samples'):
            assert {k:v['case_id'] for k,v in before[role].items()}=={k:v['case_id'] for k,v in packed[role].items()}
        store=pool.LocalStore(bundle/'repository')
        selected=pool.select(packed,store,[f"{k}={v['case_id']}" for k,v in before['cases'].items()],[],
                             format_samples=[f"{k}={v['case_id']}" for k,v in before['samples'].items()])
        selected['notes']='Offline RC5 continuous NRMSE grading revision; input/reference arrays/sample bytes preserved from RC4. New descriptors are local only, not uploaded to HF.'
        pool.write_json(target/'data-manifest.json',selected)
        assembled=pool.assemble(target,selected,store)
        current=ROOT/entry['task_path']
        current_receipt=current/'.data-assembly.json'
        refreshed=False
        if current_receipt.exists():
            pool.assemble(current,selected,store,update=True)
            refreshed=True
        pool.write_json(current/'data-manifest.json',selected)
        if refreshed: assert pool.verify(current,strict=True)['valid']
    else:
        selected=before
        for name in ('data-manifest.json','.data-assembly.json'):
            shutil.copyfile(old/name,target/name)
        assembled={'unchanged_infrastructure':True}
    verified=pool.verify(target,strict=True)
    assert verified['valid'],verified
    for name,expected in original_record['unchanged_assets'].items():
        assert pool.identity(target/name)==expected,(entry['task'],name)
    result={'task':entry['task'],'case_count':len(before['cases']),'sample_count':len(before['samples']),
            'case_ids_preserved':True,'sample_input_ids_preserved':True,
            'unchanged_assets_verified':len(original_record['unchanged_assets']),
            'grading_changed':len(original_record['revised_grading']),'assembly':assembled,'strict':verified,
            'pool':str(WORK/'pools'/entry['task']) if original_record['revised_grading'] else None,
            'hf_uploaded':False}
    state['tasks'].append(result);save()
    entry['source_root']=str(STAGE)
    if original_record['revised_grading']:
        entry['limitations'].append('RC5 continuous 5%-10% max-NRMSE grading; inherited scale floors are explicit migration choices, not numerical calibration. Input/reference arrays unchanged; local descriptor revision not uploaded to HF.')
    print(entry['task'],'strict verified',len(state['tasks']),'/82',flush=True)
if only:
    entry=next(t for t in plan['tasks'] if t['task']==only)
    pool.write_json(WORK/'task-entries'/(only+'.json'),entry)
    state.update(stage='packed_task_complete',ended_unix=time.time());save()
    sys.exit(0)
plan['release_id']='caeoj-qbank-20261024-rc5'
plan['capabilities']['numerical_scoring']='max-nrmse-linear-5-10-percent'
plan['release_notes'].append('第1、2章80题630个正式case统一为逐物理量／分量／时刻NRMSE的最大值E：E≤5%得1分、E≥10%得0分，中间线性；题目reward为所有正式case分数平均。第0章17个case保留原二元规则。')
plan['release_notes'].append('归一化尺度下限继承既有绝对尺度，题面逐量列明；既有权重与压力处理保留，未宣称与旧容差等价或完成尺度校准。正式输入、参考数组、96个随机格式样例及case身份保持RC4。')
pool.write_json(WORK/'plan.json',plan)
state.update(stage='packed_pending_publication',ended_unix=time.time());save()
