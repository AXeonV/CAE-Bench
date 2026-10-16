"""Viewer lifecycle checks use temporary local servers, never model trials."""
import importlib.util
import json
from pathlib import Path
import socket
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('benchmark_viewer', ROOT/'.agents/skills/caeoj-run-benchmark/scripts/viewer.py')
viewer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(viewer)


def free_port():
    with socket.socket() as listener:
        listener.bind(('127.0.0.1',0))
        return listener.getsockname()[1]


class ViewerTests(unittest.TestCase):
    def setUp(self):
        if sys.platform == 'win32':
            self.skipTest('POSIX lifecycle helper')
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.jobs=self.root/'jobs';self.state=self.root/'monitor'
        self.port=free_port()
        self.fake=self.root/'harbor'
        self.write_server(True)

    def write_server(self, html):
        self.fake.write_text(f'''#!{sys.executable}
import argparse,json
from http.server import BaseHTTPRequestHandler,HTTPServer
p=argparse.ArgumentParser();p.add_argument('action');p.add_argument('folder');p.add_argument('--jobs',action='store_true');p.add_argument('--host');p.add_argument('--port',type=int);a=p.parse_args()
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  if self.path=='/api/health':data={{'status':'ok'}}
  elif self.path=='/api/config':data={{'folder':a.folder,'mode':'jobs'}}
  else:
   self.send_response({200 if html else 404});self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(b'<html><body>Viewer</body></html>');return
  self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps(data).encode())
HTTPServer((a.host,a.port),Handler).serve_forever()
''')
        self.fake.chmod(0o700)

    def manage(self, action, jobs=None, timeout=5):
        return viewer.manage(action,jobs or self.jobs,self.state,'127.0.0.1',self.port,str(self.fake),timeout)

    def test_start_ready_reuse_and_owned_stop(self):
        first=self.manage('start');self.addCleanup(self.manage,'stop')
        self.assertEqual(first['status'],'ready')
        self.assertEqual(first['urls'],[f'http://127.0.0.1:{self.port}'])
        second=self.manage('start')
        self.assertTrue(second['reused']);self.assertEqual(second['pid'],first['pid'])
        self.assertEqual(self.manage('status')['status'],'ready')
        with self.assertRaisesRegex(ValueError,'another directory'):
            self.manage('start',self.root/'other-jobs')
        self.assertEqual(self.manage('stop')['status'],'stopped')

    def test_port_collision_never_replaces_other_listener(self):
        with socket.socket() as listener:
            listener.bind(('127.0.0.1',self.port));listener.listen()
            with self.assertRaisesRegex(ValueError,'unavailable'):
                self.manage('start')
            with socket.create_connection(('127.0.0.1',self.port),timeout=1):
                pass
            self.assertFalse((self.state/f'viewer-{self.port}.json').exists())

    def test_api_only_server_is_not_reported_ready_and_is_cleaned(self):
        self.write_server(False)
        with self.assertRaisesRegex(ValueError,'HTML page'):
            self.manage('start',timeout=.5)
        self.assertEqual(self.manage('status')['status'],'stopped')

    def test_recycled_pid_identity_does_not_kill_a_process(self):
        first=self.manage('start');self.addCleanup(self.manage,'stop')
        path=Path(first['state_file']);state=json.loads(path.read_text())
        path.write_text(json.dumps({**state,'identity':'different process birth and command'}))
        self.assertEqual(self.manage('stop')['status'],'stale')
        self.assertTrue(viewer.probe('127.0.0.1',self.port,self.jobs.resolve()))
        path.write_text(json.dumps(state))
        self.assertEqual(self.manage('stop')['status'],'stopped')
