"""Manage a local Harbor Viewer owned by this workflow (POSIX hosts only)."""
import argparse
from contextlib import contextmanager
import ipaddress
import json
import math
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import time
from urllib.request import ProxyHandler, build_opener


HTTP = build_opener(ProxyHandler({}))
CHILDREN = {}


def process_identity(pid):
    if type(pid) is not int or pid <= 1:
        return None
    result = subprocess.run(['ps', '-p', str(pid), '-o', 'lstart=', '-o', 'command='],
                            capture_output=True, text=True, timeout=5)
    return result.stdout.strip() if result.returncode == 0 else None


def owned(state):
    return bool(state.get('identity') and process_identity(state.get('pid')) == state['identity'])


def probe(host, port, jobs):
    address = '127.0.0.1' if host == '0.0.0.0' else host
    base = f'http://{address}:{port}'
    try:
        with HTTP.open(base+'/api/health', timeout=1) as response:
            health = json.load(response)
        with HTTP.open(base+'/api/config', timeout=1) as response:
            config = json.load(response)
        with HTTP.open(base+'/', timeout=1) as response:
            html = response.read(1024*1024).lower()
            content_type = response.headers.get('Content-Type', '')
        return (health.get('status') == 'ok' and config.get('mode') == 'jobs' and
                Path(config['folder']).resolve() == jobs and 'text/html' in content_type and b'<html' in html)
    except (OSError, ValueError, KeyError, TypeError):
        return False


def urls(host, port):
    if host != '0.0.0.0':
        return [f'http://{host}:{port}']
    addresses = {'127.0.0.1'}
    try:
        addresses.update(item[4][0] for item in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET))
        # UDP connect only selects a route/local address; no payload is sent.
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as route:
            route.connect(('192.0.2.1', 9))
            addresses.add(route.getsockname()[0])
    except OSError:
        pass
    return [f'http://{ip}:{port}' for ip in sorted(addresses)
            if ipaddress.ip_address(ip).is_loopback or
            (not ipaddress.ip_address(ip).is_unspecified and not ipaddress.ip_address(ip).is_link_local)]


@contextmanager
def locked(directory):
    import fcntl
    directory.mkdir(parents=True, exist_ok=True)
    with (directory/'viewer.lock').open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def snapshot(state):
    identity = process_identity(state.get('pid'))
    alive = bool(state.get('identity') and identity == state['identity'])
    ready = alive and probe(state['host'], state['port'], Path(state['jobs_dir']))
    return {**state, 'status': 'ready' if ready else 'not_ready' if alive else 'stale' if identity else 'stopped',
            'urls': urls(state['host'], state['port']) if ready else []}


def terminate(state):
    if not owned(state):
        return
    if os.getpgid(state['pid']) == state['pid']:
        os.killpg(state['pid'], signal.SIGTERM)
    else:
        os.kill(state['pid'], signal.SIGTERM)
    child = CHILDREN.pop(state['pid'], None)
    if child is not None:
        child.wait(timeout=5)
    deadline = time.monotonic()+5
    while owned(state) and time.monotonic() < deadline:
        time.sleep(.1)


def manage(action, jobs, directory, host='0.0.0.0', port=8080, harbor='harbor', timeout=30):
    if os.name != 'posix':
        raise ValueError('Use native process management on this platform; helper supports POSIX only')
    if not 1 <= port <= 65535 or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('Port must be 1..65535 and startup timeout positive')
    # This helper promises IPv4 local/LAN URLs; fail clearly for unsupported hosts.
    ipaddress.IPv4Address(host)
    jobs = Path(jobs).resolve(); directory = Path(directory).resolve()
    jobs.mkdir(parents=True, exist_ok=True)
    path = directory/f'viewer-{port}.json'
    with locked(directory):
        state = json.loads(path.read_text()) if path.exists() else None
        if state and (state['jobs_dir'] != str(jobs) or state['host'] != host):
            raise ValueError(f'Existing state belongs to another directory or binding: {path}')
        if action == 'status':
            return snapshot(state) if state else {'status':'not_started','state_file':str(path),'urls':[]}
        if action == 'stop':
            if state:
                terminate(state)
                return snapshot(state)
            return {'status':'not_started','state_file':str(path),'urls':[]}
        if state and owned(state):
            result = snapshot(state)
            if result['status'] != 'ready':
                raise ValueError(f'Owned Viewer is running but not ready; inspect {state["log"]}')
            return {**result, 'reused':True}
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            try:
                listener.bind((host,port))
            except OSError as exc:
                raise ValueError(f'Port {port} is unavailable; do not kill its owner or silently change port') from exc
        executable = shutil.which(harbor)
        if not executable:
            raise ValueError(f'Harbor executable not found: {harbor}')
        command = [executable, 'view', str(jobs), '--jobs', '--host', host, '--port', str(port)]
        log = directory/f'viewer-{port}.log'
        with log.open('ab') as output:
            child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output,
                                     stderr=subprocess.STDOUT, start_new_session=True)
        CHILDREN[child.pid] = child
        state = {'pid':child.pid,'identity':process_identity(child.pid),'command':command,
                 'jobs_dir':str(jobs),'host':host,'port':port,'log':str(log),'state_file':str(path)}
        if not state['identity']:
            child.terminate(); child.wait(timeout=5)
            raise ValueError(f'Viewer exited before process identity could be recorded; inspect {log}')
        pending = path.with_suffix('.tmp')
        pending.write_text(json.dumps(state,indent=2)+'\n'); pending.replace(path)
        deadline = time.monotonic()+timeout
        while child.poll() is None and time.monotonic() < deadline:
            if probe(host,port,jobs):
                # The shebang interpreter can replace its startup argv after Popen.
                # Capture ownership only after the actual Viewer is serving.
                state['identity'] = process_identity(child.pid)
                pending.write_text(json.dumps(state,indent=2)+'\n'); pending.replace(path)
                result = snapshot(state)
                if result['status'] == 'ready':
                    return {**result,'reused':False}
            time.sleep(.2)
        if child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        CHILDREN.pop(child.pid, None)
        raise ValueError(f'Viewer did not provide the expected jobs API and HTML page; inspect {log}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['start','status','stop'])
    parser.add_argument('--jobs-dir',type=Path,required=True)
    parser.add_argument('--state-dir',type=Path)
    parser.add_argument('--host',default='0.0.0.0')
    parser.add_argument('--port',type=int,default=8080)
    parser.add_argument('--harbor',default='harbor')
    parser.add_argument('--timeout',type=float,default=30)
    args = parser.parse_args()
    try:
        result = manage(args.action,args.jobs_dir,args.state_dir or args.jobs_dir.resolve().parent/'monitor',
                        args.host,args.port,args.harbor,args.timeout)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0 if result['status'] in ('ready','stopped','not_started') else 1
    except (OSError,ValueError,subprocess.SubprocessError) as exc:
        print(json.dumps({'status':'error','message':str(exc)},ensure_ascii=False))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
