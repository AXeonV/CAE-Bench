"""Rebuild all 126 statement pairs from the checked upstream snapshot."""
from pathlib import Path
import argparse
import subprocess
import sys

from source_snapshot import ROOT, fetch, read_source, source_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch', action='store_true', help='Fetch missing source bytes at fixed revision with SHA256 checks')
    args = parser.parse_args()
    if args.fetch:
        fetch()
    for kind in ['basic', 'advanced']:
        read_source(kind)
    here = Path(__file__).resolve().parent
    for name in ['generate_basic_a.py', 'generate_basic_b.py', 'generate_basic_c.py']:
        subprocess.run([sys.executable, '-X', 'utf8', str(here / name)], cwd=ROOT, check=True)
    subprocess.run([sys.executable, '-X', 'utf8', str(here / 'generate_advanced.py'), '--source', str(source_path('advanced'))], cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
