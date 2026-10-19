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
import tarfile
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
    if value.get('schema_version') != 4 or not re.fullmatch(r'caeoj-\d{6}', value.get('task_id', '')):
        raise PoolError('Expected pool selection schema_version 4 and stable task_id')
    if set(value) - {'schema_version', 'task_id', 'repository', 'pool', 'cases', 'samples', 'notes'}:
        raise PoolError('Selection has unsupported fields; migrate the old layout explicitly')
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
            if set(selection) != {'case_id', 'case'}:
                raise PoolError('Selection must bind one case descriptor, without attachments')
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


def consumer_store(value, store):
    """Choose physical transport without changing logical selection bindings."""
    if not isinstance(store,(LocalStore,HubStore)):
        return store
    prefix=value['repository']['path']
    views=getattr(store,'_pool_views',{})
    if prefix in views: return views[prefix]
    index=checked_json(store.get(prefix+'/'+relative(value['pool']['index'])))
    if index.get('schema_version')==4:
        from .data_pool_shards import PartitionStore
        cache=getattr(store,'cache_dir',None)
        if cache is None:
            cache=store.root/'.extracted' if isinstance(store,LocalStore) else Path(tempfile.gettempdir()).resolve()/'caeoj-shards'
        view=PartitionStore(store,prefix,Path(cache)/'pool-members',index)
    else:
        view=store
    store._pool_views=views;views[prefix]=view
    return view


def shard_bundle(bundle, output, *, target_bytes=128*1024*1024):
    """Experimental immutable transport; logical case format stays unchanged.

    Only a validated existing bundle is accepted. The root routes by case-ID
    ranges; per-shard member inventories avoid a global payload-file map.
    """
    value, source, index = validate_bundle(bundle)
    if type(target_bytes) is not int or target_bytes < 1024:
        raise PoolError('Invalid shard byte target')
    output = Path(output).absolute()
    if output.exists() and any(output.iterdir()):
        raise PoolError('Shard output must be empty')
    if output.is_relative_to(Path(bundle).absolute()) or Path(bundle).absolute().is_relative_to(output):
        raise PoolError('Shard output and bundle must be separate trees')
    prefix = value['repository']['path']
    output.mkdir(parents=True, exist_ok=True)
    groups, group, size = [], [], 0
    for cid in sorted(index['cases']):
        paths = sorted((source.root/prefix/'pool/cases'/cid).rglob('*'))
        paths = [p for p in paths if p.is_file()]
        total = sum(p.stat().st_size + 2048 for p in paths)
        if group and size + total > target_bytes:
            groups.append(group); group, size = [], 0
        group.append((cid, paths)); size += total
    if group:
        groups.append(group)
    root = {'schema_version': 1, 'kind': 'experimental-case-tar-transport',
            'task_path': prefix, 'case_count': len(index['cases']), 'shards': []}
    for number, cases in enumerate(groups):
        name = f'shards/{number:05d}.tar'
        archive = output/name; archive.parent.mkdir(exist_ok=True)
        members = {}
        with tarfile.open(archive, 'w', format=tarfile.USTAR_FORMAT) as tar:
            for cid, paths in cases:
                for path in paths:
                    logical = path.relative_to(source.root).as_posix()
                    within(source.root, logical)
                    info = tarfile.TarInfo(logical)
                    info.size = path.stat().st_size; info.mode = 0o644
                    with path.open('rb') as stream:
                        tar.addfile(info, stream)
                    members[logical] = identity(path)
        locator = f'shards/{number:05d}.json'
        write_json(output/locator, {'schema_version': 1, 'members': members})
        root['shards'].append({'first_case': cases[0][0], 'last_case': cases[-1][0],
                              'archive': {'path': name, **identity(archive)},
                              'locator': {'path': locator, **identity(output/locator)}})
    # Logical root index is a member-independent metadata file, not a payload.
    logical_index = source.get(prefix+'/'+value['pool']['index'])
    shutil.copyfile(logical_index, output/'index.json')
    root['index'] = {'path': 'index.json', **identity(output/'index.json')}
    write_json(output/'transport.json', root)
    write_json(output/'selection.json', value)
    return root


class ShardStore:
    """Read one immutable transport through a LocalStore/HubStore.

    The current experiment downloads a whole selected shard, never the pool.
    It does not yet implement HTTP range reads or production CLI discovery.
    """
    def __init__(self, backing, transport_prefix, cache):
        self.backing = backing
        self.prefix = relative(transport_prefix)
        self.revision = backing.revision
        self.root = Path(cache).absolute()
        self.root.mkdir(parents=True, exist_ok=True)
        self.catalog = checked_json(backing.get(self.prefix+'/transport.json'))
        if (self.catalog.get('schema_version') != 1 or
                self.catalog.get('kind') != 'experimental-case-tar-transport'):
            raise PoolError('Unknown shard transport')
        self.task = relative(self.catalog['task_path'])
        self.loaded, self.paths, self.offsets = {}, {}, {}
        previous = ''
        for shard in self.catalog['shards']:
            first, last = shard['first_case'], shard['last_case']
            if not re.fullmatch('case-[0-9a-f]{24}', first) or not re.fullmatch('case-[0-9a-f]{24}', last) or not previous < first <= last:
                raise PoolError('Invalid/overlapping shard range')
            previous = last

    def _bound(self, entry):
        check_entry(entry)
        path = self.backing.get(self.prefix+'/'+relative(entry['path']))
        if not matches(path, entry):
            raise PoolError('Corrupt shard transport asset')
        return path

    def get(self, name):
        name = relative(name)
        if name in self.paths:
            return self.paths[name]
        if name == self.task+'/pool/index.json':
            return self._bound(self.catalog['index'])
        base = self.task+'/pool/cases/'
        if not name.startswith(base):
            raise PoolError('Path is outside shard task')
        cid = name[len(base):].split('/')[0]
        shard = next((s for s in self.catalog['shards'] if s['first_case'] <= cid <= s['last_case']), None)
        if shard is None:
            raise PoolError('Case absent from shard transport')
        key = shard['archive']['path']
        if key not in self.loaded:
            locator = checked_json(self._bound(shard['locator']))
            if locator.get('schema_version') != 1:
                raise PoolError('Unknown shard locator')
            for member, entry in locator['members'].items():
                relative(member); check_entry(entry)
                if not member.startswith(base):
                    raise PoolError('Shard member outside task')
            archive = self._bound(shard['archive'])
            with tarfile.open(archive, 'r:') as tar:
                seen = set()
                offsets = {}
                for member in tar.getmembers():
                    if member.name in seen or member.name not in locator['members'] or not member.isfile():
                        raise PoolError('Duplicate, linked or undeclared TAR member')
                    relative(member.name)
                    if member.size != locator['members'][member.name]['size_bytes']:
                        raise PoolError('TAR member size mismatch')
                    seen.add(member.name)
                    offsets[member.name] = member.offset_data
                if seen != set(locator['members']):
                    raise PoolError('Missing TAR member')
            self.loaded[key] = archive, locator['members']
            self.offsets[key] = offsets
        archive, members = self.loaded[key]
        if name not in members:
            raise PoolError('Missing shard member')
        target = within(self.root, name)
        if not matches(target, members[name]):
            target.parent.mkdir(parents=True, exist_ok=True)
            fd, temporary = tempfile.mkstemp(dir=target.parent)
            try:
                with os.fdopen(fd, 'wb') as out, archive.open('rb') as stream:
                    stream.seek(self.offsets[key][name])
                    remaining = members[name]['size_bytes']
                    while remaining:
                        block = stream.read(min(remaining,1024*1024))
                        if not block: raise PoolError('Truncated TAR member')
                        out.write(block); remaining -= len(block)
                if not matches(temporary, members[name]):
                    raise PoolError('TAR member digest mismatch')
                atomic_replace(temporary, target)
            finally:
                Path(temporary).unlink(missing_ok=True)
        self.paths[name] = target
        return target


def upload_shards(directory, repo_id, revision, prefix, *, interrupt_after=None):
    """Publish an experimental transport, immutable assets first, root last.

    An intentional interruption hook supports preflight recovery experiments.
    Existing differences stop; identical assets skip without payload downloads.
    """
    from huggingface_hub import HfApi, CommitOperationAdd
    directory = Path(directory).absolute(); prefix = relative(prefix)
    catalog = checked_json(directory/'transport.json')
    if catalog.get('kind') != 'experimental-case-tar-transport':
        raise PoolError('Not an experimental shard transport')
    assets = [entry[key]['path'] for entry in catalog['shards'] for key in ('archive','locator')]
    assets += ['index.json', 'selection.json', 'transport.json']
    if {p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file()} != set(assets):
        raise PoolError('Undeclared shard transport files')
    for shard in catalog['shards']:
        for key in ('archive','locator'):
            entry = shard[key]
            if not matches(within(directory, entry['path']), entry):
                raise PoolError('Changed local shard asset')
    if not matches(directory/'index.json',catalog['index']):
        raise PoolError('Changed local shard index')
    api = HfApi()
    head = api.repo_info(repo_id, repo_type='dataset', revision=revision).sha
    names = {x.rfilename:x for x in api.repo_info(repo_id,repo_type='dataset',revision=head,files_metadata=True).siblings}
    skipped, uploaded = 0, 0
    for logical in assets:
        name = prefix+'/'+relative(logical); path = within(directory, logical)
        previous = names.get(name)
        if previous is not None:
            if previous.lfs:
                same = previous.lfs.sha256 == digest(path)
            else:
                git = hashlib.sha1(f'blob {path.stat().st_size}\0'.encode())
                with path.open('rb') as stream:
                    for block in iter(lambda:stream.read(1024*1024),b''): git.update(block)
                same = previous.blob_id == git.hexdigest()
            if not same:
                raise PoolError('Remote experimental transport differs: '+name)
            skipped += 1
            continue
        result = api.create_commit(repo_id=repo_id,repo_type='dataset',revision=revision,parent_commit=head,
            operations=[CommitOperationAdd(path_in_repo=name,path_or_fileobj=path)],
            commit_message='Stage immutable preflight transport: '+logical)
        head = result.oid; uploaded += 1
        if interrupt_after is not None and uploaded >= interrupt_after:
            raise InterruptedError('Intentional interruption after committed immutable asset')
    return {'revision': head, 'uploaded_files': uploaded, 'skipped_files': skipped}


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
    if value.get('schema_version') != 3:
        raise PoolError(f'Unknown descriptor version: {name}')
    if descriptors is not None:
        descriptors[name] = path.read_text(encoding='utf-8')
    return value


def item_files(store, prefix, binding, item, descriptors):
    """A case is self-contained: there are no cross-directory data references."""
    if set(item) != {'schema_version', 'case_id', 'origin', 'files', 'input', 'reference', 'example'}:
        raise PoolError('Case descriptor has unsupported fields')
    base = f"pool/cases/{item['case_id']}"
    if binding['path'] != base + '/case.json':
        raise PoolError('Case descriptor must be pool/cases/<case-id>/case.json')
    files = {}
    for logical, entry in item['files'].items():
        relative(logical); check_entry(entry)
        if set(entry) != {'size_bytes', 'sha256'}:
            raise PoolError('File entries cannot redirect to shared or external data')
        if not logical.startswith(('input/', 'reference/')):
            raise PoolError('Only input and declared reference assets belong in a case')
        files[logical] = {**entry, 'source': base + '/' + logical}
    declared = item['input'].get('files', []) + item['reference'].get('files', [])
    if len(declared) != len(set(declared)) or set(declared) != set(files):
        raise PoolError('Case file groups must partition all declared files')
    example = item.get('example')
    if example is not None and (not isinstance(example, str) or example not in item['reference']['files']):
        raise PoolError('Example must bind a declared reference asset')
    return files


def plan(value, store, cases=None, samples=None):
    store = consumer_store(value, store)
    prefix = value['repository']['path']
    result = {'files': {}, 'descriptors': {}, 'incomplete': [], 'overlaps': [], 'public_cases': [], 'scope': {}}
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
            item = bound(store, prefix, selection['case'], result['descriptors'])
            if item.get('case_id') != selection['case_id']:
                raise PoolError('Selection case ID differs from bound descriptor')
            files = item_files(store, prefix, selection['case'], item, result['descriptors'])
            signature = {}
            for kind, group_prefix in (('input', 'input/'), ('reference', 'reference/')):
                group = item.get(kind, {})
                names_in_group = group.get('files')
                if type(group.get('complete')) is not bool or not isinstance(names_in_group, list):
                    raise PoolError(f'Invalid {kind} group')
                if group['complete'] and group_prefix + ('problem.json' if kind == 'input' else 'grading.json') not in names_in_group:
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
                    else:
                        target = f'samples/{name}/reference/{leaf}'
                    add(target, files[logical])
                    if role == 'samples' and logical == item.get('example'):
                        add(f'samples/{name}/output/result.h5', files[logical])
            keys = ['input:' + hashlib.sha256(json.dumps(signature, sort_keys=True).encode()).hexdigest()]
            origin = item.get('origin', {}).get('certificate_identity', {})
            if all(key in origin for key in ('source_id', 'source_md5', 'sample_index')):
                keys.append('trajectory:' + json.dumps({k: origin[k] for k in (
                    'source_id', 'source_md5', 'sample_index')}, sort_keys=True))
            if all(key in origin for key in ('source_repository', 'source_sha256', 'sample_index')):
                # Content identity survives a renamed file or a new Hub commit.
                keys.append('trajectory-sha256:' + json.dumps({k: origin[k] for k in (
                    'source_repository', 'source_sha256', 'sample_index')}, sort_keys=True))
            # The same explicitly selected pool item may be both a public sample
            # and a scored case. Keep every prior identity to catch duplicates
            # within a role, even when a public pair also exists.
            prior = {entry[0]: entry for key in keys for entry in fingerprints.get(key, [])}
            identity = f'{role}/{name}'
            for previous, previous_role, previous_name, previous_selection in prior.values():
                if (previous_role != role and previous_selection == selection):
                    case_name = name if role == 'cases' else previous_name
                    sample_name = name if role == 'samples' else previous_name
                    result['public_cases'].append({'case': case_name, 'sample': sample_name,
                                                   'case_id': selection['case_id']})
                else:
                    result['overlaps'].append([previous, identity])
            for key in keys:
                fingerprints.setdefault(key, []).append((identity, role, name, selection))
    # File/directory collisions must fail before any download or mutation.
    for target in result['files']:
        for parent in PurePosixPath(target).parents:
            if str(parent).casefold() in destinations:
                raise PoolError('Assembly file/directory collision')
    return result


def fetch(value, store, **options):
    store = consumer_store(value, store)
    result = plan(value, store, **options)
    for entry in result['files'].values():
        path = store.get(value['repository']['path'] + '/' + entry['source'])
        if not matches(path, entry):
            raise PoolError(f'Pool payload SHA/size mismatch: {entry["source"]}')
    from caeoj.case_grading import prepare_case
    from caeoj.sdk import load_problem
    with tempfile.TemporaryDirectory(prefix='caeoj-pool-preflight-') as temporary:
        for role, names in result['scope'].items():
            for name in names:
                if any(v.startswith(f'{role}/{name}/') for v in result['incomplete']): continue
                task = Path(temporary)/role/name
                for target, entry in result['files'].items():
                    input_prefix = f'cases/{name}/' if role == 'cases' else f'samples/{name}/input/'
                    reference_prefix = f'reference/{name}/' if role == 'cases' else f'samples/{name}/reference/'
                    for prefix, category in ((input_prefix, 'input'), (reference_prefix, 'reference')):
                        if target.startswith(prefix):
                            destination = task/category/target.removeprefix(prefix)
                            destination.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copyfile(store.get(value['repository']['path']+'/'+entry['source']), destination)
                prepared = prepare_case(load_problem(task/'input/problem.json'), task/'reference/grading.json')
                example_key = f'samples/{name}/output/result.h5'
                if role == 'samples' and example_key in result['files']:
                    from caeoj.sdk import load_result
                    example = store.get(value['repository']['path']+'/'+result['files'][example_key]['source'])
                    arrays = load_result(prepared.problem, example)
                    if prepared.evaluate(arrays)['score'] != 1: raise PoolError('Declared example fails case evaluation')
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
    store = consumer_store(value, store)
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
        if not name.startswith(('cases/', 'reference/', 'samples/')):
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
               'descriptors': desired['descriptors'],
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
            'incomplete': desired['incomplete'], 'overlaps': desired['overlaps'],
            'public_cases': desired['public_cases']}


def verify(task, *, strict=False, samples_only=False):
    """Offline verification derives expectations from SHA-bound receipt descriptors."""
    task = Path(task)
    value = manifest(task/'data-manifest.json')
    errors = []
    public_cases = []
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
                           samples=None)
        public_cases = current['public_cases']
        for name, entry in current['files'].items():
            if not matches(within(task, name), entry):
                errors.append('Local SHA/size mismatch or missing: ' + name)
        from caeoj.case_grading import prepare_case
        from caeoj.sdk import load_problem
        for role in (('samples',) if samples_only else ('cases', 'samples')):
            for name in value[role]:
                if errors or any(v.startswith(f'{role}/{name}/') for v in current['incomplete']): continue
                input_path = task/'cases'/name/'problem.json' if role == 'cases' else task/'samples'/name/'input/problem.json'
                reference_path = task/'reference'/name/'grading.json' if role == 'cases' else task/'samples'/name/'reference/grading.json'
                prepared = prepare_case(load_problem(input_path), reference_path)
                example = task/'samples'/name/'output/result.h5'
                if role == 'samples' and example.is_file():
                    from caeoj.sdk import load_result
                    if prepared.evaluate(load_result(prepared.problem, example))['score'] != 1:
                        raise PoolError('Declared example fails case evaluation')
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
    except (ValueError, RuntimeError, OSError, KeyError, TypeError) as exc:
        errors.append(str(exc))
    if errors and strict:
        raise PoolError('; '.join(errors))
    for error in errors:
        warnings.warn(error, stacklevel=2)
    return {'valid': not errors, 'errors': errors, 'public_cases': public_cases}


def list_cases(value, store, *, offset=0, limit=20):
    """List a bounded page of case bindings without reading numerical payloads."""
    if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 1000:
        raise PoolError('List requires offset >= 0 and limit in 1..1000')
    store = consumer_store(value, store)
    prefix = value['repository']['path']
    index = checked_json(store.get(prefix + '/' + relative(value['pool']['index'])))
    if index.get('schema_version') == 4:
        total = index['case_count']
        def pages():
            skip = offset
            for key, binding in sorted(index['partitions'].items()):
                if skip >= binding['case_count']:
                    skip -= binding['case_count']
                    continue
                entries = sorted(store.partition(key).items())
                yield from entries[skip:]
                skip = 0
    elif index.get('schema_version') == 3:
        total = len(index['cases'])
        def pages():
            yield from sorted(index['cases'].items())[offset:]
    else:
        raise PoolError('Invalid pool index')
    from itertools import islice
    cases = [{'case_id': cid, **{k: entry[k] for k in
             ('sha256', 'input_complete', 'reference_complete')}}
             for cid, entry in islice(pages(), limit)]
    next_offset = offset + len(cases)
    return {'revision': store.revision, 'total': total, 'offset': offset,
            'next_offset': next_offset if next_offset < total else None, 'cases': cases}


def select(value, store, cases, samples, *, allow_incomplete=False):
    store = consumer_store(value, store)
    prefix = value['repository']['path']
    index = checked_json(store.get(prefix + '/' + relative(value['pool']['index'])))
    if index.get('schema_version') not in (3,4):
        raise PoolError('Invalid pool index')
    selected = {**value, 'cases': {}, 'samples': {}}
    for role, choices in (('cases', cases), ('samples', samples)):
        for number, choice in enumerate(choices, 1):
            name, case_id = choice.split('=', 1) if '=' in choice else (f'{number:03d}', choice)
            if '/' in relative(name) or name in selected[role]:
                raise PoolError('Invalid or repeated local selection name')
            entry = store.lookup(case_id) if index['schema_version']==4 else index['cases'].get(case_id)
            if entry is None:
                raise PoolError(f'Unknown pool case ID: {case_id}')
            binding = {k: entry[k] for k in ('path', 'sha256')}
            selected[role][name] = {'case_id': case_id, 'case': binding}
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
    if value.get('schema_version') != 4 or not re.fullmatch(r'caeoj-\d{6}', value.get('task_id', '')):
        raise PoolError('Pack requires a stable task ID and selection version 4')
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
            item = items.setdefault(case_id, {'schema_version': 3, 'case_id': case_id,
                'origin': {'kind': 'prepared-input', 'key': name, 'input_identity_sha256': input_id},
                'files': {}, 'input': {'complete': complete_input(inputs), 'files': []},
                'reference': {'complete': False, 'files': []}, 'example': None})
            certificate_path = source/'reference'/name/'certificate.json' if role == 'cases' else source/'reference/sample-certificates'/name/'certificate.json'
            archived = source/'author/data-evidence'/certificate_path.relative_to(source)
            if archived.is_file():
                certificate_path = archived
            if certificate_path.is_file():
                certificate = checked_json(certificate_path)
                declared = certificate.get('input_files', {})
                if declared and any(key not in inputs or digest(inputs[key]) != checksum
                                    for key, checksum in declared.items()):
                    raise PoolError('Source certificate does not bind this input')
                item['origin']['certificate_identity'] = {key: certificate[key] for key in (
                    'source_id', 'source_md5', 'source_repository', 'source_revision', 'source_file',
                    'source_sha256', 'sample_index', 'contract_sha256', 'tool_sha256') if key in certificate}
            base = f'pool/cases/{case_id}/'
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
            reference_dir = source/'reference'/name if role == 'cases' else directory/'reference'
            refs = inventory(reference_dir)
            from caeoj.case_grading import prepare_case
            from caeoj.sdk import load_problem
            declared = {}
            if 'grading.json' in refs:
                prepared = prepare_case(load_problem(inputs['problem.json']), refs['grading.json'])
                declared = {key: refs[key] for key in prepared.evidence['assets']}
                item['reference']['complete'] = True
            for logical, path in declared.items():
                key = 'reference/' + logical
                entry = identity(path)
                if key in item['files'] and item['files'][key] != entry:
                    raise PoolError(f'Different grading assets for identical input: {name}')
                item['files'][key] = put(path, base + key)
                if key not in item['reference']['files']: item['reference']['files'].append(key)
            example = directory/'output/result.h5' if role == 'samples' else None
            if example is not None and example.is_file():
                from caeoj.sdk import load_result
                load_result(load_problem(inputs['problem.json']), example)
                # Reuse an identical reference; sparse references stay separate.
                existing = next((key for key in item['reference']['files']
                                 if item['files'][key] == identity(example)), None)
                key = existing or 'reference/example.h5'
                if not existing:
                    item['files'][key] = put(example, base + key)
                    item['reference']['files'].append(key)
                consumed.add(example.relative_to(source).as_posix())
                item['example'] = key
            choice = {'case_id': case_id}
            selections[role][name] = choice
    if not items:
        raise PoolError('No case/sample inputs found')
    index = {'schema_version': 3, 'cases': {}}
    for case_id, item in items.items():
        name = f'pool/cases/{case_id}/case.json'
        write_json(within(repo, prefix + '/' + name), item)
        binding = {'path': name, 'sha256': digest(within(repo, prefix + '/' + name))}
        index['cases'][case_id] = {**binding, 'input_complete': item['input']['complete'],
                                  'reference_complete': item['reference']['complete']}
        for group in selections.values():
            for choice in group.values():
                if choice['case_id'] == case_id:
                    choice['case'] = binding
    selected = {k: value[k] for k in ('schema_version', 'task_id', 'repository')}
    selected.update(pool={'index': 'pool/index.json'}, **selections)
    # Keep non-consumer records outside the upload tree, for author review.
    evidence = output/'evidence'
    for directory in ('reference', 'samples'):
        for logical, path in inventory(source/directory).items():
            target = directory + '/' + logical
            if target not in consumed:
                saved = within(evidence, target)
                saved.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, saved)
    archived = source/'author/data-evidence'
    if archived.exists():
        for logical, path in inventory(archived).items():
            saved = within(evidence, logical)
            if saved.exists() and identity(saved) != identity(path):
                raise PoolError('Conflicting author evidence: ' + logical)
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, saved)
    write_json(within(repo, prefix + '/pool/index.json'), index)
    # Verify the complete staging tree before advertising a usable selection.
    fetch(selected, LocalStore(repo))
    write_json(output/'selection.json', selected)
    return {'bundle': str(output), 'selection': str(output/'selection.json'), 'cases': len(items), 'evidence': str(evidence)}


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
    for number, (case_id, binding) in enumerate(index.get('cases', {}).items()):
        all_items['cases'][str(number)] = {'case_id': case_id, 'case': binding}
        item = bound(store, prefix, binding, descriptors)
        if (binding.get('input_complete') != item['input']['complete']
                or binding.get('reference_complete') != item['reference']['complete']):
            raise PoolError('Index completeness differs from the item descriptor')
        # Verify every case payload, including cases outside the default selection.
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
    if (Path(bundle)/'transport.json').is_file():
        from .data_pool_shards import publish
        return publish(bundle, revision=revision, update=update)
    from huggingface_hub import HfApi, CommitOperationAdd
    value, local, index = validate_bundle(bundle)
    repo = value['repository']; prefix = repo['path']
    remote = HubStore(repo['repo_id'], revision)
    api = HfApi()
    names = set(api.list_repo_files(repo['repo_id'], repo_type='dataset', revision=remote.revision))
    index_name = prefix + '/' + value['pool']['index']
    previous = checked_json(remote.get(index_name)) if index_name in names else {'schema_version': 3, 'cases': {}}
    if previous.get('schema_version') != 3:
        raise PoolError('Unsupported remote pool index')
    for case_id, entry in index['cases'].items():
        if case_id in previous['cases'] and previous['cases'][case_id] != entry and not update:
            raise PoolError('Remote item changed; review and use --update: ' + case_id)
    merged = {'schema_version': 3, 'cases': {**previous['cases'], **index['cases']}}
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
    all_items = {**value, 'cases': {str(n): {'case_id': cid, 'case': b}
                 for n, (cid, b) in enumerate(index['cases'].items())}, 'samples': {}}
    fetch(all_items, verified)
    return {'revision': commit.oid, 'uploaded_files': len(operations)}
