"""Sequential final RC consumer; checkpointed source assembly already completed."""
import json
from pathlib import Path
import subprocess
import sys
import time

work=Path(__file__).resolve().parent
deadline=time.monotonic()+1800
while len(json.loads((work/'provenance-preservation.json').read_text(encoding='utf-8')))!=80:
    if time.monotonic()>deadline:raise TimeoutError('Final provenance did not complete')
    time.sleep(10)
for script,log in [('build.py','build.log'),('consume.py','consume.log'),
                   ('package_delivery.py','package.log'),('verify_delivery.py','delivery-verify.log')]:
    print('Starting '+script,flush=True)
    with (work/log).open('w',encoding='utf-8') as output:
        subprocess.run([sys.executable,'-X','utf8',str(work/script)],stdout=output,stderr=subprocess.STDOUT,check=True)
    print('Passed '+script,flush=True)
state_path=work/'state.json'
state=json.loads(state_path.read_text(encoding='utf-8'))
state.update(stage='complete',completed_unix=time.time(),
             validation='independent-consumption.json; delivery-verification.json',
             ready_for_formal_benchmark=False)
state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
try:
    with (work/'record.log').open('w',encoding='utf-8') as output:
        subprocess.run([sys.executable,'-X','utf8',str(work/'record.py')],stdout=output,stderr=subprocess.STDOUT,check=True)
except Exception:
    state['stage']='verified_pending_evidence_record'
    state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
    raise
print('RC5 verified and evidence recorded',flush=True)
