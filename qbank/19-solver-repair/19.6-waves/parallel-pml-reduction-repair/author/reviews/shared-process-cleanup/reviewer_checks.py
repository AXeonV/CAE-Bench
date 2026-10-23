"""Independent bounded checks; no active task assembly or source edits."""
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path('/audit') if sys.platform == 'linux' else Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('review_judge', ROOT/'src/utils/harbor/tests/judge.py')
judge = importlib.util.module_from_spec(spec); spec.loader.exec_module(judge)

class ReviewerChecks(unittest.TestCase):
    @unittest.skipUnless(sys.platform == 'linux', 'Linux only')
    def test_thread_fork_environment_receipt_and_same_uid_sentinel(self):
        self.assertEqual(signal.getsignal(signal.SIGCHLD), signal.SIG_DFL)
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); root.chmod(0o755)
            work=root/'work'; work.mkdir(mode=0o777); work.chmod(0o777)
            logs=root/'logs'; logs.mkdir(mode=0o700)
            config=root/'tests'; config.mkdir()
            (config/'source-repair.json').write_text(json.dumps({'build_directory':'/tmp'}))
            script=work/'thread.py'
            script.write_text('''import os,threading,time,json
from pathlib import Path
Path('identity.json').write_text(json.dumps({'uid':os.geteuid(),'env':dict(os.environ),'logs_access':os.access(LOGS,os.R_OK|os.X_OK)}))
def record(): Path('pid-'+str(os.getpid())).write_text(str(os.getpid()))
def worker():
 if os.fork()==0:
  os.setsid();record()
  if os.fork()==0:
   os.setsid();record();time.sleep(60)
  time.sleep(60)
t=threading.Thread(target=worker);t.start();t.join();time.sleep(.3)
'''.replace('LOGS',repr(str(logs))))
            command=['setpriv','--reuid=1000','--regid=1000','--clear-groups','sleep','60']
            sentinel=subprocess.Popen(command)
            try:
                backend=types.SimpleNamespace(command=lambda directory:['python',str(script)])
                with patch.object(judge,'SOURCE_REPAIR',True),patch.object(judge,'TESTS',config),patch.dict(sys.modules,{'source_repair':backend}),patch.dict(os.environ,{'REVIEW_SECRET':'must-not-leak'}):
                    self.assertIsNone(judge.execute(work,2,logs))
                self.assertIsNone(sentinel.poll())
                identity=json.loads((work/'identity.json').read_text())
                self.assertEqual(identity['uid'],1000)
                self.assertFalse(identity['logs_access'])
                self.assertNotIn('REVIEW_SECRET',identity['env'])
                self.assertEqual(identity['env']['LD_LIBRARY_PATH'],'/tmp/lib')
                pids=list(work.glob('pid-*'));self.assertEqual(len(pids),2)
                for pid in pids:self.assertFalse(Path('/proc',pid.read_text()).exists())
                self.assertIsNone(json.loads((logs/'execution.json').read_text()))
                self.assertEqual((logs/'execution.json').stat().st_uid,0)
            finally:sentinel.kill();sentinel.wait()

    def test_supervisor_nonzero_is_infrastructure_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);logs=root/'logs';logs.mkdir()
            (root/'source-repair.json').write_text(json.dumps({'build_directory':'/tmp'}))
            backend=types.SimpleNamespace(command=lambda directory:['unused'])
            with patch.object(judge,'SOURCE_REPAIR',True),patch.object(judge,'TESTS',root),patch.dict(sys.modules,{'source_repair':backend}),patch.object(judge.subprocess,'run',return_value=types.SimpleNamespace(returncode=1)):
                with self.assertRaisesRegex(RuntimeError,'supervision failed'):judge.execute(root,1,logs)

    def test_cleanup_error_stops_before_second_case_without_reward(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);private=root/'tests';private.mkdir();logs=root/'logs'
            (private/'judge-config.json').write_text(json.dumps({'timeout_seconds':1}))
            (private/'selection.json').write_text(json.dumps({'public_cases':[]}))
            for name in ('01','02'):
                case=private/'cases'/name;case.mkdir(parents=True);(case/'problem.json').write_text('{}')
            with patch.object(judge,'TESTS',private),patch.object(judge,'LOGS',logs),patch.object(judge,'load_problem'),patch.object(judge,'prepare_case',return_value=types.SimpleNamespace(evidence={})),patch.object(judge,'freeze_submission',return_value=True),patch.object(judge.os,'chown',create=True),patch.object(judge,'execute',side_effect=RuntimeError('Solver process supervision failed')) as execute:
                with self.assertRaisesRegex(RuntimeError,'supervision failed'):judge.main()
            self.assertEqual(execute.call_count,1)
            self.assertFalse((logs/'02').exists())
            self.assertFalse((logs/'reward.txt').exists())

if __name__=='__main__':unittest.main(verbosity=2)
