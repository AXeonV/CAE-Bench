import json,hashlib,os,subprocess
from pathlib import Path
manifest=json.loads(Path('/review/source-closure.json').read_text());base=Path('/opt/moose-source');bad=[]
for rec in manifest['files']:
 p=base/rec['path']
 if hashlib.sha256(p.read_bytes()).hexdigest()!=rec['sha256']:bad.append(rec['path'])
assert not bad,bad
print(json.dumps({'source_files':len(manifest['files']),'source_hashes_match_fixed_archive':True,'target_source':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [base/'modules/phase_field/src/materials/GrandPotentialSinteringMaterial.C',base/'modules/phase_field/include/materials/GrandPotentialSinteringMaterial.h']},'executable':str(base/'modules/phase_field/phase_field-opt'),'native_executable_exists':(base/'modules/phase_field/phase_field-opt').is_file()}))
