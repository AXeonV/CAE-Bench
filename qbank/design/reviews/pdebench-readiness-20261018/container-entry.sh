#!/bin/bash
set -euo pipefail
cd /tmp
rm -rf /app /tests /tmp/agent.zip /tmp/requirements.txt
mkdir -p /app/submission /tests /logs/verifier
cp -a /candidate-materials/public/. /app/
mv /new-tests/. /tests/ 2>/dev/null || cp -a /new-tests/. /tests/
rm -rf /new-tests
chown -R 0:0 /tests
chmod 700 /tests
python -m pip install --no-index --no-deps --force-reinstall /candidate-materials/wheels/*.whl
cp /submitted/solve.py /app/submission/solve.py
cd /app
python - <<'PY'
from pathlib import Path
import caeoj,importlib.util,json
assert '/site-packages/' in caeoj.__file__
assert importlib.util.find_spec('caeoj_tools') is None
print(json.dumps({'installed_core':caeoj.__file__,'maintenance_package_present':False,
 'cpu_max':Path('/sys/fs/cgroup/cpu.max').read_text().strip(),
 'memory_max':Path('/sys/fs/cgroup/memory.max').read_text().strip(),
 'swap_max':Path('/sys/fs/cgroup/memory.swap.max').read_text().strip()}))
PY
bash /tests/test.sh
