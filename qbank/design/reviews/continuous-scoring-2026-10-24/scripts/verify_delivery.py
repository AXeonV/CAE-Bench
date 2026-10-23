import hashlib
import json
from pathlib import Path
import time
import zipfile

root = Path('D:/Code/CAE-Bench-OJ/runs/releases/caeoj-qbank-20261024-rc5')
work = Path('D:/Code/CAE-Bench-OJ/runs/continuous-scoring')
delivery = json.loads((work / 'delivery.json').read_text(encoding='utf-8'))
checks = json.loads((root / 'SHA256SUMS.json').read_text(encoding='utf-8'))
print(type(checks).__name__, flush=True)
if 'files' in checks:
    checks = checks['files']
checks['SHA256SUMS.json'] = {
    'sha256': hashlib.sha256((root / 'SHA256SUMS.json').read_bytes()).hexdigest(),
    'size_bytes': (root / 'SHA256SUMS.json').stat().st_size,
}
started = time.time()
with zipfile.ZipFile(delivery['archive']) as archive:
    names = [root.name + '/' + p for p in checks]
    assert len(archive.namelist()) == len(names) and set(archive.namelist()) == set(names)
    for name, expected in checks.items():
        full = root.name + '/' + name
        digest = hashlib.sha256()
        size = 0
        with archive.open(full) as source:
            while block := source.read(1024 * 1024):
                digest.update(block)
                size += len(block)
        assert digest.hexdigest() == expected['sha256'], name
        assert size == expected['size_bytes'], name
result = {'status': 'passed', 'members': len(names), 'elapsed_seconds': time.time() - started,
          'method': 'Stream every outer ZIP member and compare bytes/SHA256 to independently verified release directory.',
          'archive': delivery['archive'], 'sha256': delivery['sha256']}
(work / 'delivery-verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(result), flush=True)
