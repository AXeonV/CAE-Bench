"""Disposable actual ASPECT builds against the frozen shared trusted backend."""
import hashlib,json,os,shutil,subprocess,sys,tempfile,threading,time,re
from pathlib import Path
sys.path.insert(0,'/tests')
import source_repair as backend
mode=sys.argv[1];config=json.loads(Path('/tests/source-repair.json').read_text());task=Path(config['runner']).parents[1]
logs=Path('/logs/verifier');logs.mkdir(parents=True,exist_ok=True)
for p in [logs,Path('/tests'),Path('/probe')]:p.chmod(0o700)
submission=Path('/app/submission');submission.mkdir(exist_ok=True);source=submission/'core.cc';source.write_bytes(Path('/probe/core.cc').read_bytes())
def evidence():
 return {'reports':{p.name:json.loads(p.read_text()) for p in (logs/'build').glob('*report.json')},'stderr_tails':{p.name:p.read_text()[-2500:] for p in (logs/'build').glob('*stderr.log')}}
if mode=='extra':(submission/'extra.cc').write_text('')
if mode=='symlink':source.unlink();source.symlink_to('/probe/core.cc')
if mode=='syntax':source.write_text('invalid C++ source !!!\n')
if mode=='compiler':Path('/usr/bin/c++').rename('/usr/bin/c++-disabled-probe')
if mode=='baseline-runtime':(task/'public/baseline_probe.py').rename(task/'public/baseline_probe-disabled.py')
if mode=='protected-include':source.write_text('#include "/tests/source-repair.json"\n'+source.read_text())
if mode=='valid':
 for name in config['rebuild_files']:os.utime(name,(4102444800,4102444800))
if mode=='runtime-timeout':
 text=source.read_text();needle='  compute_current_constraints ()\n  {';assert text.count(needle)==1
 text='#include <unistd.h>\n#include <fstream>\n'+text
 source.write_text(text.replace(needle,needle+'\n    std::ofstream("/tmp/aspect-timeout-native-pid") << getpid();\n    for (;;) sleep(1);\n'))
(logs/'source-repair.json').write_text(json.dumps(config,indent=2))
if source.is_file():(logs/'actual-submission-core.cc').write_bytes(source.read_bytes())
try:backend.prepare()
except backend.SubmissionError as exc:
 expected='build_error' if mode in ['syntax','protected-include'] else 'invalid_submission'
 assert mode in ['extra','symlink','syntax','protected-include'] and exc.status==expected,(mode,exc.status)
 if mode=='protected-include':assert 'Permission denied' in (logs/'build/candidate-stderr.log').read_text()
 print(json.dumps({'mode':mode,'passed':True,'classification':exc.status,**evidence()}));raise SystemExit()
except RuntimeError as exc:
 expected='Trusted baseline build failed: build_error' if mode=='compiler' else 'Trusted baseline runtime probe failed: probe_error'
 assert mode in ['compiler','baseline-runtime'] and str(exc)==expected,(mode,str(exc))
 print(json.dumps({'mode':mode,'passed':True,'classification':'infrastructure_error','reason':str(exc),**evidence()}));raise SystemExit()
assert mode in ['valid','runtime-timeout']
import judge
from caeoj.case_grading import grade_case
samples=[]
for sample in (['01'] if mode=='runtime-timeout' else ['01','02']):
 with tempfile.TemporaryDirectory() as tmp:
  directory=Path(tmp);directory.chmod(0o700);os.chown(directory,1000,1000);shutil.copytree(task/'samples'/sample/'input',directory/'input')
  runlogs=logs/('sample-'+sample);runlogs.mkdir()
  sentinel=subprocess.Popen(['setpriv','--reuid=1000','--regid=1000','--clear-groups','sleep','120'])
  try:
   result=judge.execute(directory,3 if mode=='runtime-timeout' else 60,runlogs)
   assert sentinel.poll() is None,'Unrelated same UID process was killed'
  finally:sentinel.kill();sentinel.wait()
  if mode=='runtime-timeout':
   assert result['status']=='timeout',result
   pid=int(Path('/tmp/aspect-timeout-native-pid').read_text());assert not Path('/proc',str(pid)).exists(),pid
   print(json.dumps({'mode':mode,'passed':True,'actual_native_candidate_timeout':True,'native_pid':pid,'native_absent_including_zombie':True,'unrelated_same_uid_sentinel_survived':True,**evidence()}));raise SystemExit()
  assert result is None,result
  score=grade_case(directory/'input/problem.json',directory/'result.h5',task/'samples'/sample/'reference/grading.json')
  assert score['score']==1,score;samples.append({'sample':sample,'status':score['status'],'score':score['score']})
  shutil.copytree(directory/'input',runlogs/'actual-input');shutil.copyfile(directory/'result.h5',runlogs/'actual-result.h5')
report=json.loads((logs/'build/report.json').read_text())
assert report['sources_sha256']['core.cc']==hashlib.sha256(source.read_bytes()).hexdigest()
for name,digest in report['built_artifacts_sha256'].items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest
ldd=subprocess.check_output(['ldd','/opt/aspect-build/aspect-release'],text=True)
dependencies=[]
for line in ldd.splitlines():
 for value in re.findall(r'/[^\s()]+',line):
  p=Path(value)
  if p.exists():dependencies.extend([str(p),str(p.resolve()),*[str(a) for a in p.resolve().parents]])
paths=list(dict.fromkeys(['/tests','/logs/verifier','/probe','/app/submission','/opt/aspect','/opt/aspect/source/simulator/core.cc','/opt/aspect-build','/opt/caeoj-python','/opt/caeoj-python/bin/python',config['runner']]+config['rebuild_files']+dependencies))
code='''import os,json,socket
paths=PATH_LIST
access={p:{'read':os.access(p,os.R_OK),'write':os.access(p,os.W_OK)} for p in paths}
assert os.geteuid()==1000
assert not any(v['write'] for v in access.values()),{p:v for p,v in access.items() if v['write']}
assert all(not access[p]['read'] for p in paths[:3])
try:socket.create_connection(('1.1.1.1',80),timeout=1);network='allowed'
except OSError:network='denied'
assert network=='denied'
import caeoj.sdk,numpy,h5py,gmsh
print(json.dumps({'uid':os.geteuid(),'permissions':access,'network':network,'python':__import__('sys').executable,'numpy':numpy.__version__}))
'''.replace('PATH_LIST',repr(paths))
r=subprocess.run(['setpriv','--reuid=1000','--regid=1000','--clear-groups','--no-new-privs','python','-c',code],text=True,capture_output=True,env={'PATH':'/usr/local/bin:/usr/bin:/bin','HOME':'/home/solver'})
assert r.returncode==0,r.stdout+'\n'+r.stderr
print(json.dumps({'mode':mode,'passed':True,'future_mtime_artifacts_actually_rebuilt':True,'samples':samples,'ldd':ldd,'binding':json.loads(r.stdout),'cpu_max':Path('/sys/fs/cgroup/cpu.max').read_text(),'memory_max':Path('/sys/fs/cgroup/memory.max').read_text(),'memory_peak':Path('/sys/fs/cgroup/memory.peak').read_text(),**evidence()}))
