"""Loopback-only, read-only SSH/SCP lab for the repository data CLI.

Optional dependency: paramiko>=3.5,<5. Keys, payloads and logs stay in runs/.
This fixture is for local transfer testing, not a production SSH server.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import socket
import subprocess
import sys
import threading
import time

from caeoj_tools import data_lock, data_pool as pool


PROJECT = Path(__file__).resolve().parents[2]


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def state(work):
    return json.loads((work/'lab.json').read_text(encoding='utf-8'))


def target(work, name, repo_id=None):
    if not name or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in name):
        raise ValueError('Target name must use lowercase letters, digits or hyphens')
    info = state(work)
    source = PROJECT/info['task_path']
    root = work/'targets'/name
    if root.exists():
        raise ValueError(f'Target exists; choose another name: {root}')
    destination = root/info['task_path']
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns(
        'cases', 'reference', 'samples', '__pycache__', '.data-assembly.json', '.data-pool.lock'))
    shutil.copyfile(PROJECT/'pyproject.toml', root/'pyproject.toml')
    if repo_id:
        value = pool.manifest(destination/'data-manifest.json')
        value['repository']['repo_id'] = repo_id
        write_json(destination/'data-manifest.json', value)
        (destination/'data-lock.json').unlink()
    return root


def prepare(work, task, port):
    import paramiko
    if work.exists():
        raise ValueError('Use a new work directory; preparation never overwrites an existing lab')
    matches = list((PROJECT/'qbank').glob(f'*/*/{task}/data-manifest.json'))
    if len(matches) != 1:
        raise ValueError('Select one registered task slug')
    source = matches[0].parent
    value = pool.manifest(matches[0])
    lock = data_lock.read(source, value)
    planned = data_lock.plan(source, value, lock)
    # Validate first; never advertise a mirror made from incomplete local data.
    for name, entry in planned['files'].items():
        if not pool.matches(pool.within(source, name), entry):
            raise ValueError(f'Fetch and strictly verify the task first: {name}')
    pool.verify(source, strict=True)
    work.mkdir(parents=True)
    prefix = value['repository']['path']
    mirror = work/'repository'
    index = {'schema_version': 3, 'cases': {}}
    for name, text in lock['descriptors'].items():
        destination = pool.within(mirror, prefix+'/'+name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(text.encode('utf-8'))
        descriptor = json.loads(text)
        index['cases'][Path(name).parent.name] = {
            'path': name, 'sha256': hashlib.sha256(text.encode()).hexdigest(),
            'input_complete': descriptor['input']['complete'],
            'reference_complete': descriptor['reference']['complete']}
    for name, entry in planned['files'].items():
        destination = pool.within(mirror, prefix+'/'+entry['source'])
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source/name, destination)
    write_json(mirror/prefix/value['pool']['index'], index)
    for name in ('host_key', 'client_key'):
        path = work/name
        paramiko.ECDSAKey.generate(bits=256).write_private_key_file(str(path))
        path.chmod(0o600)
        if os.name == 'nt':
            identity = subprocess.check_output(['whoami'], text=True).strip()
            subprocess.run(['icacls', str(path), '/inheritance:r', '/grant:r', identity+':F'],
                           check=True, capture_output=True, text=True)
    host = paramiko.ECDSAKey.from_private_key_file(str(work/'host_key'))
    (work/'known_hosts').write_text(
        f'[127.0.0.1]:{port} {host.get_name()} {host.get_base64()}\n', encoding='ascii')
    (work/'ssh_config').write_text(
        'Host caeoj-lab\n  HostName 127.0.0.1\n'
        f'  User caeoj-test\n  Port {port}\n'
        f'  IdentityFile "{(work/"client_key").as_posix()}"\n'
        f'  UserKnownHostsFile "{(work/"known_hosts").as_posix()}"\n'
        '  IdentitiesOnly yes\n  BatchMode yes\n  StrictHostKeyChecking yes\n', encoding='utf-8')
    # JSON quoting is valid for these TOML basic strings; paths use forward slashes.
    quoted = lambda path: json.dumps(Path(path).as_posix())
    (work/'sources.toml').write_text(
        'default_source = "local"\n[sources.local]\ntype = "local"\n'
        f'root = {quoted(mirror)}\n'
        '[sources.scp]\ntype = "scp"\nhost = "caeoj-lab"\nroot = "/"\n'
        f'ssh_config = {quoted(work/"ssh_config")}\ntransport = "sftp"\ntimeout = 30\n'
        '[sources.scp-legacy]\ntype = "scp"\nhost = "caeoj-lab"\nroot = "/"\n'
        f'ssh_config = {quoted(work/"ssh_config")}\ntransport = "scp"\ntimeout = 30\n'
        '[sources.hf]\ntype = "hf"\n', encoding='utf-8')
    write_json(work/'lab.json', {'task': task, 'task_path': source.relative_to(PROJECT).as_posix(),
                               'port': port, 'files': len(planned['files']),
                               'size_bytes': sum(e['size_bytes'] for e in planned['files'].values())})
    for name in ('local', 'scp', 'scp-legacy', 'hf'):
        target(work, name)
    return state(work)


def serve(work):
    import paramiko
    info = state(work)
    root = work/'repository'
    host = paramiko.ECDSAKey.from_private_key_file(str(work/'host_key'))
    client_key = paramiko.ECDSAKey.from_private_key_file(str(work/'client_key'))
    log_lock = threading.Lock()
    connections = []

    def log(**event):
        with log_lock, (work/'server-events.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'time': time.time(), **event})+'\n')

    def remote_path(name):
        return pool.within(root, name.lstrip('/'))

    class ReadOnly(paramiko.SFTPServerInterface):
        def stat(self, name):
            try:
                return paramiko.SFTPAttributes.from_stat(remote_path(name).stat())
            except (OSError, ValueError):
                return paramiko.SFTP_NO_SUCH_FILE

        lstat = stat

        def open(self, name, flags, attr):
            if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
                return paramiko.SFTP_PERMISSION_DENIED
            try:
                handle = paramiko.SFTPHandle(flags)
                handle.readfile = remote_path(name).open('rb')
                log(protocol='sftp', path=name, event='open')
                return handle
            except (OSError, ValueError):
                return paramiko.SFTP_NO_SUCH_FILE

    class Auth(paramiko.ServerInterface):
        def get_allowed_auths(self, username):
            return 'publickey'

        def check_auth_publickey(self, username, key):
            return (paramiko.AUTH_SUCCESSFUL if username == 'caeoj-test' and key == client_key
                    else paramiko.AUTH_FAILED)

        def check_channel_request(self, kind, channel_id):
            return (paramiko.OPEN_SUCCEEDED if kind == 'session'
                    else paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED)

        def check_channel_exec_request(self, channel, command):
            def send():
                try:
                    args = shlex.split(command.decode('utf-8'))
                    if args == ['echo', 'connected']:
                        channel.sendall(b'connected\n')
                    elif args[:2] == ['scp', '-f'] and len(args) == 3:
                        path = remote_path(args[2])
                        if channel.recv(1) != b'\0':
                            return
                        channel.sendall(f'C0644 {path.stat().st_size} {path.name}\n'.encode())
                        if channel.recv(1) != b'\0':
                            return
                        with path.open('rb') as stream:
                            while block := stream.read(1024*1024):
                                channel.sendall(block)
                        channel.sendall(b'\0')
                        channel.recv(1)
                        log(protocol='scp', path=args[2], event='read')
                    elif args and args[0] == 'dd':
                        values = dict(arg.split('=', 1) for arg in args[1:])
                        if set(values) != {'if', 'bs', 'skip'} or int(values['bs']) != 1024*1024 or int(values['skip']) < 0:
                            raise ValueError('Unsupported dd arguments')
                        offset = int(values['bs']) * int(values['skip'])
                        with remote_path(values['if']).open('rb') as stream:
                            stream.seek(offset)
                            while block := stream.read(1024*1024):
                                channel.sendall(block)
                        log(protocol='ssh-dd', path=values['if'], offset=offset, event='read')
                    else:
                        raise ValueError('This test server does not provide a shell')
                    channel.send_exit_status(0)
                except Exception as exc:
                    log(event='error', error=type(exc).__name__)
                    try:
                        channel.send_exit_status(1)
                    except OSError:
                        pass
                finally:
                    channel.close()
            threading.Thread(target=send, daemon=True).start()
            return True

    listener = socket.socket()
    listener.bind(('127.0.0.1', info['port']))
    listener.listen(16)
    listener.settimeout(0.5)
    write_json(work/'server.json', {'pid': os.getpid(), 'host': '127.0.0.1', 'port': info['port']})
    print(f'Read-only test SSH server listening on 127.0.0.1:{info["port"]}', flush=True)
    try:
        while True:
            try:
                client, _ = listener.accept()
            except socket.timeout:
                connections[:] = [connection for connection in connections if connection.is_active()]
                continue
            connection = paramiko.Transport(client)
            connection.add_server_key(host)
            connection.set_subsystem_handler('sftp', paramiko.SFTPServer, ReadOnly)
            connections.append(connection)
            try:
                connection.start_server(server=Auth())
            except (paramiko.SSHException, EOFError, OSError):
                connection.close()
    except KeyboardInterrupt:
        pass
    finally:
        listener.close()
        for connection in connections:
            connection.close()


def test(work, names):
    info = state(work)
    results = []

    def call(name, *args, expected=0):
        root = work/'targets'/name
        command = [sys.executable, '-m', 'caeoj', 'data', *args, '--task', info['task'],
                   '--root', str(root), '--config', str(work/'sources.toml'),
                   '--cache-dir', str(root/'.caeoj/cache')]
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', timeout=180)
        number = len(list((work/'logs').glob('*.stdout.json'))) + 1
        prefix = work/'logs'/f'{number:02d}-{name}-{args[0]}'
        prefix.parent.mkdir(exist_ok=True)
        prefix.with_suffix('.stdout.json').write_text(result.stdout, encoding='utf-8')
        prefix.with_suffix('.stderr.txt').write_text(result.stderr, encoding='utf-8')
        if result.returncode != expected:
            raise RuntimeError(f'{name}: expected exit {expected}, got {result.returncode}: {result.stdout} {result.stderr}')
        return json.loads(result.stdout)

    for name in names:
        root = work/'targets'/name
        initial = call(name, 'list')['tasks'][0]
        if initial['present_files'] or (root/'.caeoj/cache').exists():
            raise ValueError(f'{name}: choose a fresh lab to measure a cold transfer')
        first = call(name, 'fetch', '--source', name)['tasks'][0]
        if first['downloaded_files'] <= 0 or not first['complete']:
            raise AssertionError(f'{name}: cold transfer did not fetch complete data')
        call(name, 'verify', '--strict')
        again = call(name, 'fetch', '--source', name)['tasks'][0]
        if again['downloaded_files'] != 0 or again['changed']:
            raise AssertionError(f'{name}: repeat download was not reused')
        task = root/info['task_path']
        value = pool.manifest(task/'data-manifest.json')
        planned = data_lock.plan(task, value, data_lock.read(task, value))
        filename = next(iter(planned['files']))
        damaged = task/filename
        damaged.write_bytes(damaged.read_bytes()+b'\ncorruption probe\n')
        call(name, 'verify', '--strict', expected=2)
        # Explicitly authorized repair is restricted to this generated lab target.
        repaired = call(name, 'fetch', '--source', name, '--update')['tasks'][0]
        call(name, 'verify', '--strict')
        results.append({'source': name, 'cold_downloaded_files': first['downloaded_files'],
                        'installed_files': initial['files'], 'size_bytes': initial['size_bytes'],
                        'repeat_downloaded_files': again['downloaded_files'], 'repeat_changed': again['changed'],
                        'corruption_detected': True, 'repaired': repaired['complete'],
                        'repair_downloaded_files': repaired['downloaded_files']})
    path = work/'results.json'
    existing = json.loads(path.read_text()) if path.exists() else []
    write_json(path, existing+results)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir', type=Path, default=PROJECT/'runs/data-lab')
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('prepare')
    p.add_argument('--task', default='smoke-test')
    p.add_argument('--port', type=int, default=22222)
    commands.add_parser('serve')
    p = commands.add_parser('test')
    p.add_argument('--sources', nargs='+', choices=['local', 'scp', 'scp-legacy', 'hf'],
                   default=['local', 'scp', 'scp-legacy'])
    p = commands.add_parser('target')
    p.add_argument('--name', required=True)
    p.add_argument('--hf-repo')
    args = parser.parse_args()
    work = args.work_dir.resolve()
    if args.command == 'prepare':
        result = prepare(work, args.task, args.port)
    elif args.command == 'serve':
        serve(work)
        return
    elif args.command == 'target':
        result = str(target(work, args.name, args.hf_repo))
    else:
        result = test(work, args.sources)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
