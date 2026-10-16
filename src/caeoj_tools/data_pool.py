"""Author-side task pools: transport, bound selections and transactional assembly.

No physics or grading rules live here. Hub support is optional and imported lazily.
"""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
import warnings
from .files import atomic_replace


class PoolError(ValueError):
    pass


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def identity(path):
    return {'size_bytes': Path(path).stat().st_size, 'sha256': digest(path)}


def relative(value):
    if (not isinstance(value, str) or not value or '\\' in value or ':' in value
            or '\x00' in value or value.startswith('/')
            or any(p in ('', '.', '..') for p in value.split('/'))):
        raise PoolError(f'Unsafe relative path: {value!r}')
    for part in value.split('/'):
        if (part.endswith((' ', '.')) or any(c in part for c in '<>"|?*') or any(ord(c) < 32 for c in part)
                or re.fullmatch(r'(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\..*)?', part)):
            raise PoolError(f'Non-portable path: {value!r}')
    return value


def within(root, name):
    root = Path(root).absolute()
    target = root / relative(name)
    for current in (root, *target.parents, target):
        if current.is_symlink() or getattr(current, 'is_junction', lambda: False)():
            raise PoolError(f'Linked data path: {current}')
    if not target.resolve().is_relative_to(root.resolve()):
        raise PoolError(f'Path escapes root: {name}')
    return target


def checked_json(path):
    def pairs(entries):
        result = {}
        for key, value in entries:
            if key in result:
                raise PoolError(f'Duplicate JSON key: {key}')
            result[key] = value
        return result
    try:
        value = json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=pairs)
    except (ValueError, UnicodeError) as exc:
        raise PoolError(f'Invalid JSON in {path}: {exc}') from exc
    if not isinstance(value, dict):
        raise PoolError(f'Expected JSON object: {path}')
    return value


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(encoded(value))
        atomic_replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def check_entry(entry):
    if (not isinstance(entry, dict) or type(entry.get('size_bytes')) is not int
            or entry['size_bytes'] < 0 or not re.fullmatch('[0-9a-f]{64}', str(entry.get('sha256', '')))):
        raise PoolError('Invalid file size/SHA-256 declaration')


def matches(path, entry):
    check_entry(entry)
    return Path(path).is_file() and identity(path) == {k: entry[k] for k in ('size_bytes', 'sha256')}


def manifest(path):
    value = checked_json(path)
    if value.get('schema_version') != 2 or not re.fullmatch(r'caeoj-\d{6}', value.get('task_id', '')):
        raise PoolError('Expected pool selection schema_version 2 and stable task_id')
    repo = value.get('repository', {})
    if repo.get('repo_type') != 'dataset' or not re.fullmatch(r'[\w.-]+/[\w.-]+', repo.get('repo_id', '')):
        raise PoolError('Expected a dataset repository owner/name')
    relative(repo.get('path'))
    for role in ('cases', 'samples'):
        if not isinstance(value.get(role), dict):
            raise PoolError(f'Missing selection mapping: {role}')
        for name, selection in value[role].items():
            if '/' in relative(name):
                raise PoolError('Selection names must be single path segments')
            if not isinstance(selection, dict) or not re.fullmatch(r'[\w-]+', selection.get('case_id', '')):
                raise PoolError('Invalid case ID')
    return value


class LocalStore:
    """A repository-shaped directory, useful for offline staging and tests."""
    def __init__(self, root):
        self.root = Path(root).absolute()
        self.revision = 'local'

    def get(self, name):
        path = within(self.root, name)
        if not path.is_file():
            raise PoolError(f'Missing pool file: {name}')
        return path


class HubStore:
    """All reads use one resolved commit; cached payloads are still hash-checked."""
    def __init__(self, repo_id, revision='main', cache_dir=None):
        try:
            from huggingface_hub import HfApi, hf_hub_download
        except ImportError as exc:
            raise PoolError("Install maintenance dependencies: pip install -e '.[maint]'") from exc
        self.repo_id, self.cache_dir = repo_id, cache_dir
        self.revision = HfApi().repo_info(repo_id, repo_type='dataset', revision=revision).sha
        self.download = hf_hub_download
        self.paths = {}

    def get(self, name):
        if name not in self.paths:
            self.paths[name] = Path(self.download(self.repo_id, relative(name), repo_type='dataset',
                                                 revision=self.revision, cache_dir=self.cache_dir))
        return self.paths[name]


def bound(store, prefix, binding, descriptors=None):
    if not isinstance(binding, dict) or not re.fullmatch('[0-9a-f]{64}', str(binding.get('sha256', ''))):
        raise PoolError('Invalid descriptor binding')
    name = relative(binding.get('path'))
    if not name.startswith('pool/'):
        raise PoolError('Descriptor must be inside the task pool')
    path = store.get(prefix + '/' + name)
    if digest(path) != binding['sha256']:
        raise PoolError(f'Descriptor SHA mismatch: {name}; explicitly reselect after reviewing changes')
    value = checked_json(path)
    if value.get('schema_version') != 1:
        raise PoolError(f'Unknown descriptor version: {name}')
    if descriptors is not None:
        descriptors[name] = path.read_text(encoding='utf-8')
    return value


def item_files(store, prefix, binding, item, descriptors, active=None):
    """Dependency descriptors map logical item paths to task-local shared sources."""
    active = set() if active is None else active
    name = relative(binding['path'])
    if name in active:
        raise PoolError('Cyclic shared dependency')
    active.add(name)
    files = {}
    base = str(PurePosixPath(name).parent)
    for logical, entry in item.get('files', {}).items():
        relative(logical); check_entry(entry)
        source = entry.get('source', base + '/' + logical)
        relative(source)
        if not source.startswith(base + '/') and not source.startswith('pool/shared/'):
            raise PoolError(f'File source must be in this item or task shared data: {source}')
        files[logical] = {**entry, 'source': source}
    dependencies = item.get('shared_dependencies', [])
    if not isinstance(dependencies, list):
        raise PoolError('shared_dependencies must be a descriptor binding list')
    for dependency in dependencies:
        value = bound(store, prefix, dependency, descriptors)
        for logical, entry in item_files(store, prefix, dependency, value, descriptors, active).items():
            if logical in files and files[logical] != entry:
                raise PoolError('Conflicting shared dependency destination')
            files[logical] = entry
    active.remove(name)
    return files


def plan(value, store, cases=None, samples=None, auxiliary=True):
    prefix = value['repository']['path']
    result = {'files': {}, 'descriptors': {}, 'incomplete': [], 'overlaps': [], 'scope': {}}
    fingerprints = {}
    destinations = {}
    def add(target, entry):
        target = relative(target)
        if target in result['files'] and result['files'][target] != entry:
            raise PoolError(f'Conflicting assembly target: {target}')
        key = target.casefold()
        if key in destinations and destinations[key] != target:
            raise PoolError('Case-insensitive destination collision')
        destinations[key] = target
        result['files'][target] = entry
    for role, chosen in (('cases', cases), ('samples', samples)):
        names = list(value[role]) if chosen is None else list(chosen)
        if len(names) != len(set(names)) or set(names) - set(value[role]):
            raise PoolError(f'Unknown or repeated {role} selection')
        result['scope'][role] = names
        for name in names:
            selection = value[role][name]
            item = bound(store, prefix, selection['item'], result['descriptors'])
            if item.get('case_id') != selection['case_id']:
                raise PoolError('Selection case ID differs from bound descriptor')
            files = item_files(store, prefix, selection['item'], item, result['descriptors'])
            signature = {}
            for kind, group_prefix in (('input', 'input/'), ('reference', 'reference/')):
                group = item.get(kind, {})
                names_in_group = group.get('files')
                if type(group.get('complete')) is not bool or not isinstance(names_in_group, list):
                    raise PoolError(f'Invalid {kind} group')
                if group['complete'] and group_prefix + ('problem.json' if kind == 'input' else 'reference.h5') not in names_in_group:
                    raise PoolError(f'Complete {kind} lacks its entry point')
                if not group['complete']:
                    result['incomplete'].append(f'{role}/{name}/{kind}')
                for logical in names_in_group:
                    if logical not in files or not logical.startswith(group_prefix):
                        raise PoolError('Group references missing or misplaced file')
                    leaf = logical.removeprefix(group_prefix)
                    if kind == 'input':
                        signature[leaf] = files[logical]['sha256']
                        target = f'cases/{name}/{leaf}' if role == 'cases' else f'samples/{name}/input/{leaf}'
                    elif role == 'cases':
                        target = f'reference/{name}/{leaf}'
                    elif leaf == 'reference.h5':
                        target = f'samples/{name}/output/result.h5'
                    else:
                        continue  # Author reference sidecars do not belong to sample output.
                    add(target, files[logical])
            keys = ['input:' + hashlib.sha256(json.dumps(signature, sort_keys=True).encode()).hexdigest()]
            origin = item.get('origin', {}).get('certificate_identity', {})
            if all(key in origin for key in ('source_id', 'source_md5', 'sample_index')):
                keys.append('trajectory:' + json.dumps({k: origin[k] for k in (
                    'source_id', 'source_md5', 'sample_index')}, sort_keys=True))
            duplicate = next((fingerprints[k] for k in keys if k in fingerprints), None)
            if duplicate:
                result['overlaps'].append([duplicate, f'{role}/{name}'])
            for key in keys:
                fingerprints[key] = f'{role}/{name}'
            for logical, target in selection.get('attachments', {}).items():
                if logical not in files or not logical.startswith('attachments/'):
                    raise PoolError('Selection refers to undeclared attachment')
                if role != 'samples':
                    raise PoolError('Only samples support attachment mappings')
                dest = relative(target)
                if dest.startswith(('input/', 'output/')):
                    raise PoolError('Attachment cannot overwrite sample input/output')
                add(f'samples/{name}/{dest}', files[logical])
    if auxiliary and 'auxiliary' in value:
        desc = bound(store, prefix, value['auxiliary'], result['descriptors'])
        for target, entry in desc.get('files', {}).items():
            if not target.startswith(('reference/', 'shared/')):
                raise PoolError('Auxiliary destination must be reference/ or shared/')
            check_entry(entry)
            source = relative(entry.get('source'))
            if not source.startswith('pool/'):
                raise PoolError('Auxiliary source must be in the pool')
            add(target, entry)
    # File/directory collisions must fail before any download or mutation.
    for target in result['files']:
        for parent in PurePosixPath(target).parents:
            if str(parent).casefold() in destinations:
                raise PoolError('Assembly file/directory collision')
    return result


def fetch(value, store, **options):
    result = plan(value, store, **options)
    for entry in result['files'].values():
        path = store.get(value['repository']['path'] + '/' + entry['source'])
        if not matches(path, entry):
            raise PoolError(f'Pool payload SHA/size mismatch: {entry["source"]}')
    result['revision'] = store.revision
    return result


RECEIPT = '.data-assembly.json'


@contextmanager
def task_lock(task):
    path = within(task, '.data-pool.lock')
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(str(os.getpid()))
        yield
    finally:
        path.unlink()


def assemble(task, value, store, *, update=False, **options):
    task = Path(task).absolute()
    task.mkdir(parents=True, exist_ok=True)
    with task_lock(task):
        return _assemble(task, value, store, update=update, **options)


def _assemble(task, value, store, *, update=False, **options):
    desired = fetch(value, store, **options)
    receipt_path = within(task, RECEIPT)
    previous = checked_json(receipt_path) if receipt_path.exists() else {'files': {}}
    for name, entry in previous.get('files', {}).items():
        relative(name); check_entry(entry)
        if not name.startswith(('cases/', 'reference/', 'samples/', 'shared/')):
            raise PoolError('Receipt cannot manage files outside data directories')
    stale = set(previous['files']) - set(desired['files'])
    # Check every change before mutating anything. --update authorizes replacement,
    # but never silently removes user-modified files from an old selection.
    conflicts = [name for name, entry in desired['files'].items()
                 if within(task, name).exists() and not matches(within(task, name), entry)]
    if conflicts and not update:
        raise PoolError('Local files differ; review and use --update: ' + ', '.join(conflicts[:8]))
    for name in stale:
        path = within(task, name)
        if path.exists() and not matches(path, previous['files'][name]):
            raise PoolError(f'Refusing to remove modified old assembly file: {name}')
        if path.exists() and not update:
            raise PoolError('Selection removed old files; use --update after review')
    receipt = {'schema_version': 1, 'selection_sha256': hashlib.sha256(encoded(value)).hexdigest(),
               'revision': store.revision, 'scope': desired['scope'],
               'auxiliary': options.get('auxiliary', True), 'descriptors': desired['descriptors'],
               'files': {name: {k: e[k] for k in ('size_bytes', 'sha256')} for name, e in desired['files'].items()}}
    with tempfile.TemporaryDirectory(prefix='.pool-stage-', dir=task) as temporary:
        stage = Path(temporary)
        changes = []
        for name, entry in desired['files'].items():
            if matches(within(task, name), entry):
                continue
            target = within(stage, 'new/' + name)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(store.get(value['repository']['path'] + '/' + entry['source']), target)
            if not matches(target, entry):
                raise PoolError('Source changed while copying')
            changes.append(name)
        # One staged receipt is committed last; rollback covers every file mutation.
        write_json(stage/'receipt.json', receipt)
        touched = []
        try:
            for name in [*sorted(set(changes) | stale), RECEIPT]:
                target = within(task, name)
                backup = within(stage, 'old/' + name)
                existed = target.exists()
                if existed:
                    backup.parent.mkdir(parents=True, exist_ok=True)
                    atomic_replace(target, backup)
                touched.append((name, existed))
                if name in stale:
                    continue
                source = stage/'receipt.json' if name == RECEIPT else within(stage, 'new/' + name)
                target.parent.mkdir(parents=True, exist_ok=True)
                atomic_replace(source, target)
        except BaseException:
            for name, existed in reversed(touched):
                target = within(task, name)
                if target.is_file():
                    target.unlink()
                if existed:
                    atomic_replace(within(stage, 'old/' + name), target)
            raise
    return {'revision': store.revision, 'files': len(desired['files']), 'changed': len(changes),
            'removed': len(stale), 'complete': not desired['incomplete'],
            'incomplete': desired['incomplete'], 'overlaps': desired['overlaps']}


def verify(task, *, strict=False, samples_only=False):
    """Offline verification derives expectations from SHA-bound receipt descriptors."""
    task = Path(task)
    value = manifest(task/'data-manifest.json')
    errors = []
    try:
        receipt = checked_json(within(task, RECEIPT))
        if receipt.get('selection_sha256') != hashlib.sha256(encoded(value)).hexdigest():
            raise PoolError('Selection changed; reassemble before consuming data')
        class ReceiptStore:
            revision = receipt.get('revision')
            def get(self, name):
                key = name.removeprefix(value['repository']['path'] + '/')
                if key not in receipt['descriptors']:
                    raise PoolError(f'Missing bound descriptor in receipt: {key}')
                target = within(temporary, key)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(receipt['descriptors'][key].encode('utf-8'))
                return target
        with tempfile.TemporaryDirectory() as temporary:
            current = plan(value, ReceiptStore(), cases=[] if samples_only else None,
                           samples=None, auxiliary=not samples_only)
        for name, entry in current['files'].items():
            if not matches(within(task, name), entry):
                errors.append('Local SHA/size mismatch or missing: ' + name)
        if strict:
            errors += ['Incomplete group: ' + name for name in current['incomplete']]
            if not samples_only:
                errors += ['Overlapping inputs: ' + ', '.join(pair) for pair in current['overlaps']]
            for role in (('samples',) if samples_only else ('cases', 'samples')):
                pattern = '*/input/problem.json' if role == 'samples' else '*/problem.json'
                actual = {p.parent.parent.name if role == 'samples' else p.parent.name
                          for p in (task/role).glob(pattern)}
                if actual != set(value[role]):
                    errors.append('Stale or missing ' + role + ' entry points')
    except (PoolError, OSError, KeyError, TypeError) as exc:
        errors.append(str(exc))
    if errors and strict:
        raise PoolError('; '.join(errors))
    for error in errors:
        warnings.warn(error, stacklevel=2)
    return {'valid': not errors, 'errors': errors}


def select(value, store, cases, samples, *, allow_incomplete=False):
    prefix = value['repository']['path']
    index = checked_json(store.get(prefix + '/' + relative(value['pool']['index'])))
    if index.get('schema_version') != 1 or not isinstance(index.get('items'), dict):
        raise PoolError('Invalid pool index')
    selected = {**value, 'cases': {}, 'samples': {}}
    selected.pop('auxiliary', None)
    if 'auxiliary' in index:
        selected['auxiliary'] = index['auxiliary']
    for role, choices in (('cases', cases), ('samples', samples)):
        for number, choice in enumerate(choices, 1):
            name, case_id = choice.split('=', 1) if '=' in choice else (f'{number:03d}', choice)
            if '/' in relative(name) or name in selected[role]:
                raise PoolError('Invalid or repeated local selection name')
            if case_id not in index['items']:
                raise PoolError(f'Unknown pool case ID: {case_id}')
            binding = {k: index['items'][case_id][k] for k in ('path', 'sha256')}
            selected[role][name] = {'case_id': case_id, 'item': binding}
    result = plan(selected, store)
    if result['overlaps']:
        raise PoolError('Selections contain duplicate inputs: ' + str(result['overlaps']))
    if result['incomplete'] and not allow_incomplete:
        raise PoolError('Selected entries are incomplete: ' + str(result['incomplete']))
    return selected


def pack(source, output, value):
    """Convert generated task directories into a staged repository and selection.

    Complete means all declared input assets exist, not numerical certification.
    References and examples are included only when they actually exist.
    """
    source, output = Path(source).absolute(), Path(output).absolute()
    if value.get('schema_version') != 2 or not re.fullmatch(r'caeoj-\d{6}', value.get('task_id', '')):
        raise PoolError('Pack requires a stable task ID and selection version 2')
    if output.exists() and any(output.iterdir()):
        raise PoolError('Pack output must be empty; use a new staging directory')
    if output.is_relative_to(source) or source.is_relative_to(output):
        raise PoolError('Pack source and output must be separate trees')
    prefix = relative(value['repository']['path'])
    repo = output/'repository'
    items, selections, consumed = {}, {'cases': {}, 'samples': {}}, set()
    def inventory(directory):
        if not directory.exists():
            return {}
        result = {}
        for path in sorted(directory.rglob('*')):
            within(source, path.relative_to(source).as_posix())
            if path.is_file():
                result[path.relative_to(directory).as_posix()] = path
        return result
    def complete_input(files):
        if 'problem.json' not in files:
            return False
        problem = checked_json(files['problem.json'])
        assets = [problem.get('data_file')]
        for key in ('geometries', 'meshes'):
            assets += [v.get('file') for v in problem.get(key, {}).values()]
        return all(relative(name) in files for name in assets)
    def put(path, target):
        destination = within(repo, prefix + '/' + target)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
        consumed.add(path.relative_to(source).as_posix())
        return identity(destination)
    for role in ('cases', 'samples'):
        directories = source/role
        if not directories.exists():
            continue
        for directory in sorted(directories.iterdir()):
            if not directory.is_dir():
                raise PoolError('Case/sample roots must contain named directories')
            name = relative(directory.name)
            inputs = inventory(directory if role == 'cases' else directory/'input')
            if not inputs:
                raise PoolError(f'Empty input: {role}/{name}')
            input_id = hashlib.sha256(json.dumps({p: digest(f) for p, f in inputs.items()}, sort_keys=True).encode()).hexdigest()
            case_id = 'case-' + input_id[:24]
            item = items.setdefault(case_id, {'schema_version': 1, 'case_id': case_id,
                'origin': {'kind': 'prepared-input', 'key': name, 'input_identity_sha256': input_id},
                'files': {}, 'input': {'complete': complete_input(inputs), 'files': []},
                'reference': {'complete': False, 'files': []}, 'shared_dependencies': [], 'attachments': {}})
            certificate_path = source/'reference'/name/'certificate.json' if role == 'cases' else source/'reference/sample-certificates'/name/'certificate.json'
            if certificate_path.is_file():
                certificate = checked_json(certificate_path)
                declared = certificate.get('input_files', {})
                if declared and any(key not in inputs or digest(inputs[key]) != checksum
                                    for key, checksum in declared.items()):
                    raise PoolError('Source certificate does not bind this input')
                item['origin']['certificate_identity'] = {key: certificate[key] for key in (
                    'source_id', 'source_md5', 'sample_index', 'contract_sha256', 'tool_sha256') if key in certificate}
            base = f'pool/items/{case_id}/'
            for logical, path in inputs.items():
                key = 'input/' + logical
                entry = put(path, base + key)
                if key in item['files'] and item['files'][key] != entry:
                    raise PoolError('Input ID collision')
                item['files'][key] = entry
                if key not in item['input']['files']:
                    item['input']['files'].append(key)
            copied_id = hashlib.sha256(json.dumps({key.removeprefix('input/'): item['files'][key]['sha256']
                for key in item['input']['files']}, sort_keys=True).encode()).hexdigest()
            if copied_id != input_id:
                raise PoolError('Input changed while packing; retry from a stable source')
            refs = inventory(source/'reference'/name if role == 'cases' else directory/'output')
            for logical, path in refs.items():
                key = 'reference/' + ('reference.h5' if role == 'samples' and logical == 'result.h5' else logical)
                entry = identity(path)
                if key in item['files'] and item['files'][key] != entry:
                    raise PoolError(f'Different references for identical input: {name}')
                item['files'][key] = put(path, base + key)
                if key not in item['reference']['files']:
                    item['reference']['files'].append(key)
            item['reference']['complete'] = 'reference/reference.h5' in item['reference']['files']
            choice = {'case_id': case_id}
            if role == 'samples':
                choice['attachments'] = {}
                for logical, path in inventory(directory).items():
                    if logical.startswith(('input/', 'output/')):
                        continue
                    key = f'attachments/sample-{name}/{logical}'
                    item['files'][key] = put(path, base + key)
                    item['attachments'][key] = {'role': 'sample-verification', 'sample_name': name}
                    choice['attachments'][key] = logical
            selections[role][name] = choice
    if not items:
        raise PoolError('No case/sample inputs found')
    # Content-address repeated assets within one task. Input JSON keeps its
    # contract paths; assembly materializes shared payloads under those paths.
    counts = {}
    for item in items.values():
        for key, entry in item['files'].items():
            counts.setdefault(entry['sha256'], []).append((item, key, entry))
    for checksum, copies in counts.items():
        if len(copies) < 2:
            continue
        shared = 'pool/shared/' + checksum + '/' + PurePosixPath(copies[0][1]).name
        for item, key, entry in copies:
            old = within(repo, f'{prefix}/pool/items/{item["case_id"]}/{key}')
            target = within(repo, prefix + '/' + shared)
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                shutil.copyfile(old, target)
            old.unlink()
            entry['source'] = shared
    index = {'schema_version': 1, 'items': {}, 'shared': {}}
    for case_id, item in items.items():
        name = f'pool/items/{case_id}/item.json'
        write_json(within(repo, prefix + '/' + name), item)
        binding = {'path': name, 'sha256': digest(within(repo, prefix + '/' + name))}
        index['items'][case_id] = {**binding, 'input_complete': item['input']['complete'],
                                  'reference_complete': item['reference']['complete']}
        for group in selections.values():
            for choice in group.values():
                if choice['case_id'] == case_id:
                    choice['item'] = binding
    auxiliary = {}
    for directory in ('reference', 'shared'):
        for logical, path in inventory(source/directory).items():
            target = directory + '/' + logical
            if target not in consumed:
                remote = 'pool/attachments/' + target
                auxiliary[target] = {'source': remote, **put(path, remote)}
    selected = {k: value[k] for k in ('schema_version', 'task_id', 'repository')}
    selected.update(pool={'index': 'pool/index.json'}, **selections)
    if auxiliary:
        name = 'pool/attachments.json'
        write_json(within(repo, prefix + '/' + name), {'schema_version': 1, 'files': auxiliary})
        binding = {'path': name, 'sha256': digest(within(repo, prefix + '/' + name))}
        selected['auxiliary'] = index['auxiliary'] = binding
    write_json(within(repo, prefix + '/pool/index.json'), index)
    # Verify the complete staging tree before advertising a usable selection.
    fetch(selected, LocalStore(repo))
    write_json(output/'selection.json', selected)
    return {'bundle': str(output), 'selection': str(output/'selection.json'), 'items': len(items)}


def validate_bundle(bundle):
    bundle = Path(bundle)
    value = manifest(bundle/'selection.json')
    store = LocalStore(bundle/'repository')
    prefix = value['repository']['path']
    index_path = prefix + '/' + value['pool']['index']
    index = checked_json(store.get(index_path))
    all_items = {**value, 'cases': {}, 'samples': {}}
    allowed = {index_path}
    descriptors = {}
    for number, (case_id, binding) in enumerate(index.get('items', {}).items()):
        all_items['cases'][str(number)] = {'case_id': case_id, 'item': binding}
        item = bound(store, prefix, binding, descriptors)
        if (binding.get('input_complete') != item['input']['complete']
                or binding.get('reference_complete') != item['reference']['complete']):
            raise PoolError('Index completeness differs from the item descriptor')
        # Unselected attachments are still uploaded and must be checked.
        for entry in item_files(store, prefix, binding, item, descriptors).values():
            allowed.add(prefix + '/' + entry['source'])
            if not matches(store.get(prefix + '/' + entry['source']), entry):
                raise PoolError('Bundle contains corrupt payload or attachment')
    if not all_items['cases']:
        raise PoolError('Cannot upload an empty pool index')
    for result in (fetch(all_items, store), fetch(value, store)):
        descriptors.update(result['descriptors'])
        allowed.update(prefix + '/' + entry['source'] for entry in result['files'].values())
    allowed.update(prefix + '/' + name for name in descriptors)
    actual = set()
    for path in store.root.rglob('*'):
        name = path.relative_to(store.root).as_posix()
        within(store.root, name)
        if path.is_file():
            actual.add(name)
    if actual != allowed:
        raise PoolError('Bundle contains undeclared or missing files: ' + str(sorted(actual.symmetric_difference(allowed))[:8]))
    return value, store, index


def upload(bundle, *, update=False, revision='main'):
    """Merge a validated bundle in one optimistic commit; preserve unrelated items."""
    from huggingface_hub import HfApi, CommitOperationAdd
    value, local, index = validate_bundle(bundle)
    repo = value['repository']; prefix = repo['path']
    remote = HubStore(repo['repo_id'], revision)
    api = HfApi()
    names = set(api.list_repo_files(repo['repo_id'], repo_type='dataset', revision=remote.revision))
    index_name = prefix + '/' + value['pool']['index']
    previous = checked_json(remote.get(index_name)) if index_name in names else {'schema_version': 1, 'items': {}, 'shared': {}}
    if previous.get('schema_version') != 1:
        raise PoolError('Unsupported remote pool index')
    for case_id, entry in index['items'].items():
        if case_id in previous['items'] and previous['items'][case_id] != entry and not update:
            raise PoolError('Remote item changed; review and use --update: ' + case_id)
    merged = {**previous, **index, 'items': {**previous['items'], **index['items']},
              'shared': {**previous.get('shared', {}), **index.get('shared', {})}}
    operations = []
    paths = [p for p in sorted(local.root.rglob('*')) if p.is_file()]
    existing = [p.relative_to(local.root).as_posix() for p in paths
                if p.relative_to(local.root).as_posix() in names]
    metadata = {}
    for offset in range(0, len(existing), 100):
        metadata.update({f.path: f for f in api.get_paths_info(repo['repo_id'], existing[offset:offset+100],
                         repo_type='dataset', revision=remote.revision)})
    for path in paths:
        if not path.is_file():
            continue
        name = path.relative_to(local.root).as_posix()
        within(local.root, name)
        if not name.startswith(prefix + '/pool/'):
            raise PoolError('Bundle may only upload files under this task pool')
        if name == index_name:
            continue
        if name in names:
            info = metadata.get(name)
            if info is None:
                raise PoolError('Remote file metadata missing at the resolved revision')
            if info.lfs:
                same = info.lfs.sha256 == digest(path)
            else:
                git = hashlib.sha1(f'blob {path.stat().st_size}\0'.encode())
                with path.open('rb') as stream:
                    for block in iter(lambda: stream.read(1024*1024), b''):
                        git.update(block)
                same = info.blob_id == git.hexdigest()
            if same:
                continue
            if not update:
                raise PoolError('Remote file differs; review and use --update: ' + name)
        operations.append(CommitOperationAdd(path_in_repo=name, path_or_fileobj=path))
    if merged != previous:
        operations.append(CommitOperationAdd(path_in_repo=index_name, path_or_fileobj=encoded(merged)))
    if not operations:
        return {'revision': remote.revision, 'uploaded_files': 0}
    commit = api.create_commit(repo_id=repo['repo_id'], repo_type='dataset', revision=revision,
                              parent_commit=remote.revision, operations=operations,
                              commit_message='Publish validated task pool: ' + value['task_id'])
    verified = HubStore(repo['repo_id'], commit.oid)
    fetch(value, verified)
    # Validate every index item in the bundle, not just the default selection.
    all_items = {**value, 'cases': {str(n): {'case_id': cid, 'item': b}
                 for n, (cid, b) in enumerate(index['items'].items())}, 'samples': {}}
    fetch(all_items, verified)
    return {'revision': commit.oid, 'uploaded_files': len(operations)}
