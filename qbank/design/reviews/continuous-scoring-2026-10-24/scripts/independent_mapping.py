"""Independent all-task configuration migration check, without migration helper."""
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from caeoj_tools.grading_policy import author_case_grading
WORK=ROOT/'runs/continuous-scoring'
records=json.loads((WORK/'preparation.json').read_text(encoding='utf-8'))
SCORING={'metric':'max_nrmse','full_credit':.05,'zero_credit':.10}
def read(path): return json.loads(path.read_text(encoding='utf-8'))
def rule(old):
    if old['metric']=='nrmse': floor=old['scale_floor']
    elif old['metric'] in ('pointwise','violation_fraction'): floor=old['atol']
    elif old['metric']=='max_abs': floor=old['limit']
    else: raise AssertionError(old)
    out={'metric':'nrmse','time':'per_time','components':'per_component','limit':.05,'scale_floor':floor}
    out.update({k:v for k,v in old.items() if k in ('reference_offset','weight_field')})
    return out
def policy(old):
    out={'version':old['version']}
    if old['version']==1: out['fields']={k:rule(v) for k,v in old['fields'].items()}
    else:
        if 'default' in old: out['default']=rule(old['default'])
        if 'quantities' in old: out['quantities']={k:{**v,'rule':rule(v['rule'])} for k,v in old['quantities'].items()}
    return out
def config(old):
    return {**old,'scoring':SCORING,'checks':[{**c,**({'policy':policy(c['policy'])} if 'policy' in c else {'rule':rule(c['rule'])})} for c in old['checks']]}
tasks=[];total=0;unchanged=0;author_count=0
for rec in records:
    formal=list((Path(rec['prepared'])/'reference').glob('*/grading.json'))
    assert len(formal)==rec['case_count'], rec['task']
    if rec['chapter'].startswith('00-'):
        for path in formal:
            before=Path(rec['original_root'])/'reference'/path.parent.name/'grading.json'
            assert path.read_bytes()==before.read_bytes()
            assert 'scoring' not in read(path)
        unchanged+=len(formal)
    else:
        task=next(ROOT.glob('qbank/**/'+rec['task']+'/instruction.md')).parent
        template=author_case_grading(task)
        assert template['scoring']==SCORING,rec['task']
        assert not (task/'author/case-grading-template.json').exists(),rec['task']
        for path in formal:
            before=Path(rec['original_root'])/'reference'/path.parent.name/'grading.json'
            assert read(path)==config(read(before)), str(path)
            current=read(path)
            assert current['scoring']==template['scoring'],str(path)
            assert len(current['checks'])==len(template['checks']),str(path)
            # Check IDs label diagnostics; they do not bind numerical targets.
            for actual,planned in zip(current['checks'],template['checks']):
                assert {k:v for k,v in actual.items() if k!='id'}=={k:v for k,v in planned.items() if k!='id'},(str(path),actual,planned)
        author_count+=1
        total+=len(formal)
    tasks.append({'task':rec['task'],'cases':len(formal),'mode':'binary' if rec['chapter'].startswith('00-') else 'continuous','status':'passed',**({} if rec['chapter'].startswith('00-') else {'author_template_sha256':hashlib.sha256((task/'author/grading-template.json').read_bytes()).hexdigest()})})
assert len(tasks)==82 and total==630 and unchanged==17 and author_count==80
sources=['src/caeoj/case_grading.py','src/caeoj/grading_metrics.py','src/caeoj/grading_policy.py','src/caeoj/case-grading.schema.json','src/caeoj/grading.schema.json','src/utils/harbor/tests/judge.py','qbank/extensions/caeoj_ext/normalized_fields.py','src/caeoj_tools/grading_policy.py','src/caeoj_tools/continuous_scoring.py','src/utils/PDEBench/pipeline.py','qbank/01-prescribed-pdes/1.1-elliptic/heat-conduction-steady-2d/author/generate.py','qbank/01-prescribed-pdes/1.2-diffusion-reaction/heat-conduction-transient-2d/author/generate.py','qbank/02-fluid-mechanics/2.13-cfdcodebench/author/render.py','qbank/02-fluid-mechanics/2.13-cfdcodebench/author/build_local.py','qbank/maintenance/authoring/verify_install.py']
sources.append('qbank/02-fluid-mechanics/author/ten-case-candidates/build_designs.py')
out={'status':'passed','tasks':tasks,'continuous_cases':total,'unchanged_binary_cases':unchanged,'complete_author_plans':author_count,'scope':'all prepared formal grading configs versus immutable RC4 originals; independent conversion implementation; all 80 complete current author templates versus every prepared formal grading','reviewed_source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources}}
(WORK/'independent-mapping.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'status':'passed','tasks':len(tasks),'continuous_cases':total,'unchanged_binary_cases':unchanged}))
