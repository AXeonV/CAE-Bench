"""Audit every actual input/output, independently recompute geometry, and test contract variants."""
import argparse,copy,hashlib,importlib.util,json,shutil,tempfile
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem,load_result
from caeoj.storage import write_hdf5
from caeoj.validation import ContractError,write_json,read_mesh,resolve_file
from caeoj.case_grading import grade_case
from independent import evaluate
TASK=Path(__file__).resolve().parents[1]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=TASK/'author/data-evidence/data-audit.json');args=parser.parse_args()
    contract=module('projection_check',TASK/'extension/caeoj_task_ext/projection.py');adapter=module('projection_adapter',TASK/'public/run_case.py')
    report={'cases':[],'samples':[],'variants':[]}
    for kind,paths in [('cases',sorted((TASK/'cases').glob('*/problem.json'))),('samples',sorted((TASK/'samples').glob('*/input/problem.json')))]:
        for path in paths:
            problem=load_problem(path);errors=[];contract.check(problem,errors)
            if errors:raise ValueError(errors)
            reference=(TASK/'reference'/path.parent.name) if kind=='cases' else path.parent.parent/'reference'
            result=load_result(problem,reference/'reference.h5');exact=adapter.adapt(json.dumps(evaluate(json.loads(adapter.serialize(problem)))))
            checks={}
            for name,value in exact.items():
                actual=result[name];atol=1e-9 if name=='weights' else 1e-8
                error=np.abs(actual-value);ratio=error/(atol+1e-8*np.abs(value));assert np.all(ratio<=1),(path,name)
                checks[name]={'max_absolute_error':float(error.max()),'max_tolerance_fraction':float(ratio.max())}
            assert grade_case(path,reference/'reference.h5',reference/'grading.json')['score']==1
            if kind=='samples':
                output=path.parent.parent/'output/result.h5';load_result(problem,output);assert grade_case(path,output,reference/'grading.json')['score']==1
            mesh=read_mesh(resolve_file(path.parent,'source.msh','.msh'),geometry=True)
            report[kind].append({'path':path.relative_to(TASK).as_posix(),'nodes':len(mesh['nodes']),'queries':len(problem.arrays['probe_ids']),
              'types':sorted({kind for kind,nodes in mesh['connectivity'].values()}),'mode':problem.manifest['physics']['parameters']['mode']['value'],'checks':checks,
              'input_sha256':{name:hashlib.sha256((path.parent/name).read_bytes()).hexdigest() for name in ['problem.json','input.h5','source.msh']}})
    original=load_problem(next((TASK/'samples').glob('*/input/problem.json')))
    mutations=[('mode-nearest',True,lambda m,a:m['physics']['parameters']['mode'].update(value=0)),
      ('zero-node-values',True,lambda m,a:a['nodal_values'].fill(0)),
      ('probe-labels',True,lambda m,a:a.update(probe_ids=np.arange(len(a['probe_ids']),dtype='int64'))),
      ('bad-mode',False,lambda m,a:m['physics']['parameters']['mode'].update(value=2)),
      ('bool-mode',False,lambda m,a:m['physics']['parameters']['mode'].update(value=False)),
      ('bad-field-unit',False,lambda m,a:m['fields']['nodal_values'].update(unit='m')),
      ('bad-weight-label',False,lambda m,a:m['outputs']['weights']['components'].reverse()),
      ('extra-parameter',False,lambda m,a:m['physics']['parameters'].update(extra={'value':1,'unit':'1'})),
      ('missing-nodal-field',False,lambda m,a:m['fields'].pop('nodal_values')),
      ('query-outside-bound',False,lambda m,a:a['probe_coordinates'].__setitem__((0,0),201)),
      ('nodal-value-outside-bound',False,lambda m,a:a['nodal_values'].__setitem__((0,0,0),1001)),
      ('node-order',False,lambda m,a:a['node_ids'].sort() or a.update(node_ids=a['node_ids'][::-1])),
      ('wrong-output-unit',False,lambda m,a:m['outputs']['distance'].update(unit='1'))]
    with tempfile.TemporaryDirectory() as temp:
        directory=Path(temp);shutil.copyfile(original.path.parent/'source.msh',directory/'source.msh')
        for name,expected,mutate in mutations:
            manifest=copy.deepcopy(original.manifest);arrays={k:v.copy() for k,v in original.arrays.items()};mutate(manifest,arrays)
            write_json(directory/'problem.json',manifest);write_hdf5(directory/'input.h5',arrays)
            accepted=True
            try:
                problem=load_problem(directory/'problem.json');errors=[];contract.check(problem,errors);accepted=not errors
            except ContractError:accepted=False
            assert accepted==expected,(name,accepted,expected);report['variants'].append({'name':name,'expected_accept':expected,'accepted':accepted})
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'cases':len(report['cases']),'samples':len(report['samples']),'variants':len(report['variants']),'passed':True}))
