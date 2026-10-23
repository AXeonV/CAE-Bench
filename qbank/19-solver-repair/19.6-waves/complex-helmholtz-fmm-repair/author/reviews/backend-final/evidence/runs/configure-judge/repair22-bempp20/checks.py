"""Read-only backend/version audit; never prepare or launch an Oracle."""
from pathlib import Path
import sys,json,hashlib,zipfile,difflib,subprocess,datetime,struct

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
TASK=ROOT/'qbank/19-solver-repair/19.6-waves/complex-helmholtz-fmm-repair'
def sha(data):return hashlib.sha256(data).hexdigest()
def fileinfo(p):return {'path':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
def save(name,data):(OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
old=ROOT/'runs/authoring/repair-22/bempp-oracle-v1-prepared/tests/agent.zip'
new=ROOT/'dist/complex-helmholtz-fmm-repair-agent.zip'
with zipfile.ZipFile(old) as a,zipfile.ZipFile(new) as b:
    aa={n:a.read(n) for n in a.namelist()};bb={n:b.read(n) for n in b.namelist()}
    diff={'old':fileinfo(old),'new':fileinfo(new),'old_count':len(aa),'new_count':len(bb),'added':sorted(bb.keys()-aa.keys()),'removed':sorted(aa.keys()-bb.keys()),'members':[], 'changed':[]}
    for n in sorted(aa.keys()|bb.keys()):
        diff['members'].append({'name':n,'old_sha256':sha(aa[n]) if n in aa else None,'new_sha256':sha(bb[n]) if n in bb else None})
        if n in aa and n in bb and aa[n]!=bb[n]:
            diff['changed'].append({'name':n,'diff':''.join(difflib.unified_diff(aa[n].decode().splitlines(True),bb[n].decode().splitlines(True),fromfile='old',tofile='new'))})
    diff['private_names']=[n for n in bb if any(x in n.split('/') for x in ['author','cases','harbor']) or n.startswith('tests/')]
save('zip-comparison.json',diff)
probes=ROOT/'runs/authoring/repair-22/bempp-backend-probes-v1'
probe_results=[]
for row in json.loads((probes/'report.json').read_text()):
    if row['mode']=='image-build':continue
    log=probes/(row['mode']+'.stdout.log')
    result=json.loads(log.read_text().strip().splitlines()[-1]);assert result['passed'] and row['returncode']==0
    probe_results.append({'mode':row['mode'],'run':row,'result':result,'stdout':fileinfo(log),'stderr':fileinfo(log.with_name(row['mode']+'.stderr.log'))})
save('probes-independent.json',{'origin_zip':fileinfo(ROOT/'work/repair-22/bempp-20/probe-context/tests/agent.zip'),'fixture':fileinfo(ROOT/'work/repair-22/bempp-20/backend_probe.py'),'probe_context_fixture':fileinfo(ROOT/'work/repair-22/bempp-20/probe-context/backend_probe.py'),'results':probe_results})
sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'src/utils'))
from prepare_harbor import task_config
import tomllib
config=json.loads((TASK/'judge-config.json').read_text());repair=json.loads((TASK/'harbor/source-repair.json').read_text())
merged=tomllib.loads(task_config((ROOT/'src/utils/harbor/task.toml').read_text(),tomllib.loads((TASK/'harbor/task.toml').read_text()),judge_config=config,case_count=12))
versions=[ROOT/'docs/CONTRACT.md',TASK/'instruction.md',TASK/'DATA.md',TASK/'judge-config.json',TASK/'harbor/source-repair.json',TASK/'harbor/task.toml',TASK/'public/CMakeLists.txt',TASK/'public/driver.py',TASK/'public/run_case.py',TASK/'extension/runtime.json',TASK/'extension/caeoj_task_ext/helmholtz.py',ROOT/'src/caeoj_tools/source_repair.py',ROOT/'src/utils/harbor/tests/source_repair.py',ROOT/'src/utils/harbor/tests/judge.py',ROOT/'src/utils/prepare_harbor.py']
snapshot=ROOT/'runs/authoring/repair-22/bempp-oracle-v1-prepared'
v1=json.loads((ROOT/'runs/authoring/repair-22/repair22-bempp20-oracle-v1.json').read_text())
recorded=v1['task_sha256'];snapshot_mismatches=[]
for name,h in recorded.items():
    p=snapshot/name
    if not p.exists() or sha(p.read_bytes())!=h:snapshot_mismatches.append(name)
backend_matches={}
for p in [ROOT/'src/utils/harbor/tests/source_repair.py',ROOT/'src/utils/harbor/tests/judge.py',TASK/'harbor/source-repair.json',TASK/'judge-config.json']:
    dest='tests/'+('source-repair.json' if p.name=='source-repair.json' else p.name)
    backend_matches[dest]={'exact':p.read_bytes()==(snapshot/dest).read_bytes(),'normalized_lf':p.read_bytes().replace(b'\r\n',b'\n')==(snapshot/dest).read_bytes().replace(b'\r\n',b'\n')}
save('configuration-and-identity.json',{'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'versions':[fileinfo(p) for p in versions],'merged_task':merged,'minimum_explicit_budget':60+60+60+12*(600+30),'remaining_overhead_seconds':merged['verifier']['timeout_sec']-(60+60+60+12*(600+30)),'v1_snapshot_count':len(recorded),'v1_snapshot_mismatches':snapshot_mismatches,'current_backend_matches_old_snapshot_lf':backend_matches,'pipeline_state':json.loads((ROOT/'runs/authoring/repair-22/bempp-final-oracle-pipeline.json').read_text()),'v1_run_phase':v1['phase'],'v1_has_returncode':'returncode' in v1})
plans=[]
from caeoj.case_grading import prepare_case
from caeoj.sdk import load_problem
for path in sorted((TASK/'cases').glob('*/problem.json')):
    m=json.loads(path.read_text());grading=TASK/'reference'/path.parent.name/'grading.json'
    plan=json.loads(grading.read_text());pol=plan['checks'][0]['policy']['quantities']
    bindings={}
    for name,v in m['outputs'].items():
        q=pol[v['quantity']];assert q['unit']==v['unit']
        assert q['rule']=={'metric':'pointwise','time':'per_time','components':'per_component','atol':1e-6,'rtol':1e-5}
        bindings[name]={'quantity':v['quantity'],'array':v['array'],'components':v['components'],'unit':v['unit'],'rule':q['rule']}
    prepared=prepare_case(load_problem(path),grading)
    plans.append({'case':path.parent.name,'problem':fileinfo(path),'grading':fileinfo(grading),'reference':fileinfo(grading.parent/'reference.h5'),'bindings':bindings,'preflight_evidence':prepared.evidence})
save('actual-case-plans.json',plans)
refs=json.loads((ROOT/'work/repair-22/bempp-20/dataset-v2/reference-report.json').read_text())
save('reference-run-summary.json',{'report':fileinfo(ROOT/'work/repair-22/bempp-20/dataset-v2/reference-report.json'),'keys':list(refs),'image_id':refs['image_id'],'driver_sha256':refs['driver_sha256'],'case_results':[{'case':x['case'],'score':x['score'],'returncode':x['returncode'],'elapsed_seconds':x['elapsed_seconds'],'output_sha256':x['output_sha256']} for x in refs['cases']]})
print(json.dumps({'changed':[x['name'] for x in diff['changed']],'private_names':diff['private_names'],'merged_task':merged,'snapshot_count':len(recorded),'snapshot_mismatches':snapshot_mismatches,'backend_matches':backend_matches,'probes':len(probe_results)},ensure_ascii=False))
