import json
from pathlib import Path
import re
import tomllib

ROOT = Path('D:/Code/CAE-Bench-OJ')
WORK = ROOT / 'runs/prepublication-review-rc2'
audit = json.loads((WORK / 'asset-audit.json').read_text(encoding='utf-8'))
plan = json.loads((ROOT / 'runs/release-assembly-rc2/plan.json').read_text(encoding='utf-8'))
paths = {t['task']: t['task_path'] for t in plan['tasks']}
records = []
errors = []
for task in audit['tasks']:
    source = Path(task['source'])
    public = ROOT / paths[task['task']]
    text = (public / 'instruction.md').read_text(encoding='utf-8')
    tables = {}
    for line in text.splitlines():
        cells = [s.strip().strip('`') for s in line.strip().strip('|').split('|')]
        if line.startswith('|') and len(cells) >= 3:
            try:
                atol = float(cells[1])
            except ValueError:
                continue
            try:
                rtol = float(cells[2])
            except ValueError:
                rtol = 0.01 if '相对容差均为 0.01' in text else None
            tables[cells[0]] = {'atol': atol, 'rtol': rtol}
    configs = {}
    for entry in task['grading']:
        raw = json.dumps(entry['config'], sort_keys=True)
        configs.setdefault(raw, []).append(entry['case'])
        for check in entry['config']['checks']:
            quantities = check.get('policy', {}).get('quantities', {})
            for name, policy in quantities.items():
                rule = policy['rule']
                if name in tables and rule.get('metric') == 'pointwise':
                    expected = tables[name]
                    if expected['atol'] != rule.get('atol') or expected['rtol'] is not None and expected['rtol'] != rule.get('rtol'):
                        errors.append({'task': task['task'], 'case': entry['case'], 'quantity': name, 'public': expected, 'actual': rule})
    manifest = json.loads((source / 'data-manifest.json').read_text(encoding='utf-8'))
    inventory = json.loads((WORK / 'data-inventory' / (task['task'] + '.json')).read_text(encoding='utf-8'))
    output_quantities = {}
    for entry in inventory['inputs']:
        for name, output in entry['manifest'].get('outputs', {}).items():
            q = output['quantity']
            output_quantities.setdefault(q, set()).add(output.get('unit'))
    overrides = tomllib.loads((source / 'harbor/task.toml').read_text(encoding='utf-8')) if (source / 'harbor/task.toml').exists() else {}
    template = tomllib.loads((ROOT / 'src/utils/harbor/task.toml').read_text(encoding='utf-8'))
    environment = template.get('environment', {}) | overrides.get('environment', {})
    records.append({'task': task['task'], 'formal_cases': task['cases'], 'public_samples': task['samples'],
                    'sample_kinds': {n: v.get('kind', 'numerical') for n, v in manifest['samples'].items()},
                    'output_quantities_units': {k: sorted(v, key=str) for k, v in output_quantities.items()},
                    'public_tolerance_table': tables,
                    'actual_unique_grading': [{'cases': cases, 'config': json.loads(raw)} for raw, cases in configs.items()],
                    'execution': task['execution'], 'effective_environment': environment})
result = {'tasks': records, 'pointwise_table_mismatches': errors,
          'notice': 'Every case scoring config enumerated; table comparison covers pointwise quantity rows. Other metric/normalization semantics require manual audit; resource values are configured, not newly calibrated.'}
(WORK / 'scoring-map.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print('Mapped', len(records), 'tasks;', sum(t['formal_cases'] for t in records), 'case configs; pointwise mismatches', len(errors))
for e in errors[:12]: print(e)
