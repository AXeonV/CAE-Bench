"""Analytical metric fixtures, logical quantifiers and publication contracts."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np

from caeoj.grading import grade_arrays, grade_files
from caeoj.grading_policy import load_policy, policy_hash, render_policy, validate_policy
from caeoj.sdk import load_problem
from caeoj.validation import output_support

ROOT = Path(__file__).resolve().parents[1]


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.problem = load_problem(ROOT / 'tasks/echo-field/cases/09-vector-2d/problem.json')
        p = self.problem
        self.reference = {key: p.arrays[key].copy() for key in output_support(p) | {s['array'] for s in p.manifest['outputs'].values()}}
        self.reference['velocity'][:] = 0
        self.actual = deepcopy(self.reference)

    def leaf(self, metric='rmse', **kw):
        d = dict(metric=metric, time='per_time', components='per_component')
        if metric in ('pointwise', 'max_scaled', 'violation_fraction'):
            d.update(atol=.1, rtol=0)
        if metric != 'pointwise':
            d['limit'] = .1
        if metric == 'nrmse':
            d['scale_floor'] = 1
        d.update(kw)
        return d

    def policy(self, tree):
        return {'version': 1, 'fields': {'velocity': tree}}

    def grade(self, tree):
        return grade_arrays(self.problem, self.actual, self.reference, policy=self.policy(tree))

    def test_rmse_known_value_and_equality(self):
        self.actual['velocity'][:] = .1
        self.assertEqual(self.grade(self.leaf())['score'], 1)
        self.assertEqual(self.grade(self.leaf(limit=.099))['score'], 0)
        self.actual['velocity'][:] = 0
        self.actual['velocity'][:, 0, :] = .2
        n = self.actual['velocity'].shape[1]
        report = self.grade(self.leaf(limit=1))
        self.assertAlmostEqual(report['fields']['velocity']['groups'][0]['value'], .2/np.sqrt(n))

    def test_all_any_and_fraction(self):
        self.actual['velocity'][:, 0, 0] = .09
        n = self.actual['velocity'].shape[1]
        a = self.leaf('pointwise')
        b = self.leaf('violation_fraction', atol=.01, limit=1/n)
        tree = {'all': [a, b]}
        self.assertEqual(self.grade(tree)['score'], 1)
        b['limit'] = 0
        self.assertEqual(self.grade(tree)['score'], 0)
        self.assertEqual(self.grade({'any': [b, a]})['score'], 1)
        self.assertEqual(len(self.grade({'any': [a,b]})['fields']['velocity']['children']), 2)

    def test_spatial_points_count_all_components(self):
        self.actual['velocity'][:, 0, 0] = .2
        n = self.actual['velocity'].shape[1]; c = self.actual['velocity'].shape[2]
        scalar = self.leaf('violation_fraction', components='joint', limit=1/(n*c))
        self.assertEqual(self.grade(scalar)['score'], 1)
        points = dict(scalar, count='spatial_points')
        self.assertEqual(self.grade(points)['score'], 0)
        points['limit'] = 1/n
        self.assertEqual(self.grade(points)['score'], 1)
        with self.assertRaises(ValueError): self.grade(dict(points, components='per_component'))

    def test_time_quantifier_is_outside_or(self):
        # A passes only first time, B only second: neither leaf passes all times.
        p = self.problem
        p.arrays['times'] = np.array([0., 1.])
        for d in [self.reference,self.actual]:
            d['times'] = p.arrays['times'].copy()
            d['velocity'] = np.repeat(d['velocity'][:1],2,axis=0)
        self.reference['velocity'][1] = 100
        self.actual['velocity'][0] = .05
        self.actual['velocity'][1] = 101
        a=self.leaf('pointwise',atol=.1)
        b=self.leaf('pointwise',atol=0,rtol=.02)
        self.assertEqual(self.grade({'any':[a,b]})['score'],0)

    def test_joint_and_per_component_differ(self):
        self.actual['velocity'][:,:,0] = .13
        self.assertEqual(self.grade(self.leaf())['score'],0)
        self.assertEqual(self.grade(self.leaf(components='joint'))['score'],1)

    def test_pooled_does_not_mean_time_integral(self):
        p=self.problem; p.arrays['times']=np.array([0.,1.,100.])
        for d in [self.reference,self.actual]:
            d['times']=p.arrays['times'].copy(); d['velocity']=np.repeat(d['velocity'][:1],3,axis=0)
        self.actual['velocity'][2] = .15
        self.assertEqual(self.grade(self.leaf())['score'],0)
        self.assertEqual(self.grade(self.leaf(time='pooled'))['score'],1)

    def test_nrmse_zero_reference_floor(self):
        self.actual['velocity'][:] = .1
        self.assertEqual(self.grade(self.leaf('nrmse',scale_floor=1,limit=.1))['score'],1)
        self.assertEqual(self.grade(self.leaf('nrmse',scale_floor=.1,limit=.1))['score'],0)
        self.reference['velocity'][:]=2;self.actual['velocity'][:]=2.2
        self.assertAlmostEqual(self.grade(self.leaf('nrmse',limit=1))['fields']['velocity']['groups'][0]['value'],.1)

    def test_maxima_and_zero_denominator(self):
        self.actual['velocity'][:,0,0] = .3
        self.assertEqual(self.grade(self.leaf('max_abs',limit=.3))['score'],1)
        self.assertEqual(self.grade(self.leaf('max_scaled',limit=2))['score'],0)
        r=self.grade(self.leaf('max_scaled',atol=0,limit=100))
        self.assertEqual(r['score'],0);self.assertEqual(r['fields']['velocity']['groups'][0]['value'],'overflow')
        self.actual['velocity'][:] = 0
        self.assertEqual(self.grade(self.leaf('max_scaled',atol=0,limit=0))['score'],1)

    def test_stable_extreme_rms_and_normalization(self):
        self.actual['velocity'][:]=1e200
        self.assertEqual(self.grade(self.leaf(limit=1e201))['score'],1)
        self.actual['velocity'][:]=1e308;self.reference['velocity'][:]=-1e308
        self.assertEqual(self.grade(self.leaf('nrmse',limit=2))['score'],1)
        r=self.grade(self.leaf(limit=1e308))
        self.assertEqual(r['score'],0);json.dumps(r,allow_nan=False)
        self.assertEqual(r['fields']['velocity']['groups'][0]['value'],'overflow')

    def test_weighted_rms_and_unweighted_proportion(self):
        p=self.problem;n=self.actual['velocity'].shape[1]
        p.manifest['fields']['weights']={'array':'weights','quantity':'weight','location':'domain','time_axis':'weight_time',
            'dtype':'float64','kind':'scalar','component_shape':[1],'components':['value'],'unit':'1','value_kind':'point'}
        # Use the actual output location, which is not necessarily named domain.
        p.manifest['fields']['weights']['location']=p.manifest['outputs']['velocity']['location']
        p.manifest['time_axes']['weight_time']='weight_times';p.arrays['weight_times']=np.array([0.])
        w=np.ones((1,n,1));w[0,0,0]=9;p.arrays['weights']=w
        self.actual['velocity'][:,0,0]=1
        r=self.grade(self.leaf(limit=10,weight_field='weights'))
        self.assertAlmostEqual(r['fields']['velocity']['groups'][0]['value'],np.sqrt(9/(n+8)))
        self.assertEqual(self.grade(self.leaf('violation_fraction',limit=1/n,weight_field='weights'))['score'],1)
        w[0,0,0]=0
        with self.assertRaises(ValueError): self.grade(self.leaf(weight_field='weights'))

    def test_structure_cannot_be_bypassed_by_or(self):
        self.actual['velocity'][0,0,0]=np.nan
        self.assertEqual(self.grade({'any':[self.leaf(limit=100),self.leaf('max_abs',limit=100)]})['status'],'invalid_output')
        self.actual=deepcopy(self.reference);self.actual['times'] += 1e-12
        self.assertEqual(self.grade(self.leaf(limit=100))['status'],'invalid_output')

    def test_configuration_rejects_ambiguity_and_unknown_fields(self):
        for tree in [{'any':[]},self.leaf(metric='unknown'),self.leaf(limit=-1),self.leaf(limit=np.inf),self.leaf(extra=True),self.leaf('nrmse',scale_floor=0)]:
            with self.subTest(tree=tree),self.assertRaises(ValueError):self.grade(tree)
        with self.assertRaises(ValueError):grade_arrays(self.problem,self.actual,self.reference,policy=self.policy(self.leaf()),atol=.1)
        with self.assertRaises(ValueError):validate_policy({'version':1,'fields':{}},self.problem)
        with self.assertRaises(ValueError):validate_policy({'version':True,'fields':{}})

    def test_worst_location_hash_render_and_no_mutation(self):
        self.actual['velocity'][:,0,0]=.3;before=deepcopy(self.actual)
        r=self.grade(self.leaf('max_abs',limit=.1));group=r['fields']['velocity']['groups'][0]
        loc=self.problem.manifest['locations'][self.problem.manifest['outputs']['velocity']['location']]
        self.assertEqual(group['worst_location']['id'],int(self.problem.arrays[loc['ids']][0]))
        self.assertEqual(r['policy_sha256'],policy_hash(self.policy(self.leaf('max_abs',limit=.1))))
        self.assertIn('空间点',render_policy(self.policy(self.leaf('violation_fraction',components='joint',count='spatial_points'))))
        for key in self.actual:np.testing.assert_array_equal(self.actual[key],before[key])

    def test_chunk_boundaries_and_small_error_with_large_reference(self):
        from unittest.mock import patch
        from caeoj import grading_metrics
        self.actual['velocity'][:,0,0] = .2
        tree=self.leaf(limit=1)
        normal=self.grade(tree)
        with patch.object(grading_metrics, 'CHUNK_SIZE', 2):
            chunked=self.grade(tree)
        self.assertEqual(normal,chunked)
        self.reference['velocity'][:]=1e200; self.actual['velocity'][:]=1e200
        self.reference['velocity'][:,0,0]=0;self.actual['velocity'][:,0,0]=1e-100
        value=self.grade(tree)['fields']['velocity']['groups'][0]['value']
        self.assertGreater(value,0)

    def test_integer_fields_and_reference_error_remain_mandatory(self):
        p=load_problem(ROOT/'tasks/echo-field/cases/08-scalars-and-dtypes/problem.json')
        keys=output_support(p)|{s['array'] for s in p.manifest['outputs'].values()}
        ref={k:p.arrays[k].copy() for k in keys}; actual=deepcopy(ref)
        policy={'version':1,'fields':{name:self.leaf(limit=1e6) for name,spec in p.manifest['outputs'].items() if spec['dtype']=='float64'}}
        actual['region_label'][0,0,0]+=1
        self.assertEqual(grade_arrays(p,actual,ref,policy=policy)['score'],0)
        ref['temperature']=ref['temperature'][0]
        self.assertIsNone(grade_arrays(p,actual,ref,policy=policy)['score'])

    def test_cli_policy_and_conflict(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'runs') as tmp:
            root=Path(tmp);np.savez(root/'result.npz',**self.actual);np.savez(root/'reference.npz',**self.reference)
            policy=root/'grading.json';policy.write_text(json.dumps(self.policy(self.leaf())))
            args=[sys.executable,'-m','caeoj','grade','--input',str(self.problem.path),'--output',str(root/'result.npz'),
                  '--reference',str(root/'reference.npz'),'--grading',str(policy)]
            r=subprocess.run(args,capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads(r.stdout)['score'],1)
            r=subprocess.run(args+['--atol','.1'],capture_output=True,text=True)
            self.assertEqual(r.returncode,2)
            policy.write_text('{"version":1,"version":1,"fields":{}}')
            with self.assertRaises(ValueError):load_policy(policy)


if __name__ == '__main__':unittest.main()
