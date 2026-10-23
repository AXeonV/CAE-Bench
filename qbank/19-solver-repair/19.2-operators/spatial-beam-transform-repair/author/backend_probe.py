"""Run in a disposable verifier: verify actual compiler, loading and isolation."""
import hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path
sys.path.insert(0,'/tests')
import source_repair as backend
mode=sys.argv[1];public=Path('/app/qbank/19-solver-repair/19.2-operators/spatial-beam-transform-repair');submission=Path('/app/submission');logs=Path('/logs/verifier');logs.mkdir(parents=True,exist_ok=True);logs.chmod(0o700);Path('/tests').chmod(0o700);submission.mkdir(exist_ok=True)
config=json.loads(Path('/tests/source-repair.json').read_text());candidate=submission/'timoshenko_beam_element_3D2N.cpp';reference=Path('/probe/timoshenko_beam_element_3D2N.cpp').read_bytes();library=Path('/opt/beam-build/libbeam_repair.so');before=hashlib.sha256(library.read_bytes()).hexdigest()
if mode=='symlink':candidate.symlink_to('/probe/timoshenko_beam_element_3D2N.cpp')
else:candidate.write_bytes(b'invalid C++ !!!' if mode=='syntax' else reference)
if mode=='extra':(submission/'extra.cpp').write_text('')
if mode=='compiler':Path('/usr/bin/clang++').rename('/usr/bin/clang++-disabled')
if mode=='baseline-runtime':Path('/opt/beam-build/beam_driver').rename('/opt/beam-build/beam_driver-disabled')
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
paths=['/tests/cases','/tests/reference','/logs/verifier','/opt/beam-build/libbeam_repair.so','/opt/beam-build/beam_driver','/opt/kratos-source/applications/StructuralMechanicsApplication/custom_elements/beam_elements/timoshenko_beam_element_3D2N.cpp']
r={'uid':os.geteuid(),'access':{p:{'read':os.access(p,os.R_OK),'write':os.access(p,os.W_OK)} for p in paths}}
try:socket.create_connection(('1.1.1.1',80),timeout=1);r['network']='allowed'
except OSError:r['network']='denied'
print(json.dumps(r))'''
def low(command):return subprocess.run(['setpriv','--reuid=1000','--regid=1000','--clear-groups','--no-new-privs',*command],capture_output=True,text=True,check=True)
access=json.loads(low(['python','-c',code]).stdout);assert access['uid']==1000 and access['network']=='denied';assert all(not v['write'] for v in access['access'].values());assert all(not access['access'][p]['read'] for p in ['/tests/cases','/tests/reference','/logs/verifier'])
output='/tmp/beam-probe.h5';low(['python',str(public/'public/run_case.py'),'--input',str(public/'samples/02/input/problem.json'),'--output',output]);from caeoj.case_grading import grade_case
assert grade_case(public/'samples/02/input/problem.json',output,public/'samples/02/reference/grading.json')['score']==1
linked=subprocess.check_output(['ldd','/opt/beam-build/beam_driver'],text=True);assert '/opt/beam-build/libbeam_repair.so' in linked and '/opt/kratos-build/kratos/libKratosCore.so' in linked
print(json.dumps({'mode':mode,'passed':True,'before_library_sha256':before,'after_library_sha256':after,'access':access,'forced_rebuild':json.loads((logs/'build/report.json').read_text()),'actual_sample_score':1,'actual_linked_paths':linked,'cpu_max':Path('/sys/fs/cgroup/cpu.max').read_text().strip(),'memory_max':Path('/sys/fs/cgroup/memory.max').read_text().strip()}))
