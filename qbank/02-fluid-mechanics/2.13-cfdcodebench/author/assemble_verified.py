"""Assemble the verified local CFDCodeBench cases through existing data commands.

No HF operation, reference recomputation, public sample selection, or benchmark.
Heavy staging stays under runs; canonical manifests and light audit evidence are
maintained with each task. Existing differing data always require review.
"""
import argparse,hashlib,json,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
from catalog import ROOT,SECTION,WORK,REVISION,catalog
from caeoj_tools import data_pool

def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--first-task-number',type=int,default=6);args=ap.parse_args()
 out=args.output.resolve();out.relative_to((ROOT/'runs').resolve());out.mkdir(parents=True,exist_ok=True)
 if (out/'summary.json').exists():raise ValueError('Assembly report already exists; choose a fresh output directory')
 certification=read(WORK/'certification.json');verified={r['index']:r for r in certification if r['status']=='verified_with_stated_limits'}
 installed={r['index']:r for r in read(WORK/'installed-real-cases/summary.json')['rows']}
 if len(verified)!=23 or 19 in verified:raise ValueError('This reviewed operation expects the23 verified cases excludingC19')
 ids={read(p)['task_id']:p.parent.name for p in (ROOT/'qbank').rglob('data-manifest.json')}
 rows=[]
 for c in catalog():
  i=c['index']
  if i not in verified:continue
  task=SECTION/c['task'];source=WORK/'local-pool'/c['task']/f'C{i:02}-base';cert=verified[i]
  reference=source/'reference/reference.h5'
  if sha(reference)!=cert['reference_sha256']:raise ValueError('Reference changed after numerical validation')
  if installed[i].get('status')!='passed' or installed[i].get('reference_sha256')!=sha(reference):raise ValueError('Installed CLI validation does not bind current reference')
  task_id=f"caeoj-{args.first_task_number+i-1:06d}"
  if task_id in ids and ids[task_id]!=c['task']:raise ValueError('Stable task ID already owned: '+task_id)
  if (task/'data-manifest.json').exists() and read(task/'data-manifest.json')['task_id']!=task_id:raise ValueError('Cannot reassign stable task ID')
  prepared=out/'prepared'/c['task'];bundle=out/'bundles'/c['task'];logs=out/'logs'/c['task'];logs.mkdir(parents=True,exist_ok=True)
  if prepared.exists() or bundle.exists():raise ValueError('Staging destination already exists; preserve/review partial attempt')
  shutil.copytree(source/'input',prepared/'cases/001');shutil.copytree(source/'reference',prepared/'reference/001')
  input_hashes={p.relative_to(source/'input').as_posix():sha(p) for p in (source/'input').rglob('*') if p.is_file()}
  ref_hashes={p.relative_to(source/'reference').as_posix():sha(p) for p in (source/'reference').rglob('*') if p.is_file()}
  certificate=dict(source_id='CFDCodeBench:'+REVISION+':'+c['source_id'],source_revision=REVISION,source_problem=c['source_id'],development_case_id=f'C{i:02}-base',input_files=input_hashes,reference_files=ref_hashes,contract_sha256=sha(ROOT/'docs/CONTRACT.md'),numerical_validation_sha256=sha(source/'certification.json'),numerical_validation=cert,reference_production=read(source/'validation.json'),conversion_tool_sha256=sha(Path(__file__)),resource_status='provisional',hf_uploaded=False)
  evidence=prepared/'author/data-evidence/reference/001';write(evidence/'certificate.json',certificate)
  def cli(label,*arguments):
   command=[sys.executable,'-m','caeoj_tools.cli','data',*map(str,arguments)]
   p=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
   (logs/(label+'.stdout.json')).write_text(p.stdout,encoding='utf-8');(logs/(label+'.stderr.log')).write_text(p.stderr,encoding='utf-8')
   if p.returncode:raise RuntimeError(label+': '+p.stderr+p.stdout)
   return json.loads(p.stdout)
  cli('pack','pack','--task',c['task'],'--source',prepared,'--output',bundle,'--task-id',task_id)
  validated=data_pool.validate_bundle(bundle)
  selection=read(bundle/'selection.json');case_id=selection['cases']['001']['case_id']
  # Notes are reviewed selection metadata, never an assembly receipt.
  selection['notes']='Local-only verified test data; not uploaded to HF. Assemble offline using --source-dir. No public sample selected; resource calibration remains provisional.'
  data_pool.write_json(bundle/'selection.json',selection)
  cli('select','select','--task',c['task'],'--manifest',bundle/'selection.json','--source-dir',bundle/'repository','--case','001='+case_id,'--output',task/'data-manifest.json')
  assembly=cli('assemble','assemble','--task',c['task'],'--source-dir',bundle/'repository')
  strict=cli('verify','verify','--task',c['task'],'--strict')
  installed_python=ROOT/'runs/install-check/cfdcodebench-20261019/venv/Scripts/python.exe'
  p=subprocess.run([str(installed_python),'-I','-m','caeoj','grade','--input',str(task/'cases/001/problem.json'),'--output',str(task/'reference/001/reference.h5'),'--grading',str(task/'reference/001/grading.json')],cwd=logs,capture_output=True,text=True,encoding='utf-8',errors='replace')
  (logs/'installed-grade.json').write_text(p.stdout,encoding='utf-8')
  if p.returncode or json.loads(p.stdout).get('score')!=1:raise RuntimeError('Actual installed consumption failed: '+p.stderr+p.stdout)
  if sha(task/'reference/001/reference.h5')!=cert['reference_sha256']:raise ValueError('Assembled reference SHA mismatch')
  row=dict(index=i,task=c['task'],task_id=task_id,development_case_id=f'C{i:02}-base',pool_case_id=case_id,case_name='001',samples=0,numerical_validation='passed_with_stated_limits',strict_integrity=strict,installed_cli_grade='passed',reference_sha256=cert['reference_sha256'],manifest_sha256=sha(task/'data-manifest.json'),descriptor_sha256=read(task/'data-manifest.json')['cases']['001']['case']['sha256'],offline_repository=(bundle/'repository').relative_to(ROOT).as_posix(),assembly_report=assembly,resource_status='provisional')
  target=task/'author/data-evidence';target.mkdir(parents=True,exist_ok=True)
  write(target/'certificate.json',certificate);write(target/'local-assembly.json',row)
  rows.append(row);write(out/'progress.json',dict(completed=len(rows),rows=rows));print(json.dumps(dict(index=i,task=c['task'],strict_verified=True,installed_cli_grade='passed')),flush=True)
 summary=dict(schema_version=1,created_utc=datetime.now(timezone.utc).isoformat(),task_count=len(rows),cases=len(rows),samples=0,excluded=[dict(index=19,reason='Reference numerical validation incomplete')],hf_uploaded=False,resource_status='provisional',rows=rows)
 write(out/'summary.json',summary)
 write(SECTION/'author/local-assembly-index.json',{k:v for k,v in summary.items() if k!='rows'}|dict(rows=[{k:r[k] for k in ('index','task','task_id','pool_case_id','case_name','samples','reference_sha256','manifest_sha256','descriptor_sha256','offline_repository')} for r in rows],full_report=(out/'summary.json').relative_to(ROOT).as_posix()))
 print(json.dumps(dict(tasks=len(rows),strict_verify='passed',installed_cli='passed',hf_uploaded=False)))
if __name__=='__main__':main()
