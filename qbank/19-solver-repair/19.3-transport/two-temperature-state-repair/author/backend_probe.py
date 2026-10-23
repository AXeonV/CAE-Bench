"""Run in a disposable private verifier; test trusted compilation and actual candidate binding."""
import json,hashlib,os,subprocess,sys,tempfile,shutil
from pathlib import Path
sys.path.insert(0,'/tests')
import source_repair as b
mode=sys.argv[1];config=json.loads(Path('/tests/source-repair.json').read_text());public=Path('/app/qbank/19-solver-repair/19.3-transport/two-temperature-state-repair')
logs=Path('/logs/verifier');logs.mkdir(parents=True,exist_ok=True);logs.chmod(0o700);Path('/tests').chmod(0o700);Path('/probe').chmod(0o700)
s=Path('/app/submission');s.mkdir(exist_ok=True);p=s/'PlasmaPhase.h';p.write_bytes(Path('/probe/PlasmaPhase.h').read_bytes())
if mode=='extra':(s/'extra.cpp').write_text('')
if mode=='syntax':p.write_text('this is invalid C++ !!!')
if mode=='baseline-compiler':Path('/usr/bin/g++').rename('/usr/bin/g++disabled')
if mode=='valid':
 for n in config['rebuild_files']:os.utime(n,(4102444800,4102444800))
try:b.prepare()
except b.SubmissionError as e:
 assert mode in ['extra','syntax'];assert e.status==('invalid_submission' if mode=='extra' else 'build_error'),e.status
 print(json.dumps({'mode':mode,'passed':True,'classification':e.status}));raise SystemExit()
except RuntimeError as e:
 assert mode=='baseline-compiler' and 'Trusted baseline build failed' in str(e),str(e)
 print(json.dumps({'mode':mode,'passed':True,'classification':'infrastructure_error'}));raise SystemExit()
assert mode=='valid'
import judge
with tempfile.TemporaryDirectory() as td:
 d=Path(td);d.chmod(0o700);os.chown(d,1000,1000);shutil.copytree(public/'samples/01/input',d/'input');case_logs=logs/'sample';case_logs.mkdir()
 assert judge.execute(d,30,case_logs) is None
 from caeoj.case_grading import grade_case
 assert grade_case(d/'input/problem.json',d/'result.h5',public/'samples/01/reference/grading.json')['score']==1
status=json.loads((logs/'build/report.json').read_text());assert status['sources_sha256']['PlasmaPhase.h']==hashlib.sha256(p.read_bytes()).hexdigest()
for n,h in status['built_artifacts_sha256'].items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h
ldd=subprocess.check_output(['ldd','/opt/cantera-source/build/bin/plasma-driver'],text=True);assert '/opt/cantera-source/build/lib/libcantera_shared.so.3' in ldd,ldd
code="""import os,json,socket
from pathlib import Path
paths=['/tests','/logs/verifier','/probe','/app/submission','/opt/cantera-source/include/cantera/thermo/PlasmaPhase.h','/opt/cantera-source/include/cantera/thermo/ThermoPhase.h','/opt/cantera-source/src/thermo/PlasmaPhase.cpp','/opt/cantera-source','/opt/cantera-source/src','/opt/cantera-source/include','/opt/repair-driver','/opt/repair-driver/driver.cpp','/opt/repair-cmake','/opt/repair-cmake/CMakeLists.txt','/opt/cantera-source/build/bin/plasma-driver','/opt/cantera-source/build/lib/libcantera_shared.so.3.1.0']
a={p:{'read':os.access(p,os.R_OK),'write':os.access(p,os.W_OK)} for p in paths};assert not any(v['write'] for v in a.values());assert all(not a[p]['read'] for p in paths[:3]);assert os.geteuid()==1000
try:socket.create_connection(('1.1.1.1',80),timeout=1);network='allowed'
except OSError:network='denied'
assert network=='denied';print(json.dumps({'uid':os.geteuid(),'permissions':a,'network':network}))
"""
r=subprocess.run(['setpriv','--reuid=1000','--regid=1000','--clear-groups','--no-new-privs','python','-c',code],text=True,capture_output=True)
if r.returncode:raise RuntimeError(r.stdout+'\n'+r.stderr)
print(json.dumps({'mode':mode,'passed':True,'ldd':ldd,'binding':json.loads(r.stdout),'build':status,'cpu_max':Path('/sys/fs/cgroup/cpu.max').read_text(),'memory_max':Path('/sys/fs/cgroup/memory.max').read_text()}))
