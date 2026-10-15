"""Compatibility of the chapter-2 opt-in envelope, before loading any payload."""
from copy import deepcopy
import unittest
from caeoj.validation import schema_errors


class FluidEnvelopeTests(unittest.TestCase):
    def minimal(self):
        return {'spatial_dimension': 2, 'data_file': 'input.h5', 'geometries': {},
                'meshes': {}, 'locations': {}, 'time_axes': {}, 'fields': {},
                'outputs': {}, 'conditions': [],
                'physics': {'model': 'fluid-energy-unknown-v1', 'parameters': {}}}

    def test_explicit_domain_model_uses_existing_general_structure(self):
        for family in ('energy', 'multiphase', 'reduced'):
            m = self.minimal()
            m['physics']['model'] = f'fluid-{family}-unknown-v1'
            self.assertEqual(schema_errors(m), [])  # Domain registry checks the name later.

    def test_domain_profile_cannot_be_mixed_with_cfd_profile(self):
        m = self.minimal()
        m.update(contract_version=2, profile='cfd-2.1',
                 analysis={'type':'steady','compressibility':'incompressible',
                           'flow_regime':'laminar','temperature':{'value':300,'unit':'K'},
                           'pressure':{'representation':'absolute'}},
                 materials={'fluid':{'region':'domain',
                     'density':{'kind':'constant','parameters':{}},
                     'viscosity':{'kind':'newtonian','parameters':{}}}})
        for family in ('energy', 'multiphase', 'reduced'):
            mixed = deepcopy(m)
            mixed['physics']['model'] = f'fluid-{family}-unknown-v1'
            self.assertTrue(any(e['code']=='E_SCHEMA' for e in schema_errors(mixed)))

    def test_unrelated_old_physics_remains_schema_compatible(self):
        m = self.minimal()
        m['physics']['model'] = 'steady_heat'
        self.assertEqual(schema_errors(m), [])

    def test_old_empty_condition_stays_invalid(self):
        m = self.minimal()
        m['conditions'] = [{'role':'boundary','variable':'velocity',
                            'location':'wall','operator':'no_slip','data':{}}]
        self.assertTrue(schema_errors(m))


if __name__ == '__main__':
    unittest.main()
