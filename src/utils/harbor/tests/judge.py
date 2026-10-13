"""Harbor adapter: execute unprivileged submissions, then use caeoj grading."""
import json
import os
from pathlib import Path
import signal
import shutil
import stat
import subprocess
import tempfile
import time

from caeoj.grading import grade_files
from caeoj.grading_policy import load_policy, validate_policy, policy_hash, legacy_policy
from caeoj.sdk import load_problem, load_result

TESTS = Path('/tests')
LOGS = Path('/logs/verifier')
SUBMISSION = Path('/app/submission')


def output_limit(config):
    limit = config.get('max_output_bytes', 128 * 1024**2)
    if type(limit) is not int or limit <= 0:
        raise ValueError('max_output_bytes must be a positive integer')
    return limit


def output_within_limit(path, limit):
    info = path.lstat()
    return stat.S_ISREG(info.st_mode) and info.st_size <= limit


def freeze_submission():
    """Reject links and remove solver write permissions before execution."""
    if not SUBMISSION.is_dir() or SUBMISSION.is_symlink():
        raise ValueError('Missing regular submission directory')
    for path in [SUBMISSION, *SUBMISSION.rglob('*')]:
        mode = path.lstat().st_mode
        if not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
            raise ValueError('Submission contains a link or special file')
        os.chown(path, 0, 0)
        path.chmod(0o755 if stat.S_ISDIR(mode) else 0o644)
    return (SUBMISSION / 'solve.py').is_file()


def execute(directory, timeout, logs):
    command = ['setpriv', '--reuid=1000', '--regid=1000', '--clear-groups',
               '--no-new-privs', 'python', str(SUBMISSION / 'solve.py'),
               '--input', str(directory / 'input/problem.json'),
               '--output', str(directory / 'result.npz')]
    # Credentials from the agent phase are never passed to solver processes.
    env = {'PATH': '/usr/local/bin:/usr/bin:/bin', 'HOME': '/home/solver',
           'PYTHONDONTWRITEBYTECODE': '1'}
    with (logs / 'stdout.log').open('wb') as out, (logs / 'stderr.log').open('wb') as err:
        process = subprocess.Popen(command, cwd=directory, env=env, stdout=out,
                                   stderr=err, start_new_session=True)
        try:
            code = process.wait(timeout=timeout)
            result = {'score': 0, 'status': 'runtime_error', 'exit_code': code} if code else None
        except subprocess.TimeoutExpired:
            result = {'score': 0, 'status': 'timeout'}
        finally:
            # End descendants as well; no background solver may change later outputs.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
    return result


def save_report(config, results, total, policy_sha256, *, complete=False):
    passed = sum(row['score'] == 1 for row in results)
    report = {'score': passed, 'total_cases': total, 'completed_cases': len(results),
              'complete': complete, 'reward': passed / total, 'cases': results,
              'policy_sha256': policy_sha256}
    if 'atol' in config:
        report['tolerance'] = {'atol': config['atol'], 'rtol': config['rtol']}
    if config.get('stage'):
        report['stage'] = config['stage']
    report['limits'] = {'timeout_seconds': config['timeout_seconds'],
                        'max_output_bytes': output_limit(config)}
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
    paths = sorted((TESTS / 'cases').glob('*/problem.json'))
    if not paths:
        raise ValueError('No judge cases')
    policy = load_policy(TESTS / 'grading.json') if (TESTS / 'grading.json').is_file() else None
    if policy is not None and ('atol' in config or 'rtol' in config):
        raise ValueError('Cannot combine grading.json with legacy tolerances')
    grade_options = {'policy': policy} if policy is not None else {'atol': config['atol'], 'rtol': config['rtol']}
    active_policy = policy if policy is not None else legacy_policy(load_problem(paths[0]), config['atol'], config['rtol'])
    policy_sha256 = policy_hash(active_policy)
    # Validate trusted inputs/references before running any candidate code.
    for path in paths:
        if policy is not None:
            validate_policy(policy, load_problem(path))
        load_result(load_problem(path), TESTS / 'reference' / path.parent.name / 'reference.npz')
    try:
        submitted = freeze_submission()
        submission_error = 'missing_submission' if not submitted else None
    except ValueError:
        submission_error = 'invalid_submission'
    results = []
    for path in paths:
        case = path.parent.name
        logs = LOGS / case
        logs.mkdir()
        if submission_error:
            results.append({'case': case, 'score': 0, 'status': submission_error})
            save_report(config, results, len(paths), policy_sha256)
            continue
        with tempfile.TemporaryDirectory(prefix='caeoj-') as temporary:
            directory = Path(temporary)
            shutil.copytree(path.parent, directory / 'input')
            os.chown(directory, 1000, 1000)
            directory.chmod(0o700)
            started = time.monotonic()
            outcome = execute(directory, config['timeout_seconds'], logs)
            elapsed = time.monotonic() - started
            output = directory / 'result.npz'
            if outcome is None:
                if not output.exists():
                    outcome = {'score': 0, 'status': 'missing_output'}
                elif not output_within_limit(output, maximum_output_bytes):
                    outcome = {'score': 0, 'status': 'invalid_output_file'}
                else:
                    shutil.copyfile(output, logs / 'result.npz')
                    outcome = grade_files(path, logs / 'result.npz',
                                          TESTS / 'reference' / case / 'reference.npz',
                                          **grade_options)
                    if outcome['score'] is None:
                        raise RuntimeError(f'Judge infrastructure error: {case}: {outcome}')
            row = {'case': case, **outcome, 'elapsed_seconds': elapsed}
            results.append(row)
            (logs / 'report.json').write_text(json.dumps(row, indent=2, allow_nan=False) + '\n')
            save_report(config, results, len(paths), policy_sha256)
    report = save_report(config, results, len(paths), policy_sha256, complete=True)
    print(json.dumps({key: value for key, value in report.items() if key != 'cases'}))


if __name__ == '__main__':
    main()
