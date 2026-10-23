"""Bind existing genuine raw runs to final metadata; never regenerate references."""
import argparse,hashlib,importlib.util,json,shutil,tempfile
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem,load_result
from caeoj.case_grading import grade_case
from caeoj_tools.grading_policy import author_policy,write_direct_grading
TASK=Path(__file__).resolve().parents[1]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--dataset',type=Path,required=True);a=p.parse_args()
    adapter=module('wave_adapter',TASK/'public/run_case.py');contract=module('wave_contract',TASK/'extension/caeoj_task_ext/parallel_wave.py')
    policy=author_policy(TASK);checks=[];raw_rows=json.loads((a.dataset/'reference-replay.json').read_text());old={r['case']:r for r in raw_rows}
    for path in sorted((a.dataset/'cases').glob('*/problem.json')):
        problem=load_problem(path);errors=[];contract.check(problem,errors)
        if errors:raise ValueError(errors)
        raw=a.dataset/'replay/reference'/path.parent.name
        with tempfile.TemporaryDirectory() as tmp:
            adapter.prepare(problem,tmp)
            files={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (Path(tmp)/'DATA').iterdir()}
            if files!={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (raw/'DATA').iterdir()}:raise ValueError('Final metadata serializes different physical inputs: '+path.parent.name)
        reference=a.dataset/'reference'/path.parent.name;result=load_result(problem,reference/'reference.h5')
        if hashlib.sha256((reference/'reference.h5').read_bytes()).hexdigest()!=old[path.parent.name]['output_sha256']:raise ValueError('Existing genuine reference changed')
        write_direct_grading(reference,policy);grade=grade_case(path,reference/'reference.h5',reference/'grading.json')
        if grade['score']!=1:raise ValueError(grade)
        row={'case':path.parent.name,'old_native_run_manifest_sha256':old[path.parent.name]['input_sha256'],
             'current_input_assets':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in path.parent.iterdir() if f.is_file()},
             'native_DATA_exactly_unchanged':True,'native_DATA_sha256':files,'reference_sha256':old[path.parent.name]['output_sha256'],
             'self_score':grade['score'],'metadata_change':'branch now selected by physics.model rather than numeric parameter; source/mesh/time/fields and native input byte-for-byte unchanged'}
        original=a.dataset/'replay/original'/path.parent.name/'result.h5'
        if original.is_file():
            delta=np.max(np.abs(load_result(problem,original)['wave_response']-result['wave_response']));row['original_completed_max_absolute_difference']=float(delta)
        checks.append(row)
    for number,case in [('01','01-connected-sh'),('02','04-isolated-master-pml')]:
        sample=a.dataset/'samples'/number;shutil.copytree(a.dataset/'cases'/case,sample/'input',dirs_exist_ok=True)
        shutil.copytree(a.dataset/'reference'/case,sample/'reference',dirs_exist_ok=True)
        (sample/'output').mkdir(parents=True,exist_ok=True);shutil.copyfile(sample/'reference/reference.h5',sample/'output/result.h5')
    evidence=TASK/'author/data-evidence'
    (evidence/'final-input-binding.json').write_text(json.dumps(checks,indent=2))
    for source in ['reference-replay.json','original-replay.json','independent-report.json','catalog.json']:
        shutil.copyfile(a.dataset/source,evidence/source)
    print('Final metadata matches all genuine native inputs; eight references retained, graded and sampled.')
