from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[3];TASK=ROOT/'qbank/19-solver-repair/19.2-operators/grand-potential-derivatives-repair';OUT=Path(__file__).parent
J=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v=J(TASK/'author/data-evidence/target-source-versions.json')
for file,role in [('reference-image.json','author-complete'),('upstream-image.json','upstream'),('probe-image.json','baseline')]:
 image=J(OUT/file)
 for name,hashes in v['files'].items():
  path='/opt/moose-source/modules/phase_field/'+('src/materials/' if name.endswith('.C') else 'include/materials/')+name
  assert image['hashes'][path]==hashes[role]
 for observer in ['RepairDofMap.C','RepairDerivativeAverage.C']:
  hashes=[s for p,s in image['hashes'].items() if p.endswith('/'+observer)];assert hashes==[sha(TASK/'public'/observer)]
probe=J(OUT/'probe-image.json')['hashes'];assert probe['/tmp/agent.zip']==sha(ROOT/'dist/grand-potential-derivatives-repair-agent.zip')
assert probe['/tests/source_repair.py']==hashlib.sha256((ROOT/'src/utils/harbor/tests/source_repair.py').read_bytes().replace(b'\r\n',b'\n')).hexdigest()
cli=J(OUT/'public-cli-rerun.json');assert [r['returncode'] for s in cli['samples'] for r in s['commands']]==[0,0,0,1]*2
assert [json.loads(s['commands'][-1]['stdout'])['score'] for s in cli['samples']]==[0,0]
for directory in [OUT,ROOT/'runs/data-review/repair22-moose30236']:
 files=[p for p in directory.rglob('*') if p.is_file() and p.name!='materials-sha256.json']
 files += [ROOT/p for p in ['AGENTS.md','.agents/skills/caeoj-data-review/SKILL.md','.agents/skills/caeoj-configure-judge/SKILL.md','.agents/skills/caeoj-configure-judge/references/workflow.md','.agents/skills/caeoj-configure-judge/references/current-backend.md','docs/CONTRACT.md','docs/GRADING.md','qbank/maintenance/DATA-SYNC.md','qbank/maintenance/CASE-SOURCING.md','qbank/maintenance/EVALUATION.md','runs/configure-judge/repair22-mpi-cleanup/report.md','runs/configure-judge/repair22-mpi-cleanup/materials-sha256.json','runs/authoring/repair-22/moose-30236-verifier-build-v1.job.log']]
 files += [TASK/p for p in ['instruction.md','DATA.md','judge-config.json','harbor/task.toml','harbor/source-repair.json','author/backend_probe.py','author/run_backend_probes.py','author/replay.py','author/prepare_source.py','author/verify_public_inside.py','public/run_case.py','public/native_result.py','public/CMakeLists.txt','public/RepairDofMap.C','public/RepairDerivativeAverage.C','extension/caeoj_task_ext/grand_potential.py','author/data-evidence/hf-assembly.json','author/data-evidence/target-source-versions.json','author/data-evidence/harbor-oracle-v1/frozen-run.json','author/data-evidence/harbor-oracle-v1/manifest.json']]
 records={str(p.relative_to(ROOT)).replace('\\','/'):{'sha256':sha(p),'bytes':p.stat().st_size} for p in files}
 (directory/'materials-sha256.json').write_text(json.dumps(records,indent=2)+'\n')
print('PASS image source/observer/backend/ZIP identities and fresh 8CLI; review frozen')
