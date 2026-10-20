"""Bounded serial local NGSolve grid/time convergence jobs."""
import argparse
from pathlib import Path
from catalog import WORK
from local_jobs import run

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--order',type=int,default=2);a=ap.parse_args()
    for index in (18,12):
        for level,factor in ((0,1),(1,1),(2,1),(2,2)):
            job=WORK/('cavity-corners' if a.order==2 else f'cavity-p{a.order}')/f'C{index:02}'/f'L{level}-dt{factor}'
            args=['--order',a.order,'--index',index,'--level',level,'--factor',factor,'--output',job/'native.npz']
            if not run(job,Path(__file__).with_name('cavity_ngsolve.py'),args):return
if __name__=='__main__':main()
