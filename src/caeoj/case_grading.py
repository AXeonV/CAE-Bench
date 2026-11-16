"""Self-contained case evaluation. Configurations select trusted code, never imports."""
from dataclasses import dataclass, field
import hashlib
import inspect
import math
from importlib.resources import files as package_files
from importlib.metadata import version
import sys
import json
from pathlib import Path, PurePosixPath

import jsonschema
import numpy as np

from . import runtime
from .grading_metrics import evaluate_field, evaluate_observation
from .grading_policy import resolve_policy, validate_policy
from .sdk import load_problem
from .validation import ContractError, check_result, read_hdf5, read_mesh, resolve_file


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''): h.update(chunk)
    return h.hexdigest()


def parse_config(text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result: raise ValueError('Duplicate case grading key: ' + key)
            result[key] = value
        return result
    def bad(value): raise ValueError('Nonfinite case grading value: ' + value)
    value = json.loads(text, object_pairs_hook=unique, parse_constant=bad)
    schema = json.loads(Path(__file__).with_name('case-grading.schema.json').read_text(encoding='utf-8'))
    try: jsonschema.Draft202012Validator(schema).validate(value)
    except jsonschema.ValidationError as exc: raise ValueError('Invalid case grading: ' + exc.message) from exc
    ids = [c['id'] for c in value['checks']]
    if len(set(ids)) != len(ids): raise ValueError('Repeated evaluation ID')
    scoring = value.get('scoring')
    if scoring and (not all(math.isfinite(scoring[k]) for k in ('full_credit', 'zero_credit')) or
                    not scoring['full_credit'] < scoring['zero_credit']):
        raise ValueError('Finite full_credit must be less than finite zero_credit')
    return value


def direct_config(policy):
    validate_policy(policy)
    return {'version': 1, 'checks': [{'id': 'outputs', 'evaluator': 'direct_outputs',
            'reference': 'reference.h5', 'policy': policy}]}


@dataclass
class Assets:
    root: Path
    hashes: dict = field(default_factory=dict)
    used: dict = field(default_factory=dict)
    arrays: dict = field(default_factory=dict)

    def file(self, name):
        if not isinstance(name, str) or '\\' in name or ':' in name:
            raise ValueError('Asset must be a relative POSIX path')
        relative = PurePosixPath(name)
        if relative.is_absolute() or not relative.parts or any(x in ('', '.', '..') for x in name.split('/')):
            raise ValueError('Unsafe grading asset path: ' + name)
        path = self.root
        for part in relative.parts:
            path = path / part
            if path.is_symlink() or getattr(path, 'is_junction', lambda: False)():
                raise ValueError('Grading assets cannot be links')
        if not path.resolve().is_relative_to(self.root.resolve()) or not path.is_file():
            raise ValueError('Missing or unsafe grading asset: ' + name)
        self.hashes[name] = sha(path)
        return path

    def h5(self, name):
        path = self.file(name)
        if name not in self.arrays: self.arrays[name] = read_hdf5(path)
        return self.arrays[name]

    def array(self, name, key):
        values = self.h5(name)
        if key not in values: raise ValueError('Missing reference/observation array: ' + key)
        self.used.setdefault(name, set()).add(key)
        return values[key]

    def finish(self):
        for name, values in self.arrays.items():
            if set(values) != self.used.get(name, set()):
                raise ValueError('Unbound grading arrays in ' + name)


def _direct(problem, check, assets):
    if set(check) != {'id', 'evaluator', 'reference', 'policy'}:
        raise ValueError('Invalid direct_outputs parameters')
    reference = assets.h5(check['reference'])
    diagnostics = check_result(problem, reference)
    if not diagnostics['valid']: raise ContractError(diagnostics)
    assets.used.setdefault(check['reference'], set()).update(reference)
    policy = resolve_policy(check['policy'], problem)
    def evaluate(result):
        fields = {}
        for name, spec in problem.manifest['outputs'].items():
            actual, expected = result[spec['array']], reference[spec['array']]
            if spec['dtype'] == 'float64':
                record = evaluate_field(problem, name, actual, expected, policy['fields'][name])
            else:
                record = {'passed': bool(np.array_equal(actual, expected)),
                          'failed_values': int(np.count_nonzero(actual != expected))}
            record['observation'] = {k: spec[k] for k in ('quantity', 'unit', 'components', 'location', 'time_axis')}
            fields[name] = record
        return {'passed': all(r['passed'] for r in fields.values()), 'fields': fields}
    return evaluate


def _sample_points(problem, check, assets):
    required = {'id', 'evaluator', 'source_output', 'components', 'observations', 'reference', 'rule'}
    if set(check) != required: raise ValueError('Invalid field.sample_points parameters')
    spec = problem.manifest['outputs'].get(check['source_output'])
    if not spec or spec['dtype'] != 'float64': raise ValueError('Sampling requires a declared float64 output')
    loc = problem.manifest['locations'][spec['location']]
    if (problem.manifest['spatial_dimension'] != 2 or loc['kind'] != 'mesh' or
            loc['entity'] != 'node' or spec['value_kind'] != 'point'):
        raise ValueError('P1 sampling requires a 2D mesh-node point field')
    mesh = read_mesh(resolve_file(problem.path.parent, problem.manifest['meshes'][loc['mesh']]['file'], '.msh'), geometry=True)
    if any(mesh['connectivity'][tag][0] != 2 for tag in mesh['elements'][2]):
        raise ValueError('P1 sampling requires first-order triangular domain cells')
    labels = check['components']
    if (not labels or len(set(labels)) != len(labels) or
            labels != [v for v in spec['components'] if v in labels]):
        raise ValueError('Components must be a nonempty canonical subset of the output labels')
    columns = [spec['components'].index(x) for x in labels]
    obs, ref = check['observations'], check['reference']
    if set(obs) != {'file', 'points', 'ids', 'times', 'cells'}:
        raise ValueError('Observation binding requires points, ids, times and containing cells')
    if set(ref) != {'file', 'array', 'ids', 'times', 'unit'} or ref['unit'] != spec['unit']:
        raise ValueError('Reference unit/binding mismatch')
    points = assets.array(obs['file'], obs['points'])
    ids = assets.array(obs['file'], obs['ids'])
    times = assets.array(obs['file'], obs['times'])
    cells = assets.array(obs['file'], obs['cells'])
    if (ids.dtype != np.dtype('int64') or ids.ndim != 1 or not len(ids) or
            len(np.unique(ids)) != len(ids) or points.dtype != np.dtype('float64') or
            points.shape != (len(ids), 2) or not np.all(np.isfinite(points)) or
            cells.dtype != np.dtype('int64') or cells.shape != ids.shape):
        raise ValueError('Invalid observation points, IDs or containing cells')
    if (times.dtype != np.dtype('float64') or times.ndim != 1 or not len(times) or
            not np.all(np.isfinite(times)) or np.any(np.diff(times) <= 0)):
        raise ValueError('Invalid observation time axis')
    output_times = problem.arrays[problem.manifest['time_axes'][spec['time_axis']]]
    time_indices = []
    for t in times:
        match = np.flatnonzero(output_times == t)
        if len(match) != 1: raise ValueError('Observation times must exactly match submitted times')
        time_indices.append(int(match[0]))
    rows = {int(v): i for i, v in enumerate(problem.arrays[loc['ids']])}
    indices, barycentric = [], []
    for point, cell in zip(points, cells):
        if int(cell) not in mesh['elements'][2]: raise ValueError('Unknown containing domain cell')
        _, conn = mesh['connectivity'][int(cell)]
        if any(n not in rows for n in conn): raise ValueError('Sample cell nodes missing from output location')
        xyz = np.array([mesh['node_coordinates'][n] for n in conn], dtype=float)
        if np.ptp(xyz[:, 2]) != 0: raise ValueError('Sampling mesh must lie in the xy plane')
        vertices = xyz[:, :2]
        matrix = np.column_stack((vertices[1]-vertices[0], vertices[2]-vertices[0]))
        scale = np.max(np.abs(matrix))
        if scale == 0 or abs(np.linalg.det(matrix/scale)) <= 64*np.finfo(float).eps:
            raise ValueError('Degenerate sampling triangle')
        coordinates = np.linalg.solve(matrix, point-vertices[0])
        weights = np.array([1-coordinates.sum(), *coordinates])
        if np.any(weights < -64*np.finfo(float).eps) or np.any(weights > 1+64*np.finfo(float).eps):
            raise ValueError('Observation point is outside its declared containing cell')
        weights = np.clip(weights, 0., 1.); weights /= weights.sum()
        indices.append([rows[n] for n in conn]); barycentric.append(weights)
    expected = assets.array(ref['file'], ref['array'])
    if (expected.dtype != np.dtype('float64') or expected.shape != (len(times), len(ids), len(labels)) or
            not np.all(np.isfinite(expected)) or
            not np.array_equal(assets.array(ref['file'], ref['ids']), ids) or
            assets.array(ref['file'], ref['ids']).dtype != ids.dtype or
            not np.array_equal(assets.array(ref['file'], ref['times']), times) or
            assets.array(ref['file'], ref['times']).dtype != times.dtype):
        raise ValueError('Reference must cover all requested points, times and components')
    # Reuse the numerical condition schema, without manufacturing a Problem.
    validate_policy({'version': 1, 'fields': {'observation': check['rule']}})
    def validate_tree(node):
        if 'all' in node or 'any' in node:
            for child in node.get('all', node.get('any')): validate_tree(child)
        elif 'weight_field' in node:
            raise ValueError('Point observations use equal sample weights; weight_field is not supported')
    validate_tree(check['rule'])
    indices, barycentric = np.array(indices), np.array(barycentric)
    def evaluate(result):
        values = result[spec['array']].reshape(len(output_times), len(rows), -1)
        selected = values[np.array(time_indices)[:, None, None], indices[None, :, :]][..., columns]
        scale = np.max(np.abs(selected), axis=2, keepdims=True)
        scaled = np.divide(selected, scale, out=np.zeros_like(selected), where=scale != 0)
        actual = np.sum(scaled*barycentric[None,:,:,None], axis=2)*scale[:,:,0,:]
        record = evaluate_observation(actual, expected, check['rule'], ids=ids, times=times)
        record['observation'] = {'quantity': spec['quantity'], 'unit': spec['unit'],
                                 'components': labels, 'ids': ids.tolist(), 'times': times.tolist()}
        return record
    return evaluate


def _evaluators(problem):
    registry = {'direct_outputs': _direct, 'field.sample_points': _sample_points}
    for name in runtime.selected(problem.manifest):
        for identity, target in runtime.descriptor()['extensions'][name].get('evaluators', {}).items():
            if identity in registry: raise ValueError('Repeated trusted evaluator ID: ' + identity)
            registry[identity] = runtime.load_symbol(target)
    return registry


@dataclass
class PreparedCase:
    problem: object
    checks: list
    evidence: dict
    assets: Assets
    input_assets: dict
    scoring: dict | None = None

    def verify_assets(self):
        for name, expected in self.evidence['input_assets'].items():
            if sha(self.input_assets[name]) != expected: raise ValueError('Evaluation input changed after preflight')
        for name, expected in self.evidence['assets'].items():
            if sha(self.assets.file(name)) != expected: raise ValueError('Evaluation asset changed after preflight')

    def evaluate(self, result):
        self.verify_assets()
        diagnostics = check_result(self.problem, result)
        if not diagnostics['valid']: return {'status': 'invalid_output', 'score': 0, 'contract': diagnostics, **self.evidence}
        records = {}
        for name, evaluator, evaluate in self.checks:
            record = evaluate(result)
            if type(record.get('passed')) is not bool: raise ValueError('Evaluator must return boolean passed')
            records[name] = {'evaluator': evaluator, **record}
        if self.scoring is None:
            score = int(all(x['passed'] for x in records.values()))
            extra = {}
        else:
            errors, hard_failure = [], False
            def collect(record):
                nonlocal hard_failure
                if 'fields' in record:
                    for child in record['fields'].values(): collect(child)
                elif 'children' in record:
                    for child in record['children']: collect(child)
                elif 'condition' in record:
                    for group in record['groups']:
                        value = group['value']
                        errors.append(math.inf if value == 'overflow' else float(value))
                elif not record['passed']:
                    # Exact integer/bool checks and normalization overflow are hard failures.
                    hard_failure = True
            for record in records.values(): collect(record)
            if not errors and not hard_failure:
                raise ValueError('Continuous scoring requires numerical NRMSE observations')
            # Scale before squaring: finite NRMSE values may exceed sqrt(DBL_MAX).
            scale = max(errors, default=math.inf)
            error = (scale * math.sqrt(math.fsum((value / scale)**2 for value in errors) / len(errors))
                     if 0 < scale < math.inf else scale)
            full, zero = self.scoring['full_credit'], self.scoring['zero_credit']
            score = 0.0 if hard_failure or error >= zero else 1.0 if error <= full else (zero-error)/(zero-full)
            extra = {'total_nrmse': error if math.isfinite(error) else 'overflow',
                     'scoring': self.scoring}
        status = 'accepted' if score == 1 else 'partial_credit' if score > 0 else 'wrong_answer'
        return {'status': status, 'score': score, 'checks': records, **extra, **self.evidence}


def prepare_case(problem, grading_path):
    path = Path(grading_path)
    assets = Assets(path.parent.resolve())
    config = parse_config(assets.file(path.name).read_text(encoding='utf-8'))
    scoring = config.get('scoring')
    if scoring:
        def continuous_rule(node):
            if 'all' in node:
                for child in node['all']: continuous_rule(child)
            elif (node.get('metric') != 'nrmse' or node.get('time') != 'per_time' or
                  node.get('components') != 'per_component' or node.get('limit') != scoring['full_credit']):
                raise ValueError('rms_nrmse scoring requires per-time/per-component NRMSE rules at full_credit')
        for check in config['checks']:
            if check['evaluator'] in ('direct_outputs', 'field.normalized_outputs'):
                policy = resolve_policy(check['policy'], problem)
                if not policy['fields']: raise ValueError('Continuous scoring requires floating outputs')
                for rule in policy['fields'].values(): continuous_rule(rule)
            elif check['evaluator'] == 'field.sample_points':
                continuous_rule(check['rule'])
            else:
                raise ValueError('Evaluator does not support rms_nrmse scoring')
    registry = _evaluators(problem); checks = []; code = {}
    for check in config['checks']:
        evaluator = registry.get(check['evaluator'])
        if evaluator is None: raise ValueError('Unknown or unavailable evaluator: ' + check['evaluator'])
        code_path = Path(inspect.getfile(evaluator))
        code[check['evaluator']] = sha(code_path)
        checks.append((check['id'], check['evaluator'], evaluator(problem, check, assets)))
    assets.finish()
    # Include the shared numerical/structural implementation, not only dispatch code.
    for filename in json.loads(Path(__file__).with_name('public-runtime.json').read_text(encoding='utf-8'))['files']:
        code['core/'+filename] = sha(Path(__file__).with_name(filename))
    code['core/case-grading.schema.json'] = sha(Path(__file__).with_name('case-grading.schema.json'))
    code['core/problem.schema.json'] = sha(Path(__file__).with_name('problem.schema.json'))
    selected = runtime.selected(problem.manifest)
    binding = {name: runtime.descriptor()['extensions'][name] for name in selected}
    for extension in binding.values():
        for resource in extension.get('files', []):
            package, *parts = PurePosixPath(resource).parts
            data = package_files(package).joinpath(*parts).read_bytes()
            code['extension/'+resource] = hashlib.sha256(data).hexdigest()
    names = [problem.path.name, problem.manifest['data_file']]
    names += [v['file'] for table in ('meshes','geometries') for v in problem.manifest[table].values()]
    input_assets = {name: problem.path.parent/name for name in names}
    evidence = {'grading_sha256': hashlib.sha256(canonical(config)).hexdigest(),
                'assets': dict(assets.hashes), 'evaluator_code_sha256': code,
                'input_assets': {name: sha(path) for name,path in input_assets.items()},
                'runtime_binding_sha256': hashlib.sha256(canonical(binding)).hexdigest(),
                'dependencies': {name: version(name) for name in ('numpy','h5py','gmsh','jsonschema')},
                'python': '.'.join(map(str,sys.version_info[:3]))}
    evidence['evaluation_sha256'] = hashlib.sha256(canonical(evidence)).hexdigest()

    return PreparedCase(problem, checks, evidence, assets, input_assets, scoring)


def grade_case(input_path, output_path, grading_path):
    try:
        problem = load_problem(input_path)
    except (OSError, ValueError, RuntimeError, ContractError, ImportError) as exc:
        return {'status': 'input_error', 'score': None, 'message': str(exc)}
    try:
        prepared = prepare_case(problem, grading_path)
    except Exception as exc:
        return {'status': 'evaluation_error', 'score': None, 'message': type(exc).__name__+': '+str(exc)}
    try: result = read_hdf5(output_path)
    except (OSError, ValueError, ContractError) as exc:
        return {'status': 'invalid_output', 'score': 0, 'message': str(exc), **prepared.evidence}
    try: return prepared.evaluate(result)
    except Exception as exc:
        return {'status': 'evaluation_error', 'score': None, 'message': type(exc).__name__+': '+str(exc), **prepared.evidence}
