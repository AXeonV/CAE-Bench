from pathlib import Path
import hashlib,importlib.util,json
from caeoj.sdk import load_problem,load_result
from caeoj.case_grading import grade_case
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent;TASK=ROOT/'qbank/19-solver-repair/19.6-waves/complex-helmholtz-fmm-repair';DATA=ROOT/'work/repair-22/bempp-20/dataset-v2'
sp=importlib.util.spec_from_file_location('decl',TASK/'extension/caeoj_task_ext/helmholtz.py');ext=importlib.util.module_from_spec(sp);sp.loader.exec_module(ext)
paths=[TASK/'instruction.md',TASK/'DATA.md',ROOT/'docs/CONTRACT.md',TASK/'extension/caeoj_task_ext/helmholtz.py']
e={'sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'cases':[]}
scope=[(p,p.parent.name,DATA/'reference'/p.parent.name) for p in sorted((DATA/'cases').glob('*/problem.json'))]+[(p,'sample-'+p.parents[1].name,p.parents[1]/'reference') for p in sorted((TASK/'samples').glob('*/input/problem.json'))]
for path,name,ref in scope:
 p=load_problem(path);errors=[];ext.check(p,errors);r=load_result(p,ref/'reference.h5');grade=grade_case(path,ref/'reference.h5',ref/'grading.json');e['cases'].append({'case':name,'extension_errors':errors,'grade_status':grade['status'],'score':grade['score']})
p=load_problem(OUT/'filename-variant/problem.json');err=[];ext.check(p,err);e['other_filename_rejected']=bool(err) and err[0]['code']=='E_HELMHOLTZ' and err[0]['path']=='$.data_file';e['other_filename_errors']=err
e['passed']=all(not x['extension_errors'] and x['grade_status']=='accepted' for x in e['cases']) and e['other_filename_rejected']
(OUT/'final-evidence.json').write_text(json.dumps(e,indent=2)+'\n');print(json.dumps(e,indent=2))
