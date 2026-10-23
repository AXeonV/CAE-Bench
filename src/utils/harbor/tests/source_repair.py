"""Trusted submission backend: replace declared sources and compile as solver UID."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

CONFIG = Path('/tests/source-repair.json')
SUBMISSION = Path('/app/submission')
LOGS = Path('/logs/verifier/build')


class SubmissionError(ValueError):
    def __init__(self, status, message):
        self.status = status
        super().__init__(message)


def compile_source(config, label, timeout, command_override=None):
    build = Path(config['build_directory'])
    command = ['setpriv', '--reuid=1000', '--regid=1000', '--clear-groups', '--no-new-privs',
               'cmake', '--build', str(build), '--target', config['build_target'], '--parallel', '4']
    if command_override:
        command = ['setpriv', '--reuid=1000', '--regid=1000', '--clear-groups', '--no-new-privs', *command_override]
    env = {'PATH': '/usr/local/bin:/usr/bin:/bin', 'HOME': '/home/solver',
           'LD_LIBRARY_PATH': str(build / 'lib')}
    started = time.monotonic()
    status = {'command': command}
    with (LOGS / (label + '-stdout.log')).open('wb') as out, (LOGS / (label + '-stderr.log')).open('wb') as err:
        process = subprocess.Popen(command, env=env, stdout=out, stderr=err, start_new_session=True)
        try:
            code = process.wait(timeout=timeout)
            status.update(exit_code=code, status=('ready' if code == 0 else 'probe_error') if command_override
                          else ('built' if code == 0 else 'build_error'))
        except subprocess.TimeoutExpired:
            status['status'] = 'build_timeout'
        finally:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
    status['elapsed_seconds'] = time.monotonic() - started
    return status


def remove_build_artifacts(config):
    removed = []
    for name in config['rebuild_files']:
        artifact = Path(name)
        if not artifact.is_file() or artifact.is_symlink():
            raise RuntimeError('Trusted rebuild artifact missing or linked: ' + name)
        artifact.unlink()
        removed.append(name)
    return removed


def prepare():
    config = json.loads(CONFIG.read_text())
    expected = {row['submission'] for row in config['replacements']}
    if (not SUBMISSION.is_dir() or SUBMISSION.is_symlink()
            or {p.name for p in SUBMISSION.iterdir()} != expected):
        raise SubmissionError('invalid_submission', 'Submit exactly the declared source files')
    LOGS.mkdir(parents=True, exist_ok=True)
    source_hashes, replacements = {}, []
    for row in config['replacements']:
        path = SUBMISSION / row['submission']
        if not path.is_file() or path.is_symlink() or path.stat().st_size > config['max_source_bytes']:
            raise SubmissionError('invalid_submission', 'Invalid source file')
        os.chown(path, 0, 0)
        path.chmod(0o644)
        data = path.read_bytes()
        source_hashes[row['submission']] = hashlib.sha256(data).hexdigest()
        replacements.append((Path(row['target']), data))
    os.chown(SUBMISSION, 0, 0)
    SUBMISSION.chmod(0o755)
    build = Path(config['build_directory'])
    for path in [build, *build.rglob('*')]:
        if not path.is_symlink():
            os.chown(path, 1000, 1000)
    # Test the pristine trusted build before introducing candidate code. Missing
    # dependencies/targets or a broken baseline are infrastructure failures.
    baseline_removed = remove_build_artifacts(config)
    baseline = compile_source(config, 'baseline', config.get(
        'baseline_timeout_seconds', min(60, config['build_timeout_seconds'])))
    baseline['removed_build_artifacts'] = baseline_removed
    (LOGS / 'baseline-report.json').write_text(json.dumps(baseline, indent=2) + '\n')
    if baseline['status'] != 'built':
        raise RuntimeError('Trusted baseline build failed: ' + baseline['status'])
    if config.get('baseline_probe'):
        probe = compile_source(config, 'baseline-probe', min(60, config['build_timeout_seconds']),
                               command_override=config['baseline_probe'])
        (LOGS / 'baseline-probe-report.json').write_text(json.dumps(probe, indent=2) + '\n')
        if probe['status'] != 'ready':
            raise RuntimeError('Trusted baseline runtime probe failed: ' + probe['status'])
    for target, data in replacements:
        target.write_bytes(data)
        os.utime(target, None)
    removed = remove_build_artifacts(config)
    status = compile_source(config, 'candidate', config['build_timeout_seconds'])
    status['sources_sha256'] = source_hashes
    status['removed_build_artifacts'] = removed
    if status['status'] == 'built':
        status['built_artifacts_sha256'] = {name: hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in removed}
    (LOGS / 'report.json').write_text(json.dumps(status, indent=2) + '\n')
    if status['status'] != 'built':
        raise SubmissionError(status['status'], 'Source compilation failed')
    # The resulting implementation is shared by the cases but immutable to the
    # solver UID. No case can rewrite the library used by a later invocation.
    for path in [build, *build.rglob('*')]:
        if not path.is_symlink():
            executable = bool(path.stat().st_mode & 0o111)
            os.chown(path, 0, 0)
            path.chmod(0o755 if path.is_dir() or executable else 0o644)
    return True


def command(directory):
    config = json.loads(CONFIG.read_text())
    return ['python', config['runner'], '--input', str(directory / 'input/problem.json'),
            '--output', str(directory / 'result.h5')]
