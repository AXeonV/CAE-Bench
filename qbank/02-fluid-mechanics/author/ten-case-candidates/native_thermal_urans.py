"""Finite native Elmer URANS queue; only constant public k/length inputs.

Nonuniform initial state stays pending rather than being replaced by a constant.
Native physical initial velocity is zero, so isotropic modeled initial stress
is compatible with the standard KE eddy-viscosity initialization.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path

from native_closed_cavity import save, digest
from native_thermal_rans import run


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--root', type=Path, required=True); ap.add_argument('--snapshot', type=Path, required=True); ap.add_argument('--workers', type=int, default=40); args = ap.parse_args()
    freeze = json.loads((args.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text()); tasks = []; deferred = []
    for p in args.snapshot.glob('qbank/02-fluid-mechanics/*/thermal-urans-3d/author/chapter02-ten-20261020/design.json'):
        assert digest(p) == freeze['designs'][p.relative_to(args.snapshot).as_posix()]
        r = json.loads(p.read_text())
        for e in r['proposed_cases']:
            initial = e['detailed_spec']['initial']
            if any(not isinstance(initial[q]['expression'], (float, int)) for q in ('turbulent_kinetic_energy', 'turbulence_length_scale')):
                deferred.append(e['design_id']); continue
            tasks.append(({**e, 'task': r['task'], 'model': r['model']}, json.loads((p.parents[1]/'grading-template.json').read_text())))
    assert len(tasks) == 9 and len(deferred) == 1
    with ProcessPoolExecutor(max_workers=min(args.workers, len(tasks))) as pool:
        states = list(pool.map(run, [args.root]*len(tasks), [e for e, g in tasks], [g for e, g in tasks]))
    save(args.root/'maintenance/thermal-urans-summary.json', {'states': states, 'pending_nonuniform_initial_state': deferred, 'numerical_validation': False})


if __name__ == '__main__': main()
