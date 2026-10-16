"""Execute a solver per case; grade independently and measure resource use."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import psutil

from caeoj.grading import grade_files
from caeoj.grading_policy import load_policy, policy_hash
from caeoj.validation import write_json

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[3]


def run(program, *, time_mode='fixed', selected=None, output=None):
    config = json.loads((ROOT/'judge-config.json').read_text(encoding='utf-8'))
    policy = load_policy(ROOT/'grading.json')
    output = Path(output) if output else PROJECT/'runs/heat-conduction-transient-2d'/time_mode
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in sorted((ROOT/'cases').glob('*/problem.json')):
        name = path.parent.name
        if selected and name not in selected:
            continue
        logs = output/name
        logs.mkdir(exist_ok=True)
        result = logs/'result.h5'
        if result.exists():
            result.unlink()
        command = [sys.executable, str(Path(program).resolve()), '--input', str(path), '--output', str(result)]
        if Path(program).resolve() == (ROOT/'author/baseline.py').resolve():
            command += ['--time-mode', time_mode]
        env = os.environ.copy()
        env.update(PYTHONUTF8='1', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
        start = time.perf_counter()
        peak = 0
        failure = None
        with (logs/'stdout.txt').open('w', encoding='utf-8') as stdout, (logs/'stderr.txt').open('w', encoding='utf-8') as stderr:
            process = subprocess.Popen(command, stdout=stdout, stderr=stderr, env=env)
            monitor = psutil.Process(process.pid)
            while process.poll() is None:
                try:
                    processes = [monitor, *monitor.children(recursive=True)]
                    peak = max(peak, sum(p.memory_info().rss for p in processes if p.is_running()))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                if time.perf_counter()-start > config['timeout_seconds']:
                    failure = 'timeout'
                elif peak > config['memory_mb']*1024**2:
                    failure = 'memory_limit'
                if failure:
                    for child in monitor.children(recursive=True):
                        child.kill()
                    process.kill()
                    break
                time.sleep(0.02)
            process.wait()
        duration = time.perf_counter()-start
        if failure or process.returncode:
            report = {'status': failure or 'runtime_error', 'score': 0}
        else:
            report = grade_files(path, result, ROOT/'reference'/name/'reference.h5',
                                 policy=policy)
        stats_path = logs/'stdout.txt'
        try:
            stats = json.loads(stats_path.read_text(encoding='utf-8'))
        except ValueError:
            stats = None
        rows.append({'case': name, 'wall_seconds': duration, 'peak_rss_mb': peak/1024**2,
                     'solver_stats': stats, **report})
        print(json.dumps({'case': name, 'status': report['status'], 'wall_seconds': round(duration, 3),
                          'peak_rss_mb': round(peak/1024**2, 1)}, ensure_ascii=True), flush=True)
    if not rows:
        raise ValueError('No cases selected')
    score = None if any(row['score'] is None for row in rows) else sum(row['score'] for row in rows)
    summary = {'score': score, 'total_cases': len(rows), 'time_mode': time_mode,
               'max_wall_seconds': max(row['wall_seconds'] for row in rows),
               'max_peak_rss_mb': max(row['peak_rss_mb'] for row in rows),
               'limits': config, 'policy_sha256': policy_hash(policy), 'cases': rows}
    write_json(output/'report.json', summary)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--program', type=Path, default=ROOT/'author/baseline.py')
    parser.add_argument('--time-mode', choices=('fixed', 'adaptive'), default='fixed')
    parser.add_argument('--case', action='append')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = run(args.program, time_mode=args.time_mode, selected=args.case, output=args.output)
    print(json.dumps({key: value for key, value in report.items() if key != 'cases'}, indent=2))
    raise SystemExit(0 if report['score'] == report['total_cases'] else 1)
