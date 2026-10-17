"""Public constant reference offsets: analytical decisions and extreme scales."""
from copy import deepcopy
from decimal import Decimal, localcontext
from pathlib import Path
import unittest

import numpy as np

from caeoj.grading import grade_arrays
from caeoj.grading_policy import parse_policy, render_policy, validate_policy
from caeoj.sdk import load_problem
from caeoj.validation import output_support

from task_fixtures import task_fixture
SMOKE=task_fixture('smoke-test')


class ReferenceOffsetTests(unittest.TestCase):
    def setUp(self):
        self.problem=load_problem(SMOKE/'cases/09-vector-2d/problem.json')
        keys=output_support(self.problem)|{s['array'] for s in self.problem.manifest['outputs'].values()}
        self.reference={k:self.problem.arrays[k].copy() for k in keys}
        self.actual=deepcopy(self.reference)

    def leaf(self,metric='pointwise',**kw):
        leaf=dict(metric=metric,time='per_time',components='joint',atol=.5,rtol=.1,reference_offset=100000.)
        if metric!='pointwise':leaf['limit']=0. if metric=='violation_fraction' else 1.
        leaf.update(kw);return leaf

    def policy(self,tree):return {'version':1,'fields':{'velocity':tree}}

    def grade(self,tree):return grade_arrays(self.problem,self.actual,self.reference,policy=self.policy(tree))

    def set_values(self,a,b):self.actual['velocity'][:]=a;self.reference['velocity'][:]=b

    def test_background_does_not_mask_error_all_three_metrics(self):
        # Reference fluctuation 10 Pa permits .5+.1*10=1.5 Pa, below 2 Pa error.
        self.set_values(100012.,100010.)
        for metric in ('pointwise','violation_fraction','max_scaled'):
            leaf=self.leaf(metric)
            with self.subTest(metric=metric):
                report=self.grade(leaf);self.assertEqual(report['score'],0)
                if metric=='max_scaled':self.assertAlmostEqual(report['fields']['velocity']['groups'][0]['value'],4/3)
                leaf.pop('reference_offset');self.assertEqual(self.grade(leaf)['score'],1)
        self.set_values(100011.5,100010.)
        for metric in ('pointwise','violation_fraction','max_scaled'):self.assertEqual(self.grade(self.leaf(metric))['score'],1)

    def test_cache_distinguishes_offsets_in_same_tree(self):
        self.set_values(100012.,100010.)
        tree={'all':[self.leaf(),self.leaf(reference_offset=0)]}
        r=self.grade(tree)['fields']['velocity']
        self.assertFalse(r['children'][0]['passed']);self.assertTrue(r['children'][1]['passed'])
        self.assertEqual(self.grade({'any':list(reversed(tree['all']))})['score'],1)

    def test_zero_default_old_behavior_and_signed_offset(self):
        for metric in ('pointwise','violation_fraction','max_scaled'):
            self.set_values(10.,11.)
            leaf=self.leaf(metric);leaf.pop('reference_offset')
            before=self.grade(leaf)['fields']['velocity']
            after=self.grade(dict(leaf,reference_offset=0))['fields']['velocity']
            self.assertEqual(before['groups'],after['groups']);self.assertEqual(before['passed'],after['passed'])
        self.set_values(-100012.,-100010.)
        self.assertEqual(self.grade(self.leaf(reference_offset=-100000.))['score'],0)

    def test_zero_tolerance_and_exact_error_without_double_subtraction(self):
        self.set_values(100000.,100000.)
        self.assertEqual(self.grade(self.leaf(atol=0))['score'],1)
        self.actual['velocity'][:]=100001.
        self.assertEqual(self.grade(self.leaf(atol=0))['score'],0)
        # Subtracting a giant offset from a and b first would collapse both to -1e100.
        self.set_values(2.,1.)
        self.assertEqual(self.grade(self.leaf(atol=0,rtol=0,reference_offset=1e100))['score'],0)

    def test_overflowing_difference_reference_scale_and_tolerance_product(self):
        cases=[(1.1e308,1e308,-1e308,0.,.03),
               (1.01e308,1e308,-1e308,0.,.03),
               (1e308,-1e308,1e308,0.,2.),
               (1e308,0.,-1e308,0.,1e-308),
               (1.,0.,-1e308,0.,1e-308),
               (1e308,0.,-1e308,0.,1e308),
               (1e-300,0.,-1e-308,0.,1e-300)]
        for a,b,offset,atol,rtol in cases:
            self.set_values(a,b)
            with localcontext() as ctx:
                ctx.prec=100
                da,db,do,dt,dr=map(Decimal.from_float,(a,b,offset,atol,rtol))
                expected=abs(da-db)/(dt+dr*abs(db-do))
            leaf=self.leaf('max_scaled',atol=atol,rtol=rtol,reference_offset=offset,limit=1)
            report=self.grade(leaf);value=report['fields']['velocity']['groups'][0]['value']
            with self.subTest(case=(a,b,offset,rtol)):
                self.assertEqual(report['score'],int(expected<=1))
                if expected>Decimal.from_float(np.finfo(float).max):self.assertEqual(value,'overflow')
                else:self.assertAlmostEqual(value/float(expected),1.,places=13)

    def test_schema_finiteness_allowed_metrics_and_renderer(self):
        for value in (True,'100000',{'field':'pressure_reference'},float('inf'),float('nan')):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):validate_policy(self.policy(self.leaf(reference_offset=value)))
        for metric in ('rmse','max_abs','nrmse'):
            leaf=dict(metric=metric,time='per_time',components='joint',limit=1,reference_offset=1)
            if metric=='nrmse':leaf['scale_floor']=1
            with self.assertRaises(ValueError):validate_policy(self.policy(leaf))
        with self.assertRaises(ValueError):validate_policy(self.policy({'all':[self.leaf()], 'reference_offset':1}))
        with self.assertRaises(ValueError):parse_policy('{"version":1,"fields":{"velocity":{"metric":"pointwise","time":"pooled","components":"joint","atol":1,"rtol":0,"reference_offset":1e400}}}')
        text=render_policy(self.policy(self.leaf('max_scaled')))
        self.assertIn('|参考−(100000.0)|',text)
        self.assertIn('默认0',text)


if __name__=='__main__':unittest.main()
