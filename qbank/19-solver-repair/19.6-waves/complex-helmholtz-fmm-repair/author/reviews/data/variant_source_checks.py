from pathlib import Path
import copy,hashlib,importlib.util,json,subprocess,tarfile
import numpy as np
from caeoj.sdk import load_problem,load_result
from caeoj.validation import schema_errors,check_result
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
TASK=ROOT/'qbank/19-solver-repair/19.6-waves/complex-helmholtz-fmm-repair';DATA=ROOT/'work/repair-22/bempp-20/dataset-v2'
spec=importlib.util.spec_from_file_location('decl',TASK/'extension/caeoj_task_ext/helmholtz.py');ext=importlib.util.module_from_spec(spec);spec.loader.exec_module(ext)
points=load_problem(DATA/'cases/01-point-real/problem.json');boundary=load_problem(DATA/'cases/07-boundary-complex/problem.json')
rows=[]
def trial(name,expect,base,change):
 p=copy.deepcopy(base);change(p);errs=list(schema_errors(p.manifest))
 if not errs:ext.check(p,errs)
 rows.append(dict(name=name,expected_valid=expect,actual_valid=not errs,passed=(not errs)==expect,errors=errs))
def par(name,val):return lambda p:p.manifest['physics']['parameters'][name].update(value=val)
for name in ['wavenumber_real','wavenumber_imag']:
 for value in ([.5,3] if name.endswith('real') else [0,1.2]):trial(name+'='+str(value),True,points,par(name,value))
 for value in ([-.1,3.01] if name.endswith('real') else [-.001,1.201]):trial(name+'='+str(value),False,points,par(name,value))
trial('operation boolean',False,points,par('operation',True));trial('operation float',False,points,par('operation',0.0))
trial('wave boolean',False,points,par('wavenumber_real',True))
trial('zero complex strength',True,points,lambda p:p.arrays['strength'].fill(0))
trial('zero complex density',True,boundary,lambda p:p.arrays['density'].fill(0))
trial('strength boundary +/-2',True,points,lambda p:p.arrays['strength'].__setitem__((0,0,slice(None)),[-2,2]))
trial('strength >2',False,points,lambda p:p.arrays['strength'].__setitem__((0,0,0),2.00001))
trial('wrong component order',False,points,lambda p:p.manifest['outputs']['fmm_gradient']['components'].reverse())
trial('wrong gradient units',False,points,lambda p:p.manifest['outputs']['fmm_gradient'].update(unit='1/m'))
trial('unknown field',False,points,lambda p:p.manifest.update(unexpected=1))
trial('wrong input filename',False,points,lambda p:p.manifest.update(data_file='other.h5'))
trial('source/target coincident',False,points,lambda p:p.arrays['target_coordinates'].__setitem__(0,p.arrays['source_coordinates'][0]))
trial('targets repeated',False,points,lambda p:p.arrays['target_coordinates'].__setitem__(1,p.arrays['target_coordinates'][0]))
trial('unreferenced dataset',False,points,lambda p:p.arrays.update(extra=np.array([1.])))
trial('absent strength',False,points,lambda p:p.arrays.pop('strength'))
trial('extra condition',False,points,lambda p:p.manifest['conditions'].append({'role':'source','variable':'x','location':'sources','operator':'assign','data':{'value':{'value':0,'unit':'1'}}}))
out=load_result(points,DATA/'reference/01-point-real/reference.h5');output=[]
for name,modify in [('missing output',lambda r:r.pop('local_gradient')),('extra output',lambda r:r.update(extra=np.array([0.]))),('NaN',lambda r:r['fmm_gradient'].__setitem__((0,0,0),np.nan)),('wrong IDs',lambda r:r['target_ids'].__setitem__(0,99999)),('wrong shape',lambda r:r.update(fmm_gradient=r['fmm_gradient'][0]))]:
 r=copy.deepcopy(out);modify(r);result=check_result(points,r);output.append(dict(name=name,result=result,passed=not result['valid']))
# Read complete public archives independently, hash each regular upstream file.
orig=json.loads((TASK/'author/data-evidence/source-archives.json').read_text());archives=[]
for name,filename in [('base','bempp-source.tar.gz'),('exafmm-v0.1.0','exafmm-source.tar.gz')]:
 p=TASK/'public'/filename;expected=orig[name];actual={}
 with tarfile.open(p) as tf:
  for member in tf.getmembers():
   if member.isfile():actual['/'.join(member.name.split('/')[1:])]=hashlib.sha256(tf.extractfile(member).read()).hexdigest()
 archives.append(dict(name=name,archive_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),expected_archive_sha256=expected['sha256'],archive_hash_passed=hashlib.sha256(p.read_bytes()).hexdigest()==expected['sha256'],file_count=len(actual),manifest_equal=actual==expected['manifest']))
# Independently read all 371 production source files from each immutable image.
prior=json.loads((ROOT/'runs/authoring/repair-22/bempp-production-source-audit.json').read_text());production=[]
docker='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
for image in prior:
 expected={}
 for row in image['rows']:
  path=row['path']; rel=path.split('bempp-cl-84345ee9ee314c85750f045c7ad38090f5ea5f26/')[-1]
  if '/exafmm-t-0.1.0/' in path:want=orig['exafmm-v0.1.0']['manifest'][path.split('/exafmm-t-0.1.0/')[1]]
  elif image['kind']=='reference' and rel in ['bempp/api/fmm/'+n+'.py' for n in ['exafmm','fmm_assembler','helpers']]:want=hashlib.sha256((TASK/'author/generated'/Path(rel).name).read_bytes()).hexdigest()
  else:want=orig['base']['manifest'][rel]
  expected[path]=want
 code='import hashlib,json,pathlib\npaths='+repr(list(expected))+"\nprint(json.dumps({p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for p in paths}))"
 run=subprocess.run([docker,'run','--rm','--network','none','--read-only','-i',image['image_id'],'python','-'],input=code,text=True,capture_output=True,timeout=60);actual=json.loads(run.stdout)
 production.append(dict(kind=image['kind'],image_id=image['image_id'],files=len(actual),passed=actual==expected,expected=expected,actual=actual))
result={'input_variants':rows,'output_variants':output,'archives':archives,'production_sources':production}
(OUT/'variant-source-evidence.json').write_text(json.dumps(result,indent=2)+'\n')
print([(r['name'],r['expected_valid'],r['actual_valid']) for r in rows if not r['passed']]);print([(r['name'],r['manifest_equal']) for r in archives]);print([(r['kind'],r['files'],r['passed']) for r in production])
