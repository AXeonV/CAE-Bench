"""Run in a disposable verifier: verify actual compiler, loading and isolation."""
import hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path
sys.path.insert(0,'/tests')
import source_repair as backend
mode=sys.argv[1];public=Path('/app/qbank/19-solver-repair/19.1-constraints/hysteretic-trial-state-repair');submission=Path('/app/submission');logs=Path('/logs/verifier');logs.mkdir(parents=True,exist_ok=True);logs.chmod(0o700);Path('/tests').chmod(0o700);submission.mkdir(exist_ok=True)
config=json.loads(Path('/tests/source-repair.json').read_text());library=Path('/opt/material-build/material_driver');before=hashlib.sha256(library.read_bytes()).hexdigest()
for row in config['replacements']:
 candidate=submission/row['submission'];reference=Path('/probe')/row['submission']
 if mode=='symlink':candidate.symlink_to(reference)
 else:candidate.write_bytes(b'invalid C++ !!!' if mode=='syntax' else reference.read_bytes())
if mode=='extra':(submission/'extra.cpp').write_text('')
if mode=='compiler':Path('/usr/bin/c++').rename('/usr/bin/c++-disabled')
if mode=='baseline-runtime':Path('/opt/material-driver/probe-input.txt').rename('/opt/material-driver/probe-input-disabled.txt')
if mode=='valid':
    for name in config['rebuild_files']:os.utime(name,(4102444800,4102444800))
try:backend.prepare()
except backend.SubmissionError as e:
    expected='build_error' if mode=='syntax' else 'invalid_submission';assert mode in ['syntax','extra','symlink'] and e.status==expected,(mode,e.status);print(json.dumps({'mode':mode,'passed':True,'classification':e.status}));raise SystemExit()
except RuntimeError as e:
    expected='Trusted baseline runtime probe failed' if mode=='baseline-runtime' else 'Trusted baseline build failed';assert mode in ['compiler','baseline-runtime'] and expected in str(e),str(e);print(json.dumps({'mode':mode,'passed':True,'classification':'infrastructure_error','reason':str(e)}));raise SystemExit()
assert mode=='valid'
after=hashlib.sha256(library.read_bytes()).hexdigest();assert after!=before
code='''import json,os,socket
from pathlib import Path
paths=['/tests/cases','/tests/reference','/logs/verifier','/opt/material-build/material_driver','/opt/material-driver/driver.cpp','/opt/material-driver/CMakeLists.txt','/opt/opensees-source','/opt/opensees-source/SRC/material/uniaxial/HystereticMaterial.h','/opt/opensees-source/SRC/material/uniaxial/HystereticMaterial.cpp','/opt/opensees-source/SRC/material/uniaxial/HystereticSMMaterial.cpp']
r={'uid':os.geteuid(),'access':{p:{'read':os.access(p,os.R_OK),'write':os.access(p,os.W_OK)} for p in paths}}
try:socket.create_connection(('1.1.1.1',80),timeout=1);r['network']='allowed'
except OSError:r['network']='denied'
print(json.dumps(r))'''
def low(command):return subprocess.run(['setpriv','--reuid=1000','--regid=1000','--clear-groups','--no-new-privs',*command],capture_output=True,text=True,check=True)
access=json.loads(low(['python','-c',code]).stdout);assert access['uid']==1000 and access['network']=='denied';assert all(not v['write'] for v in access['access'].values());assert all(not access['access'][p]['read'] for p in ['/tests/cases','/tests/reference','/logs/verifier'])
output='/tmp/material-probe.h5';low(['python',str(public/'public/run_case.py'),'--input',str(public/'samples/02/input/problem.json'),'--output',output]);from caeoj.case_grading import grade_case
assert grade_case(public/'samples/02/input/problem.json',output,public/'samples/02/reference/grading.json')['score']==1
linked=subprocess.check_output(['nm','-C','/opt/material-build/material_driver'],text=True);assert 'HystereticMaterial::setTrialStrain(double, double)' in linked and 'HystereticSMMaterial::setTrialStrain(double, double)' in linked
print(json.dumps({'mode':mode,'passed':True,'before_executable_sha256':before,'after_executable_sha256':after,'access':access,'forced_rebuild':json.loads((logs/'build/report.json').read_text()),'actual_sample_score':1,'real_material_symbols_present':True,'cpu_max':Path('/sys/fs/cgroup/cpu.max').read_text().strip(),'memory_max':Path('/sys/fs/cgroup/memory.max').read_text().strip()}))
