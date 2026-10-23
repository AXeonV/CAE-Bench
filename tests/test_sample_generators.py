"""Public sample generation needs input declarations and never numerical references."""
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from caeoj_tools.author import load_author_module
from caeoj_tools import data_pool as pool
from caeoj.validation import validate_output
from task_fixtures import task_fixture


class SampleGeneratorTests(unittest.TestCase):
    def assert_format_samples(self, destination):
        samples = sorted((destination/'samples').iterdir())
        self.assertEqual(len(samples), 2)
        for sample in samples:
            self.assertEqual(pool.checked_json(sample/'example.json'), {'kind':'format'})
            self.assertFalse((sample/'reference').exists())
            self.assertTrue(validate_output(sample/'input/problem.json',sample/'output/result.h5')['valid'])

    def test_heat_publishers_work_without_any_reference_tree(self):
        for task, cases, publish in [
                ('heat-conduction-steady-2d',['01-constant-dirichlet'],'publish_sample'),
                ('heat-conduction-transient-2d',['01-zero','15-four-operators'],'publish_samples')]:
            with self.subTest(task=task), tempfile.TemporaryDirectory() as temporary:
                destination = Path(temporary)
                for case in cases:
                    shutil.copytree(task_fixture(task)/'cases'/case,destination/'cases'/case)
                author=task_fixture(task)/'author'
                with patch.dict(sys.modules), patch.object(sys,'path',[str(author),*sys.path]):
                    for name in ('catalog','mesh','oracle'):
                        sys.modules.pop(name,None)
                    module=load_author_module(task,'generate')
                if task.endswith('transient-2d'):
                    with patch.object(module,'reference',side_effect=AssertionError('sample generation called oracle')):
                        getattr(module,publish)(destination)
                else:
                    with patch.object(module,'polyval2d',side_effect=AssertionError('sample generation computed reference')):
                        getattr(module,publish)(destination)
                self.assertFalse((destination/'reference').exists())
                self.assert_format_samples(destination)

    def test_case_grading_samples_skip_reference_generation(self):
        module=load_author_module('case-grading-test','generate')
        with tempfile.TemporaryDirectory() as temporary:
            destination=Path(temporary)/'generated'
            calls=[]
            def reference(input_dir, reference_dir, *args):
                self.assertIn('cases',input_dir.parts)
                self.assertNotIn('samples',reference_dir.parts)
                calls.append(input_dir)
            with patch.object(module,'make_reference',side_effect=reference):
                module.generate(destination)
            self.assertEqual(len(calls),len(module.CASES))
            self.assert_format_samples(destination)
