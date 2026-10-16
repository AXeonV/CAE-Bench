"""Authoring must emit UTF-8 without relying on Python UTF-8 mode."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
GENERATE = """
import importlib.util,json,sys
from pathlib import Path
script,destination=map(Path,sys.argv[1:])
spec=importlib.util.spec_from_file_location('encoding_probe',script)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.ROOT=destination
(destination/'qbank/extensions/caeoj_ext'/script.stem).mkdir(parents=True)
module.write()
print(json.dumps({'utf8_mode':sys.flags.utf8_mode,'tasks':len(module.MODELS)}))
"""


class AuthoringEncodingTests(unittest.TestCase):
    def generated_chapter(self, name, count):
        script = ROOT / 'qbank/maintenance/authoring' / (name + '.py')
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary)
            environment = dict(os.environ, PYTHONUTF8='0')
            process = subprocess.run(
                [sys.executable, '-X', 'utf8=0', '-c', GENERATE, str(script), temporary],
                env=environment, capture_output=True, encoding='utf-8', errors='backslashreplace')
            self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
            self.assertEqual(json.loads(process.stdout), {'utf8_mode': 0, 'tasks': count})
            documents = sorted(destination.rglob('instruction.md'))
            self.assertEqual(len(documents), count)
            for emitted in destination.rglob('*'):
                if emitted.is_file():
                    relative = emitted.relative_to(destination)
                    with self.subTest(file=str(relative)):
                        content = emitted.read_text(encoding='utf-8')
                        expected = (ROOT / relative).read_text(encoding='utf-8')
                        self.assertEqual(content, expected)

    def test_multiphysics_text_without_utf8_mode(self):
        self.generated_chapter('multiphysics', 12)

    def test_systems_text_without_utf8_mode(self):
        self.generated_chapter('systems', 10)


if __name__ == '__main__':
    unittest.main()
