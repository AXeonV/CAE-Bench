"""Collect genuine per-task assembly results after the large prefix finishes."""
from copy import deepcopy
import json
from pathlib import Path
from caeoj_tools import data_pool as pool

ROOT=Path('D:/Code/CAE-Bench-OJ');WORK=ROOT/'runs/continuous-scoring'
load=lambda p:json.loads(Path(p).read_text(encoding='utf-8'))
plan=load(ROOT/'runs/uniform-samples/plan.json');state=load(WORK/'state.json')
original_entries=deepcopy(plan['tasks'])
prefix={row['task']:row for row in state['tasks']}
assert all(t['task'] in prefix for t in plan['tasks'][:15])
rows=[]
for i,entry in enumerate(plan['tasks']):
    slug=entry['task']
    if i<15:
        result=prefix[slug];entry['source_root']=str(WORK/'stage')
        if not entry['chapter'].startswith('00-'):
            entry['limitations'].append('RC5 continuous 5%-10% max-NRMSE grading; inherited scale floors are explicit migration choices, not numerical calibration. Input/reference arrays unchanged; local descriptor revision not uploaded to HF.')
    else:
        task_state=load(WORK/'task-state'/(slug+'.json'))
        assert task_state['stage']=='packed_task_complete'
        assert len(task_state['tasks'])==1
        result=task_state['tasks'][0]
        revised_entry=load(WORK/'task-entries'/(slug+'.json'))
        assert revised_entry['task']==slug and revised_entry['task_path']==entry['task_path']
        assert Path(revised_entry['source_root'])==WORK/'stage'
        plan['tasks'][i]=revised_entry
    assert result['task']==slug
    assert result['strict']['valid'] and result['case_ids_preserved']
    original_entry=original_entries[i]
    old_manifest=pool.manifest(Path(original_entry['source_root'])/entry['task_path']/'data-manifest.json')
    new_manifest=pool.manifest(WORK/'stage'/entry['task_path']/'data-manifest.json')
    assert old_manifest['task_id']==new_manifest['task_id']
    assert result['case_count']==len(old_manifest['cases']) and result['sample_count']==len(old_manifest['samples'])
    for role in ('cases','samples'):
        assert {k:v['case_id'] for k,v in old_manifest[role].items()}=={k:v['case_id'] for k,v in new_manifest[role].items()}
    rows.append(result)
plan['release_id']='caeoj-qbank-20261024-rc5'
plan['capabilities']['numerical_scoring']='max-nrmse-linear-5-10-percent'
plan['release_notes']=[
    '本版82题、647个正式case角色：第0章2题、第1章13题、第2章43道流动能力题及24道CFDCodeBench题；第19章未纳入。',
    '第1、2章80题630个正式case统一为逐物理量／分量／时刻NRMSE的最大值E：E≤5%得1分、E≥10%得0分，中间线性；题目reward为所有正式case分数平均。第0章17个case保留原二元规则。',
    '归一化尺度下限继承既有绝对尺度，题面逐量列明；既有权重与压力处理保留，未宣称与旧容差等价或完成尺度校准。',
    '本版96个公开样例均为随机格式输出，不保证数值答案正确；不公开样例reference或样例数值判分材料。正式输入、参考数组、观测资产、样例字节及case身份保持RC4，仅数值case评分配置更新。',
    '80题新评分题面完成独立考生审阅，核心与全量配置映射完成独立审阅；未改变的输入审计及第0章材料审阅沿用此前匹配版本。文件校验和参考自判分不代表独立数值资格。',
    '41道新增流动候选的320个正式case仍为unvalidated-reference-rc；参考数值资格、资源校准及异机验收待完成。',
    '此前全题审查记录的17题输入分支覆盖缺口及14题压力误差尺度设计问题仍需复核；统一NRMSE不自动解决科学尺度校准问题。',
    '2.1.1、2.1.3各保留既有10例，未将更大维护池自动纳入选样。新描述绑定仅在本地池与本包，未上传HF；来源身份保留旧生成证据，不重签为新评分认证。',
    '三维可压流的独立评价预算按代表例实测留余量调整为120秒，求解时限不变；未据此宣称全部case或异机资源资格。',
    '本版未重新求解参考、调用模型或下载HF；未提供模型运行器、全部系统镜像、整仓patch接口或快速判分。当前仍为内部试运行RC。'
]
pool.write_json(WORK/'plan.json',plan)
state.update(stage='packed_pending_final_provenance',tasks=rows)
pool.write_json(WORK/'state.json',state)
print('Merged82 genuinely strict assemblies,647 formal cases and96 format samples',flush=True)
