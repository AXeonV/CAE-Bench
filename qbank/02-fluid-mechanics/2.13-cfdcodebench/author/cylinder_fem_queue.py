"""Bounded local annulus independent-verification queue."""
from pathlib import Path
from catalog import WORK
from local_jobs import run

def main():
    for level,factor in ((0,1),(1,1),(2,1),(2,2)):
        job=WORK/'cylinder-fem'/f'L{level}-dt{factor}'
        args=['--level',level,'--factor',factor,'--output',job/'native.npz']
        if not run(job,Path(__file__).with_name('cylinder_ngsolve.py'),args):return
if __name__=='__main__':main()
