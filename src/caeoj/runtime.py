"""Trusted, installed contract assembly. No chapter or physical model dispatch."""
from copy import deepcopy
from functools import lru_cache
from importlib import import_module
from importlib.resources import files
from importlib.util import find_spec
import importlib.abc
import importlib.util
import json
import sys
from jsonschema import Draft202012Validator, SchemaError


class DeclarationError(ValueError):
    """A declaration is outside the explicitly registered input contract."""
    def __init__(self, model, code, path="$.physics.model"):
        self.model, self.code, self.path = model, code, path
        super().__init__(f"Unregistered physical declaration: {model}")


class RuntimeSupportError(RuntimeError):
    """The installed materials cannot provide their promised contract checks."""


def read_metadata(text):
    def unique(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError(f'Duplicate runtime metadata key: {key}')
            value[key] = item
        return value
    return json.loads(text, object_pairs_hook=unique)


@lru_cache(maxsize=1)
def descriptor():
    if find_spec('caeoj_bundle') is None:
        return {'version': 1, 'id': 'core-only', 'extensions': {}, 'tasks': {},
                'strict_tasks': False, 'aliases': {}, 'modules': {}}
    try:
        data = read_metadata(files('caeoj_bundle').joinpath('runtime.json').read_text(encoding='utf-8'))
        if not isinstance(data, dict) or type(data.get('version')) is not int or data['version'] != 1:
            raise ValueError('unsupported assembly version')
        if not isinstance(data.get('extensions'), dict) or not isinstance(data.get('tasks'), dict):
            raise ValueError('extensions and tasks must be objects')
        return data
    except (OSError, ValueError, KeyError) as exc:
        raise RuntimeSupportError(f'Invalid installed materials: {exc}') from exc


def load_symbol(target):
    module, name = target.split(':', 1)
    try:
        return getattr(import_module(module), name)
    except (ImportError, AttributeError) as exc:
        raise RuntimeSupportError(f'Installed materials are incomplete: {target}') from exc


def resolve_alias(name):
    target = descriptor().get('aliases', {}).get(name)
    if target is None:
        raise AttributeError(name)
    return load_symbol(target)


def _value(manifest, path):
    value = manifest
    for part in path.split('.'):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def selector_matches(manifest, selector):
    for key, expected in selector.items():
        value = _value(manifest, key[:-7] if key.endswith('_prefix') else key)
        if key.endswith('_prefix'):
            if not isinstance(value, str) or not value.startswith(expected):
                return False
        elif value != expected:
            return False
    return True


def selected(manifest, *, validate=True):
    data = descriptor()
    if not isinstance(manifest, dict) or ('task' in manifest and not isinstance(manifest['task'], str)):
        return []
    task = manifest.get('task')
    binding = data.get('tasks', {}).get(task)
    if task is None and data.get('strict_tasks') and len(data.get('tasks', {})) == 1:
        binding = next(iter(data['tasks'].values()))
    if data.get('strict_tasks') and binding is None:
        raise RuntimeSupportError(f'Task {task!r} is not included in the installed materials')
    requested = list(binding or [])
    if data.get('strict_tasks') and validate:
        for name in requested:
            declaration = data['extensions'].get(name, {})
            selectors = declaration.get('selectors', [])
            if selectors and not any(selector_matches(manifest, item) for item in selectors):
                key = next(iter(selectors[0]))
                raise DeclarationError(_value(manifest, key), declaration.get('error_code', 'E_METADATA'), '$.'+key)
    matched = []
    for name, spec in data['extensions'].items():
        if any(selector_matches(manifest, item) for item in spec.get('selectors', [])):
            requested.append(name)
            matched.append(name)
    model = _value(manifest, 'physics.model')
    if validate and isinstance(model, str) and any(model.startswith(prefix) for prefix in data.get('model_namespaces', [])) and not matched:
        prefix = next(p for p in data['model_namespaces'] if model.startswith(p))
        codes = data.get('model_namespace_diagnostics', {})
        raise DeclarationError(model, codes.get(prefix, 'E_METADATA'))
    ordered, active = [], set()
    def visit(name):
        if name in active:
            raise RuntimeSupportError(f'Cyclic installed extension dependency: {name}')
        if name in ordered:
            return
        spec = data['extensions'].get(name)
        if spec is None:
            raise RuntimeSupportError(f'Installed materials are missing extension {name}')
        active.add(name)
        for dependency in spec.get('requires', []):
            visit(dependency)
        active.remove(name)
        ordered.append(name)
    for name in requested:
        visit(name)
    return ordered


def compose_schema(base, fragments, allowed_overrides=()):
    """Add declarations without silent overwrites of core or peer schemas."""
    base = deepcopy(base)
    override_owners = {}
    def identical(left, right):
        return json.dumps(left, sort_keys=True) == json.dumps(right, sort_keys=True)
    def merge(left, right, owner, overrides, path=''):
        for key, value in right.items():
            location = path+'.'+key if path else key
            if key not in left:
                left[key] = deepcopy(value)
            elif identical(left[key], value):
                continue
            elif isinstance(value, dict) and isinstance(left[key], dict):
                merge(left[key], value, owner, overrides, location)
            elif key == 'allOf' and isinstance(value, list) and isinstance(left[key], list):
                left[key].extend(deepcopy(value))
            elif location in overrides and location in allowed_overrides:
                if location in override_owners:
                    raise RuntimeSupportError(f'Conflicting schema override owners: {override_owners[location]} and {owner}: {location}')
                override_owners[location] = owner
                left[key] = deepcopy(value)
            else:
                raise RuntimeSupportError(f'Conflicting contract resource from {owner}: {location}')
    for owner, fragment, overrides in fragments:
        if set(overrides) - set(allowed_overrides):
            raise RuntimeSupportError(f'Unsupported schema override from {owner}')
        merge(base, fragment, owner, overrides)
    return base


def schema(manifest):
    return _assembled_schema(tuple(selected(manifest, validate=False)), descriptor().get('id'))


@lru_cache(maxsize=64)
def _assembled_schema(names, identity):
    base = json.loads(files('caeoj').joinpath('problem.schema.json').read_text(encoding='utf-8'))
    points = json.loads(files('caeoj').joinpath('public-runtime.json').read_text(encoding='utf-8')).get('schema_overrides', [])
    fragments = []
    for name in names:
        spec = descriptor()['extensions'][name]
        for resource in spec.get('schemas', []):
            package, path = resource.split(':', 1)
            try:
                fragment = json.loads(files(package).joinpath(path).read_text(encoding='utf-8'))
            except (ImportError, OSError, ValueError) as exc:
                raise RuntimeSupportError(f'Missing installed contract resource {resource}') from exc
            fragments.append((name, fragment, spec.get('schema_overrides', [])))
    result = compose_schema(base, fragments, points)
    try:
        Draft202012Validator.check_schema(result)
    except SchemaError as exc:
        raise RuntimeSupportError(f'Invalid installed contract schema: {exc.message}') from exc
    return result


def needs_geometry(manifest):
    return any(descriptor()['extensions'][name].get('geometry', False) for name in selected(manifest))


def check(problem, errors):
    for name in selected(problem.manifest):
        entry = descriptor()['extensions'][name].get('check')
        if entry and not errors:
            load_symbol(entry)(problem, errors)


def condition_compatibility(problem, condition, spec):
    for name in selected(problem.manifest):
        entry = descriptor()['extensions'][name].get('condition_compatibility')
        if entry:
            answer = load_symbol(entry)(problem, condition, spec)
            if answer is not None:
                return answer
    return None


def bundle_info():
    data = descriptor()
    return {'assembly': data.get('id'), 'extensions': sorted(data['extensions']),
            'tasks': sorted(data.get('tasks', {})), 'scope': 'assembled' if data.get('strict_tasks') else 'development' if data['extensions'] else 'generic-structure'}


def describe(manifest):
    if not isinstance(manifest, dict):
        raise ValueError('Input declaration must be a JSON object')
    names = selected(manifest)
    return {**bundle_info(), 'task': manifest.get('task'), 'selected_extensions': names,
            'scope': 'task-contract' if descriptor().get('strict_tasks') else 'declared-extensions' if names else 'generic-structure'}


class _AliasLoader(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def find_spec(self, fullname, path=None, target=None):
        if not fullname.startswith('caeoj.'):
            return None
        target_name = descriptor().get('modules', {}).get(fullname)
        if target_name:
            return importlib.util.spec_from_loader(fullname, self)
        return None

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        target = import_module(descriptor()['modules'][module.__name__])
        for name, value in vars(target).items():
            if name not in {'__name__', '__loader__', '__spec__', '__package__'}:
                setattr(module, name, value)


def install_aliases():
    if not any(isinstance(item, _AliasLoader) for item in sys.meta_path):
        sys.meta_path.append(_AliasLoader())
