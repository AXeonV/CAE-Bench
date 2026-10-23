"""Exercise actual budget consumer without solver or large-case reload."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tomllib
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'src/utils'),str(ROOT/'qbank/extensions')]
WORK=ROOT/'runs/continuous-scoring'
relative=Path('qbank/01-prescribed-pdes/1.7-coupled-systems/compressible-navier-stokes-3d')
task=ROOT/relative
spec=importlib.util.spec_from_file_location('independent_prepare_harbor',ROOT/'src/utils/prepare_harbor.py')
consumer=importlib.util.module_from_spec(spec);spec.loader.exec_module(consumer)
config=json.loads((task/'judge-config.json').read_text(encoding='utf-8'))
overrides=tomllib.loads((task/'harbor/task.toml').read_text(encoding='utf-8'))
template=(ROOT/'src/utils/harbor/task.toml').read_text(encoding='utf-8')
rendered=tomllib.loads(consumer.task_config(template,overrides,judge_config=config,case_count=6))
assert config['timeout_seconds']==1800 and config['evaluation_timeout_seconds']==120
assert rendered['verifier']['timeout_sec']==12180
assert 300+6*(1800+120+60)==12180
stage=WORK/'publish-stage'/relative
assert (stage/'judge-config.json').read_bytes()==(task/'judge-config.json').read_bytes()
assert (stage/'harbor/task.toml').read_bytes()==(task/'harbor/task.toml').read_bytes()
files=[task/'judge-config.json',task/'harbor/task.toml',WORK/'large-preflight.json',ROOT/'src/utils/prepare_harbor.py',ROOT/'src/utils/harbor/tests/judge.py']
out={'status':'passed','actual_task_config_consumer':True,'case_count':6,'solver_timeout_seconds':1800,'evaluation_timeout_seconds':120,'verifier_timeout_seconds':12180,'main_and_publish_stage_private_resources_identical':True,'limitations':'Representative host measurement only; no solver/resource/container/full-case/cross-machine calibration performed by this check. Managed-worker timeout consumption independently read in judge source.','sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(WORK/'independent-resource.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='sha256'}))
