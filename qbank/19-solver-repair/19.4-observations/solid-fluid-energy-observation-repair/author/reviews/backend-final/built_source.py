import hashlib,json,os
from pathlib import Path
R=Path('/workspace');T=R/'qbank/19-solver-repair/19.4-observations/solid-fluid-energy-observation-repair';O=R/'runs/configure-judge/repair22-moose22074';m=json.loads((T/'author/data-evidence/source-closure.json').read_text());errors=[]
for record in m['files']:
 p=Path('/opt/moose-source-2022')/record['path']
 try:
  with p.open('rb') as f:s=hashlib.file_digest(f,'sha256').hexdigest()
  if s!=record['sha256']:errors.append({'file':record['path'],'actual':s,'expected':record['sha256']})
 except Exception as exc:errors.append({'file':record['path'],'error':str(exc)})
target=Path('/opt/moose-source-2022/modules/navier_stokes');absence={str(target/sub/name):not (target/sub/name).exists() for sub,name in [('src/postprocessors','INSElementIntegralEnergyAdvection.C'),('include/postprocessors','INSElementIntegralEnergyAdvection.h')]}
r={'files_checked':len(m['files']),'errors':errors,'target_files_absent':absence,'uid':os.getuid()};(O/'built-source.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));assert not errors and all(absence.values())
