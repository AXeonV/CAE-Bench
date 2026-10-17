"""Chapter-zero evaluation witnesses exercise actual case assets and semantics."""
from pathlib import Path
import tempfile
import unittest

import numpy as np

from caeoj.case_grading import grade_case
from caeoj.sdk import load_problem
from caeoj.storage import write_hdf5
from caeoj.validation import output_support, read_hdf5
from caeoj_tools.author import load_author_module
from caeoj_tools import data_pool as pool


class ChapterZeroGradingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary=tempfile.TemporaryDirectory()
        cls.root=Path(cls.temporary.name)
        cls.generator=load_author_module('case-grading-test','generate')
        cls.generator.generate(cls.root/'source')
        cls.source=cls.root/'source'

    @classmethod
    def tearDownClass(cls):cls.temporary.cleanup()

    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.output=Path(temporary.name)/'result.h5'

    def grade(self,name,change=None):
        path=self.source/'cases'/name/'problem.json'
        problem=load_problem(path)
        arrays={key:problem.arrays[key].copy() for key in output_support(problem)|{'velocity'}}
        if change:change(arrays)
        write_hdf5(self.output,arrays)
        return grade_case(path,self.output,self.source/'reference'/name/'grading.json')

    def test_all_cases_and_samples_have_complete_passing_submissions(self):
        for name,_ in self.generator.CASES:
            with self.subTest(case=name):self.assertEqual(self.grade(name)['score'],1)
        for name,_ in self.generator.SAMPLES:
            sample=self.source/'samples'/name
            self.assertEqual(grade_case(sample/'input/problem.json',sample/'output/result.h5',sample/'reference/grading.json')['score'],1)

    def test_sparse_reference_is_p1_not_the_bilinear_formula_between_nodes(self):
        path=self.source/'cases/02-x/problem.json'
        p=load_problem(path)
        ref=read_hdf5(self.source/'reference/02-x/probe-reference.h5')
        # Center of diagonal BL->TR: equal corner weights, not a bilinear center.
        expected=1.+2*.7+2*p.arrays['times']+1.5
        np.testing.assert_allclose(ref['x'][:,2,0],expected,atol=1e-14,rtol=0)

    def test_only_selected_component_is_compared_but_full_output_is_required(self):
        def y_changed(a):a['velocity'][:,:,1]+=100.
        self.assertEqual(self.grade('02-x',y_changed)['score'],1)
        self.assertEqual(self.grade('03-y',y_changed)['score'],0)
        self.assertEqual(self.grade('04-xy',y_changed)['score'],0)
        def missing_component(a):a['velocity']=a['velocity'][:,:,:1]
        self.assertEqual(self.grade('02-x',missing_component)['status'],'invalid_output')

    def test_split_checks_fail_in_both_directions(self):
        for component,failed,passed in [(0,'probes-x','probes-y'),(1,'probes-y','probes-x')]:
            def change(a):a['velocity'][:,:,component]+=.1
            result=self.grade('05-two-checks',change)
            self.assertEqual(result['score'],0)
            self.assertFalse(result['checks'][failed]['passed'])
            self.assertTrue(result['checks'][passed]['passed'])

    def test_full_check_catches_a_field_change_in_the_probe_nullspace(self):
        def change(a):
            # Node IDs are [BR,TL,BL,TR]; these x changes cancel on x=width/2.
            a['velocity'][:,:,0]+=np.array([-1.,1.,1.,-1.])*.1
        result=self.grade('06-full-and-probes',change)
        self.assertEqual(result['score'],0)
        self.assertFalse(result['checks']['outputs']['passed'])
        self.assertTrue(result['checks']['probes-x']['passed'])

    def test_node_rows_and_times_cannot_be_reordered(self):
        def wrong_rows(a):a['velocity']=a['velocity'][:,::-1,:]
        self.assertEqual(self.grade('04-xy',wrong_rows)['score'],0)
        def wrong_times(a):a['times']=a['times'][::-1]
        self.assertEqual(self.grade('02-x',wrong_times)['status'],'invalid_output')

    def test_pool_selection_is_disjoint_and_sparse_examples_are_separate(self):
        base=self.output.parent
        value={'schema_version':4,'task_id':'caeoj-000004',
               'repository':{'repo_id':'test/cases','repo_type':'dataset',
                             'path':'qbank/00-basic-tests/0.2-grading/case-grading-test'}}
        pool.pack(self.source,base/'bundle',value)
        selection,store,index=pool.validate_bundle(base/'bundle')
        self.assertEqual(len(index['cases']),8)
        result=pool.fetch(selection,store)
        self.assertFalse(result['overlaps'])
        self.assertFalse(result['incomplete'])
        sample=selection['samples']['02']
        item=pool.checked_json(store.get(value['repository']['path']+'/'+sample['case']['path']))
        self.assertEqual(item['example'],'reference/example.h5')
        self.assertIn('reference/probe-reference.h5',item['reference']['files'])


if __name__=='__main__':unittest.main()
