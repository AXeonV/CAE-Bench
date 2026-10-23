"""CFDCodeBench public declarations and actual per-case grading consumption.

Disposable asymmetric fixtures verify rules, never stand in for numerical cases.
"""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from caeoj.sdk import load_problem
from caeoj.storage import write_hdf5
from caeoj.case_grading import prepare_case, grade_case
from caeoj.validation import check_problem
from caeoj_ext.cfdcodebench import models
from caeoj_ext.normalized_fields import _transform

ROOT=Path(__file__).resolve().parents[1]
SECTION=ROOT/'qbank/02-fluid-mechanics/2.13-cfdcodebench'

def fixture(root,index):
    model,cfg=next((k,v) for k,v in models().items() if v['index']==index)
    d=cfg['domain'];n=1 if index==23 else 3
    loc=dict(kind='entities' if index==23 else 'points',ids='ids')
    data=dict(ids=np.array([11,20,71][:n],dtype='int64'),times=np.array([cfg['time']],dtype='float64'),weights=np.array([.25,2.,.5][:n],dtype='float64')[None,:,None])
    if index!=23:
        loc['coordinates']='xy'
        if index==19:xy=np.array([[1.,0.],[2.,.2],[.7,.1]])
        elif cfg['dimension']==1:xy=np.linspace(d[0],d[1],5)[1:4,None]
        else:xy=np.array([[d[0]+(d[1]-d[0])*f,d[2]+(d[3]-d[2])*g] for f,g in ((.2,.3),(.7,.4),(.6,.8))])
        data['xy']=xy
    def field(name,quantity):return dict(array=name,quantity=quantity,location='observations',time_axis='output',dtype='float64',kind='scalar',component_shape=[1],components=['value'],unit='1',value_kind='point')
    m=dict(task=cfg['task'],spatial_dimension=cfg['dimension'],data_file='input.h5',meshes={},geometries={},locations=dict(observations=loc),time_axes=dict(output='times'),fields=dict(weights=field('weights','observation_weight')),outputs={n:field(n,n) for n in cfg['fields']},conditions=[],physics=dict(model=model,parameters={}))
    root.mkdir(parents=True,exist_ok=True)
    (root/'problem.json').write_text(json.dumps(m),encoding='utf-8');write_hdf5(root/'input.h5',data)
    ref=dict(ids=data['ids'],times=data['times'])
    for name in cfg['fields']:
        origin=20 if index==15 else 1 if index==16 else 0
        ref[name]=(np.array([.3,-.2,.5][:n])+origin)[None,:,None]
    (root/'reference').mkdir()
    write_hdf5(root/'reference/reference.h5',ref)
    from caeoj_tools.grading_policy import author_case_grading
    grading=author_case_grading(SECTION/cfg['task'])
    (root/'reference/grading.json').write_text(json.dumps(grading))
    return m,data,ref,grading

class CFDCodeBenchTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def test_all_24_registered_contracts_and_real_self_grading(self):
        self.assertEqual(len(models()),24)
        for i in range(1,25):
            with self.subTest(index=i):
                path=self.root/str(i);m,data,ref,config=fixture(path,i)
                problem=load_problem(path/'problem.json')
                plan=prepare_case(problem,path/'reference/grading.json')
                self.assertEqual(plan.evaluate(ref)['score'],1)
                for name in m['outputs']:
                    bad={k:v.copy() for k,v in ref.items()}
                    bad[name][0,0,0]+=10
                    self.assertEqual(plan.evaluate(bad)['score'],0,name)

    def test_pressure_constant_gauge_only_temperature_fixed_origin(self):
        path=self.root/'pressure';m,data,ref,_=fixture(path,12)
        plan=prepare_case(load_problem(path/'problem.json'),path/'reference/grading.json')
        a={k:v.copy() for k,v in ref.items()};a['p']+=127
        self.assertEqual(plan.evaluate(a)['score'],1)
        a['p']=ref['p']*2
        self.assertEqual(plan.evaluate(a)['score'],0)
        path=self.root/'temperature';m,data,ref,_=fixture(path,15)
        plan=prepare_case(load_problem(path/'problem.json'),path/'reference/grading.json')
        a={k:v.copy() for k,v in ref.items()};a['T']+=.1
        # Absolute-Celsius scaling would let this pass; temperature-rise
        # scaling must reject it against the O(.3) reference variation.
        self.assertEqual(plan.evaluate(a)['score'],0)
        a['T']=ref['T']+273.15
        self.assertEqual(plan.evaluate(a)['score'],0)

    def test_nrmse_threshold_sides_and_bad_reference_classification(self):
        path=self.root/'threshold';m,data,ref,config=fixture(path,16)
        ref['T'][:]=2.;write_hdf5(path/'reference/reference.h5',ref)
        plan=prepare_case(load_problem(path/'problem.json'),path/'reference/grading.json')
        # Explicit continuous case configuration independently of author defaults.
        config['scoring']=dict(metric='max_nrmse',full_credit=.05,zero_credit=.10)
        for entry in config['checks'][0]['policy'].get('quantities',{}).values(): entry['rule']['limit']=.05
        for rule in config['checks'][0]['policy'].get('fields',{}).values(): rule['limit']=.05
        (path/'reference/grading.json').write_text(json.dumps(config))
        plan=prepare_case(load_problem(path/'problem.json'),path/'reference/grading.json')
        for shift,score in ((.04,1),(.07,.6),(.1,0)):
            actual={k:v.copy() for k,v in ref.items()};actual['T']+=shift
            self.assertAlmostEqual(plan.evaluate(actual)['score'],score)
        bad={k:v.copy() for k,v in ref.items()};bad['T'][0,0,0]=np.nan
        write_hdf5(path/'reference/reference.h5',bad);write_hdf5(path/'result.h5',ref)
        result=grade_case(path/'problem.json',path/'result.h5',path/'reference/grading.json')
        self.assertEqual(result['status'],'evaluation_error');self.assertIsNone(result['score'])

    def test_continuous_weighted_gauge_invariant_error_is_not_diluted(self):
        path=self.root/'continuous-gauge';m,data,ref,config=fixture(path,12)
        config['scoring']=dict(metric='max_nrmse',full_credit=.05,zero_credit=.10)
        for entry in config['checks'][0]['policy'].get('quantities',{}).values(): entry['rule']['limit']=.05
        for rule in config['checks'][0]['policy'].get('fields',{}).values(): rule['limit']=.05
        (path/'reference/grading.json').write_text(json.dumps(config))
        plan=prepare_case(load_problem(path/'problem.json'),path/'reference/grading.json')
        actual={k:v.copy() for k,v in ref.items()}
        actual['p']=ref['p']*1.07+127.
        report=plan.evaluate(actual)
        self.assertAlmostEqual(report['total_nrmse'],.07,places=11)
        self.assertAlmostEqual(report['score'],.6,places=10)
        self.assertEqual(report['status'],'partial_credit')

    def test_max_finite_pressure_gauge_has_no_rounding_overflow(self):
        w=np.random.default_rng(34).uniform(.1,1,100)
        v=np.full((1,100,1),np.finfo(float).max)
        centered=_transform(v,dict(offset=0,remove_mean=True),w)
        self.assertTrue(np.all(centered==0))
        self.assertTrue(np.all(np.isfinite(centered)))

    def test_declared_geometry_units_ids_time_and_extra_fields_are_enforced(self):
        path=self.root/'input';m,data,ref,_=fixture(path,12)
        for change in ('model','task','unit','coordinate','weights','ids','times','extra'):
            with self.subTest(change=change):
                candidate=deepcopy(m);arrays={k:v.copy() for k,v in data.items()}
                if change=='model':candidate['physics']['model']='cfdcodebench-c18-v1'
                elif change=='task':candidate['task']='cc-1d-diffusion'
                elif change=='unit':candidate['outputs']['p']['unit']='Pa'
                elif change=='coordinate':arrays['xy'][0,0]=3
                elif change=='weights':arrays['weights'][0,0,0]=0
                elif change=='ids':arrays['ids'][0]=arrays['ids'][1]
                elif change=='times':arrays['times'][0]+=.1
                elif change=='extra':candidate['outputs']['s']=dict(candidate['outputs']['p'])
                (path/'problem.json').write_text(json.dumps(candidate));write_hdf5(path/'input.h5',arrays)
                self.assertFalse(check_problem(path/'problem.json')[1]['valid'])

    def test_pressure_transform_overflow_is_candidate_failure_not_infrastructure(self):
        path=self.root/'overflow';m,data,ref,config=fixture(path,16)
        config['scoring']=dict(metric='max_nrmse',full_credit=.05,zero_credit=.10)
        for entry in config['checks'][0]['policy'].get('quantities',{}).values(): entry['rule']['limit']=.05
        for rule in config['checks'][0]['policy'].get('fields',{}).values(): rule['limit']=.05
        config['checks'][0]['transforms']['T']['offset']=np.finfo(float).max
        # Reference remains representable, but candidate subtraction cannot.
        (path/'reference/grading.json').write_text(json.dumps(config))
        ref['T'][:]=np.finfo(float).max;write_hdf5(path/'reference/reference.h5',ref)
        plan=prepare_case(load_problem(path/'problem.json'),path/'reference/grading.json')
        actual={k:v.copy() for k,v in ref.items()};actual['T'][:]=-np.finfo(float).max
        result=plan.evaluate(actual);self.assertEqual(result['score'],0)
        self.assertEqual(result['checks']['fields']['fields']['T']['reason'],'normalization_overflow')

if __name__=='__main__':unittest.main()
