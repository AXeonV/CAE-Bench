"""Wait for fixed controller identities, then collect storage/hash inventory.

Finite postprocessing only. No numerical verification or solver restart.
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from titan_resources import identity
from native_closed_cavity import save


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--controllers',nargs='+',required=True);ap.add_argument('--max-hours',type=float,default=24);args=ap.parse_args();targets=[]
    for name in args.controllers:
        p=args.root/'maintenance'/name
        if p.exists():
            j=json.loads(p.read_text());targets.append({'path':str(p),'pid':j['pid'],'starttime':j['starttime']})
    deadline=time.monotonic()+args.max_hours*3600
    while time.monotonic()<deadline:
        alive=[j for j in targets if identity(j['pid'])==str(j['starttime'])]
        if not alive:break
        time.sleep(60)
    else:alive=[j for j in targets if identity(j['pid'])==str(j['starttime'])]
    save(args.root/'maintenance/finalizer-observation.json',{'at_unix':time.time(),'tracked':targets,'still_active':alive,'reason':'bounded_wait_expired' if alive else 'fixed_controllers_ended','completion_claim':'No overall completion claim; inventory includes unsolved, held and unconverted cases.'})
    subprocess.run([sys.executable,str(Path(__file__).with_name('execution_report.py')),'--root',str(args.root),'--snapshot',str(args.snapshot)],check=True)


if __name__=='__main__':main()
