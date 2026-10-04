"""Harbor adapter: execute unprivileged submissions, then use caeoj grading."""
import json
import os
from pathlib import Path
import signal
import shutil
import stat
import subprocess
import tempfile

from caeoj.grading import grade_files
from caeoj.sdk import load_problem, load_result

TESTS = Path('/tests')
LOGS = Path('/logs/verifier')
SUBMISSION = Path('/app/submission')


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
           'PYTHONDONTWRITEBYTECODE': '1', 'OPENBLAS_NUM_THREADS': '1',
           'OMP_NUM_THREADS': '1'}
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


def main():
    LOGS.mkdir(parents=True, exist_ok=True)
    config = json.loads((TESTS / 'judge-config.json').read_text())
    paths = sorted((TESTS / 'cases').glob('*/problem.json'))
    if not paths:
        raise ValueError('No judge cases')
    # Validate trusted inputs/references before running any candidate code.
    for path in paths:
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
            continue
        with tempfile.TemporaryDirectory(prefix='caeoj-') as temporary:
            directory = Path(temporary)
            shutil.copytree(path.parent, directory / 'input')
            os.chown(directory, 1000, 1000)
            directory.chmod(0o700)
            outcome = execute(directory, config['timeout_seconds'], logs)
            output = directory / 'result.npz'
            if outcome is None:
                if not output.exists():
                    outcome = {'score': 0, 'status': 'missing_output'}
                elif not stat.S_ISREG(output.lstat().st_mode) or output.stat().st_size > 128 * 1024**2:
                    outcome = {'score': 0, 'status': 'invalid_output_file'}
                else:
                    shutil.copyfile(output, logs / 'result.npz')
                    outcome = grade_files(path, logs / 'result.npz',
                                          TESTS / 'reference' / case / 'reference.npz',
                                          atol=config['atol'], rtol=config['rtol'])
                    if outcome['score'] is None:
                        raise RuntimeError(f'Judge infrastructure error: {case}: {outcome}')
            results.append({'case': case, **outcome})
    passed = sum(row['score'] == 1 for row in results)
    report = {'score': passed, 'total_cases': len(results),
              'reward': passed / len(results), 'cases': results,
              'tolerance': {'atol': config['atol'], 'rtol': config['rtol']}}
    (LOGS / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    (LOGS / 'reward.txt').write_text(str(report['reward']) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'cases'}))


if __name__ == '__main__':
    main()
