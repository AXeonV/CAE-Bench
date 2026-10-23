import hashlib
import json
from pathlib import Path
import shutil
import time
import zipfile

repo = Path('D:/Code/CAE-Bench-OJ')
work = repo / 'runs/continuous-scoring'
root = Path('D:/Code/CAE-Bench-OJ/runs/releases/caeoj-qbank-20261024-rc5')
target = root.with_suffix('.zip')
started = time.time()
with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
    for p in sorted(root.rglob('*')):
        if not p.is_file():
            continue
        info = zipfile.ZipInfo(root.name + '/' + p.relative_to(root).as_posix(), (1980, 1, 1, 0, 0, 0))
        info.external_attr = 0o100644 << 16
        with p.open('rb') as src, archive.open(info, 'w', force_zip64=True) as dst:
            shutil.copyfileobj(src, dst, 1024 * 1024)
h = hashlib.sha256()
with target.open('rb') as f:
    while block := f.read(1024 * 1024):
        h.update(block)
result = {'archive': str(target), 'bytes': target.stat().st_size, 'sha256': h.hexdigest(),
          'elapsed_seconds': time.time() - started, 'method': 'ZIP_STORED wrapper; inner qbank.zip is compressed; no dataset duplication inside wrapper'}
(work / 'delivery.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
state = json.loads((work / 'state.json').read_text(encoding='utf-8'))
state.update(stage='packaged_pending_verification', delivery=result, validation='independent-consumption.json', completed_unix=time.time())
(work / 'state.json').write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(result, ensure_ascii=False), flush=True)
