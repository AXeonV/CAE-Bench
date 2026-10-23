"""Independent read-only production-image access inventory, run as UID1000."""
import os,json,sys
from pathlib import Path
assert os.geteuid()==1000
count=0;writable=[]
for root in ['/opt/aspect','/opt/aspect-build','/opt/caeoj-python']:
 for p in [Path(root),*Path(root).rglob('*')]:
  if p.is_symlink():continue
  count+=1
  if os.access(p,os.W_OK):writable.append(str(p))
for p in ['/','/opt','/usr','/usr/local','/usr/local/bin','/opt/aspect/source','/opt/aspect/source/simulator','/opt/caeoj-python/bin']:
 if os.access(p,os.W_OK):writable.append(p)
assert not writable,writable
print(json.dumps({'uid':os.geteuid(),'all_source_build_sdk_paths_checked':count,'writable':writable,'python':sys.executable}))
