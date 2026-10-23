import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];WORK=ROOT/'work/repair-22/aspect-6818';PREP=ROOT/'runs/harbor/tasks/deformed-tangential-boundary-repair';OUT=Path(__file__).parent
context=WORK/'backend-probe-context-v4';logs=WORK/'backend-probe-evidence-v4';report={'binding':{},'probes':{},'pending':[]}
for name in ['agent.zip','source_repair.py','source-repair.json','judge.py','judge-config.json','selection.json']:
 a=(context/'tests'/name).read_bytes();b=(PREP/'tests'/name).read_bytes();assert a==b,name;report['binding'][name]=hashlib.sha256(a).hexdigest()
for mode in ['valid','runtime-timeout','syntax','baseline-runtime','protected-include','compiler','extra','symlink']:
 p=logs/(mode+'.stdout.json');state=json.loads((logs/(mode+'-state.json')).read_text())
 if not p.exists() or not p.stat().st_size or state['phase']!='complete':report['pending'].append(mode);continue
 assert state['last_returncode']==0
 row=json.loads(p.read_text());assert row['passed'] and row['mode']==mode
 raw=logs/(mode+'-raw/verifier/build')
 for name,value in row.get('reports',{}).items():assert json.loads((raw/name).read_text())==value,(mode,name)
 if mode=='valid':
  assert row['future_mtime_artifacts_actually_rebuilt'] and len(row['samples'])==2 and all(x['score']==1 for x in row['samples'])
  assert row['cpu_max'].strip()=='400000 100000' and row['memory_max'].strip()=='8589934592'
  assert row['binding']['uid']==1000 and row['binding']['network']=='denied'
  assert not any(x['write'] for x in row['binding']['permissions'].values())
  assert all(not row['binding']['permissions'][k]['read'] for k in ['/tests','/logs/verifier','/probe'])
  assert 'not found' not in row['ldd']
  for name in ['baseline','candidate']:
   text=(raw/(name+'-stdout.log')).read_text();assert 'Building CXX object CMakeFiles/aspect.exe.release.dir/Unity/unity_45_cxx.cxx.o' in text and 'Linking CXX executable aspect-release' in text
 if mode=='runtime-timeout':assert row['actual_native_candidate_timeout'] and row['native_absent_including_zombie'] and row['unrelated_same_uid_sentinel_survived']
 if mode in ['syntax','protected-include']:assert row['classification']=='build_error'
 if mode=='protected-include':assert 'Permission denied' in (raw/'candidate-stderr.log').read_text()
 if mode in ['compiler','baseline-runtime']:assert row['classification']=='infrastructure_error'
 if mode in ['extra','symlink']:assert row['classification']=='invalid_submission'
 report['probes'][mode]=row
report['complete']=not report['pending'];(OUT/'probe-check.json').write_text(json.dumps(report,indent=2));print({'complete':report['complete'],'passed':list(report['probes']),'pending':report['pending']})
