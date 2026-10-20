"""One bounded nonuniform-initial-state URANS run using stock Elmer."""
import argparse
import json
from pathlib import Path
from native_closed_cavity import digest, save
from native_initial_ke import build
from native_thermal_rans import run


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--root', type=Path, required=True); ap.add_argument('--snapshot', type=Path, required=True); ap.add_argument('--workers', type=int, default=1); args = ap.parse_args()
    freeze = json.loads((args.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text())
    p = next(args.snapshot.glob('qbank/02-fluid-mechanics/*/thermal-urans-3d/author/chapter02-ten-20261020/design.json'))
    assert digest(p) == freeze['designs'][p.relative_to(args.snapshot).as_posix()]
    r = json.loads(p.read_text()); e = r['proposed_cases'][9]
    assert e['design_id'] == 'ch02-2-4-2-10-thermal_pulse_or_split'
    build(args.root)
    state = run(args.root, {**e, 'task': r['task'], 'model': r['model']}, json.loads((p.parents[1]/'grading-template.json').read_text()))
    save(args.root/'maintenance/thermal-urans-nonuniform-summary.json', state)


if __name__ == '__main__': main()
