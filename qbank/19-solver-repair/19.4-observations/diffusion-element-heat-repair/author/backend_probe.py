"""Execute inside disposable private verifier images, never the public image."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0,'/tests')
import source_repair as backend

mode=sys.argv[1]
public=Path('/app/qbank/19-solver-repair/19.4-observations/diffusion-element-heat-repair')
config=json.loads(Path('/tests/source-repair.json').read_text())
submission=Path('/app/submission')
logs=Path('/logs/verifier')
logs.mkdir(parents=True,exist_ok=True)
logs.chmod(0o700)
Path('/tests').chmod(0o700)
Path('/probe').chmod(0o700)
submission.mkdir(exist_ok=True)
sources={name:(Path('/probe')/name).read_bytes() for name in ['diffusion_element.py','thermal.py']}
before={name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in config['rebuild_files']}
for name,value in sources.items():
    path=submission/name
    if mode=='symlink' and name=='thermal.py':path.symlink_to('/probe/thermal.py')
    else:path.write_bytes(value)
if mode=='extra':(submission/'extra.py').write_text('')
if mode=='syntax':(submission/'thermal.py').write_text('this is not valid python !!!\n')
if mode=='baseline-runtime':
    init=Path('/usr/local/lib/python3.14/site-packages/numpy/__init__.py')
    init.rename(init.with_name('__init__probe_disabled.py'))
if mode=='valid':
    for name in config['rebuild_files']:os.utime(name,(4102444800,4102444800))
if mode=='runtime-timeout':
    path=submission/'thermal.py'
    path.write_bytes(path.read_bytes()+b'\nimport os,time\nopen("/tmp/probe-loop.pid","w").write(str(os.getpid()))\nwhile True: time.sleep(1)\n')

try:
    backend.prepare()
except backend.SubmissionError as exc:
    expected='build_error' if mode=='syntax' else 'invalid_submission'
    assert mode in ['syntax','extra','symlink'] and exc.status==expected,(mode,exc.status)
    print(json.dumps({'mode':mode,'passed':True,'classification':exc.status}))
    raise SystemExit()
except RuntimeError as exc:
    assert mode=='baseline-runtime' and 'Trusted baseline runtime probe failed' in str(exc),str(exc)
    print(json.dumps({'mode':mode,'passed':True,'classification':'infrastructure_error'}))
    raise SystemExit()

assert mode in ['valid','runtime-timeout']
import judge
with tempfile.TemporaryDirectory() as temp:
    directory=Path(temp)
    directory.chmod(0o700)
    os.chown(directory,1000,1000)
    shutil.copytree(public/'samples/01/input',directory/'input')
    case_logs=logs/'sample'
    case_logs.mkdir()
    result=judge.execute(directory,5 if mode=='runtime-timeout' else 30,case_logs)
    if mode=='runtime-timeout':
        assert result['status']=='timeout'
        pid=Path('/tmp/probe-loop.pid').read_text().strip()
        stat=Path('/proc')/pid/'stat'
        assert not stat.exists() or stat.read_text().split()[2]=='Z'
        print(json.dumps({'mode':mode,'passed':True,'actual_candidate_import_timeout':True}))
        raise SystemExit()
    assert result is None,result
    from caeoj.case_grading import grade_case
    assert grade_case(directory/'input/problem.json',directory/'result.h5',public/'samples/01/reference/grading.json')['score']==1

code='''import importlib,json,os,socket,sys,hashlib
from pathlib import Path
prefix='/opt/pybamm-build/source/packages/pybamm/src/pybamm/models/submodels/equivalent_circuit_elements/'
modules={}
for name in ['diffusion_element','thermal']:
 m=importlib.import_module('pybamm.models.submodels.equivalent_circuit_elements.'+name)
 assert str(Path(m.__file__).resolve())==prefix+name+'.py'
 assert m.__cached__==prefix+'__pycache__/'+name+'.cpython-314.pyc'
 modules[name]={'source':m.__file__,'cache':m.__cached__,'source_sha256':hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest(),'pyc_sha256':hashlib.sha256(Path(m.__cached__).read_bytes()).hexdigest()}
paths=['/tests','/tests/cases','/tests/reference','/logs/verifier','/probe','/app/submission','/opt/repair-driver/driver.py']
paths += [m[k] for m in modules.values() for k in ['source','cache']]
access={p:{'read':os.access(p,os.R_OK),'write':os.access(p,os.W_OK)} for p in paths}
assert all(not v['write'] for v in access.values())
assert all(not access[p]['read'] for p in ['/tests','/tests/cases','/tests/reference','/logs/verifier','/probe'])
try:socket.create_connection(('1.1.1.1',80),timeout=1);network='allowed'
except OSError:network='denied'
assert os.geteuid()==1000 and sys.implementation.cache_tag=='cpython-314' and network=='denied'
print(json.dumps({'uid':os.geteuid(),'cache_tag':sys.implementation.cache_tag,'modules':modules,'permissions':access,'network':network}))
'''
probe=subprocess.run(['setpriv','--reuid=1000','--regid=1000','--clear-groups','--no-new-privs','python','-c',code],
                     capture_output=True,text=True,check=True,env={**os.environ,'PYBAMM_DISABLE_TELEMETRY':'true'})
binding=json.loads(probe.stdout)
build=json.loads((logs/'build/report.json').read_text())
for module in binding['modules'].values():
    assert module['source_sha256']==build['sources_sha256'][Path(module['source']).name]
    assert module['pyc_sha256']==build['built_artifacts_sha256'][module['cache']]
assert all(before[name]!=build['built_artifacts_sha256'][name] for name in before)
print(json.dumps({'mode':mode,'passed':True,'binding':binding,'build':build,
                  'baseline_probe':json.loads((logs/'build/baseline-probe-report.json').read_text()),
                  'cpu_max':Path('/sys/fs/cgroup/cpu.max').read_text().strip(),
                  'memory_max':Path('/sys/fs/cgroup/memory.max').read_text().strip()}))
