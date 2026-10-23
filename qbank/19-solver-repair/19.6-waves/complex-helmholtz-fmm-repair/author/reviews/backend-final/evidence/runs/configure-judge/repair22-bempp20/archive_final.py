"""Archive exact review/raw evidence under the task; no public changes."""
from pathlib import Path
import shutil,json,hashlib
root=Path(__file__).resolve().parents[3];review=Path(__file__).resolve().parent
task=root/'qbank/19-solver-repair/19.6-waves/complex-helmholtz-fmm-repair'
dest=task/'author/reviews/backend-final';dest.mkdir(parents=True,exist_ok=True)
sources=list(p for p in review.iterdir() if p.is_file())
sources+=list(p for p in (root/'runs/authoring/repair-22/bempp-backend-probes-v4').rglob('*') if p.is_file())
sources+=list(p for p in (root/'runs/authoring/repair-22/bempp-backend-probes-v1').rglob('*') if p.is_file())
sources+=list(p for p in (root/'runs/harbor/jobs/repair22-bempp20-oracle-v4').rglob('*') if p.is_file())
sources+=list(p for p in (root/'runs/harbor/tasks'/task.name).rglob('*') if p.is_file())
sources+=list(p for p in (task/'author/data-evidence/offline-install-v2').rglob('*') if p.is_file())
for n in ['repair22-bempp20-oracle-v1.json','repair22-bempp20-oracle-v2.json','repair22-bempp20-oracle-v3.json','repair22-bempp20-oracle-v4.json','bempp-probes-v4-pipeline.py']:
 sources.append(root/'runs/authoring/repair-22'/n)
sources += [root/'tests/test_harbor_process_cleanup.py',root/'src/utils/harbor/tests/judge.py',root/'src/utils/harbor/tests/source_repair.py',root/'src/caeoj_tools/source_repair.py',root/'src/utils/prepare_harbor.py',root/'work/repair-22/bempp-20/probe-context-v4/backend_probe.py',root/'work/repair-22/bempp-20/probe-context-v4/Dockerfile',root/'work/repair-22/bempp-20/check-offline.py']
entries=[]
for p in sorted(set(sources)):
 rel=p.relative_to(root);target=dest/'evidence'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
 data=p.read_bytes();assert target.read_bytes()==data
 entries.append({'archive_path':target.relative_to(dest).as_posix(),'source_path':rel.as_posix(),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
shutil.copyfile(review/'report.md',dest/'report.md')
data=(dest/'report.md').read_bytes();entries.append({'archive_path':'report.md','source_path':(review/'report.md').relative_to(root).as_posix(),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
index={'version':1,'review_result':'passed final bounded backend closure','public_zip_sha256':'3b2f5344125bf5679bd026bef828bbe97a44c9a132cca97a5975a25ed8d319bf','oracle':'repair22-bempp20-oracle-v4','judge_sha256_lf':'5595500ff6c8612f4682f4eda0cdc6521c5af94343dcba6c825bb3555141180f','files':entries}
index_path=dest/'archive-index.json';index_path.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(dest/'archive-index.sha256').write_text(hashlib.sha256(index_path.read_bytes()).hexdigest()+'  archive-index.json\n',encoding='ascii')
for e in entries:assert hashlib.sha256((dest/e['archive_path']).read_bytes()).hexdigest()==e['sha256']
print(json.dumps({'files':len(entries),'archive':str(dest),'index_sha256':hashlib.sha256(index_path.read_bytes()).hexdigest(),'all_copies_verified':True}))
