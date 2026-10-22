"""Audit all selected data, outputs and grading against the public contract."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem, load_result
from caeoj.case_grading import grade_case, prepare_case

TASK = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('assembly_declarations', TASK / 'extension/caeoj_task_ext/assembly_repair.py')
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    report = {'status': 'passed', 'scope': 'all selected cases and public samples', 'records': [], 'materials_sha256': {}}
    for name in ('instruction.md', 'DATA.md'):
        report['materials_sha256'][name] = hashlib.sha256((TASK / name).read_bytes()).hexdigest()
    contract = TASK.parents[3] / 'docs/CONTRACT.md'
    report['materials_sha256']['CONTRACT.md'] = hashlib.sha256(contract.read_bytes()).hexdigest()
    items = [(path, TASK/'reference'/path.parent.name, None, False)
             for path in sorted((TASK/'cases').glob('*/problem.json'))]
    items += [(path, path.parent.parent/'reference', path.parent.parent/'output/result.h5', True)
              for path in sorted((TASK/'samples').glob('*/input/problem.json'))]
    for path, reference, output, public in items:
        problem = load_problem(path)
        errors = []
        checker.check(problem, errors)
        if errors:
            raise ValueError((str(path), errors))
        prepared = prepare_case(problem, reference/'grading.json')
        values = load_result(problem, reference/'reference.h5')
        if grade_case(path, reference/'reference.h5', reference/'grading.json')['score'] != 1:
            raise ValueError('Reference fails its bound plan')
        if public:
            load_result(problem, output)
            if grade_case(path, output, reference/'grading.json')['score'] != 1:
                raise ValueError('Public output fails its bound plan')
        fields = problem.manifest['fields']
        record = {'path': str(path.relative_to(TASK)), 'public_sample': public,
                  'body_count': len(problem.arrays['body_ids']), 'link_count': len(problem.arrays.get('link_ids', [])),
                  'action': problem.manifest['physics']['parameters']['action']['value'],
                  'fields': {name: {'shape': list(problem.arrays[value['array']].shape), 'unit': value['unit'],
                                    'dtype': str(problem.arrays[value['array']].dtype)} for name, value in fields.items()},
                  'outputs': {name: {'shape': list(values[value['array']].shape), 'unit': value['unit']}
                              for name, value in problem.manifest['outputs'].items()},
                  'evaluation_sha256': prepared.evidence['evaluation_sha256'],
                  'input_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        report['records'].append(record)
    # Declaration counterexamples chosen from DATA requirements. These mutate
    # copies only; they never repair the actual data or solver results.
    path = next((TASK/'cases').glob('01-*/problem.json'))
    base = load_problem(path)
    mutations = {
        'unknown_body_id': lambda p: p.arrays['endpoints'].__setitem__((0, 0, 0), 999999),
        'moving_fixed_body': lambda p: p.arrays['velocity'].__setitem__((0, 0, 0), 1.),
        'incompatible_acceleration_state': lambda p: p.arrays['position'].__setitem__((0, 1, 0), 1.2),
        'missing_vector_reaction': lambda p: p.manifest['outputs'].pop('reaction'),
        'wrong_force_unit': lambda p: p.manifest['fields']['force'].__setitem__('unit', 'Pa')}
    report['invalid_variants'] = {}
    for name, mutation in mutations.items():
        problem = load_problem(path)
        mutation(problem)
        errors = []
        checker.check(problem, errors)
        if not errors:
            raise ValueError('Publicly illegal variant accepted: ' + name)
        report['invalid_variants'][name] = {'rejected': True, 'diagnostic_count': len(errors)}
    report['cases'] = sum(not row['public_sample'] for row in report['records'])
    report['samples'] = sum(row['public_sample'] for row in report['records'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: report[key] for key in ('status', 'cases', 'samples', 'invalid_variants')}))


if __name__ == '__main__':
    main()
