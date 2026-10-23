"""Explicit author configurations survive generation without binary fallback."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from caeoj_tools.continuous_scoring import convert_grading, convert_rule, SCORING
from caeoj_tools.grading_policy import (author_case_grading, author_policy,
                                       materialize_references, write_case_grading)


class ContinuousAuthoringTests(unittest.TestCase):
    def test_migration_preserves_domain_transform_weight_and_offset(self):
        rule = dict(metric='pointwise', time='per_time', components='per_component',
                    atol=.5, rtol=.02, reference_offset={'parameter':'pressure_reference'})
        config = {'version':1,'checks':[{'id':'outputs','evaluator':'field.normalized_outputs',
            'reference':'reference.h5','weight_field':'weights',
            'transforms':{'pressure':{'remove_mean':True,'offset':0}},
            'policy':{'version':2,'quantities':{'pressure':{'unit':'Pa','rule':rule}}}}]}
        original = deepcopy(config)
        migrated = convert_grading(config)
        self.assertEqual(config, original)
        check = migrated['checks'][0]
        self.assertEqual(check['transforms'], original['checks'][0]['transforms'])
        self.assertEqual(check['weight_field'], 'weights')
        self.assertEqual(check['policy']['quantities']['pressure']['rule'],
            dict(metric='nrmse',time='per_time',components='per_component',scale_floor=.5,
                 limit=.05,reference_offset={'parameter':'pressure_reference'}))
        self.assertEqual(migrated['scoring'], SCORING)

    def test_missing_or_zero_inherited_scale_is_not_silently_calibrated(self):
        for rule in ({'metric':'pointwise','atol':0}, {'metric':'unknown'},
                     {'metric':'nrmse','scale_floor':float('nan')}):
            with self.subTest(rule=rule), self.assertRaises(ValueError):
                convert_rule(rule)

    def test_outer_template_is_written_without_losing_scoring(self):
        policy={'version':2,'default':dict(metric='nrmse',time='per_time',
                  components='per_component',scale_floor=.1,limit=.05)}
        config={'version':1,'scoring':SCORING,'checks':[dict(id='all',
                evaluator='direct_outputs',reference='reference.h5',policy=policy)]}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'author').mkdir()
            template=root/'author/grading-template.json'
            template.write_text(json.dumps(config),encoding='utf-8')
            self.assertEqual(author_case_grading(root),config)
            self.assertEqual(author_policy(root),policy)
            reference=root/'reference/one';reference.mkdir(parents=True)
            (root/'cases/one').mkdir(parents=True)
            (root/'cases/one/problem.json').write_text('{}')
            (reference/'reference.h5').write_bytes(b'writer does not inspect arrays')
            materialize_references(root,case_config=author_case_grading(root))
            self.assertEqual(json.loads((reference/'grading.json').read_text()),config)
            template.write_text(json.dumps(policy),encoding='utf-8')
            legacy=author_case_grading(root)
            self.assertNotIn('scoring',legacy)
            self.assertEqual(legacy['checks'][0]['policy'],policy)

    def test_multicheck_template_cannot_be_extracted_as_one_policy(self):
        policy={'version':2,'default':dict(metric='pointwise',time='per_time',
                components='per_component',atol=0,rtol=0)}
        checks=[dict(id=n,evaluator='direct_outputs',reference='reference.h5',policy=policy)
                for n in ('a','b')]
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'author').mkdir()
            (root/'author/grading-template.json').write_text(json.dumps(dict(version=1,checks=checks)))
            self.assertEqual(len(author_case_grading(root)['checks']),2)
            with self.assertRaisesRegex(ValueError,'one numerical policy'):
                author_policy(root)
