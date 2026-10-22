"""Run inside a disposable verifier image; exercise isolation and failure paths."""
import json
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, '/tests')
import source_repair as backend

MODE = sys.argv[1]
PUBLIC = Path('/app/qbank/19-solver-repair/19.1-constraints/constrained-assembly-repair')
CONFIG = Path('/tests/source-repair.json')
SUBMISSION = Path('/app/submission')
LOGS = Path('/logs/verifier')
LOGS.mkdir(parents=True, exist_ok=True)
Path('/tests').chmod(0o700)
LOGS.chmod(0o700)
SUBMISSION.mkdir(exist_ok=True)
config = json.loads(CONFIG.read_text())
reference = Path('/probe/ChAssemblyAnalysis.cpp').read_text()
candidate = SUBMISSION / 'ChAssemblyAnalysis.cpp'
original_library_sha256 = hashlib.sha256(Path('/opt/chrono-build/lib/libChrono_core.so').read_bytes()).hexdigest()


def unprivileged(command, **kwargs):
    return subprocess.run(['setpriv', '--reuid=1000', '--regid=1000', '--clear-groups',
                           '--no-new-privs', *command], capture_output=True, text=True, **kwargs)


def report(data):
    print(json.dumps({'mode': MODE, 'passed': True, **data}), flush=True)


if MODE == 'generic':
    CONFIG.unlink()
    import judge
    (SUBMISSION/'solve.py').write_text(
        'import sys,shutil\nshutil.copyfile(' + repr(str(PUBLIC/'samples/01/output/result.h5'))
        + ',sys.argv[sys.argv.index("--output")+1])\n')
    assert judge.freeze_submission()
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        directory.chmod(0o700)
        os.chown(directory, 1000, 1000)
        shutil.copytree(PUBLIC/'samples/01/input', directory/'input')
        logs = LOGS/'generic'
        logs.mkdir()
        assert judge.execute(directory, 10, logs) is None
        from caeoj.case_grading import grade_case
        assert grade_case(directory/'input/problem.json', directory/'result.h5', PUBLIC/'samples/01/reference/grading.json')['score'] == 1
    report({'actual_standard_submission': 'passed'})
    raise SystemExit()

if MODE == 'symlink':
    candidate.symlink_to('/probe/ChAssemblyAnalysis.cpp')
else:
    candidate.write_text('invalid C++ source\n' if MODE == 'syntax' else reference)
if MODE == 'extra':
    (SUBMISSION/'unexpected.py').write_text('')
if MODE == 'baseline':
    Path('/opt/chrono-build/build.ninja').unlink()
if MODE == 'compiler':
    Path('/usr/bin/c++').rename('/usr/bin/c++-probe-disabled')
if MODE == 'runtime-timeout':
    text = reference.replace('AssemblyAnalysis(int action, double dt) {',
                             'AssemblyAnalysis(int action, double dt) { while (true) {}', 1)
    assert text != reference
    candidate.write_text(text)
if MODE == 'valid':
    # A future object/output timestamp must not suppress candidate compilation.
    for name in config['rebuild_files']:
        os.utime(name, (4102444800, 4102444800))

try:
    backend.prepare()
except backend.SubmissionError as error:
    expected = 'build_error' if MODE == 'syntax' else 'invalid_submission' if MODE in ('extra', 'symlink') else None
    assert error.status == expected, (MODE, error.status)
    report({'classified_status': error.status})
    raise SystemExit()
except RuntimeError as error:
    assert MODE in ('baseline', 'compiler') and 'Trusted baseline build failed' in str(error)
    report({'classified_status': 'infrastructure_error'})
    raise SystemExit()

assert MODE in ('valid', 'compile-timeout', 'runtime-timeout'), MODE
if MODE == 'compile-timeout':
    # An actual process tree, controlled only by this trusted test fixture.
    path = Path('/usr/local/bin/cmake')
    path.write_text('#!/bin/sh\nsleep 60 &\necho $! > /tmp/probe-child.pid\nwait\n')
    path.chmod(0o755)
    result = backend.compile_source(config, 'timeout-probe', .2)
    assert result['status'] == 'build_timeout'
    child = Path('/proc') / Path('/tmp/probe-child.pid').read_text().strip() / 'stat'
    assert not child.exists() or child.read_text().split()[2] == 'Z'
    report({'actual_compile_process_tree_timeout': 'passed'})
elif MODE == 'runtime-timeout':
    import judge
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        directory.chmod(0o700)
        os.chown(directory, 1000, 1000)
        shutil.copytree(PUBLIC/'samples/01/input', directory/'input')
        logs = LOGS/'timeout'
        logs.mkdir()
        assert judge.execute(directory, .2, logs)['status'] == 'timeout'
        for entry in Path('/proc').glob('[0-9]*'):
            try:
                if (entry/'comm').read_text().strip() == 'assembly-driver':
                    assert (entry/'stat').read_text().split()[2] == 'Z'
            except FileNotFoundError:
                pass
    report({'actual_driver_descendant_timeout': 'passed'})
else:
    code = '''import json,os,socket
from pathlib import Path
paths=['/tests/cases','/tests/reference','/logs/verifier','/app/submission/ChAssemblyAnalysis.cpp',
       '/opt/chrono-build/lib/libChrono_core.so','/opt/chrono-build/lib',
       '/opt/driver-build/assembly-driver','/opt/chrono-source/src/chrono/timestepper/ChAssemblyAnalysis.cpp']
data={'uid':os.geteuid(),'access':{p:{'read':os.access(p,os.R_OK),'write':os.access(p,os.W_OK)} for p in paths}}
try:Path('/tests/source-repair.json').read_bytes();data['private_read']='allowed'
except PermissionError:data['private_read']='denied'
try:socket.create_connection(('1.1.1.1',80),timeout=1);data['network']='allowed'
except OSError:data['network']='denied'
print(json.dumps(data))
'''
    result = unprivileged(['python', '-c', code], check=True)
    access = json.loads(result.stdout)
    assert access['uid'] == 1000 and access['private_read'] == 'denied' and access['network'] == 'denied'
    assert all(not row['write'] for row in access['access'].values())
    assert all(not access['access'][name]['read'] for name in ('/tests/cases', '/tests/reference', '/logs/verifier'))
    output = Path('/tmp/probe-result.h5')
    env = os.environ.copy()
    env.update(LD_DEBUG='libs', LD_LIBRARY_PATH='/opt/chrono-build/lib')
    execution = unprivileged(['python', str(PUBLIC/'public/run_case.py'), '--input',
                             str(PUBLIC/'samples/01/input/problem.json'), '--output', str(output)], env=env, check=True)
    # The adapter captures the child loader trace. Inspect the linked binary
    # independently as well to bind the installed driver's dependency.
    linked = subprocess.check_output(['ldd', '/opt/driver-build/assembly-driver'], text=True)
    assert '/opt/chrono-build/lib/libChrono_core.so' in linked
    new_library_sha256 = hashlib.sha256(Path('/opt/chrono-build/lib/libChrono_core.so').read_bytes()).hexdigest()
    assert new_library_sha256 != original_library_sha256
    from caeoj.case_grading import grade_case
    assert grade_case(PUBLIC/'samples/01/input/problem.json', output, PUBLIC/'samples/01/reference/grading.json')['score'] == 1
    report({'permissions': access, 'cpu_max': Path('/sys/fs/cgroup/cpu.max').read_text().strip(),
            'memory_max': Path('/sys/fs/cgroup/memory.max').read_text().strip(),
            'forced_rebuild': json.loads((LOGS/'build/report.json').read_text()),
            'original_library_sha256': original_library_sha256, 'new_library_sha256': new_library_sha256,
            'driver_uses_rebuilt_library': True})
