"""Locally reproduce pinned authors' programs; no candidate or remote workstation.

Each producer has its own directory. Unmodified source and process evidence are
retained, including failures. These are source reproductions, not certifications.
Run with the scientific WSL Python after fetch_upstream.py.
"""
from __future__ import annotations
import concurrent.futures as cf
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
WORK = ROOT / 'runs/cfdcodebench-local-20261019'
SOURCE = WORK / 'upstream/CFDCodeBench/PDE_Benchmark/solution'

def run(source):
    task = source.stem
    job = WORK / 'replay' / task
    evidence = job / 'process.json'
    if evidence.exists() and json.loads(evidence.read_text()).get('returncode') == 0:
        return json.loads(evidence.read_text())
    path = job / 'PDE_Benchmark/solution' / source.name
    path.parent.mkdir(parents=True, exist_ok=True)
    (job / 'PDE_Benchmark/results/solution').mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, path)
    env = {**os.environ, 'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1',
           'MKL_NUM_THREADS': '1', 'NUMEXPR_NUM_THREADS': '1', 'MPLBACKEND': 'Agg'}
    started = time.time()
    record = {'task': task, 'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
              'started_unix': started, 'python': sys.executable, 'pid': None, 'status': 'running'}
    with (job / 'stdout.log').open('w') as out:
        process = subprocess.Popen([sys.executable, str(path)], cwd=path.parent, env=env,
                                   stdout=out, stderr=subprocess.STDOUT)
        record['pid'] = process.pid
        evidence.write_text(json.dumps(record, indent=2))
        try:
            record['returncode'] = process.wait(timeout=3600)
        except subprocess.TimeoutExpired:
            process.terminate()
            try: process.wait(timeout=10)
            except subprocess.TimeoutExpired: process.kill(); process.wait()
            record['returncode'] = process.returncode
            record['timeout_seconds'] = 3600
    record.update(status='finished', wall_seconds=time.time()-started)
    record['outputs'] = [{'file': str(p.relative_to(job)), 'bytes': p.stat().st_size,
                          'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                         for p in sorted(job.glob('PDE_Benchmark/results/solution/*.npy'))]
    evidence.write_text(json.dumps(record, indent=2))
    print(json.dumps({k: record[k] for k in ('task','returncode','wall_seconds')}), flush=True)
    return record

def main():
    tasks = sorted(SOURCE.glob('*.py'))
    # Start spectral jobs early; keep a bounded two-process local queue.
    tasks.sort(key=lambda p: ('dedalus' not in p.read_text(encoding='utf-8'), p.name))
    with cf.ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(run, tasks))
    (WORK / 'replay-summary.json').write_text(json.dumps(results, indent=2))

if __name__ == '__main__': main()
