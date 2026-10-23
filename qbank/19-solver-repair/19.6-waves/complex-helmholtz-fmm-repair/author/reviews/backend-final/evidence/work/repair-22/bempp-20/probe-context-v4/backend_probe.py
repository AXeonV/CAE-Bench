"""Private actual trusted-backend probes for the frozen public package."""
from pathlib import Path
import sys,json,subprocess,os,tempfile,shutil,hashlib
sys.path.insert(0,'/tests')
import source_repair as backend
mode=sys.argv[1];cfg=json.loads(Path('/tests/source-repair.json').read_text());public=Path('/app/qbank/19-solver-repair/19.6-waves/complex-helmholtz-fmm-repair')
logs=Path('/logs/verifier');logs.mkdir(parents=True,exist_ok=True);logs.chmod(0o700)
for p in ['/tests','/probe']:Path(p).chmod(0o700)
submission=Path('/app/submission');submission.mkdir(exist_ok=True)
for row in cfg['replacements']:
 p=submission/row['submission'];src=Path('/probe')/p.name
 if mode=='symlink' and p.name=='exafmm.py':p.symlink_to(src)
 else:p.write_bytes(src.read_bytes())
if mode=='extra':(submission/'extra.py').write_text('')
if mode=='syntax':(submission/'helpers.py').write_text('invalid python !!!')
if mode=='compiler':Path('/opt/bempp-env/bin/python').rename('/opt/bempp-env/bin/python-disabled-probe')
if mode=='baseline-runtime':Path('/opt/repair-driver/driver.py').write_text('raise RuntimeError("deliberate broken original runtime")')
if mode=='runtime-timeout':
 p=submission/'exafmm.py';p.write_bytes(p.read_bytes()+b'\nimport os,time\nopen("/tmp/bempp-loop.pid","w").write(str(os.getpid()))\nwhile True: time.sleep(1)\n')
before={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in cfg['rebuild_files']}
if mode=='valid':
 for p in cfg['rebuild_files']:os.utime(p,(4102444800,4102444800))
try:backend.prepare()
except backend.SubmissionError as exc:
 assert mode in ['extra','symlink','syntax']
 expected='build_error' if mode=='syntax' else 'invalid_submission';assert exc.status==expected
 print(json.dumps(dict(mode=mode,passed=True,classification=exc.status)));sys.exit()
except RuntimeError as exc:
 assert mode in ['compiler','baseline-runtime'];print(json.dumps(dict(mode=mode,passed=True,classification='infrastructure_error',error=str(exc))));sys.exit()
assert mode in ['valid','runtime-timeout']
import judge
with tempfile.TemporaryDirectory() as temp:
 d=Path(temp);d.chmod(0o700);os.chown(d,1000,1000);shutil.copytree(public/('samples/'+os.environ.get('BEMPP_PROBE_SAMPLE','01')+'/input'),d/'input');case=logs/'sample';case.mkdir()
 result=judge.execute(d,5 if mode=='runtime-timeout' else 600,case)
 if mode=='runtime-timeout':
  assert result['status']=='timeout',result
  pid=Path('/tmp/bempp-loop.pid').read_text().strip();stat=Path('/proc')/pid/'stat';assert not stat.exists() or stat.read_text().split()[2]=='Z'
  print(json.dumps(dict(mode=mode,passed=True,actual_pid=pid,process_stopped=True)));sys.exit()
 assert result is None,result
 from caeoj.case_grading import grade_case
 assert grade_case(d/'input/problem.json',d/'result.h5',public/('samples/'+os.environ.get('BEMPP_PROBE_SAMPLE','01')+'/reference/grading.json'))['score']==1
code='''import os,json,pathlib,hashlib,socket,importlib
names=['exafmm','fmm_assembler','helpers'];binding={}
for name in names:
 m=importlib.import_module('bempp.api.fmm.'+name)
 binding[name]={'source':m.__file__,'cache':m.__cached__,'source_sha256':hashlib.sha256(pathlib.Path(m.__file__).read_bytes()).hexdigest(),'pyc_sha256':hashlib.sha256(pathlib.Path(m.__cached__).read_bytes()).hexdigest()}
paths=['/tests','/tests/cases','/tests/reference','/logs/verifier','/probe','/app/submission','/opt/repair-driver/driver.py','/opt/bempp-repair-cmake/CMakeLists.txt','/opt/upstream','/opt/bempp-env/bin/python']+[m[k] for m in binding.values() for k in ['source','cache']]
access={p:{'read':os.access(p,os.R_OK),'write':os.access(p,os.W_OK)} for p in paths}
assert all(not v['write'] for v in access.values()),access
assert all(not access[p]['read'] for p in ['/tests','/tests/cases','/tests/reference','/logs/verifier','/probe'])
try:socket.create_connection(('1.1.1.1',80),timeout=1);network='allowed'
except OSError:network='denied'
assert os.geteuid()==1000 and network=='denied'
print(json.dumps({'uid':os.geteuid(),'network':network,'binding':binding,'permissions':access}))
'''
p=subprocess.run(['setpriv','--reuid=1000','--regid=1000','--clear-groups','--no-new-privs','/opt/bempp-env/bin/python','-c',code],text=True,capture_output=True)
assert p.returncode==0,p.stderr
binding=json.loads(p.stdout);build=json.loads((logs/'build/report.json').read_text())
for v in binding['binding'].values():
 assert v['source_sha256']==build['sources_sha256'][Path(v['source']).name]
 assert v['pyc_sha256']==build['built_artifacts_sha256'][v['cache']]
assert all(before[p]!=build['built_artifacts_sha256'][p] for p in before)
print(json.dumps(dict(mode=mode,passed=True,binding=binding,build=build,cpu_max=Path('/sys/fs/cgroup/cpu.max').read_text(),memory_max=Path('/sys/fs/cgroup/memory.max').read_text())))
