"""Audit all actual selected states and outputs against the public contract."""
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem, load_result
from caeoj.case_grading import grade_case, prepare_case

TASK=Path(__file__).resolve().parents[1]


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    spec=importlib.util.spec_from_file_location('ecm_declarations',TASK/'extension/caeoj_task_ext/inventory.py')
    checker=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    report={'status':'passed','records':[],'materials_sha256':{},'invalid_variants':{}}
    for path in [TASK/'instruction.md',TASK/'DATA.md',TASK.parents[3]/'docs/CONTRACT.md']:
        report['materials_sha256'][path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
    inputs=[(p,TASK/'reference'/p.parent.name,False) for p in sorted((TASK/'cases').glob('*/problem.json'))]
    inputs += [(p,p.parent.parent/'reference',True) for p in sorted((TASK/'samples').glob('*/input/problem.json'))]
    for path,reference,public in inputs:
        problem=load_problem(path)
        errors=[]
        checker.check(problem,errors)
        if errors:raise ValueError((str(path),errors))
        outputs=load_result(problem,reference/'reference.h5')
        bound=prepare_case(problem,reference/'grading.json')
        if grade_case(path,reference/'reference.h5',reference/'grading.json')['score']!=1:
            raise ValueError('Bound reference did not pass: '+str(path))
        if public:
            output=path.parent.parent/'output/result.h5'
            load_result(problem,output)
            if grade_case(path,output,reference/'grading.json')['score']!=1:raise ValueError('Public output failed')
        p=problem.manifest['physics']['parameters']
        report['records'].append({'path':path.relative_to(TASK).as_posix(),'public_sample':public,
            'grid_counts':{k:v['value'] for k,v in p.items()},
            'state_count':len(problem.arrays['state_ids']),
            'fields':{name:{'shape':list(problem.arrays[field['array']].shape),'dtype':str(problem.arrays[field['array']].dtype),'unit':field['unit']}
                      for name,field in problem.manifest['fields'].items()},
            'outputs':{name:{'shape':list(outputs[field['array']].shape),'unit':field['unit']}
                       for name,field in problem.manifest['outputs'].items()},
            'evaluation_sha256':bound.evidence['evaluation_sha256']})
    first=load_problem(next((TASK/'cases').glob('01-*/problem.json')))
    mutations={
        'wrong_concentration_unit':lambda p:p.manifest['fields']['concentration_n'].__setitem__('unit','mol'),
        'negative_concentration':lambda p:p.arrays['concentration_n'].__setitem__((0,0,0),-1),
        'concentration_above_maximum':lambda p:p.arrays['concentration_p'].__setitem__((0,0,0),1e7),
        'zero_volume_fraction':lambda p:p.arrays['epsilon_n'].__setitem__((0,0,0),0),
        'invalid_thickness':lambda p:p.arrays['thickness_p'].__setitem__((0,0,0),0),
        'invalid_area':lambda p:p.arrays['area'].__setitem__((0,0,0),100),
        'missing_output':lambda p:p.manifest['outputs'].pop('total_inventory'),
        'invalid_count':lambda p:p.manifest['physics']['parameters']['r_count_p'].__setitem__('value',2)}
    for name,mutate in mutations.items():
        problem=deepcopy(first)
        mutate(problem)
        errors=[]
        checker.check(problem,errors)
        if not errors:raise ValueError('Forbidden DATA variant accepted: '+name)
        report['invalid_variants'][name]={'rejected':True,'diagnostics':len(errors)}
    report['coverage']={'actual_inputs':len(inputs),'test_cases':sum(not p for _,_,p in inputs),
                        'public_samples':sum(p for _,_,p in inputs),'grid_counts':{k:sorted({r['grid_counts'][k] for r in report['records']}) for k in ['x_count_n','x_count_p','r_count_n','r_count_p']},'finite_values_checked':'all arrays via generic input/output loaders',
                        'numerical_reference':'separately certified by actual PyBaMM replay and independent algebra; this audit does not substitute for that evidence'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report['coverage']))
