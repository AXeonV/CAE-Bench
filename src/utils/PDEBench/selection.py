"""Offline, explicit source selections bound to existing task contracts."""
import hashlib
import json
import re
from pathlib import Path

from caeoj_tools.task_paths import task_directory
from .models import BY_TASK, source_files

ROOT = Path(__file__).resolve().parents[3]
CATALOG = Path(__file__).with_name('catalog.json')


def identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def contract_hash(task):
    h = hashlib.sha256()
    for name in ('instruction.md', 'DATA.md'):
        h.update(name.encode())
        h.update((Path(task)/name).read_bytes().replace(b'\r\n', b'\n'))
    return h.hexdigest()


def tool_hash():
    return identity({p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in Path(__file__).parent.glob('*.py')})


def execution_hash(root, tasks):
    """Stdlib-only freeze of public contracts, runtime and execution configuration."""
    root = Path(root)
    paths = [root/p for p in ('docs/CONTRACT.md', 'docs/GRADING.md', 'LICENSE', 'pyproject.toml',
                                    'src/utils/publish_dist.py', 'src/utils/prepare_harbor.py')]
    for folder in ('src/caeoj', 'src/caeoj_tools', 'qbank/extensions', 'src/utils/harbor'):
        paths.extend(p for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts
                     and (folder == 'src/utils/harbor' or p.suffix in ('.py', '.json', '.sh', '.toml', '.txt')))
    for slug in sorted(tasks):
        task = task_directory(slug, root)
        paths.extend(p for p in task.rglob('*') if p.is_file() and (
            p.relative_to(task).parts[0] in ('harbor', 'extension') or p.name == 'judge-config.json'))
    for p in paths:
        if p.is_symlink(): raise ValueError('Execution source must not be a symlink')
    return identity({p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted(set(paths))})


def make_selection(entries, *, root=ROOT, catalog=None):
    catalog = catalog or json.loads(CATALOG.read_text())
    if not isinstance(entries, list) or not entries:
        raise ValueError('Selection needs a nonempty entries list')
    result = []
    ids, trajectories = set(), set()
    for raw in entries:
        if not isinstance(raw, dict) or set(raw) != {'task', 'source_id', 'index', 'frames', 'role', 'id'}:
            raise ValueError('Entry keys must be task, source_id, index, frames, role, id')
        e = dict(raw)
        model = BY_TASK[e['task']]
        for key in ('source_id', 'index'):
            if type(e[key]) is not int or e[key] < 0:
                raise ValueError('Source ID/index must be nonnegative integers')
        if e['role'] not in ('sample', 'case') or not isinstance(e['id'], str) or not re.fullmatch(r'[0-9]{1,6}', e['id']):
            raise ValueError('Role must be sample/case; local ID must be 1..6 digits')
        frames = e['frames']
        limit = 5 if e['role'] == 'sample' else 9
        if (not isinstance(frames, list) or not 1 <= len(frames) <= limit or frames[0] != 0
                or any(type(f) is not int or f < 0 for f in frames)
                or any(a >= b for a, b in zip(frames, frames[1:]))):
            raise ValueError('Frames must be increasing original indices including 0, within role count limit')
        source = next((s for s in source_files(model, catalog) if s['id'] == e['source_id']), None)
        if source is None:
            raise ValueError('Source does not belong to this task in the pinned catalog')
        local = (e['task'], e['role'], e['id'])
        trajectory = (e['source_id'], e['index'])
        if local in ids or trajectory in trajectories:
            raise ValueError('Duplicate local ID or source trajectory (including public/hidden overlap)')
        ids.add(local); trajectories.add(trajectory)
        task = task_directory(e['task'], root)
        e.update(source=source, contract_sha256=contract_hash(task),
                 grading_template_sha256=hashlib.sha256((task/'author/grading-template.json').read_bytes()).hexdigest())
        result.append(e)
    body = {'schema_version': 1, 'dataset': catalog['dataset'], 'dataset_version': catalog['version'],
            'catalog_sha256': identity(catalog), 'tool_sha256': tool_hash(),
            'execution_sha256': execution_hash(root, {e['task'] for e in result}), 'entries': result,
            'network_bytes_estimate': None, 'scope': 'explicit subset; not the formal full selection'}
    return {**body, 'sha256': identity(body)}


def validate_selection(selection, *, root=ROOT, catalog=None):
    entries = [{k: e[k] for k in ('task', 'source_id', 'index', 'frames', 'role', 'id')}
               for e in selection['entries']]
    expected = make_selection(entries, root=root, catalog=catalog)
    if selection != expected:
        raise ValueError('Frozen selection differs from pinned catalog, contracts, policy or converter; make a new plan')
    return expected
