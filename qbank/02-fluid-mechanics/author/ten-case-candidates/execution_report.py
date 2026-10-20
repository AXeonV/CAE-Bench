"""Join all 630 frozen designs with actual Titan artifacts. No validation."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from datetime import datetime,timezone

# 'Held' means a specific equivalence gap, never a claim of worldwide absence.
GAPS={
 '2.5.1':'一流体自由表面、气体无惯性无黏性；尚未匹配现成实现，不能用小正气相物性替代。',
 '2.5.2':'一流体自由表面、气体无惯性无黏性；尚未匹配现成实现，不能用小正气相物性替代。',
 '2.5.5':'尚未匹配同时支持指定物理Navier滑移与初始接触角的生产链；禁止用网格滑移代替。',
 '2.5.6':'尚未匹配同时支持指定物理Navier滑移与初始接触角的生产链；禁止用网格滑移代替。',
 '2.6.1':'公开对象是Euler含率/表观相通量及单向线性松弛；尚未匹配，离散轨迹不等价。',
 '2.6.2':'两相各自应力、双向线性拖曳及混合体积约束尚未匹配。',
 '2.6.3':'泡滴两相应力/拖曳及表观相通量模型尚未匹配。',
 '2.6.4':'指定拥挤压强和黏度、拖曳及混合体积约束尚未匹配。',
 '2.7.1':'两温、两浓度及体积分数加权守恒的全部交换项尚未匹配现成模块组合。',
 '2.7.2':'尖锐界面质量率、法向速度跳跃、反冲牵引及焓跳跃尚未匹配；共速Lee源不等价。',
 '2.7.3':'Lee源、非零散度和混合焓的完整原生耦合生产者尚未匹配；不能只用等温相变模块。',
 '2.7.4':'带nuclei_fraction移位的压力线性质量率尚未匹配；常见Merkle/Kunz/Schnerr默认式不能直接代入。',
 '2.7.5':'线性糊状区、指定有限阻力/epsilon及物质相变率的完整匹配仍待完成。',
 '2.8.1':'质量守恒Elrod–Adams空化未匹配；满膜Reynolds或截断负压不能覆盖全部十例。',
 '2.8.3':'跨隙均温、两项耗散及2H换热闭合尚未匹配；不能以另一种跨隙热模型代替。',
 '2.8.4':'尚未找到已匹配的现成跨隙Carreau向量BVP生产者；有效黏度牛顿Reynolds不等价。',
 '2.9.4':'双层独立动量及指定床/层间摩擦尚未逐项匹配Clawpack原生实现。',
 '2.10.1':'硬球输运参数、可压缩等温连续方程与指定滑移/开边界组合尚未匹配。',
 '2.10.2':'硬球mu(T)、热跳跃、黏性耗散和储槽开边界组合尚未匹配。',
 '2.11.3':'线性结构黏度与build/break动力学的精确现成闭合尚未匹配。',
 '2.11.4':'指数温移Carreau和温度方程的精确原生组合尚未匹配。',
 '2.11.5':'构象自由能松弛热源及两黏度/松弛时间温移尚未匹配；全部应力功转热不等价。',
}

def pending_reason(r,e):
    f=r['family'];i=int(e['design_id'].split('-')[-2])-1
    if r['question'] in GAPS:return GAPS[r['question']]
    if f=='euler_transient':return '时变加速度源尚未接通现成原生源模块；本批rhoCentralFoam适配器明确排除此项。'
    if f=='closed_flow':return '现成层流实现已定位；本例完整牵引、周期/体力、滑移或非零初态的原生配置与输入转换尚未完成。'
    if f=='generalized_flow':return '现成非牛顿模块已定位；四种流变律、截断、完整牵引/周期/体力及输入输出映射尚未逐例完成。'
    if f=='isothermal_compressible':return '仍需匹配真正等温状态关系、独立体黏度、质量库存及完整牵引；不能运行能量方程后覆盖温度。'
    if f in ('lowmach_energy','compressible_energy','turbulent_flow'):return '已定位OpenFOAM/Elmer候选；温度幂律mu/k、体黏度/耗散、热胀、湍流公开状态或统计采样语义仍需逐项匹配和适配。'
    if f=='immiscible':return 'Basilisk原生两流体为候选；零表面张力、初始相网格、真单元平均与固定输入/输出映射尚未接通。'
    if f=='viscoelastic':return 'OpenCFD原生Maxwell已定位（sigma=-tau_p/rho）；P1节点输入/输出、构象恢复和入出口/预应变尚未完成适配。'
    if f.startswith('shallow') or f=='wetdry':return 'Clawpack/Basilisk原生浅水为候选；指定线性摩擦、特征储槽、床面P1重建及真实节点输出映射尚未完成。'
    if f=='kinetic_gas':return 'SPARTA原生硬球/无碰撞、半空间储槽和混合壁已接通20项原生计算配置；公共四面体/壁面交换量转换仍待完成，原生统计不计作公共参考。'
    return '候选求解器仍需方程/边界匹配、输入转换与实际执行；不声称找不到现成实现。'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);args=ap.parse_args();base=args.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates';idx=json.loads((base/'index.json').read_text());rows=[];cases=[]
    for rr in idx['questions']:
        r=json.loads((args.snapshot/rr['path']).read_text());counts=Counter();ids=[]
        for e in r['proposed_cases']:
            p=args.root/'cases'/e['design_id']/'status.json';state=json.loads(p.read_text()) if p.exists() else {'design_id':e['design_id'],'status':'held_unmatched_physics' if r['question'] in GAPS else 'pending_producer_adapter'}
            if not p.exists():state['reason']=pending_reason(r,e)
            if state['status']=='unvalidated_candidate':
                job=p.parent;payload=job/'reference/reference.h5';assert payload.is_file() and (job/'input/problem.json').is_file() and (job/'reference/grading.json').is_file(),e['design_id'];assert hashlib.sha256(payload.read_bytes()).hexdigest()==state['reference_sha256'],e['design_id']
                provenance=job/('producer.json' if (job/'producer.json').exists() else 'execution.json');meta=json.loads(provenance.read_text())
                state['producer_record']={k:meta[k] for k in ('producer','image','source','source_url','source_commit','script_sha256','normalization_constant_C','binary_sha256','patch_sha256','checkpoint_sha256','conversion_script_sha256','native_type_registration_sha256') if k in meta}
                state['input_sha256']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (job/'input').iterdir() if f.is_file()}
            counts[state['status']]+=1;ids.append(e['design_id']);cases.append({'question':r['question'],**state})
        reason='十项均已有未验证候选参考，出处与转换局限见生产记录。' if counts.get('unvalidated_candidate')==10 else pending_reason(r,next(e for e in r['proposed_cases'] if not (args.root/'cases'/e['design_id']/'reference/reference.h5').exists()))
        rows.append({'question':r['question'],'task':r['task'],'family':r['family'],'designed':10,'counts':dict(counts),'reason':reason,'design_ids':ids})
    total=Counter(c['status'] for c in cases);assert len(cases)==630
    result={'generated_utc':datetime.now(timezone.utc).isoformat(),'scope':{'questions':63,'detailed_designs':630,'actual_status':dict(total)},'completion_claim':'partial; not all 630 references computed','numerical_validation':'not_performed','hf_changes':False,'benchmark':False,'questions':rows,'cases':cases}
    (args.root/'maintenance/execution-summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    md=['# 第二章候选参考：实际执行状态','',f'记录时间：{result["generated_utc"]}。设计630项；实际状态：`{dict(total)}`。','', '以下是生产状态和匹配缺口；未做数值验证。“暂缓”不表示已经证明不存在其他现成实现。','', '| 题号 | 已有候选参考 | 运行中 | 暂缓/待执行 | 原因 |','|---|---:|---:|---:|---|']
    for row in rows:
        c=row['counts'];done=c.get('unvalidated_candidate',0);running=c.get('running',0)+c.get('preparing',0);md.append(f'| {row["question"]} | {done} | {running} | {10-done-running} | {row["reason"]} |')
    (args.root/'maintenance/EXECUTION.md').write_text('\n'.join(md)+'\n')
    print(json.dumps(result['scope'],ensure_ascii=False))

if __name__=='__main__':main()
