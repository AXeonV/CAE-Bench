"""Independent synthetic checks; no solver, download, or formal data mutation."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'qbank/extensions')]
from caeoj.case_grading import direct_config, prepare_case
from caeoj.grading_metrics import evaluate_observation
from caeoj.sdk import load_problem
from caeoj.storage import write_hdf5
from caeoj.validation import output_support
from caeoj_tools.author import load_author_module

records = []
def check(name, condition, details=None):
    if not condition: raise AssertionError((name, details))
    records.append({'check': name, 'status': 'passed', 'details': details})

with tempfile.TemporaryDirectory(prefix='caeoj-independent-continuous-') as tmp:
    root=Path(tmp)
    load_author_module('smoke-test','examples').make_cases(root/'cases')
    problem=load_problem(root/'cases/09-vector-2d/problem.json')
    expected={k: problem.arrays[k].copy() for k in output_support(problem)}
    for spec in problem.manifest['outputs'].values():
        expected[spec['array']]=np.ones((1,len(expected[problem.manifest['locations'][spec['location']]['ids']]),len(spec['components'])),dtype='float64')
    write_hdf5(root/'reference.h5',expected)
    rule={'metric':'nrmse','time':'per_time','components':'per_component','scale_floor':1.,'limit':.05}
    config=direct_config({'version':2,'default':rule})
    config['scoring']={'metric':'max_nrmse','full_credit':.05,'zero_credit':.10}
    grading=root/'grading.json'
    def prepare(cfg=config):
        grading.write_text(json.dumps(cfg))
        return prepare_case(problem,grading)
    for error,score in [(0.,1),(.04,1),(.05,1),(.075,.5),(.10,0),(.11,0)]:
        prepared=prepare()
        actual=copy.deepcopy(expected);actual['velocity'][:,:,0]+=error
        got=prepared.evaluate(actual)
        check('curve_'+str(error),math.isclose(got['score'],score,abs_tol=5e-14),got['score'])
    actual=copy.deepcopy(expected);actual['velocity'][:,:,0]+=.06;actual['velocity'][:,:,1]+=.09
    got=prepare().evaluate(actual)
    check('max_component_not_average',math.isclose(got['score'],.2,abs_tol=5e-14),got['score'])
    # Execute the trusted normalization evaluator against a synthetic weighted
    # fixture. Registry dispatch alone is patched; its math and case aggregator
    # are real, and no numerical values are supplied by a mocked evaluator.
    p=copy.deepcopy(problem)
    n=expected['velocity'].shape[1]
    p.arrays['weights']=np.ones((1,n,1),dtype='float64')
    p.manifest['fields']['weights']={**p.manifest['fields']['velocity'],'array':'weights','quantity':'dimensionless','unit':'1','kind':'scalar','component_shape':[],'components':['scalar']}
    p.path.write_text(json.dumps(p.manifest))
    write_hdf5(p.path.parent/p.manifest['data_file'],p.arrays)
    spec=importlib.util.spec_from_file_location('independent_normalized',ROOT/'qbank/extensions/caeoj_ext/normalized_fields.py')
    normalized=importlib.util.module_from_spec(spec);spec.loader.exec_module(normalized)
    cfg=copy.deepcopy(config)
    cfg['checks'][0].update(evaluator='field.normalized_outputs',weight_field='weights',transforms={'velocity':{'offset':-1e308,'remove_mean':False}})
    grading.write_text(json.dumps(cfg))
    with patch('caeoj.case_grading._evaluators',return_value={'field.normalized_outputs':normalized.prepare}):
        prepared=prepare_case(p,grading)
    actual=copy.deepcopy(expected);actual['velocity'][:]=1e308
    got=prepared.evaluate(actual)
    check('normalized_candidate_overflow_zero',got['score']==0 and got['status']=='wrong_answer',got['checks']['outputs']['fields']['velocity'])
    # Restore the unmodified input before subsequent direct checks.
    problem.path.write_text(json.dumps(problem.manifest))
    write_hdf5(problem.path.parent/problem.manifest['data_file'],problem.arrays)
    for mode in ['missing','nan','wrong_dtype','wrong_id']:
        actual=copy.deepcopy(expected)
        if mode=='missing': del actual['velocity']
        elif mode=='nan': actual['velocity'][0,0,0]=float('nan')
        elif mode=='wrong_dtype': actual['velocity']=actual['velocity'].astype('float32')
        else:
            key=problem.manifest['locations'][problem.manifest['outputs']['velocity']['location']]['ids']
            actual[key][0]+=1000
        got=prepare().evaluate(actual)
        check('invalid_'+mode,got['score']==0 and got['status']=='invalid_output')
    for label,change in [('legacy_metric',{'metric':'pointwise','atol':1.,'rtol':0}),('joint_components',{'components':'joint'}),('joint_time',{'time':'joint'}),('mismatched_limit',{'limit':.1})]:
        cfg=copy.deepcopy(config);cfg['checks'][0]['policy']['default'].update(change)
        try: prepare(cfg)
        except ValueError: check('reject_'+label,True)
        else: check('reject_'+label,False)
    cfg=copy.deepcopy(config);cfg['scoring']['zero_credit']=.05
    try: prepare(cfg)
    except ValueError: check('reject_equal_curve_endpoints',True)
    else: check('reject_equal_curve_endpoints',False)
    # Equal-time/component grouping is intentional: only the worst is consumed.
    b=np.full((2,2,2),4.);a=b.copy();a[0,:,0]+=.20;a[1,:,1]+=.36
    rec=evaluate_observation(a,b,rule,ids=np.array([3,7]),times=np.array([0.,1.]))
    check('time_component_groups',len(rec['groups'])==4)
    check('time_component_max',math.isclose(max(g['value'] for g in rec['groups']),.09,abs_tol=1e-14))
    # Nonuniform spatial weights must affect both RMS terms, not the max.
    weighted={**rule,'weight_field':'w'}
    b=np.ones((1,2,1));a=np.array([[[1.],[1.1]]])
    rec=evaluate_observation(a,b,weighted,ids=np.array([3,7]),times=np.array([0.]),weights={'w':np.array([3.,1.])})
    check('spatial_weight',math.isclose(rec['groups'][0]['value'],.05,abs_tol=1e-14))
    b=np.full((1,2,1),101.);a=b+.07
    rec=evaluate_observation(a,b,{**rule,'reference_offset':100.},ids=np.array([3,7]),times=np.array([0.]))
    check('offset_denominator_only',math.isclose(rec['groups'][0]['value'],.07,abs_tol=2e-14))
    b=np.zeros((1,2,1));a=b+.075
    rec=evaluate_observation(a,b,rule,ids=np.array([3,7]),times=np.array([0.]))
    check('zero_reference_floor',math.isclose(rec['groups'][0]['value'],.075,abs_tol=1e-14))
    spec=importlib.util.spec_from_file_location('independent_harbor',ROOT/'src/utils/harbor/tests/judge.py')
    harbor=importlib.util.module_from_spec(spec);spec.loader.exec_module(harbor)
    harbor.LOGS=root
    got=harbor.save_report({'timeout_seconds':10},[{'score':1},{'score':.5},{'score':0}],4,{},[],complete=False)
    check('partial_reward_preserved',got['score']==1.5 and got['reward']==.375 and got['completed_cases']==3 and not got['complete'])
    got=harbor.save_report({'timeout_seconds':10},[{'score':1},{'score':.5},{'score':0}],3,{},[],complete=True)
    check('final_reward_preserved',got['reward']==.5 and (root/'reward.txt').read_text().strip()=='0.5')

output={'status':'passed','scope':'synthetic independent numerical and contract tests; no formal reference validation','checks':records}
(ROOT/'runs/continuous-scoring/independent-checks.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps({'status':'passed','checks':len(records)}))
