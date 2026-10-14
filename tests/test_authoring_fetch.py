"""Retrieval invariants; fixture transfers only small deterministic byte strings."""
import hashlib
import http.server
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import threading
import time
import unittest

SPEC = importlib.util.spec_from_file_location(
    "authoring_fetch", Path(__file__).resolve().parents[1] / "src/utils/authoring/fetch.py")
fetcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fetcher)
PAYLOAD = b"pinned fixture data" * 100


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        offset = int(self.headers.get("Range", "bytes=0-").split("=")[1].split("-")[0])
        if self.path == "/no-range": offset = 0
        self.send_response(206 if offset else 200)
        if offset:
            start = offset + 1 if self.path == "/bad-range" else offset
            self.send_header("Content-Range", f"bytes {start}-{len(PAYLOAD)-1}/{len(PAYLOAD)}")
        self.send_header("Content-Length", str(len(PAYLOAD)-offset))
        self.end_headers()
        try:
            if self.path == "/slow":
                for value in PAYLOAD:
                    self.wfile.write(bytes([value])); self.wfile.flush(); time.sleep(.05)
            else: self.wfile.write(PAYLOAD[offset:])
        except (BrokenPipeError, ConnectionResetError): pass

    def log_message(self, *args): pass


class FetchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.cache = Path(self.temp.name) / "cache"
        source = {"id":"fixture","path":"raw/data.bin",
                  "url":f"http://127.0.0.1:{self.server.server_port}/data",
                  "sha256":hashlib.sha256(PAYLOAD).hexdigest(),"size_bytes":len(PAYLOAD),
                  "sample":True,"mapping":{"source":"fixture bytes","oj":"fixture bytes"}}
        self.manifest = {"version":1,"sources":[source]}

    def tearDown(self): self.temp.cleanup()

    def transports(self): return ["urllib"] + (["curl"] if shutil.which("curl") else [])

    def test_download_cache_and_resume(self):
        for transport in self.transports():
            with self.subTest(transport=transport):
                cache=self.cache/transport
                first=fetcher.fetch(self.manifest,cache,transport=transport)
                self.assertEqual(first["downloaded_bytes"],len(PAYLOAD))
                second=fetcher.fetch(self.manifest,cache,transport=transport)
                self.assertTrue(second["sources"][0]["cache_hit"])
                self.assertEqual(second["downloaded_bytes"],0)
                (cache/"raw/data.bin").unlink()
                (cache/"raw/data.bin.part").write_bytes(PAYLOAD[:23])
                resumed=fetcher.fetch(self.manifest,cache,transport=transport)
                self.assertEqual(resumed["downloaded_bytes"],len(PAYLOAD)-23)

    def test_corruption_rejected(self):
        fetcher.fetch(self.manifest,self.cache)
        (self.cache/"raw/data.bin").write_bytes(b"bad")
        with self.assertRaises(ValueError): fetcher.fetch(self.manifest,self.cache)

    def test_selection_and_budget_guards(self):
        for kwargs in ({"mode":"all"},{"mode":"selected"},{"max_bytes":1},
                       {"mode":"selected","selected":["unknown"]}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError): fetcher.fetch(self.manifest,self.cache,**kwargs)
        selected=fetcher.fetch(self.manifest,self.cache,mode="selected",selected=["fixture"])
        self.assertEqual(len(selected["sources"]),1)

    def test_safe_paths_and_symlinks(self):
        for value in ("../escape","/absolute","a//b","a\\b","a/./b","C:/a"):
            with self.subTest(path=value):
                with self.assertRaises(ValueError): fetcher.safe_path(self.cache,value)
        outside=Path(self.temp.name)/"outside"; outside.mkdir()
        self.cache.mkdir()
        (self.cache/"link").symlink_to(outside,target_is_directory=True)
        with self.assertRaises(ValueError): fetcher.safe_path(self.cache,"link/data")

    def test_manifest_requires_pins_and_mapping(self):
        path=Path(self.temp.name)/"manifest.json"
        for key in ("sha256","size_bytes","mapping"):
            candidate=json.loads(json.dumps(self.manifest))
            candidate["sources"][0].pop(key)
            path.write_text(json.dumps(candidate))
            with self.assertRaises((ValueError,KeyError)): fetcher.load_manifest(path)

    def test_range_rejection_and_safe_restart(self):
        for transport in self.transports():
            with self.subTest(transport=transport):
                cache=self.cache/transport
                (cache/"raw").mkdir(parents=True)
                part=cache/"raw/data.bin.part";part.write_bytes(PAYLOAD[:23])
                self.manifest["sources"][0]["url"]=f"http://127.0.0.1:{self.server.server_port}/bad-range"
                with self.assertRaises((ValueError,OSError)):
                    fetcher.fetch(self.manifest,cache,transport=transport)
                part.write_bytes(PAYLOAD[:23])
                self.manifest["sources"][0]["url"]=f"http://127.0.0.1:{self.server.server_port}/no-range"
                report=fetcher.fetch(self.manifest,cache,transport=transport)
                self.assertEqual(report["downloaded_bytes"],len(PAYLOAD))

    def test_deadline_cache_and_slow_stream(self):
        fetcher.fetch(self.manifest,self.cache)
        with self.assertRaises(TimeoutError):
            fetcher.fetch(self.manifest,self.cache,max_seconds=.000001)
        for transport in self.transports():
            with self.subTest(transport=transport):
                self.manifest["sources"][0]["url"]=f"http://127.0.0.1:{self.server.server_port}/slow"
                start=time.monotonic()
                with self.assertRaises(TimeoutError):
                    fetcher.fetch(self.manifest,self.cache/transport,max_seconds=.15,transport=transport)
                self.assertLess(time.monotonic()-start,.6)


if __name__ == "__main__": unittest.main()
