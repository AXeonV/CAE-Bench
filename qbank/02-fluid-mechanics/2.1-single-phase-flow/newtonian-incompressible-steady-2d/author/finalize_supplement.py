"""Bind delivery evidence after successful fixed-commit pool verification."""
from pathlib import Path
import argparse,json,hashlib
from huggingface_hub import HfApi

p=argparse.ArgumentParser();p.add_argument('bundle',type=Path);p.add_argument('--revision',required=True);args=p.parse_args()
author=Path(__file__).parent;task=author.parent;evidence=author/'data-evidence/supplement-20261017'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
remote=read(evidence/'remote-transport.json');upload=read(evidence/'hf-upload.json');start=read(evidence/'hf-start.json')
assert remote['revision']==upload['revision']==args.revision
assert remote['strict_verify']['valid'] and len(remote['actual_inputs_and_grading'])==20
assert remote['assembly']['complete']
choice=read(args.bundle/'selection.json');numbers=read(evidence/'evidence/numerical-validation.json')
assert len(numbers)==20 and all(r['accepted'] for r in numbers)
api=HfApi();main=api.repo_info(start['repo'],repo_type='dataset',revision='main').sha
head=api.repo_info(start['repo'],repo_type='dataset',revision=start['branch']).sha
assert main==start['main_start'] and head==args.revision
(evidence/'hf-final.json').write_text(json.dumps(dict(main_start=start['main_start'],main_final=main,main_unchanged=True,branch=start['branch'],commit=head),indent=2)+'\n')

# First pool registration establishes location only; it selects no formal cases.
empty={k:choice[k] for k in ('schema_version','task_id','repository','pool')};empty.update(cases={},samples={})
canonical=task/'data-manifest.json'
if canonical.exists():assert read(canonical)==empty
else:canonical.write_text(json.dumps(empty,indent=2)+'\n')

descriptions={
'force-island-chamber':'内岛障碍物＋旋转型体加速度',
'force-split-recess':'两个深侧凹槽＋随 x 变化的竖向体加速度',
'force-three-ribs':'三块不等高底肋＋剪切型体加速度',
'four-wall-circulation':'四侧切向运动形成整体环流',
'lid-central-pedestal':'中央底台阶＋运动顶壁',
'lid-cross-chamber':'十字形连通腔＋局部高位运动顶壁',
'lid-L-chamber':'L 形凹域＋运动顶壁',
'lid-offset-baffle':'偏置底部高挡板＋运动顶壁',
'lid-serpentine-chamber':'曲折串联腔＋运动壁及体加速度共同驱动',
'lid-square':'Re=100 标准方腔，Ghia 中线独立比对',
'lid-square-obstacle':'封闭方形内孔＋运动顶壁',
'lid-staggered-islands':'两个交错内岛＋运动顶壁',
'lid-step-floor':'不等高底面台阶＋运动顶壁',
'lid-T-chamber':'T 形主腔及下支腔＋运动顶壁',
'lid-two-obstacles':'两块并列内障碍物＋运动顶壁',
'opposed-lids':'上下壁反向运动，双侧剪切驱动',
'opposed-side-walls':'左右壁竖向反向运动',
'rotational-force-square':'全静止壁方腔＋非保守旋转型体加速度',
'shear-force-slip-channel':'剪切型体加速度＋侧面滑移、上下无滑移',
'side-driven':'单侧竖向运动壁＋封闭静止壁',
}
catalog=[]
numeric={r['name']:r for r in numbers}
for n,(name,entry) in enumerate(choice['cases'].items(),1):
    descriptor=args.bundle/'repository'/choice['repository']['path']/entry['case']['path']
    item=read(descriptor);row=numeric[name]
    catalog.append(dict(local_id=f'{n:03}',name=name,description=descriptions[name],**entry,
                        hf_commit=args.revision,input_identity_sha256=item['origin']['input_identity_sha256'],
                        input_files=row['input_files'],reference_files=row['reference_files'],probes=row['probes']))
(evidence/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(evidence/'staged-selection.json').write_text(json.dumps(choice,indent=2)+'\n')

command=['data','select','--task','newtonian-incompressible-steady-2d','--revision',args.revision,
         '--output','work/211-supplement-benchmark-selection.json']
for row in catalog:command+=['--case',row['local_id']+'='+row['case_id']]
ps='$selectionArgs = @(\n'+',\n'.join("    '"+v+"'" for v in command)+'\n)\n& ./.venv/Scripts/python.exe -m caeoj_tools.cli @selectionArgs\nif ($LASTEXITCODE -ne 0) { throw "Selection failed" }\n'
(evidence/'select-cases.ps1').write_text(ps,encoding='utf-8')
lines=['# 交付记录','',f"HF main 起点：`{main}`。指定分支：`{start['branch']}`。最终提交：`{head}`。",
       '',f"[固定提交中的数据池](https://huggingface.co/datasets/{start['repo']}/tree/{head}/{choice['repository']['path']}/pool)",
       '', '20 例全部完成参考计算、全批接口审计、本地严格核验，以及固定提交重新获取后的严格完整性／参考／判分链路验证。HF main 未改变。正式 cases／samples 均保持空；首次创建的 data-manifest.json 只登记池位置。',
       '', '| 后续本地编号 | 名称 | Case ID | 内容 |','|---|---|---|---|']
lines += [f"| {r['local_id']} | {r['name']} | `{r['case_id']}` | {r['description']} |" for r in catalog]
lines += ['', '全部 case 描述 SHA-256、输入身份及逐资产摘要在 catalog.json。来源、生产者、独立比对、数值和资源局限见 README.md。',
          '', '在仓库根目录运行以下命令，生成明确包含这 20 例的临时选择；不会启动 benchmark，也不会修改正式清单：','',
          '```powershell', '& ./qbank/02-fluid-mechanics/2.1-single-phase-flow/newtonian-incompressible-steady-2d/author/data-evidence/supplement-20261017/select-cases.ps1','```',
          '', '等价命令：','', '```sh','python -m caeoj_tools.cli '+' '.join(command),'```',
          '', '选样命令已实际执行验证。以后装配和 benchmark 应继续固定本提交，按运行技能审核并使用生成的选择；本次未装配正式测试或冻结评测条件。',
          '', '原始求解结果维护档案保留在 titan 的 `/home/zhouzhiyu/caeoj-211-supplement-20261017/evidence/raw-solver-results.tar.gz`，摘要见 raw-solver-results.sha256。清理实际结果见 cleanup.json。']
(evidence/'delivery.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

recipes={str(path.relative_to(task)):hashlib.sha256(path.read_bytes()).hexdigest() for path in author.glob('*.py')}
recipes.update({str(path.relative_to(task)):hashlib.sha256(path.read_bytes()).hexdigest() for path in (task/'instruction.md',task/'DATA.md',author/'grading-template.json')})
contract=Path('docs/CONTRACT.md');recipes[str(contract)]=hashlib.sha256(contract.read_bytes()).hexdigest()
(evidence/'recipe-and-contract-sha256.json').write_text(json.dumps(recipes,indent=2)+'\n')
print(json.dumps(dict(commit=head,cases=len(catalog),main_unchanged=True)))
