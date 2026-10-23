from pathlib import Path
import hashlib,json,tomllib
R=Path(__file__).resolve().parents[3];T=R/'qbank/19-solver-repair/19.6-waves/cylindrical-field-pml-repair';E=T/'author/data-evidence';O=Path(__file__).parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
materials={};report={};cfg=read(T/'harbor/source-repair.json');prepared=R/'runs/harbor/tasks/cylindrical-field-pml-repair';context=R/'work/repair-22/meep-2338/probe-context'
for n in ['source_repair.py','judge.py']:
 current=R/'src/utils/harbor/tests'/n
 assert (prepared/'tests'/n).read_bytes()==(context/'tests'/n).read_bytes()
 assert current.read_text()==(prepared/'tests'/n).read_text() # prepare_harbor normalizes textual CRLF to LF.
for n in ['source-repair.json','judge-config.json','agent.zip','selection.json']:
 assert (prepared/'tests'/n).read_bytes()==(context/'tests'/n).read_bytes(),n
assert (context/'step_db.cpp').read_bytes()==(T/'author/generated/step_db.cpp').read_bytes()
report['probe_and_formal_code_configuration_data_zip_closure']=True
state=read(E/'formal-oracle/runner-state.json')
assert all(sha(prepared/n)==digest for n,digest in state['task_sha256'].items())
report['formal_task_frozen_files']=len(state['task_sha256'])
for label in ['baseline','candidate']:
 path=E/('formal-oracle/build/'+label+'-stdout.log');s=path.read_text()
 for text in ['CXX      step_db.lo','CXXLD    libmeep.la','Building CXX object CMakeFiles/cylindrical_driver.dir/opt/meep-driver/driver.cpp.o','Linking CXX executable bin/cylindrical-driver']:assert text in s,(label,text)
report['formal_both_builds_actual_step_db_TU_library_driver']=True
build=read(E/'formal-oracle/build/report.json');baseline=read(E/'formal-oracle/build/baseline-report.json');health=read(E/'formal-oracle/build/baseline-probe-report.json')
assert build['sources_sha256']['step_db.cpp']==sha(T/'author/generated/step_db.cpp')
assert build['removed_build_artifacts']==baseline['removed_build_artifacts']==cfg['rebuild_files']
assert set(build['built_artifacts_sha256'])==set(cfg['rebuild_files']) and len(cfg['rebuild_files'])==7
report['formal_build']={'baseline_seconds':baseline['elapsed_seconds'],'candidate_seconds':build['elapsed_seconds'],'health_seconds':health['elapsed_seconds'],'source_sha256':build['sources_sha256'],'artifacts_sha256':build['built_artifacts_sha256']}
native=read(E/'formal-oracle/trial-result.json');verdict=read(E/'formal-oracle/verifier-report.json');assert native['exception_info'] is None
assert verdict['complete'] and verdict['score']==verdict['total_cases']==8 and verdict['reward']==1
assert len(verdict['cases'])==8 and all(x['status']=='accepted' for x in verdict['cases'])
report['formal_result']={'exception_info':native['exception_info'],'complete':True,'score':8,'total':8,'reward':1}
probes=read(E/'backend-probes.json');report['probes']=[]
for probe in probes:
 mode=probe['mode'];p=R/'runs/authoring/repair-22/meep2338-backend-probes'/(mode+'.stdout.log');raw=read(p)
 # Author manifest adds outer command/elapsed metadata; inner native JSON must match every original evidence key.
 assert all(probe[k]==v for k,v in raw.items()),mode
 assert raw['passed'] and probe['exit_code']==0
 row={'mode':mode,'actual_raw_json_matches':True,'classification':raw.get('classification','built/native-run')}
 if mode=='valid':
  assert raw['prepared_agent_zip_sha256']==sha(R/'dist/cylindrical-field-pml-repair-agent.zip')
  assert raw['binding']['uid']==1000 and raw['binding']['network']=='denied'
  assert raw['cpu_max'].strip()=='400000 100000' and raw['memory_max'].strip()=='4294967296'
  assert all(not x['write'] for x in raw['binding']['permissions'].values())
  assert all(not raw['binding']['permissions'][x]['read'] for x in ['/tests','/probe','/logs/verifier'])
  assert raw['build']['sources_sha256']['step_db.cpp']==sha(context/'step_db.cpp')
  assert raw['build']['removed_build_artifacts']==raw['baseline_build']['removed_build_artifacts']==cfg['rebuild_files']
  assert len(raw['build']['built_artifacts_sha256'])==7
  row.update(uid=1000,network='denied',cpu_max=raw['cpu_max'],memory_max=raw['memory_max'],all_7_artifacts_rebuilt=True,future_mtime_injection_in_probe_source='4102444800' in (T/'author/backend_probe.py').read_text())
 if mode=='runtime-timeout':
  assert raw['actual_cpp_timeout'] and raw['post_kill_states'][-1] in ['Z','absent'];row.update(child_pid=raw['child_pid'],post_kill_states=raw['post_kill_states'],scope='actual instrumented native main PID only')
 report['probes'].append(row)
assert len(report['probes'])==7
resources=tomllib.loads((prepared/'task.toml').read_text());judge=read(prepared/'tests/judge-config.json')
assert resources['verifier']['timeout_sec']==1000+8*(1800+30+5)==15680
assert resources['environment']['cpus']==4 and resources['environment']['memory_mb']==4096 and resources['verifier']['network_mode']=='no-network'
report['budgets']={'baseline_compile':cfg['baseline_timeout_seconds'],'candidate_compile':cfg['build_timeout_seconds'],'health_probe':min(60,cfg['build_timeout_seconds']),'per_case':judge['timeout_seconds'],'evaluation':judge['evaluation_timeout_seconds'],'outer':15680,'minimum_without_overheads':300+300+60+8*(1800+30),'resources':resources}
corner=read(E/'resource-corner.json');assert corner['native_elapsed_seconds']<1800 and corner['exit_code']==0 and corner['uid']==1000
report['corner']={k:corner[k] for k in ['payload','time_steps','nominal_cells','native_elapsed_seconds','memory_peak','cpu_max','memory_max']}
for p in [*E.rglob('*'),*prepared.rglob('*'),*context.rglob('*'),R/'src/caeoj/case_grading.py',R/'src/utils/harbor/tests/source_repair.py',R/'src/utils/harbor/tests/judge.py',R/'src/utils/prepare_harbor.py',R/'src/caeoj_tools/source_repair.py',T/'author/backend_probe.py']:
 if p.is_file() and '__pycache__' not in str(p):materials[str(p.relative_to(R))]=sha(p)
dump(O/'actual-evidence.json',report);dump(O/'materials-sha256.json',materials)
print(json.dumps({'formal':report['formal_result'],'probes':report['probes'],'frozen_task_files':report['formal_task_frozen_files'],'outer':15680},indent=2))
