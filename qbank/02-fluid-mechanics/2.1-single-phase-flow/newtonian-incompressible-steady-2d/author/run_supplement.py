"""Execute independent Lethe runs with bounded process/thread parallelism."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess, sys

root=Path(sys.argv[1]).resolve()
producer=sys.argv[2]
levels=list(map(int,sys.argv[3:])) or [4,8,16]

def run(pair):
    i,n=pair
    return subprocess.run([sys.executable,str(root/'prepare_supplement.py'),str(root/'runs'),
                           '--n',str(n),'--index',str(i),'--solver',producer],check=True).returncode

with ThreadPoolExecutor(max_workers=4) as workers:
    list(workers.map(run,[(i,n) for n in levels for i in range(20)]))
