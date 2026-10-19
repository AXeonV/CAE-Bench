"""Verified local case/example bindings for author-side publishing and assembly.

Uses the same public_cases report semantics as data pools, without fabricating
HF selection or download receipts. Bindings never enter the public archive.
"""
import hashlib
import json
from pathlib import Path
import re

from caeoj.sdk import load_problem
from caeoj.case_grading import prepare_case
from .assembly import read_public_file

BINDING = Path('author/public-examples.json')


def _name(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', value):
        raise ValueError('Invalid local case/example name')
    return value


def _hash(task, path):
    return hashlib.sha256(read_public_file(task, path)).hexdigest()


def example_snapshot(task, case, sample):
    """Require exact input, reference assets and complete example bytes."""
    task = Path(task).resolve()
    source = task/'cases'/_name(case)
    target = task/'samples'/_name(sample)
    problem = load_problem(source/'problem.json')
    m = problem.manifest
    names = {'problem.json', m['data_file']}
    names.update(v['file'] for table in ('meshes', 'geometries') for v in m[table].values())
    inputs = {n: _hash(task, source/n) for n in sorted(names)}
    if inputs != {n: _hash(task, target/'input'/n) for n in inputs}:
        raise ValueError('Public example input differs from its scored case')
    reference = task/'reference'/case
    assets = prepare_case(problem, reference/'grading.json').evidence['assets']
    refs = {n: _hash(task, reference/n) for n in sorted(assets)}
    if refs != {n: _hash(task, target/'reference'/n) for n in refs}:
        raise ValueError('Public example grading/reference differs from its scored case')
    if 'reference.h5' not in refs:
        raise ValueError('Local case reference cannot supply a complete example result')
    output = _hash(task, target/'output/result.h5')
    if output != refs['reference.h5']:
        raise ValueError('Public example output differs from the full case reference')
    return {'input_files': inputs, 'reference_files': refs, 'example_sha256': output}


def verify_public_examples(task):
    """Validate an optional local binding; never fall back from failed verification."""
    task = Path(task).resolve()
    path = task/BINDING
    root = task.parents[3]
    workspace = root/'workspace.json'
    authorization = None
    if workspace.exists():
        state = json.loads(read_public_file(root, workspace))
        authorization = state.get('public_examples', {}).get(task.name)
    if not path.exists():
        if authorization is not None:
            raise ValueError('Required local public-example binding is missing')
        return []
    if authorization is None:
        raise ValueError('Local public-example binding lacks frozen workspace authorization')
    samples = sorted(p.parent.parent.name for p in (task/'samples').glob('*/input/problem.json'))
    cases = sorted(p.parent.name for p in (task/'cases').glob('*/problem.json'))
    if samples != authorization['samples'] or cases != authorization['cases']:
        raise ValueError('Local sample/case coverage differs from frozen workspace authorization')
    if (task/'data-manifest.json').exists():
        raise ValueError('HF selection and local public-example binding cannot coexist')
    document = json.loads(read_public_file(task, path))
    if set(document) != {'schema_version', 'public_cases'} or type(document['schema_version']) is not int or document['schema_version'] != 1 or not isinstance(document['public_cases'], list):
        raise ValueError('Invalid local public-example binding')
    cases, samples, result = set(), set(), []
    for row in document['public_cases']:
        if not isinstance(row, dict) or set(row) != {'case', 'sample', 'case_id', 'snapshot'}:
            raise ValueError('Invalid local public-example identity')
        case, sample = _name(row['case']), _name(row['sample'])
        if case in cases or sample in samples or not isinstance(row['case_id'], str) or not re.fullmatch(r'[0-9a-f]{64}', row['case_id']):
            raise ValueError('Duplicate/invalid local public-example identity')
        cases.add(case); samples.add(sample)
        if row['snapshot'] != example_snapshot(task, case, sample):
            raise ValueError('Public example binding is stale or modified')
        result.append({k: row[k] for k in ('case', 'sample', 'case_id')})
    if result != authorization['public_cases']:
        raise ValueError('Local public-example identities differ from frozen workspace authorization')
    return result
