"""Run only inside a disposable private verifier; actual C++ build/execute probes."""
import json,hashlib,os,subprocess,sys,tempfile,shutil
from pathlib import Path
sys.path.insert(0,'/tests');import source_repair as backend
mode=sys.argv[1];config=json.loads(Path('/tests/source-repair.json').read_text());public=Path(config['runner']).parents[1]
logs=Path('/logs/verifier');logs.mkdir(parents=True,exist_ok=True);logs.chmod(0o700);Path('/tests').chmod(0o700);Path('/probe').chmod(0o700)
submission=Path('/app/submission');submission.mkdir(exist_ok=True)
for row in config['replacements']:(submission/row['submission']).write_bytes((Path('/probe')/row['submission']).read_bytes())
if mode=='extra':(submission/'extra.cpp').write_text('')
if mode=='syntax':(submission/'FlowReactor.cpp').write_text('invalid C++ !!!')
if mode=='baseline-compiler':Path('/usr/bin/g++').rename('/usr/bin/g++disabled')
if mode=='valid':
 for n in config['rebuild_files']:os.utime(n,(4102444800,4102444800))
if mode=='runtime-timeout':
 p=submission/'FlowReactor.cpp';s=p.read_text();s='#include <fstream>\n#include <unistd.h>\n'+s
 needle='void FlowReactor::evalDae(double time, double* y, double* ydot, double* residual)\n{'
 assert needle in s;s=s.replace(needle,needle+'\n    std::ofstream("/tmp/probe-loop.pid") << getpid(); while(true) {}');p.write_text(s)
try:backend.prepare()
except backend.SubmissionError as e:
 assert mode in ['extra','syntax'];assert e.status==('invalid_submission' if mode=='extra' else 'build_error'),e.status;print(json.dumps({'mode':mode,'passed':True,'classification':e.status}));raise SystemExit()
except RuntimeError as e:
 assert mode=='baseline-compiler' and 'Trusted baseline build failed' in str(e),str(e);print(json.dumps({'mode':mode,'passed':True,'classification':'infrastructure_error'}));raise SystemExit()
assert mode in ['valid','runtime-timeout']
import judge
with tempfile.TemporaryDirectory() as temp:
 d=Path(temp);d.chmod(0o700);os.chown(d,1000,1000);shutil.copytree(public/'samples/01/input',d/'input');case_logs=logs/'sample';case_logs.mkdir();result=judge.execute(d,3 if mode=='runtime-timeout' else 60,case_logs)
 if mode=='runtime-timeout':
  assert result['status']=='timeout',result;pid=Path('/tmp/probe-loop.pid').read_text().strip();stat=Path('/proc')/pid/'stat';assert not stat.exists() or stat.read_text().split()[2]=='Z';print(json.dumps({'mode':mode,'passed':True,'actual_candidate_cpp_timeout':True,'pid':pid,'status':result}));raise SystemExit()
 assert result is None,result
 from caeoj.case_grading import grade_case
 assert grade_case(d/'input/problem.json',d/'result.h5',public/'samples/01/reference/grading.json')['score']==1
status=json.loads((logs/'build/report.json').read_text())
for row in config['replacements']:assert status['sources_sha256'][row['submission']]==hashlib.sha256((submission/row['submission']).read_bytes()).hexdigest()
for n,h in status['built_artifacts_sha256'].items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h
ldd=subprocess.check_output(['ldd',config['rebuild_files'][-1]],text=True);assert config['build_directory']+'/lib/libcantera_shared.so.3' in ldd,ldd
paths=['/tests','/logs/verifier','/probe','/app/submission','/opt/cantera-source/include/cantera/thermo/ThermoPhase.h','/opt/cantera-source/src','/opt/cantera-source/include','/opt/cantera-source/build/src/zeroD/FlowReactor.os']+[row['target'] for row in config['replacements']]+config['rebuild_files']
# Driver and CMake source remain immutable outside the writable incremental build.
driver_src=[str(p) for p in Path('/opt').glob('cantera*-driver/driver.cpp')];cmake_src=[str(p) for p in Path('/opt').glob('cantera*-cmake/CMakeLists.txt')];paths+=driver_src+cmake_src
code="""import os,json,socket
paths=PATH_LIST
a={p:{'read':os.access(p,os.R_OK),'write':os.access(p,os.W_OK)} for p in paths};assert not any(v['write'] for v in a.values());assert all(not a[p]['read'] for p in paths[:3]);assert os.geteuid()==1000
try:socket.create_connection(('1.1.1.1',80),timeout=1);network='allowed'
except OSError:network='denied'
assert network=='denied';print(json.dumps({'uid':os.geteuid(),'permissions':a,'network':network}))
""".replace('PATH_LIST',repr(paths))
r=subprocess.run(['setpriv','--reuid=1000','--regid=1000','--clear-groups','--no-new-privs','python','-c',code],text=True,capture_output=True)
if r.returncode:raise RuntimeError(r.stdout+'\n'+r.stderr)
print(json.dumps({'mode':mode,'passed':True,'ldd':ldd,'binding':json.loads(r.stdout),'build':status,'cpu_max':Path('/sys/fs/cgroup/cpu.max').read_text(),'memory_max':Path('/sys/fs/cgroup/memory.max').read_text()}))
