from pathlib import Path
import hashlib,json,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent;TASK=ROOT/'qbank/19-solver-repair/19.6-waves/complex-helmholtz-fmm-repair';DATA=ROOT/'work/repair-22/bempp-20/dataset-v2';archive=ROOT/'dist/complex-helmholtz-fmm-repair-agent.zip'
with zipfile.ZipFile(archive) as z:
 names=z.namelist();hashes={n:hashlib.sha256(z.read(n)).hexdigest() for n in names}
 exact={n:hashes[n]==hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names if n.startswith('qbank/') or n=='docs/CONTRACT.md'}
 exact['src/caeoj_task_ext/helmholtz.py']=hashes['src/caeoj_task_ext/helmholtz.py']==hashlib.sha256((TASK/'extension/caeoj_task_ext/helmholtz.py').read_bytes()).hexdigest()
 dest=OUT/'final-package';z.extractall(dest)
scope=[(str(p),str(DATA/'reference'/p.parent.name)) for p in sorted((DATA/'cases').glob('*/problem.json'))]+[(str(p),str(p.parents[1]/'reference')) for p in sorted((TASK/'samples').glob('*/input/problem.json'))]
code='''import sys,json
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from caeoj.sdk import load_problem,load_result
from caeoj.case_grading import grade_case
from caeoj.validation import validate_input
from caeoj import runtime
scope=json.loads(sys.argv[2]);rows=[]
for path,ref in scope:
 p=load_problem(path);load_result(p,Path(ref)/'reference.h5');g=grade_case(path,Path(ref)/'reference.h5',Path(ref)/'grading.json');rows.append({'path':path,'status':g['status'],'binding_sha256':g['runtime_binding_sha256']})
variants=[]
old=json.loads(Path(sys.argv[3]).read_text())
for v in old:
 p=Path(sys.argv[3]).parent/'variants'/v['name']/'problem.json';diag=validate_input(p);variants.append({'name':v['name'],'expected_valid':v['expected_valid'],'valid':diag['valid'],'passed':diag['valid']==v['expected_valid'],'errors':diag['errors']})
print(json.dumps({'cases':rows,'variants':variants,'runtime':runtime.descriptor()}))
'''
run=subprocess.run([sys.executable,'-I','-c',code,str(dest/'src'),json.dumps(scope),str(OUT/'full-variant-evidence.json')],text=True,capture_output=True,timeout=60)
assert run.returncode==0,run.stderr
result={'zip':str(archive),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'member_count':len(names),'member_sha256':hashes,'exact_public_material_matches':exact,'package_checks':json.loads(run.stdout)}
(OUT/'final-zip-evidence.json').write_text(json.dumps(result,indent=2)+'\n');print(result['sha256'],result['member_count'],all(exact.values()));print([(x['path'],x['status']) for x in result['package_checks']['cases']]);print('variant failures',[x['name'] for x in result['package_checks']['variants'] if not x['passed']])
