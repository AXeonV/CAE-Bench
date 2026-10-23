"""Harbor adapter: execute unprivileged submissions, then use caeoj grading."""
import json
import math
import os
from pathlib import Path
import signal
import shutil
import stat
import subprocess
import tempfile
import time
import sys

from caeoj.case_grading import prepare_case
from caeoj.sdk import load_problem

TESTS = Path('/tests')
LOGS = Path('/logs/verifier')
SUBMISSION = Path('/app/submission')
SOURCE_REPAIR = (TESTS / 'source-repair.json').is_file()


def output_limit(config):
    limit = config.get('max_output_bytes', 128 * 1024**2)
    if limit is None:
        # Explicitly unlimited when the statement only bounds logical output
        # size and execution resources. Omission retains the old byte limit.
        return None
    if type(limit) is not int or limit <= 0:
        raise ValueError('max_output_bytes must be a positive integer')
    return limit


def output_within_limit(path, limit):
    info = path.lstat()
    return stat.S_ISREG(info.st_mode) and (limit is None or info.st_size <= limit)


def freeze_submission():
    """Reject links and remove solver write permissions before execution."""
    if SOURCE_REPAIR:
        import source_repair
        return source_repair.prepare()
    if not SUBMISSION.is_dir() or SUBMISSION.is_symlink():
        raise ValueError('Missing regular submission directory')
    for path in [SUBMISSION, *SUBMISSION.rglob('*')]:
        mode = path.lstat().st_mode
        if not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
            raise ValueError('Submission contains a link or special file')
        os.chown(path, 0, 0)
        path.chmod(0o755 if stat.S_ISDIR(mode) or mode & 0o111 else 0o644)
    return (SUBMISSION / 'solve.py').is_file()


def execute(directory, timeout, logs):
    # Keep the canonical submission immutable, but give each invocation its own
    # writable source tree for compiled helpers and caches. No changes survive
    # into the next case.
    if SOURCE_REPAIR:
        import source_repair
        arguments = source_repair.command(directory)
    else:
        working_submission = directory / 'submission'
        shutil.copytree(SUBMISSION, working_submission)
        for path in [working_submission, *working_submission.rglob('*')]:
            os.chown(path, 1000, 1000)
        arguments = ['python', str(working_submission / 'solve.py'),
                     '--input', str(directory / 'input/problem.json'),
                     '--output', str(directory / 'result.h5')]
    command = ['setpriv', '--reuid=1000', '--regid=1000', '--clear-groups',
               '--no-new-privs', *arguments]
    # Credentials from the agent phase are never passed to solver processes.
    env = {'PATH': '/usr/local/bin:/usr/bin:/bin', 'HOME': '/home/solver',
           'PYTHONDONTWRITEBYTECODE': '1'}
    if SOURCE_REPAIR:
        repair = json.loads((TESTS / 'source-repair.json').read_text())
        env['LD_LIBRARY_PATH'] = str(Path(repair['build_directory']) / 'lib')
    with (logs / 'stdout.log').open('wb') as out, (logs / 'stderr.log').open('wb') as err:
        # A separate root supervisor owns only this invocation's descendants.
        # MPI launchers may create sessions, so process groups are insufficient.
        receipt = logs / 'execution.json'
        process = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), '--supervise',
             str(receipt.resolve()), str(timeout), json.dumps(command)],
            cwd=directory, env=env, stdout=out, stderr=err, check=False)
        if process.returncode:
            raise RuntimeError('Solver process supervision failed')
    return json.loads(receipt.read_text())


def supervise(receipt, timeout, command):
    """Linux subreaper: collect escaped sessions as well as ordinary children."""
    import ctypes
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(36, 1, 0, 0, 0):  # PR_SET_CHILD_SUBREAPER
        raise OSError(ctypes.get_errno(), 'Cannot enable child subreaper')
    process = subprocess.Popen(command, start_new_session=True)
    try:
        try:
            code = process.wait(timeout=timeout)
            result = {'score': 0, 'status': 'runtime_error', 'exit_code': code} if code else None
        except subprocess.TimeoutExpired:
            result = {'score': 0, 'status': 'timeout'}
    finally:
        # Kill parents before children to stop further spawning. Orphaned
        # descendants are adopted here even when they called setsid/double-fork.
        def children(pid):
            try:
                return [int(p) for p in Path(f'/proc/{pid}/task/{pid}/children').read_text().split()]
            except FileNotFoundError:
                return []

        cleanup_deadline = time.monotonic() + 5
        while True:
            # Only direct children are signalled. Their PIDs cannot be reused
            # until this supervisor reaps them; deeper descendants are adopted
            # after their parent dies and handled by the next iteration.
            for pid in children(os.getpid()):
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            try:
                while os.waitpid(-1, os.WNOHANG)[0]:
                    pass
            except ChildProcessError:
                break
            if time.monotonic() >= cleanup_deadline:
                remaining = children(os.getpid())
                Path(receipt).write_text(json.dumps({
                    'infrastructure_error': 'Solver descendants could not be reaped',
                    'remaining_pids': remaining, 'cleanup_timeout_seconds': 5}) + '\n')
                raise RuntimeError(f'Solver cleanup exceeded 5 seconds; remaining PIDs: {remaining}')
            time.sleep(.01)
        process.returncode = process.poll()
    Path(receipt).write_text(json.dumps(result) + '\n')


def save_report(config, results, total, evaluation_manifest, public_cases, *, complete=False):
    passed = sum(row['score'] == 1 for row in results)
    report = {'score': passed, 'total_cases': total, 'completed_cases': len(results),
              'complete': complete, 'reward': passed / total, 'cases': results,
              'evaluation_manifest': evaluation_manifest, 'public_cases': public_cases}
    if config.get('stage'):
        report['stage'] = config['stage']
    report['limits'] = {'timeout_seconds': config['timeout_seconds'],
                        'max_output_bytes': output_limit(config),
                        'evaluation_timeout_seconds': config.get('evaluation_timeout_seconds', 60)}
    temporary = LOGS / 'report.json.tmp'
    temporary.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    temporary.replace(LOGS / 'report.json')
    if complete:
        (LOGS / 'reward.txt').write_text(str(report['reward']) + '\n')
    return report


def main():
    LOGS.mkdir(parents=True, exist_ok=True)
    config = json.loads((TESTS / 'judge-config.json').read_text())
    maximum_output_bytes = output_limit(config)
    budget = config.get('evaluation_timeout_seconds',60)
    if type(budget) not in (int,float) or not math.isfinite(budget) or budget <= 0:
        raise ValueError('Invalid evaluation_timeout_seconds')
    paths = sorted((TESTS / 'cases').glob('*/problem.json'))
    if not paths:
        raise ValueError('No judge cases')
    if 'atol' in config or 'rtol' in config:
        raise ValueError('Scoring belongs in grading.json, not judge-config atol/rtol')
    public_cases = json.loads((TESTS/'selection.json').read_text(encoding='utf-8'))['public_cases']
    public_by_case = {item['case']: item['sample'] for item in public_cases}
    evaluation_manifest = {}
    # Reject bad reference/configuration before any candidate process starts.
    for path in paths:
        prepared = prepare_case(load_problem(path), TESTS/'reference'/path.parent.name/'grading.json')
        evaluation_manifest[path.parent.name] = prepared.evidence
    try:
        submitted = freeze_submission()
        submission_error = 'missing_submission' if not submitted else None
    except ValueError as exc:
        submission_error = getattr(exc, 'status', 'invalid_submission')
    results = []
    for path in paths:
        case = path.parent.name
        logs = LOGS / case
        logs.mkdir()
        if submission_error:
            results.append({'case': case, 'score': 0, 'status': submission_error})
            save_report(config, results, len(paths), evaluation_manifest, public_cases)
            continue
        with tempfile.TemporaryDirectory(prefix='caeoj-') as temporary:
            directory = Path(temporary)
            shutil.copytree(path.parent, directory / 'input')
            os.chown(directory, 1000, 1000)
            directory.chmod(0o700)
            started = time.monotonic()
            outcome = execute(directory, config['timeout_seconds'], logs)
            elapsed = time.monotonic() - started
            output = directory / 'result.h5'
            if outcome is None:
                if not output.exists():
                    outcome = {'score': 0, 'status': 'missing_output'}
                elif not output_within_limit(output, maximum_output_bytes):
                    outcome = {'score': 0, 'status': 'invalid_output_file'}
                else:
                    shutil.copyfile(output, logs / 'result.h5')
                    # A managed worker enforces the evaluation budget separately from solver time.
                    evaluation_command = [sys.executable, '-m', 'caeoj', 'grade', '--input', str(path),
                                          '--output', str(logs/'result.h5'), '--grading',
                                          str(TESTS/'reference'/case/'grading.json')]
                    try:
                        execution = subprocess.run(evaluation_command, capture_output=True, text=True,
                                                   timeout=budget, check=False)
                    except subprocess.TimeoutExpired as exc:
                        raise RuntimeError('Evaluation infrastructure timeout: '+case) from exc
                    try: outcome = json.loads(execution.stdout)
                    except ValueError as exc: raise RuntimeError('Invalid evaluation worker report: '+execution.stderr) from exc
                    if outcome.get('evaluation_sha256') != evaluation_manifest[case]['evaluation_sha256']:
                        raise RuntimeError('Evaluation changed after preflight: '+case)
                    if outcome['score'] is None:
                        raise RuntimeError(f'Judge infrastructure error: {case}: {outcome}')
            row = {'case': case, **outcome, 'elapsed_seconds': elapsed}
            if case in public_by_case:
                row['public_sample'] = public_by_case[case]
            results.append(row)
            (logs / 'report.json').write_text(json.dumps(row, indent=2, allow_nan=False) + '\n')
            save_report(config, results, len(paths), evaluation_manifest, public_cases)
    report = save_report(config, results, len(paths), evaluation_manifest, public_cases, complete=True)
    print(json.dumps({key: value for key, value in report.items() if key != 'cases'}))


if __name__ == '__main__':
    if len(sys.argv) == 5 and sys.argv[1] == '--supervise':
        supervise(sys.argv[2], float(sys.argv[3]), json.loads(sys.argv[4]))
    else:
        main()
