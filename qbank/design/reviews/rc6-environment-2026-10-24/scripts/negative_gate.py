"""Verify missing promised dependencies stop before judge and reward creation."""
import hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path('D:/Code/CAE-Bench-OJ');WORK=ROOT/'runs/releases/rc6-authoring'
probe=WORK/'negative-gate-v2';probe.mkdir();material=probe/'material';material.mkdir();logs=probe/'logs';logs.mkdir()
for source,name in [('src/utils/harbor/environment/check_environment.py','check_environment.py'),('src/utils/harbor/tests/test.sh','test.sh')]:
    (material/name).write_bytes((ROOT/source).read_bytes().replace(b'\r\n',b'\n'))
(material/'judge.py').write_text("from pathlib import Path\nPath('/logs/verifier/judge-ran').write_text('unexpected')\n",encoding='utf-8')
command=['docker','run','--rm','--network','none','--env','PYTHONOPTIMIZE=1',
    '--mount',f'type=bind,source={material},target=/root/test-material,readonly',
    '--mount',f'type=bind,source={logs},target=/logs/verifier','caeoj-runtime:20261024-rc6','bash','-lc',
    'chmod 700 /root && cp -a /root/test-material /tests && python -m pip uninstall -y scipy && bash /tests/test.sh']
started=time.time();result=subprocess.run(command,text=True,encoding='utf-8',errors='replace',capture_output=True,timeout=180)
(probe/'stdout.log').write_text(result.stdout,encoding='utf-8');(probe/'stderr.log').write_text(result.stderr,encoding='utf-8')
assert result.returncode!=0 and "No module named 'scipy'" in result.stderr
assert not any((logs/name).exists() for name in ['judge-ran','report.json','reward.txt'])
record={'status':'passed','network':'none','python_optimization_enabled':True,'exit_code':result.returncode,
    'judge_executed':False,'report_created':False,'reward_created':False,'new_model_calls':0,'score_corrections':0,
    'elapsed_seconds':time.time()-started,'check_environment_sha256':hashlib.sha256((material/'check_environment.py').read_bytes()).hexdigest(),
    'test_sh_sha256':hashlib.sha256((material/'test.sh').read_bytes()).hexdigest()}
(WORK/'negative-environment-gate.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record),flush=True)
