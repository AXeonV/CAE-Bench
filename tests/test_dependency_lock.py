"""Dependency locks validate installed constraints and propagate extras to closure."""
from email.message import Message
from importlib import metadata
import unittest
from unittest.mock import patch

from caeoj_tools.dependencies import lock_dependencies


class Distribution:
    def __init__(self, version, requires=(), extras=()):
        self.version = version
        self.requires = list(requires)
        self.metadata = Message()
        for extra in extras:
            self.metadata['Provides-Extra'] = extra


class DependencyLockTests(unittest.TestCase):
    def resolve(self, distributions, requirements):
        def distribution(name):
            try:
                return distributions[name]
            except KeyError:
                raise metadata.PackageNotFoundError(name)
        with patch('caeoj_tools.dependencies.metadata.distribution', side_effect=distribution):
            return lock_dependencies(requirements)

    def test_transitive_constraint_conflict_is_not_hidden_by_first_visit(self):
        packages = {'a': Distribution('1', ['shared>=2']),
                    'b': Distribution('1', ['shared<2']),
                    'shared': Distribution('2.1')}
        with self.assertRaisesRegex(ValueError, 'does not satisfy shared<2 required by b'):
            self.resolve(packages, ['a', 'b'])
        with self.assertRaisesRegex(ValueError, 'does not satisfy a>=2'):
            self.resolve(packages, ['a>=2'])

    def test_markers_and_extra_union_expand_a_previously_seen_distribution(self):
        packages = {
            'a': Distribution('1', ['shared', 'shared[fast-mode]']),
            'shared': Distribution('2', ['base; python_version >= "3.0"',
                                        'absent; python_version < "2.0"',
                                        'speed; extra == "fast_mode"'], extras=['fast-mode']),
            'base': Distribution('3'), 'speed': Distribution('4'),
        }
        self.assertEqual(self.resolve(packages, ['a', 'absent; python_version < "2.0"']),
                         ['a==1', 'base==3', 'shared==2', 'speed==4'])

    def test_cycles_terminate_and_propagate_new_extras(self):
        packages = {
            'a': Distribution('1', ['b', 'feature; extra == "later"'], extras=['later']),
            'b': Distribution('2', ['a[later]>=1']),
            'feature': Distribution('3', ['a']),
        }
        self.assertEqual(self.resolve(packages, ['a']), ['a==1', 'b==2', 'feature==3'])

    def test_missing_distribution_unknown_extra_and_url_fail_before_publish(self):
        with self.assertRaisesRegex(ValueError, 'Missing installed dependency absent'):
            self.resolve({}, ['absent'])
        with self.assertRaisesRegex(ValueError, 'does not provide extras'):
            self.resolve({'a': Distribution('1')}, ['a[missing]'])
        with self.assertRaisesRegex(ValueError, 'Direct URL dependency'):
            self.resolve({}, ['a @ https://example.com/a.whl'])

    def test_distribution_python_requirement_is_checked(self):
        package = Distribution('1')
        package.metadata['Requires-Python'] = '<2'
        with self.assertRaisesRegex(ValueError, 'requires Python <2'):
            self.resolve({'a': package}, ['a'])

    def test_normalized_names_are_pinned_once(self):
        self.assertEqual(self.resolve({'my-lib': Distribution('1.2')}, ['My_Lib>=1', 'my-lib<2']),
                         ['my-lib==1.2'])


if __name__ == '__main__':
    unittest.main()
