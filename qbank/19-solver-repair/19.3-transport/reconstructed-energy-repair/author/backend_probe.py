"""Private disposable-container probes; consume the frozen, unmodified backend."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, '/tests')
import source_repair as backend

mode = sys.argv[1]
config = json.loads(Path('/tests/source-repair.json').read_text())
public = Path(config['runner']).parents[1]
logs = Path('/logs/verifier')
logs.mkdir(parents=True, exist_ok=True)
for path in [logs, Path('/tests'), Path('/probe')]:
    path.chmod(0o700)
submission = Path('/app/submission')
submission.mkdir(exist_ok=True)
for row in config['replacements']:
    (submission / row['submission']).write_bytes((Path('/probe') / row['submission']).read_bytes())
if mode == 'extra':
    (submission / 'extra.cpp').write_text('')
if mode == 'syntax':
    (submission / 'common.hpp').write_text('invalid C++ !!!')
if mode == 'baseline-compiler':
    Path('/usr/bin/g++').rename('/usr/bin/g++disabled')
if mode == 'baseline-runtime':
    config['baseline_probe'] += ['--driver', '/missing/reconstruction-driver']
    Path('/tests/source-repair.json').write_text(json.dumps(config))
if mode == 'valid':
    for name in config['rebuild_files']:
        os.utime(name, (4102444800, 4102444800))
if mode == 'runtime-timeout':
    path = submission / 'common.hpp'
    text = path.read_text(encoding='utf-8-sig')
    needle = 'static_assert(ReconVarType::nVar <= PrimVarType::nVar);'
    assert text.count(needle) == 1
    path.write_text('#include <fstream>\n#include <unistd.h>\n' + text.replace(
        needle, needle + '\n std::ofstream("/tmp/probe-loop.pid") << getpid(); while(true) {}'))
try:
    backend.prepare()
except backend.SubmissionError as error:
    expected = {'extra': 'invalid_submission', 'syntax': 'build_error'}
    assert error.status == expected.get(mode), (mode, error.status)
    print(json.dumps({'mode': mode, 'passed': True, 'classification': error.status}))
    raise SystemExit()
except RuntimeError as error:
    expected = {'baseline-compiler': 'Trusted baseline build failed',
                'baseline-runtime': 'Trusted baseline runtime probe failed'}
    assert mode in expected and expected[mode] in str(error), str(error)
    print(json.dumps({'mode': mode, 'passed': True, 'classification': 'infrastructure_error', 'error': str(error)}))
    raise SystemExit()
assert mode in ['valid', 'runtime-timeout']
import judge
with tempfile.TemporaryDirectory() as temp:
    directory = Path(temp)
    directory.chmod(0o700)
    os.chown(directory, 1000, 1000)
    shutil.copytree(public / 'samples/01/input', directory / 'input')
    case_logs = logs / 'sample'
    case_logs.mkdir()
    result = judge.execute(directory, 3 if mode == 'runtime-timeout' else 180, case_logs)
    if mode == 'runtime-timeout':
        assert result['status'] == 'timeout', result
        pid = Path('/tmp/probe-loop.pid').read_text().strip()
        stat = Path('/proc') / pid / 'stat'
        states = []
        for _ in range(20):
            state = stat.read_text().split()[2] if stat.exists() else 'absent'
            states.append(state)
            if state in ['absent', 'Z']:
                break
            time.sleep(.1)
        assert states[-1] in ['absent', 'Z'], states
        print(json.dumps({'mode': mode, 'passed': True, 'actual_candidate_cpp_timeout': True,
                          'pid': pid, 'termination_states': states, 'status': result}))
        raise SystemExit()
    assert result is None, result
    from caeoj.case_grading import grade_case
    assert grade_case(directory / 'input/problem.json', directory / 'result.h5',
                      public / 'samples/01/reference/grading.json')['score'] == 1
status = json.loads((logs / 'build/report.json').read_text())
for row in config['replacements']:
    assert status['sources_sha256'][row['submission']] == hashlib.sha256((submission / row['submission']).read_bytes()).hexdigest()
for name, digest in status['built_artifacts_sha256'].items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest
ldd = subprocess.check_output(['ldd', config['rebuild_files'][-1]], text=True)
assert 'libSU2' not in ldd  # The actual solver is linked to the two rebuilt static archives.
paths = ['/tests', '/logs/verifier', '/probe', '/app/submission',
         '/opt/su2-source', '/opt/su2-source/Common', '/opt/su2-source/Common/include',
         '/opt/su2-source/Common/include/CConfig.hpp', '/opt/su2-source/SU2_CFD/src',
         '/opt/repair-driver', '/opt/repair-driver/CMakeLists.txt',
         '/opt/su2-build/build.ninja', '/opt/su2-build/CMakeCache.txt']
paths += [row['target'] for row in config['replacements']] + config['rebuild_files']
code = '''import os,json,socket
paths=PATH_LIST
assert all(os.path.exists(p) for p in paths)
access={p:{'read':os.access(p,os.R_OK),'write':os.access(p,os.W_OK)} for p in paths}
assert not any(value['write'] for value in access.values())
assert all(not access[p]['read'] for p in paths[:3])
assert os.geteuid()==1000
try:socket.create_connection(('1.1.1.1',80),timeout=1);network='allowed'
except OSError:network='denied'
assert network=='denied'
print(json.dumps({'uid':os.geteuid(),'permissions':access,'network':network}))
'''.replace('PATH_LIST', repr(paths))
check = subprocess.run(['setpriv', '--reuid=1000', '--regid=1000', '--clear-groups',
                        '--no-new-privs', 'python', '-c', code], text=True, capture_output=True)
assert check.returncode == 0, check.stdout + check.stderr
print(json.dumps({'mode': mode, 'passed': True, 'ldd': ldd, 'binding': json.loads(check.stdout),
                  'build': status, 'baseline_probe': json.loads((logs / 'build/baseline-probe-report.json').read_text()),
                  'cpu_max': Path('/sys/fs/cgroup/cpu.max').read_text(),
                  'memory_max': Path('/sys/fs/cgroup/memory.max').read_text()}))
