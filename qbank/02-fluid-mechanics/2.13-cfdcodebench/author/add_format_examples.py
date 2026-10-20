"""Add reproducible format-only samples through the existing data-pool workflow.

Copies input identity and support arrays; randomizes every output field without
reading numerical reference values. Numerical test selections stay unchanged.
All pools remain offline. Does not compute references or run a benchmark.
"""
import argparse,hashlib,importlib.util,json,shutil,subprocess,sys,zipfile
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from catalog import ROOT,SECTION,WORK
from caeoj.sdk import load_problem,write_result
from caeoj_tools import data_pool as pool

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):pool.write_json(p,v)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
 out=args.output.resolve();out.relative_to((ROOT/'runs').resolve())
 if out.exists():raise ValueError('Use a fresh output directory; preserve prior attempts')
 out.mkdir(parents=True)
 previous=read(SECTION/'author/local-assembly-index.json')
 if previous['task_count']!=23:raise ValueError('Expected reviewed23-task assembly')
 write(out/'previous-index.json',previous)
 installed=ROOT/'runs/install-check/cfdcodebench-20261019/venv/Scripts/python.exe'
 rows=[]
 for old in previous['rows']:
  task=SECTION/old['task'];before=read(task/'data-manifest.json')
  if before['samples']:raise ValueError('Review existing samples before replacing')
  ref=task/'reference/001';reference_hashes={p.name:sha(p) for p in ref.iterdir() if p.is_file()}
  prepared=out/'prepared'/old['task'];bundle=out/'bundles'/old['task'];logs=out/'logs'/old['task'];logs.mkdir(parents=True)
  shutil.copytree(task/'cases/001',prepared/'cases/001');shutil.copytree(ref,prepared/'reference/001')
  sample=prepared/'samples/01';shutil.copytree(task/'cases/001',sample/'input')
  problem=load_problem(sample/'input/problem.json');seed=2026102000+old['index'];rng=np.random.default_rng(seed)
  fields={}
  for spec in problem.manifest['outputs'].values():
   nt=len(problem.arrays[problem.manifest['time_axes'][spec['time_axis']]])
   ne=len(problem.arrays[problem.manifest['locations'][spec['location']]['ids']])
   shape=(nt,ne,*spec['component_shape'])
   fields[spec['array']]=rng.uniform(-1.,1.,size=shape).astype(spec['dtype'])
  write_result(sample/'output/result.h5',problem,fields)
  write(sample/'example.json',{'kind':'format'})
  def cli(label,*arguments):
   cmd=[sys.executable,'-m','caeoj_tools.cli','data',*map(str,arguments)]
   p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
   (logs/(label+'.stdout.json')).write_text(p.stdout,encoding='utf-8');(logs/(label+'.stderr.log')).write_text(p.stderr,encoding='utf-8')
   if p.returncode:raise RuntimeError(label+': '+p.stdout+p.stderr)
   return json.loads(p.stdout)
  cli('pack','pack','--task',old['task'],'--source',prepared,'--output',bundle)
  pool.validate_bundle(bundle)
  value=read(bundle/'selection.json');case_id=value['cases']['001']['case_id']
  if case_id!=old['pool_case_id']:raise ValueError('Input identity changed')
  value['notes']='Local-only verified tests and random format-only public samples; no HF upload. Test references unchanged; resource calibration provisional.'
  write(bundle/'selection.json',value)
  cli('select','select','--task',old['task'],'--manifest',bundle/'selection.json','--source-dir',bundle/'repository','--case','001='+case_id,'--format-sample','01='+case_id,'--output',task/'data-manifest.json')
  assembly=cli('assemble','assemble','--task',old['task'],'--source-dir',bundle/'repository','--update')
  strict=cli('verify','verify','--task',old['task'],'--strict')
  if {p.name:sha(p) for p in ref.iterdir() if p.is_file() and p.name in reference_hashes}!=reference_hashes:raise ValueError('Numerical reference changed')
  if (task/'samples/01/reference').exists():raise ValueError('Numerical reference leaked into format sample')
  # Ordinary installed public CLI checks actual assembled output from another cwd.
  p=subprocess.run([str(installed),'-I','-m','caeoj','validate-output','--input',str(task/'samples/01/input/problem.json'),'--output',str(task/'samples/01/output/result.h5')],cwd=logs,capture_output=True,text=True,encoding='utf-8',errors='replace')
  (logs/'installed-format-validation.json').write_text(p.stdout,encoding='utf-8')
  if p.returncode:raise RuntimeError('Installed format validation failed: '+p.stdout+p.stderr)
  from caeoj.case_grading import grade_case
  numerical=grade_case(task/'samples/01/input/problem.json',task/'samples/01/output/result.h5',ref/'grading.json')
  if numerical['score']==1:raise ValueError('Unexpected randomly correct result; inspect')
  manifest=read(task/'data-manifest.json')
  row={**old,'samples':1,'sample_kind':'format','sample_name':'01','seed':seed,'random_generator':'numpy.default_rng / PCG64 / uniform[-1,1)', 'output_shapes':{k:list(v.shape) for k,v in fields.items()},'sample_output_sha256':sha(task/'samples/01/output/result.h5'),'manifest_sha256':sha(task/'data-manifest.json'),'descriptor_sha256':manifest['cases']['001']['case']['sha256'],'offline_repository':(bundle/'repository').relative_to(ROOT).as_posix(),'strict_integrity':strict,'assembly_report':assembly,'reference_files_unchanged':reference_hashes,'installed_format_validation':'passed','random_output_private_grade':numerical['score'],'numerical_validation':'unchanged; see certificate.json','resource_status':'provisional'}
  write(task/'author/data-evidence/format-example.json',row);write(task/'author/data-evidence/local-assembly.json',row)
  rows.append(row);write(out/'progress.json',{'completed':len(rows),'rows':rows})
  print(json.dumps({'task':old['task'],'format_valid':True,'reference_unchanged':True}),flush=True)
 spec=importlib.util.spec_from_file_location('publish_dist',ROOT/'src/utils/publish_dist.py');pub=importlib.util.module_from_spec(spec);spec.loader.exec_module(pub)
 release=pub.publish([r['task'] for r in rows],out/'public',ROOT)
 extracted=out/'public/extracted'
 with zipfile.ZipFile(release['archive']) as z:
  names=z.namelist()
  if any('/reference/' in n or '/cases/' in n for n in names):raise ValueError('Private data leaked into archive')
  z.extractall(extracted)
  public_manifest=json.loads(z.read('MANIFEST.json'))
  if any(v!={'01':'format'} for v in public_manifest['sample_kinds'].values()):raise ValueError('Wrong public sample metadata')
 for row in rows:
  base=extracted/(SECTION/row['task']).relative_to(ROOT)/'samples/01'
  p=subprocess.run([str(installed),'-I','-m','caeoj','validate-output','--input',str(base/'input/problem.json'),'--output',str(base/'output/result.h5')],cwd=out,capture_output=True,text=True,encoding='utf-8',errors='replace')
  if p.returncode:raise RuntimeError('Extracted public sample failed: '+p.stdout+p.stderr)
 summary={'schema_version':1,'created_utc':datetime.now(timezone.utc).isoformat(),'task_count':len(rows),'cases':len(rows),'samples':len(rows),'sample_kind':'format','excluded':previous['excluded'],'hf_uploaded':False,'resource_status':'provisional','generator_sha256':sha(Path(__file__)),'public_release':release,'exported_installed_validation':'23/23 passed','rows':rows}
 write(out/'summary.json',summary)
 index={k:v for k,v in summary.items() if k not in ('rows','public_release')}
 keys=('index','task','task_id','pool_case_id','case_name','samples','sample_kind','sample_output_sha256','reference_sha256','manifest_sha256','descriptor_sha256','offline_repository')
 index['rows']=[{k:r[k] for k in keys} for r in rows];index['full_report']=(out/'summary.json').relative_to(ROOT).as_posix()
 write(SECTION/'author/local-assembly-index.json',index)
 print(json.dumps({'tasks':len(rows),'samples':len(rows),'exported_installed_validation':'passed','hf_uploaded':False}))
if __name__=='__main__':main()
