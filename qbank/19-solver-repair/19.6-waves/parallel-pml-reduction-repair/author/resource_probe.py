"""Create a maximum-workload valid input, then measure a real bounded solve."""
import argparse,importlib.util,json,resource,subprocess,time
from pathlib import Path

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--case',type=Path,required=True);p.add_argument('--runner',type=Path,required=True);a=p.parse_args()
    start=time.monotonic();result=subprocess.run(['python',str(a.runner),'--input',str(a.case/'problem.json'),'--output',str(a.case/'result.h5')],capture_output=True,text=True)
    elapsed=time.monotonic()-start;usage=resource.getrusage(resource.RUSAGE_CHILDREN)
    model=json.loads((a.case/'problem.json').read_text())['physics']['model']
    report={'exit_code':result.returncode,'elapsed_seconds':elapsed,'max_child_rss_kib':usage.ru_maxrss,'stdout':result.stdout,'stderr':result.stderr,
            'cpu_max':Path('/sys/fs/cgroup/cpu.max').read_text(),'memory_max':Path('/sys/fs/cgroup/memory.max').read_text(),
            'memory_peak_bytes':int(Path('/sys/fs/cgroup/memory.peak').read_text()),
            'scope':'actual input 6000 elements, 6400 time steps, 4 processes, 2 sources, 8 receivers; '+model+'; UID1000 and network none set by docker caller'}
    (a.case/'resource.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
    if result.returncode:raise SystemExit(result.returncode)
