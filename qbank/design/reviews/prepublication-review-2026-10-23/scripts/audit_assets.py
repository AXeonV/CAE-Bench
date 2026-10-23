import collections
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import time

ROOT = Path('D:/Code/CAE-Bench-OJ')
WORK = ROOT / 'runs/prepublication-review-rc2'
PLAN = json.loads((ROOT / 'runs/release-assembly-rc2/plan.json').read_text(encoding='utf-8'))
spec = importlib.util.spec_from_file_location('audit_inventory', ROOT / '.agents/skills/caeoj-data-review/scripts/inventory.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def save(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding='utf-8')

records = []
for task in PLAN['tasks']:
    source = Path(task['source_root']) / task['task_path']
    current = ROOT / task['task_path']
    inv = module.inventory(source)
    save(WORK / 'data-inventory' / (task['task'] + '.json'), inv)
    docs = (source / 'instruction.md').read_text(encoding='utf-8') + '\n' + (source / 'DATA.md').read_text(encoding='utf-8')
    fields = collections.defaultdict(set)
    def walk(value, path=''):
        if isinstance(value, dict):
            for k, v in value.items():
                p = path + '.' + k if path else k
                fields[p].add(type(v).__name__)
                walk(v, p)
        elif isinstance(value, list):
            for v in value:
                walk(v, path + '[]')
    grading = []
    for entry in inv['inputs']:
        walk(entry.get('manifest', {}))
        if entry['kind'] == 'case':
            p = Path(entry['path'])
            g = source / 'reference' / p.parent.name / 'grading.json'
            grading.append({'case': p.parent.name, 'path': str(g), 'sha256': sha(g), 'config': json.loads(g.read_text(encoding='utf-8'))})
    names = ['instruction.md', 'DATA.md', 'judge-config.json', 'harbor/task.toml']
    comparisons = {n: {'release_source': str(source / n), 'release_sha256': sha(source / n) if (source / n).is_file() else None,
                       'checkout_sha256': sha(current / n) if (current / n).is_file() else None} for n in names}
    signatures = {}
    for entry in inv['inputs']:
        for f in entry.get('arrays', {}).get('content', []):
            signatures.setdefault(f['key'], set()).add((f['dtype'], len(f['shape'])))
    record = {'task': task['task'], 'chapter': task['chapter'], 'title': task['title'],
              'source': str(source), 'cases': inv['case_count'], 'samples': inv['sample_count'],
              'inventory_gaps': inv['gaps'], 'document_comparison': comparisons,
              'input_field_types': {k: sorted(v) for k, v in fields.items()},
              'input_array_signatures': {k: sorted(v) for k, v in signatures.items()},
              'grading': grading,
              'execution': json.loads((source / 'judge-config.json').read_text(encoding='utf-8'))}
    records.append(record)
    save(WORK / 'asset-audit.json', {'stage': 'inventory', 'tasks': records, 'scientific_qualification': False})
    print(task['task'], inv['case_count'], inv['sample_count'], 'inventory gaps', len(inv['gaps']), flush=True)
save(WORK / 'asset-audit.json', {'stage': 'inventory_complete', 'tasks': records, 'scientific_qualification': False})
print('COMPLETE', len(records), flush=True)
