import json,hashlib,subprocess
from pathlib import Path
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
base=Path('/opt/moose-source/modules/phase_field')
paths=[base/'src/materials/GrandPotentialSinteringMaterial.C',base/'include/materials/GrandPotentialSinteringMaterial.h',base/'src/postprocessors/RepairDerivativeAverage.C',base/'src/vectorpostprocessors/RepairDofMap.C',base/'lib/.libs/libphase_field-opt.so.0.0.0',base/'phase_field-opt',Path('/tests/judge.py'),Path('/tests/source_repair.py'),Path('/tmp/agent.zip')]
paths.append(base/'src/postprocessors/RepairDofMap.C')
print(json.dumps({'hashes':{str(p):sha(p) for p in paths if p.is_file()},'linked':subprocess.check_output(['/bin/bash','-lc','source /environment && ldd '+str(base/'phase_field-opt')],universal_newlines=True)}))
