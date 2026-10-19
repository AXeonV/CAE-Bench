"""Reviewed, offline metadata for one pool selection; contains no payloads."""
from contextlib import contextmanager
import hashlib
from pathlib import Path
import re
import tempfile

from . import data_pool as pool

LOCK = 'data-lock.json'
KINDS = ('cases', 'references', 'samples')


def selection_digest(value):
    return hashlib.sha256(pool.encoded(value)).hexdigest()


def category(target):
    return 'references' if target.startswith('reference/') else target.split('/', 1)[0]


def selected_kinds(kinds=None):
    if not kinds or kinds == ['all']:
        return set(KINDS)
    if set(kinds) - set(KINDS):
        raise pool.PoolError('Choose cases, references, samples, or all')
    return set(kinds)


@contextmanager
def metadata_store(value, lock):
    """Re-use the pool parser against exact SHA-bound descriptor bytes."""
    with tempfile.TemporaryDirectory(prefix='caeoj-metadata-') as directory:
        root = Path(directory)
        prefix = value['repository']['path'] + '/'
        for name, content in lock['descriptors'].items():
            target = pool.within(root, prefix + pool.relative(name))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content.encode('utf-8'))
        store = pool.LocalStore(root)
        store.revision = lock.get('hf_revision') or lock['release']
        yield store


def create(value, store):
    planned = pool.plan(value, store)
    if planned['overlaps']:
        raise pool.PoolError('Cannot publish overlapping case selections')
    descriptors = planned['descriptors']
    release = selection_digest({'selection': selection_digest(value), 'descriptors': descriptors})
    revision = getattr(store, 'revision', '')
    return {'schema_version': 1, 'selection_sha256': selection_digest(value),
            'release': release,
            'status': 'incomplete' if planned['incomplete'] else 'published',
            'hf_revision': revision if re.fullmatch('[0-9a-f]{40}', revision) else None,
            'descriptors': descriptors}


def read(task, value):
    lock = pool.checked_json(pool.within(task, LOCK))
    if set(lock) != {'schema_version', 'selection_sha256', 'release', 'status', 'hf_revision', 'descriptors'}:
        raise pool.PoolError('Invalid data lock fields')
    if lock['schema_version'] != 1 or lock['selection_sha256'] != selection_digest(value):
        raise pool.PoolError('Data selection changed; review and regenerate data-lock.json')
    if lock['hf_revision'] is not None and not re.fullmatch('[0-9a-f]{40}', str(lock['hf_revision'])):
        raise pool.PoolError('HF revision must be a full commit SHA')
    if not isinstance(lock['descriptors'], dict) or any(not isinstance(v, str) for v in lock['descriptors'].values()):
        raise pool.PoolError('Lock descriptors must contain exact JSON text')
    expected = selection_digest({'selection': selection_digest(value), 'descriptors': lock['descriptors']})
    if lock['release'] != expected:
        raise pool.PoolError('Data release digest does not match its metadata')
    with metadata_store(value, lock) as store:
        planned = pool.plan(value, store)
    if lock['status'] != ('incomplete' if planned['incomplete'] else 'published'):
        raise pool.PoolError('Publication status differs from declared completeness')
    if set(planned['descriptors']) != set(lock['descriptors']) or planned['overlaps']:
        raise pool.PoolError('Lock has undeclared descriptors or overlapping selections')
    return lock


def plan(task, value, lock, kinds=None):
    with metadata_store(value, lock) as store:
        result = pool.plan(value, store)
    wanted = selected_kinds(kinds)
    result['files'] = {name: entry for name, entry in result['files'].items() if category(name) in wanted}
    return result
