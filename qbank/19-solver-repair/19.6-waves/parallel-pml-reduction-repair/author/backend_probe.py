"""Disposable probes for the shared trusted compiler and real MPI executable."""
import hashlib,importlib.util,json,os,shutil,subprocess,sys,tempfile,time,threading
from pathlib import Path
sys.path.insert(0,'/tests')
import source_repair as backend
mode=sys.argv[1];config=json.loads(Path('/tests/source-repair.json').read_text());task=Path(config['runner']).parents[1]
logs=Path('/logs/verifier');logs.mkdir(parents=True,exist_ok=True);logs.chmod(0o700);Path('/tests').chmod(0o700);Path('/probe').chmod(0o700)
submission=Path('/app/submission');submission.mkdir(exist_ok=True);source=submission/'get_MPI.F90';source.write_bytes(Path('/probe/get_MPI.F90').read_bytes())
def evidence():
    return {'reports':{p.name:json.loads(p.read_text()) for p in (logs/'build').glob('*report.json')},
            'stderr_tails':{p.name:p.read_text()[-3000:] for p in (logs/'build').glob('*stderr.log')}}
if mode=='extra':(submission/'extra.f90').write_text('')
if mode=='syntax':source.write_text('invalid Fortran !!!')
if mode=='symlink':source.unlink();source.symlink_to('/probe/get_MPI.F90')
if mode=='compiler':Path('/usr/bin/gfortran').rename('/usr/bin/gfortran-probe-disabled')
if mode=='baseline-runtime':Path('/opt/specfem-repair-build/upstream/bin/xmeshfem2D').rename('/opt/specfem-repair-build/upstream/bin/xmeshfem2D-probe-disabled')
if mode=='valid':
    for name in config['rebuild_files']:os.utime(name,(4102444800,4102444800))
if mode=='runtime-timeout':
    text=source.read_text();needle='  integer :: i,iinterface,imax_all,ier'
    assert text.count(needle)==1
    source.write_text(text.replace(needle,needle+"\n  character(len=80) :: probe_pid_filename\n  write(probe_pid_filename,'(A,I0)') '/tmp/specfem-loop-',getpid()\n  open(unit=777,file=trim(probe_pid_filename),status='replace')\n  write(777,*) getpid()\n  close(777)\n  do\n  enddo\n"))
try:backend.prepare()
except backend.SubmissionError as e:
    expected='build_error' if mode=='syntax' else 'invalid_submission';assert mode in ('extra','syntax','symlink') and e.status==expected,(mode,e.status)
    print(json.dumps({'mode':mode,'passed':True,'classification':e.status,**evidence()}));raise SystemExit()
except RuntimeError as e:
    assert mode in ('compiler','baseline-runtime'),str(e)
    expected='Trusted baseline build failed: build_error' if mode=='compiler' else 'Trusted baseline runtime probe failed: probe_error'
    assert str(e)==expected,str(e)
    print(json.dumps({'mode':mode,'passed':True,'classification':'infrastructure_error','reason':str(e),**evidence()}));raise SystemExit()
assert mode in ('valid','runtime-timeout')
import judge
with tempfile.TemporaryDirectory() as tmp:
    directory=Path(tmp);directory.chmod(0o700);os.chown(directory,1000,1000);shutil.copytree(task/'samples/01/input',directory/'input')
    runlogs=logs/'sample';runlogs.mkdir()
    tracked={};stop=threading.Event()
    def observe():
        while not stop.wait(.01):
            for proc in Path('/proc').glob('[0-9]*'):
                try:
                    cmd=(proc/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
                    if 'xspecfem2D' in cmd or 'mpirun' in cmd:tracked[int(proc.name)]=cmd
                except (FileNotFoundError,ProcessLookupError):pass
    watcher=threading.Thread(target=observe);watcher.start()
    sentinel=subprocess.Popen(['setpriv','--reuid=1000','--regid=1000','--clear-groups','sleep','60'])
    try:
        result=judge.execute(directory,3 if mode=='runtime-timeout' else 210,runlogs)
        assert sentinel.poll() is None,'Unrelated same-UID sentinel killed'
    finally:
        stop.set();watcher.join();sentinel.kill();sentinel.wait()
    if mode=='runtime-timeout':
        assert result['status']=='timeout',result
        ranks=[int(p.read_text()) for p in Path('/tmp').glob('specfem-loop-*')]
        assert len(ranks)==3,ranks
        assert len(tracked)>=4,tracked
        remaining={pid:cmd for pid,cmd in tracked.items() if Path('/proc',str(pid)).exists()}
        assert not remaining,remaining
        assert all(not Path('/proc',str(pid)).exists() for pid in ranks),ranks
        print(json.dumps({'mode':mode,'passed':True,'actual_fortran_timeout':True,'rank_pids':ranks,'tracked_launcher_and_ranks':tracked,'all_absent_including_zombies':True,'unrelated_same_uid_sentinel_survived':True,**evidence()}));raise SystemExit()
    assert result is None,result
    from caeoj.case_grading import grade_case
    assert grade_case(directory/'input/problem.json',directory/'result.h5',task/'samples/01/reference/grading.json')['score']==1
report=json.loads((logs/'build/report.json').read_text());assert len(report['built_artifacts_sha256'])==2
assert report['sources_sha256']['get_MPI.F90']==hashlib.sha256(source.read_bytes()).hexdigest()
for name,digest in report['built_artifacts_sha256'].items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest
ldd=subprocess.check_output(['ldd','/opt/specfem-repair-build/upstream/bin/xspecfem2D'],text=True);assert 'libmpi' in ldd
paths=['/tests','/logs/verifier','/probe','/app/submission','/opt/specfem-cmake','/opt/specfem-cmake/CMakeLists.txt',
       '/opt/specfem-repair-build','/opt/specfem-repair-build/upstream','/opt/specfem-repair-build/upstream/src/specfem2D',
       '/opt/specfem-repair-build/upstream/src/specfem2D/get_MPI.F90','/opt/specfem-repair-build/upstream/bin/xmeshfem2D']+config['rebuild_files']
code="""import os,json,socket
paths=PATH_LIST
access={p:{'read':os.access(p,os.R_OK),'write':os.access(p,os.W_OK)} for p in paths};assert not any(x['write'] for x in access.values());assert all(not access[p]['read'] for p in paths[:3]);assert os.geteuid()==1000
try:socket.create_connection(('1.1.1.1',80),timeout=1);network='allowed'
except OSError:network='denied'
assert network=='denied';print(json.dumps({'uid':os.geteuid(),'permissions':access,'network':network}))
""".replace('PATH_LIST',repr(paths))
r=subprocess.run(['setpriv','--reuid=1000','--regid=1000','--clear-groups','--no-new-privs','python','-c',code],text=True,capture_output=True,env={**os.environ,'HOME':'/home/solver'})
if r.returncode:raise RuntimeError(r.stdout+'\n'+r.stderr)
print(json.dumps({'mode':mode,'passed':True,'ldd':ldd,'binding':json.loads(r.stdout),'build':report,
    'baseline_build':json.loads((logs/'build/baseline-report.json').read_text()),'baseline_probe':json.loads((logs/'build/baseline-probe-report.json').read_text()),
    'cpu_max':Path('/sys/fs/cgroup/cpu.max').read_text(),'memory_max':Path('/sys/fs/cgroup/memory.max').read_text(),**evidence()}))
