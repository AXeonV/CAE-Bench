from pathlib import Path
import json,re,sys
sys.path.insert(0,str(Path('src').resolve()))
from caeoj_tools.continuous_scoring import convert_grading,scoring_text
ROOT=Path.cwd()
plan=json.loads((ROOT/'runs/uniform-samples/plan.json').read_text(encoding='utf-8'))
rows=[]
for x in plan['tasks']:
 if x['chapter']=='00-basic-tests':continue
 task=ROOT/x['task_path'];p=task/'author/grading-template.json'
 old=json.loads(p.read_text(encoding='utf-8'))
 duplicate=task/'author/case-grading-template.json'
 if 'checks' in old: base=old
 elif duplicate.exists():base=json.loads(duplicate.read_text(encoding='utf-8'))
 else:base={'version':1,'checks':[{'id':'outputs','evaluator':'direct_outputs','reference':'reference.h5','policy':old}]}
 updated=convert_grading(base);policy=updated['checks'][0]['policy']
 p.write_text(json.dumps(updated,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 if duplicate.exists():duplicate.unlink()
 inst=task/'instruction.md';t=inst.read_text(encoding='utf-8')
 candidates=list(re.finditer(r'^## (?:输出与判分|判分与运行资源|评分|评价|评分规则|评价规则)\s*$',t,re.M))
 assert len(candidates)==1,(x['task'],len(candidates))
 h=candidates[0];end=re.search(r'^## ',t[h.end():],re.M);stop=h.end()+end.start() if end else len(t)
 prior=t[h.end():stop].strip();normal=[]
 for check in updated['checks']:
  if check['evaluator']=='field.normalized_outputs':
   for name,tr in check['transforms'].items():
    if tr.get('remove_mean'):normal.append(f'`{name}` 的候选与参考分别减去本时刻全部观测点上的加权均值后计算误差和参考 RMS；允许常数基准差，不拟合比例或相位。')
    if tr.get('offset'):normal.append(f'`{name}` 的候选与参考均先减去公开固定背景 `{tr["offset"]}` 后计算误差和参考 RMS。')
 body=scoring_text(policy,normalization=' '.join(normal))
 keep=''
 if 'heat-conduction' in x['task']:
  paras=prior.split('\n\n');keep='\n\n'.join(paras[:2])+'\n\n'
  old_resource=next(q for q in paras if '单点墙钟' in q or '每例墙钟' in q)
  marker='单点墙钟' if '单点墙钟' in old_resource else '每例墙钟'
  res=old_resource[old_resource.index(marker):]
  body+='\n'+res.replace('单点','每例')+'\n'
 elif x['chapter']=='01-prescribed-pdes':
  resource=next(q for q in prior.split('\n\n') if '每例求解程序墙钟上限' in q)
  resource=resource[resource.index('每例求解程序墙钟上限'):]
  body+='\n'+resource+'\n'
 inst.write_text(t[:h.end()].rstrip()+'\n\n'+keep+body.rstrip()+'\n\n'+t[stop:],encoding='utf-8')
 entries=policy.get('fields') or {n:q['rule'] for n,q in policy['quantities'].items()}
 rows.append({'task':x['task'],'task_path':x['task_path'],'scoring':updated['scoring'],'floors':{n:r['scale_floor'] for n,r in entries.items()},'weights':{n:r.get('weight_field','equal observation weights') for n,r in entries.items()},'normalized':normal,'reference_offsets':{n:r['reference_offset'] for n,r in entries.items() if 'reference_offset' in r}})
(ROOT/'runs/continuous-scoring/policy-migration.json').write_text(json.dumps({'count':len(rows),'rows':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(len(rows))
