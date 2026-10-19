"""Opt-in localhost OpenSSH transport tests; no user server or credentials.

Run with CAEOJ_TEST_SSH=1 and optional paramiko installed in the test environment.
The fixture exposes read-only test files and accepts no shell execution.
"""
import hashlib
import importlib.util
import os
from pathlib import Path
import shlex
import shutil
import socket
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch

from caeoj_tools import data_pool as pool, data_sources


@unittest.skipUnless(os.environ.get('CAEOJ_TEST_SSH') == '1' and shutil.which('sftp') and
                     importlib.util.find_spec('paramiko'), 'opt-in local SSH integration')
class SshIntegrationTests(unittest.TestCase):
    def test_real_sftp_and_legacy_scp_with_resume(self):
        self.check_transfers()

    @unittest.skipUnless(os.name == 'nt', 'Windows process PATH regression')
    def test_windows_native_path_change_does_not_hide_openssh(self):
        import ctypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        get_path = kernel.GetEnvironmentVariableW
        get_path.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint]
        get_path.restype = ctypes.c_uint
        set_path = kernel.SetEnvironmentVariableW
        set_path.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
        set_path.restype = ctypes.c_int
        buffer = ctypes.create_unicode_buffer(32768)
        size = get_path('PATH', buffer, len(buffer))
        self.assertLess(size, len(buffer))
        original = buffer.value if size else None
        self.addCleanup(set_path, 'PATH', original)
        # Native libraries can change Windows PATH without updating os.environ.
        # Exercise real clients with only Python's original search path intact.
        self.assertTrue(set_path('PATH', ''))
        self.check_transfers()

    def check_transfers(self):
        import paramiko
        with tempfile.TemporaryDirectory(prefix='caeoj ssh ') as directory:
            root = Path(directory)
            payload = b'0123456789abcdef' * 100_003
            path = root/'release one/test asset.bin'
            path.parent.mkdir()
            path.write_bytes(payload)
            (path.parent/'test.bin').write_bytes(payload)
            host_key = paramiko.ECDSAKey.generate()
            stop = threading.Event()
            connections = []
            failures = []
            requests = []

            def file_path(remote):
                return pool.within(root, remote.lstrip('/'))

            class ReadOnly(paramiko.SFTPServerInterface):
                def stat(self, remote):
                    try:
                        return paramiko.SFTPAttributes.from_stat(file_path(remote).stat())
                    except OSError:
                        return paramiko.SFTP_NO_SUCH_FILE

                lstat = stat

                def open(self, remote, flags, attr):
                    if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC):
                        return paramiko.SFTP_PERMISSION_DENIED
                    handle = paramiko.SFTPHandle(flags)
                    handle.readfile = file_path(remote).open('rb')
                    return handle

            class Auth(paramiko.ServerInterface):
                def check_auth_none(self, username):
                    return paramiko.AUTH_SUCCESSFUL

                def check_channel_request(self, kind, channel_id):
                    return paramiko.OPEN_SUCCEEDED if kind == 'session' else paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

                def check_channel_exec_request(self, channel, command):
                    requests.append(command)
                    def send():
                        try:
                            args = shlex.split(command.decode())
                            if args[:2] == ['scp', '-f'] and len(args) == 3:
                                data = file_path(args[2]).read_bytes()
                                if channel.recv(1) != b'\0':
                                    return
                                channel.sendall(f'C0644 {len(data)} {Path(args[2]).name}\n'.encode())
                                if channel.recv(1) != b'\0':
                                    return
                                channel.sendall(data+b'\0')
                                channel.recv(1)
                            elif args and args[0] == 'dd':
                                values = dict(item.split('=', 1) for item in args[1:])
                                data = file_path(values['if']).read_bytes()
                                offset = int(values['bs']) * int(values['skip'])
                                channel.sendall(data[offset:])
                            else:
                                channel.send_exit_status(1)
                                return
                            channel.send_exit_status(0)
                        except Exception as exc:
                            failures.append(exc)
                        finally:
                            channel.close()
                    threading.Thread(target=send, daemon=True).start()
                    return True

            listener = socket.socket()
            listener.bind(('127.0.0.1', 0))
            listener.listen(5)
            listener.settimeout(.2)
            port = listener.getsockname()[1]
            known = root/'known_hosts'
            known.write_text(f'[127.0.0.1]:{port} {host_key.get_name()} {host_key.get_base64()}\n')
            config = root/'ssh_config'
            config.write_text(f'Host *\n  User fixture\n  UserKnownHostsFile "{known.as_posix()}"\n')

            def serve():
                while not stop.is_set():
                    try:
                        client, _ = listener.accept()
                    except socket.timeout:
                        continue
                    except OSError:
                        break
                    connection = paramiko.Transport(client)
                    connections.append(connection)
                    connection.add_server_key(host_key)
                    connection.set_subsystem_handler('sftp', paramiko.SFTPServer, ReadOnly)
                    try:
                        connection.start_server(server=Auth())
                    except Exception as exc:
                        failures.append(exc)

            thread = threading.Thread(target=serve, daemon=True)
            thread.start()
            execute = subprocess.run

            def checked_command(*args, **kwargs):
                result = execute(*args, **kwargs)
                self.assertEqual(result.returncode, 0, (result.stderr, requests, failures))
                return result

            instrumentation = patch('caeoj_tools.data_sources.subprocess.run', side_effect=checked_command)
            instrumentation.start()
            try:
                for protocol in ('sftp', 'scp'):
                    backend = data_sources.ScpTransport({'host': '127.0.0.1', 'port': port,
                        'root': '/release one', 'transport': protocol, 'ssh_config': str(config), 'timeout': 15})
                    for filename in ('test.bin', 'test asset.bin'):
                        target = root/(protocol+filename+'.download')
                        backend.retrieve(filename, target)
                        self.assertEqual(hashlib.sha256(target.read_bytes()).digest(), hashlib.sha256(payload).digest())
                        target.write_bytes(payload[:backend.BLOCK+31])
                        backend.retrieve(filename, target)
                        self.assertEqual(target.read_bytes(), payload)
                self.assertEqual(failures, [])
            finally:
                instrumentation.stop()
                stop.set()
                listener.close()
                for connection in connections:
                    connection.close()
                thread.join(3)


if __name__ == '__main__':
    unittest.main()
