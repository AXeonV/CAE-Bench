"""Final original-queue linear failure; reuse the existing guarded executor."""
import argparse
from pathlib import Path
from retry_thermal_statistics_linear import execute

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int,default=1);args=ap.parse_args()
    execute(args.root,args.snapshot,1,'thermal-statistics-remaining-linear-repair-authorization.json','thermal-statistics-remaining-linear-repair-summary.json')
