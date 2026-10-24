"""Build the release's pinned Linux runtime; initial construction needs network."""
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parent
config = json.loads((root/'runtime.json').read_text(encoding='utf-8'))
subprocess.run(['docker', 'build', '--platform', config['platform'], '--progress=plain',
                '-t', config['image'], str(root)], check=True)
print('Runtime ready: ' + config['image'])
