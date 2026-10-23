from pathlib import Path
import hashlib,importlib.util,json,shutil
import numpy as np
from caeoj.sdk import load_problem,load_result
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent;TASK=ROOT/'qbank/19-solver-repair/19.6-waves/complex-helmholtz-fmm-repair';DATA=ROOT/'work/repair-22/bempp-20/dataset-v2'
spec=importlib.util.spec_from_file_location('decl',TASK/'extension/caeoj_task_ext/helmholtz.py');ext=importlib.util.module_from_spec(spec);spec.loader.exec_module(ext)
rows=[]
for path in sorted((DATA/'cases').glob('*/problem.json')):
 p=load_problem(path);result=load_result(p,DATA/'reference'/path.parent.name/'reference.h5');raw=json.loads((DATA/'replay/reference'/path.parent.name/'stdout.json').read_text())
 rows.append({'case':path.parent.name,'all_output_values_match_raw_replay':all(np.array_equal(result[key][0],raw[key]) for key in p.manifest['outputs'])})
samples=[]
for name,case in [('01','02-point-complex'),('02','07-boundary-complex')]:
 samples.append({'sample':name,'case':case,'problem_identical':(TASK/'samples'/name/'input/problem.json').read_bytes()==(DATA/'cases'/case/'problem.json').read_bytes(),'input_identical':(TASK/'samples'/name/'input/input.h5').read_bytes()==(DATA/'cases'/case/'input.h5').read_bytes(),'reference_identical':(TASK/'samples'/name/'reference/reference.h5').read_bytes()==(DATA/'reference'/case/'reference.h5').read_bytes()})
worker=ROOT/'runs/authoring/repair-22/bempp-formal-boundary-audit/dense-weak-worker.py';driver=(TASK/'public/driver.py').read_text();expected=driver.replace("assembler='fmm'","assembler='dense'").replace('.strong_form()', '.weak_form()')
variant=OUT/'filename-variant';variant.mkdir(exist_ok=True);m=json.loads((DATA/'cases/01-point-real/problem.json').read_text());m['data_file']='other.h5';(variant/'problem.json').write_text(json.dumps(m));shutil.copyfile(DATA/'cases/01-point-real/input.h5',variant/'other.h5');p=load_problem(variant/'problem.json');err=[];ext.check(p,err)
supp={'replay':rows,'samples':samples,'dense_worker_only_changes_dense_and_weak':worker.read_text()==expected,'dense_worker_sha256':hashlib.sha256(worker.read_bytes()).hexdigest(),'actual_wrong_filename_variant':{'core_loads':True,'extension_errors':err},'uncompleted':['Native actual execution for all-zero density/strength and exact legal geometric/parameter extrema not rerun.','Fresh HF d4011e0522e1e9dcbc8f228624fe7b1c02063928 empty-cache assembly/selection hash verification is owned by coordinator.','Full bytecode resource enforcement and ongoing baseline native pipeline are not rerun by this audit.']}
(OUT/'replay-evidence.json').write_text(json.dumps(supp,indent=2)+'\n');print(json.dumps(supp,indent=2))
