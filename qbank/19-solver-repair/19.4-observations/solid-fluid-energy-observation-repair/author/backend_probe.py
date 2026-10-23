"""Disposable fixed verifier probes; no replacement of the actual compiler or grader."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0,'/tests')
import source_repair as backend

MODE=sys.argv[1]
PUBLIC=Path('/app/qbank/19-solver-repair/19.4-observations/solid-fluid-energy-observation-repair')
SUBMISSION=Path('/app/submission')
LOGS=Path('/logs/verifier')
LIB=Path('/opt/moose-source-2022/modules/navier_stokes/lib/.libs/libnavier_stokes-opt.so.0.0.0')
APP=Path('/opt/moose-source-2022/modules/navier_stokes/navier_stokes-opt')
CONFIG=json.loads(Path('/tests/source-repair.json').read_text())


def low(command):
    result=subprocess.run(['setpriv','--reuid=1000','--regid=1000','--clear-groups','--no-new-privs',
                           'env','-i','PATH=/usr/local/bin:/usr/bin:/bin','HOME=/home/solver',*command],
                          capture_output=True,text=True,timeout=60)
    if result.returncode:raise RuntimeError((command,result.returncode,result.stdout[-2000:],result.stderr[-2000:]))
    return result


def main():
    LOGS.mkdir(parents=True,exist_ok=True);LOGS.chmod(0o700);Path('/tests').chmod(0o700)
    SUBMISSION.mkdir(exist_ok=True);before=hashlib.sha256(LIB.read_bytes()).hexdigest()
    absent_before={row['target']:not Path(row['target']).exists() for row in CONFIG['replacements']};assert all(absent_before.values())
    for row in CONFIG['replacements']:
        path=SUBMISSION/row['submission'];reference=Path('/probe')/row['submission']
        if MODE=='symlink':path.symlink_to(reference)
        else:path.write_bytes(b'invalid C++ !!!' if MODE=='syntax' else b'x'*(CONFIG['max_source_bytes']+1) if MODE=='oversize' else reference.read_bytes())
    if MODE=='extra':(SUBMISSION/'extra.C').write_text('')
    if MODE=='compiler':Path('/opt/openmpi/bin/mpicxx').rename('/opt/openmpi/bin/mpicxx-disabled')
    if MODE=='baseline-sdk':
        import caeoj
        directory=Path(caeoj.__file__).parent
        (directory/'sdk.py').rename(directory/'sdk-disabled.py')
        for path in (directory/'__pycache__').glob('sdk.*.pyc'):path.unlink()
    if MODE=='baseline-runtime':
        # The app is itself a forced-rebuild artifact. Remove it only after the
        # genuine baseline compilation, so this specifically tests runtime health.
        actual_compile=backend.compile_source
        def compile_with_runtime_fault(config,label,timeout,command_override=None):
            outcome=actual_compile(config,label,timeout,command_override)
            if label=='baseline' and outcome['status']=='built':APP.rename(APP.with_name(APP.name+'-disabled'))
            return outcome
        backend.compile_source=compile_with_runtime_fault
    if MODE=='valid':
        for name in CONFIG['rebuild_files']:os.utime(name,(4102444800,4102444800))
    try:backend.prepare()
    except backend.SubmissionError as exc:
        expected='build_error' if MODE=='syntax' else 'invalid_submission'
        assert MODE in ['syntax','extra','symlink','oversize'] and exc.status==expected,(MODE,exc.status)
        print(json.dumps({'mode':MODE,'passed':True,'classification':exc.status}));return
    except RuntimeError as exc:
        expected='Trusted baseline runtime probe failed' if MODE in ['baseline-runtime','baseline-sdk'] else 'Trusted baseline build failed'
        assert MODE in ['compiler','baseline-runtime','baseline-sdk'] and expected in str(exc),str(exc)
        print(json.dumps({'mode':MODE,'passed':True,'classification':'infrastructure_error','reason':str(exc),
                          'fault_point':'after genuine baseline compilation' if MODE=='baseline-runtime' else 'before baseline preparation'}));return
    assert MODE=='valid'
    after=hashlib.sha256(LIB.read_bytes()).hexdigest();assert after!=before
    paths=['/tests/cases','/tests/reference','/logs/verifier','/opt/moose-source-2022',str(APP),str(LIB),
           '/opt/moose-source-2022/modules/navier_stokes/src/postprocessors/INSElementIntegralEnergyAdvection.C',
           '/opt/moose-source-2022/modules/navier_stokes/include/postprocessors/INSElementIntegralEnergyAdvection.h',
           '/opt/moose-source-2022/framework/include/materials/Material.h',
           '/opt/build-control','/opt/build-control/CMakeLists.txt','/environment','/opt/task-python',
           '/opt/libmesh2022/lib','/opt/petsc2022/lib','/opt/openmpi/bin/mpicxx',str(PUBLIC/'public/run_case.py')]
    code='''import json,os,socket
from pathlib import Path
paths=__PATHS__
r={'uid':os.geteuid(),'gid':os.getegid(),'groups':os.getgroups(),'access':{p:{'exists':os.path.exists(p),'read':os.access(p,os.R_OK),'write':os.access(p,os.W_OK)} for p in paths}}
try:socket.create_connection(('1.1.1.1',80),timeout=1);r['network']='allowed'
except OSError:r['network']='denied'
print(json.dumps(r))'''.replace('__PATHS__',repr(paths))
    access=json.loads(low(['/usr/local/bin/python','-c',code]).stdout)
    assert access['uid']==1000 and access['gid']==1000 and access['groups']==[] and access['network']=='denied'
    assert all(not item['write'] for item in access['access'].values())
    assert all(not access['access'][p]['read'] for p in ['/tests/cases','/tests/reference','/logs/verifier'])
    assert all(item['exists'] for name,item in access['access'].items() if not name.startswith('/tests/'))
    output='/tmp/moose-probe-result.h5'
    low(['/usr/local/bin/python',str(PUBLIC/'public/run_case.py'),'--input',str(PUBLIC/'samples/02/input/problem.json'),'--output',output])
    from caeoj.case_grading import grade_case
    grade=grade_case(PUBLIC/'samples/02/input/problem.json',output,PUBLIC/'samples/02/reference/grading.json')
    assert grade['score']==1,grade
    public_commands=[]
    for sample in ['01','02']:
        source=PUBLIC/'samples'/sample/'input/problem.json';destination=f'/tmp/public-sample-{sample}.h5'
        commands=[['/usr/local/bin/python','-m','caeoj','validate-input',str(source)],['/usr/local/bin/python',str(PUBLIC/'public/run_case.py'),'--input',str(source),'--output',destination],['/usr/local/bin/python','-m','caeoj','validate-output','--input',str(source),'--output',destination],['/usr/local/bin/python','-m','caeoj','grade','--input',str(source),'--output',destination,'--grading',str(PUBLIC/'samples'/sample/'reference/grading.json')]]
        for command in commands:
            result=low(command);public_commands.append({'sample':sample,'command':command,'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
    from runpy import run_path
    env_code="source /environment && export LD_LIBRARY_PATH=/opt/libmesh2022/lib:/opt/petsc2022/lib:$LD_LIBRARY_PATH && ldd "
    linked=subprocess.check_output(['/bin/bash','-lc',env_code+str(APP)],text=True)
    assert 'libnavier_stokes-opt' in linked and '/opt/moose-source-2022/modules/navier_stokes/lib' in linked
    symbols=subprocess.check_output(['nm','-DC',str(LIB)],text=True)
    assert all('INSElementIntegralEnergyAdvectionTempl<'+flag+'>::computeQpIntegral()' in symbols for flag in ['false','true'])
    unity=Path('/opt/moose-source-2022/modules/navier_stokes/build/unity_src/postprocessors_Unity.C');assert 'INSElementIntegralEnergyAdvection.C' in unity.read_text()
    unity_object=Path('/opt/moose-source-2022/modules/navier_stokes/build/unity_src/.libs/postprocessors_Unity.x86_64-pc-linux-gnu.opt.o')
    object_symbols=subprocess.check_output(['nm','-C',str(unity_object)],text=True);assert all('INSElementIntegralEnergyAdvectionTempl<'+flag+'>::computeQpIntegral()' in object_symbols for flag in ['false','true'])
    print(json.dumps({'mode':MODE,'passed':True,'library_before_sha256':before,'library_after_sha256':after,
                      'forced_rebuild':json.loads((LOGS/'build/report.json').read_text()),'access':access,
                      'actual_sample_score':grade['score'],'public_cli':public_commands,'linked_paths':linked,'actual_observer_symbols':True,'baseline_target_absent':absent_before,'new_source_discovered_in_unity':True,'unity_object_sha256':hashlib.sha256(unity_object.read_bytes()).hexdigest(),
                      'cpu_max':Path('/sys/fs/cgroup/cpu.max').read_text().strip(),
                      'memory_max':Path('/sys/fs/cgroup/memory.max').read_text().strip()}))


if __name__=='__main__':main()
