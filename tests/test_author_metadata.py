"""Public declaration catalogs exclude private author execution/scoring settings."""
from copy import deepcopy
from importlib import import_module
import json
from pathlib import Path
import unittest

from caeoj_tools.author import public_model_catalog


ROOT = Path(__file__).resolve().parents[1]
CATALOGS = {
    'acoustic': ('authoring.build_acoustic', 'M'),
    'electromagnetic': ('authoring.build_electromagnetic', 'M'),
    'optics': ('authoring.build_optics', 'M'),
    'thermal': ('authoring.build_thermal', 'M'),
    'multibody': ('authoring.build_multibody', 'M'),
    'species': ('authoring.build_species', 'M'),
    'electrochemistry': ('authoring.build_electrochemistry', 'M'),
    'semiconductor': ('authoring.build_semiconductor', 'MODELS'),
    'granular': ('authoring.build_granular', 'MODELS'),
    'porous': ('authoring.build_porous', 'MODELS'),
    'radiation': ('authoring.build_radiation', 'MODELS'),
    'microstructure': ('authoring.build_microstructure', 'MODELS'),
    'solid': ('solid_authoring', 'CAT'),
}


class AuthorMetadataTests(unittest.TestCase):
    def test_projection_preserves_contract_and_does_not_modify_author(self):
        author = {'test': {'timeout': 30, 'parameters': {'atol': 'physical parameter'},
                          'outputs': {'field': {'unit': 'K', 'shape': [1], 'atol': .01, 'rtol': .02}},
                          'output_specs': {'other': {'unit': 'm', 'atol': .1}}}}
        before = deepcopy(author)
        public = public_model_catalog(author)
        self.assertEqual(author, before)
        self.assertEqual(public, {'test': {'parameters': {'atol': 'physical parameter'},
                                          'outputs': {'field': {'unit': 'K', 'shape': [1]}},
                                          'output_specs': {'other': {'unit': 'm'}}}})
        public['test']['outputs']['field']['shape'][0] = 3
        self.assertEqual(author, before)

    def test_committed_catalogs_match_author_exports(self):
        for domain, (module, name) in CATALOGS.items():
            with self.subTest(domain=domain):
                author = getattr(import_module('qbank.maintenance.' + module), name)
                # JSON represents the solid author's tuples as arrays. The two
                # write-time normalized catalogs are covered by authoring_encoding.
                expected = json.loads(json.dumps(public_model_catalog(author)))
                path = ROOT/'qbank/extensions/caeoj_ext'/domain/'models.json'
                self.assertEqual(json.loads(path.read_text(encoding='utf-8')), expected)

    def test_all_public_catalogs_have_no_execution_or_scoring_settings(self):
        for path in (ROOT/'qbank/extensions/caeoj_ext').glob('*/models.json'):
            catalog = json.loads(path.read_text(encoding='utf-8'))
            with self.subTest(domain=path.parent.name):
                for model in catalog.values():
                    self.assertNotIn('timeout', model)
                    for key in ('outputs', 'output_specs'):
                        fields = model.get(key)
                        if isinstance(fields, dict):
                            for field in fields.values():
                                self.assertTrue({'atol', 'rtol'}.isdisjoint(field))


if __name__ == '__main__':
    unittest.main()
