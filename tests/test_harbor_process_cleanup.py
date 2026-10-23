"""Real Linux process isolation, including sessions escaping MPI-style launchers."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('cleanup_judge', ROOT / 'src/utils/harbor/tests/judge.py')
judge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(judge)


@unittest.skipUnless(sys.platform == 'linux' and os.geteuid() == 0, 'Linux root verifier required')
class ProcessCleanupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.work = self.root / 'work'
        self.work.mkdir(); self.work.chmod(0o777)
        # The solver needs to traverse the outer test directory.
        self.root.chmod(0o755)
        self.logs = self.root / 'logs'; self.logs.mkdir(mode=0o700)
        self.sentinel = subprocess.Popen(['sleep', '60'])
        self.addCleanup(self.stop_sentinel)

    def stop_sentinel(self):
        self.sentinel.kill(); self.sentinel.wait()

    def run_direct(self, command, timeout=2):
        tests = self.root / 'tests'; tests.mkdir(exist_ok=True)
        (tests / 'source-repair.json').write_text(json.dumps({'build_directory': '/tmp'}))
        backend = types.SimpleNamespace(command=lambda directory: command)
        with patch.object(judge, 'SOURCE_REPAIR', True), patch.object(judge, 'TESTS', tests), \
                patch.dict(sys.modules, {'source_repair': backend}):
            result = judge.execute(self.work, timeout, self.logs)
        self.assertIsNone(self.sentinel.poll(), 'Unrelated sentinel was killed')
        return result

    def assert_no_recorded_processes(self):
        records = list(self.work.glob('pid-*'))
        self.assertTrue(records)
        for record in records:
            pid = int(record.read_text())
            self.assertFalse(Path(f'/proc/{pid}').exists(), f'{record.name}: PID {pid} remains, including zombies')

    def test_session_escape_on_timeout_and_early_parent_exit(self):
        # Double fork, separate sessions, and a grandchild: all must be reaped.
        for early in (False, True):
            with self.subTest(early=early):
                for record in self.work.glob('pid-*'): record.unlink()
                script = self.work / 'escape.py'
                script.write_text("""import os,time
from pathlib import Path
def record(): Path('pid-'+str(os.getpid())).write_text(str(os.getpid()))
record()
if os.fork()==0:
 os.setsid();record()
 if os.fork()==0:
  os.setsid();record();time.sleep(60)
 time.sleep(60)
time.sleep(.3)
""" + ('raise SystemExit(0)\n' if early else 'time.sleep(60)\n'))
                result = self.run_direct(['python', str(script)], timeout=1)
                self.assertEqual(result, None if early else {'score': 0, 'status': 'timeout'})
                self.assert_no_recorded_processes()

    def test_direct_python_success_and_error(self):
        self.assertIsNone(self.run_direct(['python', '-c', "from pathlib import Path;Path('result.h5').write_text('ok')"]))
        self.assertEqual((self.work / 'result.h5').read_text(), 'ok')
        self.assertEqual(self.run_direct(['python', '-c', 'raise SystemExit(7)']),
                         {'score': 0, 'status': 'runtime_error', 'exit_code': 7})

    @unittest.skipUnless(shutil.which('g++'), 'C++ compiler required')
    def test_direct_compiled_cpp(self):
        source = self.work / 'main.cpp'; binary = self.work / 'native'
        source.write_text('#include <fstream>\nint main(){std::ofstream("result.h5") << "native";}\n')
        subprocess.run(['g++', str(source), '-o', str(binary)], check=True)
        self.assertIsNone(self.run_direct([str(binary)]))
        self.assertEqual((self.work / 'result.h5').read_text(), 'native')

    def test_ordinary_solve_py_copy(self):
        submission = self.root / 'submission'; submission.mkdir()
        (submission / 'solve.py').write_text("from pathlib import Path;Path('result.h5').write_text('ordinary')")
        with patch.object(judge, 'SOURCE_REPAIR', False), patch.object(judge, 'SUBMISSION', submission):
            self.assertIsNone(judge.execute(self.work, 2, self.logs))
        self.assertEqual((self.work / 'result.h5').read_text(), 'ordinary')
        self.assertIsNone(self.sentinel.poll())

    def test_unreapable_child_is_bounded_infrastructure_failure(self):
        # Real uninterruptible kernel IO cannot be safely induced in a unit
        # test. Model waitpid reporting a live child after the cleanup deadline.
        from unittest.mock import Mock
        receipt = self.logs / 'execution.json'
        process = Mock(); process.wait.return_value = 0
        with patch('ctypes.CDLL', return_value=types.SimpleNamespace(prctl=lambda *a: 0)), \
                patch.object(judge.subprocess, 'Popen', return_value=process), \
                patch.object(judge.Path, 'read_text', return_value='234'), \
                patch.object(judge.os, 'kill') as kill, \
                patch.object(judge.os, 'waitpid', return_value=(0, 0)), \
                patch.object(judge.time, 'monotonic', side_effect=[0, 6]):
            with self.assertRaisesRegex(RuntimeError, 'cleanup exceeded 5 seconds'):
                judge.supervise(receipt, 1, ['unused'])
            kill.assert_called_once_with(234, judge.signal.SIGKILL)
        error = json.loads(receipt.read_text())
        self.assertEqual(error['remaining_pids'], [234])
        self.assertEqual(error['cleanup_timeout_seconds'], 5)
        self.assertIn('infrastructure_error', error)
        self.assertIsNone(self.sentinel.poll())


if __name__ == '__main__': unittest.main()
