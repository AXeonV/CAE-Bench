"""Reuse author data utilities; task definitions and outputs stay separate."""
from pathlib import Path
import sys
import argparse
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent/'navier-stokes-steady/author'))
from generate import generate

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=ROOT);ap.add_argument('--case',action='append')
    args=ap.parse_args();print('Generated',generate(args.output,True,args.case),'transient cases')
