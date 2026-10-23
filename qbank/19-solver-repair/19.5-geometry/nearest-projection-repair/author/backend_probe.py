"""Run in disposable private verifier images; never publish this instrumentation."""
import hashlib,importlib.util,json,os,shutil,subprocess,sys,tempfile,time
from pathlib import Path
sys.path.insert(0,'/tests')
import source_repair as backend
mode=sys.argv[1];config=json.loads(Path('/tests/source-repair.json').read_text());public=Path(config['runner']).parents[1]
logs=Path('/logs/verifier');logs.mkdir(parents=True,exist_ok=True);logs.chmod(0o700);Path('/tests').chmod(0o700);Path('/probe').chmod(0o700)
submission=Path('/app/submission');submission.mkdir(exist_ok=True)
source=submission/'Index.cpp';source.write_bytes(Path('/probe/Index.cpp').read_bytes())
if mode=='extra':(submission/'extra.cpp').write_text('')
if mode=='syntax':source.write_text('invalid C++ !!!')
if mode=='symlink':source.unlink();source.symlink_to('/probe/Index.cpp')
if mode=='compiler':Path('/usr/bin/g++').rename('/usr/bin/g++-probe-disabled')
if mode=='baseline-runtime':
    entry=Path(importlib.util.find_spec('numpy').origin);entry.rename(entry.with_name('__init__probe_disabled.py'))
if mode=='valid':
    for name in config['rebuild_files']:os.utime(name,(4102444800,4102444800))
if mode=='runtime-timeout':
    text=source.read_text();needle='ProjectionMatch Index::findNearestProjection(const Eigen::VectorXd &location, int n)\n{'
    assert text.count(needle)==1
    text='#include <fstream>\n#include <unistd.h>\n'+text.replace(needle,needle+'\n  std::ofstream("/tmp/probe-loop.pid") << getpid(); while(true) { ::usleep(100000); }')
    source.write_text(text)
try:backend.prepare()
except backend.SubmissionError as exc:
    expected='build_error' if mode=='syntax' else 'invalid_submission';assert mode in ['extra','syntax','symlink'] and exc.status==expected,(mode,exc.status)
    print(json.dumps({'mode':mode,'passed':True,'classification':exc.status}));raise SystemExit()
except RuntimeError as exc:
    assert mode in ['compiler','baseline-runtime'] and 'Trusted baseline' in str(exc),str(exc)
    print(json.dumps({'mode':mode,'passed':True,'classification':'infrastructure_error','reason':str(exc)}));raise SystemExit()
assert mode in ['valid','runtime-timeout']
import judge
with tempfile.TemporaryDirectory() as temp:
    directory=Path(temp);directory.chmod(0o700);os.chown(directory,1000,1000);shutil.copytree(public/'samples/01/input',directory/'input')
    case_logs=logs/'sample';case_logs.mkdir();result=judge.execute(directory,3 if mode=='runtime-timeout' else 30,case_logs)
    if mode=='runtime-timeout':
        assert result['status']=='timeout',result;pid=Path('/tmp/probe-loop.pid').read_text().strip();stat=Path('/proc')/pid/'stat';states=[]
        for attempt in range(21):
            state=stat.read_text().split()[2] if stat.exists() else 'absent';states.append(state)
            if state in ['Z','absent']:break
            time.sleep(.1)
        assert states[-1] in ['Z','absent'],states
        print(json.dumps({'mode':mode,'passed':True,'actual_cpp_timeout':True,'child_pid':pid,'post_kill_states':states,'poll_interval_seconds':.1}));raise SystemExit()
    assert result is None,result
    from caeoj.case_grading import grade_case
    assert grade_case(directory/'input/problem.json',directory/'result.h5',public/'samples/01/reference/grading.json')['score']==1
status=json.loads((logs/'build/report.json').read_text());assert status['sources_sha256']['Index.cpp']==hashlib.sha256(source.read_bytes()).hexdigest()
for name,digest in status['built_artifacts_sha256'].items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest
ldd=subprocess.check_output(['ldd',config['rebuild_files'][-1]],text=True);assert '/opt/precice-repair-build/lib/libprecice.so.2' in ldd,ldd
root=Path('/opt/precice-upstream/precice-c2a06a65631e15a6622f5ecffae194f82ba0bae3')
paths=['/tests','/logs/verifier','/probe','/app/submission','/opt/precice-driver','/opt/precice-driver/driver.cpp','/opt/precice-repair-cmake','/opt/precice-repair-cmake/CMakeLists.txt',str(root),str(root/'src/query'),str(root/'src/query/Index.hpp'),str(root/'src/mesh/Mesh.hpp')]
paths += [r['target'] for r in config['replacements']]+config['rebuild_files']
paths += [str(q) for q in Path('/opt/precice-build/CMakeFiles/precice.dir').rglob('*.o')]
code="""import os,json,socket
paths=PATH_LIST
a={p:{'read':os.access(p,os.R_OK),'write':os.access(p,os.W_OK)} for p in paths};assert not any(v['write'] for v in a.values());assert all(not a[p]['read'] for p in paths[:3]);assert os.geteuid()==1000
try:socket.create_connection(('1.1.1.1',80),timeout=1);network='allowed'
except OSError:network='denied'
assert network=='denied';print(json.dumps({'uid':os.geteuid(),'permissions':a,'network':network}))
""".replace('PATH_LIST',repr(paths))
r=subprocess.run(['setpriv','--reuid=1000','--regid=1000','--clear-groups','--no-new-privs','python','-c',code],text=True,capture_output=True,env={**os.environ,'HOME':'/home/solver'})
if r.returncode:raise RuntimeError(r.stdout+'\n'+r.stderr)
print(json.dumps({'mode':mode,'passed':True,'ldd':ldd,'binding':json.loads(r.stdout),'build':status,'baseline_probe':json.loads((logs/'build/baseline-probe-report.json').read_text()),'cpu_max':Path('/sys/fs/cgroup/cpu.max').read_text(),'memory_max':Path('/sys/fs/cgroup/memory.max').read_text()}))
