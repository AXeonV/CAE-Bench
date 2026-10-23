"""Core SDK plus explicit task extension, tolerances and malformed-input audit."""
import copy
import importlib.util
import json
import tempfile
from pathlib import Path

from caeoj.sdk import load_problem, load_result
from caeoj.storage import write_hdf5
from caeoj.case_grading import grade_case

TASK=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('task_contract',TASK/'extension/caeoj_task_ext/grand_potential.py')
CONTRACT=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTRACT)


def checked_problem(path):
    problem=load_problem(path);errors=[];CONTRACT.check(problem,errors)
    if errors:raise ValueError(errors)
    return problem


def main():
    report={'cases':[],'samples':[],'negative_variants':[]}
    for path in sorted((TASK/'cases').glob('*/problem.json')):
        problem=checked_problem(path);reference=TASK/'reference'/path.parent.name
        result=load_result(problem,reference/'reference.h5')
        grade=grade_case(path,reference/'reference.h5',reference/'grading.json')
        assert grade['score']==1
        p=problem.manifest['physics']['parameters']
        report['cases'].append({'case':path.parent.name,'programs':len(problem.arrays['program_ids']),
                                'active_grains':p['grain_count']['value'],'variable_name_set':p['variable_name_set']['value'],
                                'strict':p['strict_mass_conservation']['value'],'outputs':len(problem.manifest['outputs']),
                                'score':grade['score']})
    for path in sorted((TASK/'samples').glob('*/input/problem.json')):
        directory=path.parent.parent
        grade=grade_case(path,directory/'output/result.h5',directory/'reference/grading.json')
        assert grade['score']==1
        report['samples'].append({'sample':directory.name,'score':grade['score']})
    original=load_problem(TASK/'cases/01-coupled-polynomial-public/problem.json')
    def reject(name,mutation):
        m=copy.deepcopy(original.manifest);a={k:v.copy() for k,v in original.arrays.items()};mutation(m,a)
        # The extension is part of the public toolkit's explicit runtime; preserve
        # its lookup context when producing temporary malformed declarations.
        with tempfile.TemporaryDirectory(dir=TASK/'cases') as tmp:
            directory=Path(tmp);(directory/'problem.json').write_text(json.dumps(m));write_hdf5(directory/'input.h5',a)
            try:checked_problem(directory/'problem.json')
            except (ValueError,RuntimeError) as exc:
                report['negative_variants'].append({'name':name,'rejected':True,'exception':type(exc).__name__});return
            raise AssertionError('Accepted malformed declaration: '+name)
    reject('chemical_potential_wrong_unit',lambda m,a:m['fields']['potential'].__setitem__('unit','eV'))
    reject('excess_phi',lambda m,a:a['phi'].__setitem__((0,0,0),1.2))
    reject('inactive_grain_not_zero',lambda m,a:a['eta'].__setitem__((0,0,3),.2))
    reject('nonpositive_program_identity',lambda m,a:a['program_ids'].__setitem__(0,0))
    reject('fraction_out_of_range',lambda m,a:a['concentration'].__setitem__((0,0,0),1.01))
    reject('unbounded_potential',lambda m,a:a['potential'].__setitem__((0,0,0),1.0))
    reject('inactive_polynomial_cross_term',lambda m,a:m['physics']['parameters']['equilibrium_hessian_03'].__setitem__('value',.1))
    (TASK/'author/data-evidence/data-audit.json').write_text(json.dumps(report,indent=2)+'\n',newline='\n')
    print(json.dumps({'cases':len(report['cases']),'samples':len(report['samples']),'negative_variants':len(report['negative_variants'])}))


if __name__=='__main__':main()
