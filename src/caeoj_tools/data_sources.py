"""Local, HF and SSH/SCP transports behind verified, resumable object caching."""
from contextlib import contextmanager
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import subprocess
import time
import tomllib

from . import data_pool as pool
from .files import atomic_replace


def configuration(path=None):
    path = Path(path or os.environ.get('CAEOJ_DATA_CONFIG', Path.home()/'.config/caeoj/data.toml')).expanduser()
    if not path.exists():
        return {'sources': {'hf': {'type': 'hf'}}, 'default_source': 'hf'}
    with path.open('rb') as stream:
        result = tomllib.load(stream)
    if set(result) - {'default_source', 'cache_dir', 'sources'}:
        raise pool.PoolError('Unknown data configuration fields')
    sources = result.get('sources', {})
    for name, source in sources.items():
        if not re.fullmatch(r'[A-Za-z0-9_.-]+', name) or not isinstance(source, dict):
            raise pool.PoolError('Invalid source name or definition')
        allowed = {'type', 'root'} if source.get('type') == 'local' else (
            {'type', 'host', 'root', 'port', 'transport', 'timeout', 'ssh_config'} if source.get('type') == 'scp' else {'type'})
        if source.get('type') not in ('local', 'hf', 'scp') or set(source) - allowed:
            raise pool.PoolError('Unsupported source fields; credentials belong in SSH/HF configuration')
        if source['type'] in ('local', 'scp') and not isinstance(source.get('root'), str):
            raise pool.PoolError('Local and SCP sources require root')
        if source['type'] == 'local':
            local = Path(source['root']).expanduser()
            source['root'] = str((path.parent/local).resolve() if not local.is_absolute() else local)
        if source.get('ssh_config'):
            ssh_path = Path(source['ssh_config']).expanduser()
            source['ssh_config'] = str((path.parent/ssh_path).resolve() if not ssh_path.is_absolute() else ssh_path)
    if result.get('default_source', 'hf') not in sources:
        raise pool.PoolError('Default source is not configured')
    return result


class LocalTransport:
    def __init__(self, root):
        self.store = pool.LocalStore(Path(root).expanduser())

    def retrieve(self, name, destination):
        shutil.copyfile(self.store.get(name), destination)


class HubTransport:
    def __init__(self, value, revision, cache_dir=None):
        if not re.fullmatch('[0-9a-f]{40}', str(revision)):
            raise pool.PoolError('HF download requires a fixed commit: run caeoj data lock --source hf')
        self.value, self.revision = value, revision
        self.cache_dir = cache_dir

    def retrieve(self, name, destination):
        try:
            from huggingface_hub import hf_hub_download
        except ImportError as exc:
            raise pool.PoolError("Install repository dependencies: pip install -e '.[maint]'") from exc
        try:
            path = hf_hub_download(self.value['repository']['repo_id'], pool.relative(name),
                                   repo_type='dataset', revision=self.revision, cache_dir=self.cache_dir)
        except Exception as exc:
            # Never echo server request headers, signed URLs or tokens.
            raise pool.PoolError(f'HF download failed ({type(exc).__name__}); check access and fixed revision') from exc
        shutil.copyfile(path, destination)


class ScpTransport:
    """Use OpenSSH config/agent and host verification, without shell=True.

    SFTP reget resumes bytes. Legacy SCP uses scp -O for the first attempt;
    retrying a partial file uses ssh+POSIX dd at a completed 1 MiB boundary.
    """
    BLOCK = 1024 * 1024

    def __init__(self, source):
        self.host = source.get('host', '')
        if not re.fullmatch(r'(?:[A-Za-z0-9_.-]+@)?[A-Za-z0-9][A-Za-z0-9_.-]*', self.host):
            raise pool.PoolError('SCP host must be an SSH host alias or user@hostname')
        self.root = source['root']
        if not self.root.startswith('/') or any(c in self.root for c in '\r\n\0*?[]') or '..' in PurePosixPath(self.root).parts:
            raise pool.PoolError('SCP root must be an absolute POSIX path without parent traversal')
        self.port = source.get('port')
        self.timeout = source.get('timeout', 300)
        if self.port is not None and (type(self.port) is not int or not 1 <= self.port <= 65535):
            raise pool.PoolError('Invalid SSH port')
        if type(self.timeout) is not int or self.timeout < 1:
            raise pool.PoolError('Invalid SSH timeout')
        self.transport = source.get('transport', 'sftp')
        self.ssh_config = source.get('ssh_config')
        if self.transport not in ('sftp', 'scp'):
            raise pool.PoolError('SSH transport must be sftp or scp')

    @staticmethod
    def quoted(value):
        # SFTP batch quoting has its own grammar, independent of a shell.
        if any(c in str(value) for c in '\r\n\0'):
            raise pool.PoolError('SFTP paths cannot contain control characters')
        return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"') + '"'

    @staticmethod
    def executable(name):
        # Native libraries may change Windows PATH behind os.environ's back.
        # Resolve via Python's PATH and bypass CreateProcess's native search.
        path = shutil.which(name)
        if path is None:
            raise pool.PoolError(f'OpenSSH client {name} not found; install OpenSSH and add it to PATH')
        return str(Path(path).resolve())

    def retrieve(self, name, destination):
        remote = self.root.rstrip('/') + '/' + pool.relative(name)
        options = ['-oBatchMode=yes', '-oStrictHostKeyChecking=yes', '-oConnectTimeout=30']
        if self.ssh_config:
            options += ['-F', str(Path(self.ssh_config).expanduser())]
        try:
            if self.transport == 'sftp':
                local = Path(destination).absolute().as_posix()
                command = ('reget' if Path(destination).exists() else 'get')
                batch = f'{command} {self.quoted(remote)} {self.quoted(local)}\n'
                port = ['-P', str(self.port)] if self.port is not None else []
                result = subprocess.run([self.executable('sftp'), *port, *options, '-b', '-', self.host],
                                        input=batch, capture_output=True, text=True, timeout=self.timeout)
            elif not Path(destination).exists() and re.fullmatch('[A-Za-z0-9_.-]+', PurePosixPath(remote).name):
                port = ['-P', str(self.port)] if self.port is not None else []
                parent, leaf = remote.rsplit('/', 1)
                # Keep shell quotes out of the basename: legacy scp also uses
                # it as a filename-matching pattern on the receiving client.
                remote_argument = shlex.quote(parent) + '/' + leaf
                result = subprocess.run([self.executable('scp'), '-O', *port, *options,
                                         self.host + ':' + remote_argument, str(destination)],
                                        capture_output=True, timeout=self.timeout)
            else:
                exists = Path(destination).exists()
                offset = Path(destination).stat().st_size // self.BLOCK * self.BLOCK if exists else 0
                # Windows scp rewrites backslashes in remote names. SSH block
                # reads also handle special basenames without weakening scp's
                # strict filename checks or interpolating unquoted paths.
                executable = self.executable('ssh')
                with Path(destination).open('r+b' if exists else 'w+b') as stream:
                    stream.truncate(offset)
                    stream.seek(offset)
                    command = f'dd if={shlex.quote(remote)} bs={self.BLOCK} skip={offset // self.BLOCK}'
                    port = ['-p', str(self.port)] if self.port is not None else []
                    result = subprocess.run([executable, *port, *options, self.host, command],
                                            stdout=stream, stderr=subprocess.PIPE, timeout=self.timeout)
            if result.returncode:
                raise pool.PoolError(f'SSH transfer failed (exit {result.returncode}); check access, known_hosts and server support')
        except subprocess.TimeoutExpired as exc:
            raise pool.PoolError('SSH transfer timed out; partial download is retained') from exc


def transport(source, value, lock, cache=None):
    kind = source.get('type')
    if kind == 'local':
        return LocalTransport(source['root'])
    if kind == 'hf':
        return HubTransport(value, lock.get('hf_revision'), Path(cache)/'hub' if cache else None)
    if kind == 'scp':
        return ScpTransport(source)
    raise pool.PoolError('Unknown source type')


@contextmanager
def object_lock(path):
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise pool.PoolError(f'Cache object is busy; inspect lock before retrying: {path}') from exc
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(str(os.getpid()))
        yield
    finally:
        Path(path).unlink()


class VerifiedStore:
    def __init__(self, value, lock, metadata, planned, backend, cache, task=None, retries=3):
        self.revision = lock.get('hf_revision') or lock['release']
        self.metadata, self.backend = metadata, backend
        self.cache, self.retries = Path(cache).absolute(), retries
        self.entries, self.installed = {}, {}
        self.downloaded = 0
        for target, entry in planned['files'].items():
            name = value['repository']['path'] + '/' + entry['source']
            if name in self.entries and self.entries[name] != entry:
                raise pool.PoolError('Conflicting source identities')
            self.entries[name] = entry
            if task is not None:
                self.installed.setdefault(name, []).append(pool.within(task, target))

    def get(self, name):
        if name not in self.entries:
            return self.metadata.get(name)
        entry = self.entries[name]
        for local in self.installed.get(name, []):
            if pool.matches(local, entry):
                return local
        target = pool.within(self.cache, 'objects/' + entry['sha256'])
        if pool.matches(target, entry):
            return target
        target.parent.mkdir(parents=True, exist_ok=True)
        partial = pool.within(self.cache, 'objects/' + entry['sha256'] + '.part')
        with object_lock(str(target) + '.lock'):
            if pool.matches(target, entry):
                return target
            for attempt in range(self.retries):
                if partial.exists() and partial.stat().st_size >= entry['size_bytes']:
                    if pool.matches(partial, entry):
                        atomic_replace(partial, target)
                        return target
                    partial.unlink()
                try:
                    self.backend.retrieve(name, partial)
                    if not pool.matches(partial, entry):
                        partial.unlink(missing_ok=True)
                        raise pool.PoolError('Downloaded file failed SHA-256/size verification: ' + name)
                    atomic_replace(partial, target)
                    self.downloaded += 1
                    return target
                except (OSError, pool.PoolError):
                    if attempt + 1 == self.retries:
                        raise
                    time.sleep(min(2 ** attempt, 4))
        raise AssertionError('unreachable')
