"""Configure stock Elmer KE + Flow + Heat for steady thermal RANS.

Native standard k-epsilon, no-slip k=0/epsilon wall treatment, Pr_t=.85.
Friction Heat uses the native effective viscosity (eddy heating closure).
Outputs remain unvalidated candidates, not certified reference accuracy.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import xml.etree.ElementTree as ET

import h5py
import numpy as np
from scipy.spatial import cKDTree

import native_lowmach as base
from native_closed_cavity import SOCKET, save, put, digest
from native_gas_film import IMAGE, COMMIT
from titan_resources import reservation


def prepare(job, e):
    transient = e['detailed_spec']['analysis_kind'] == 'transient'
    k0, length0 = .001, .05
    nonuniform = False
    if transient:
        k0 = e['detailed_spec']['initial']['turbulent_kinetic_energy']['expression']
        length0 = e['detailed_spec']['initial']['turbulence_length_scale']['expression']
        nonuniform = not (isinstance(k0, (int, float)) and isinstance(length0, (int, float)))
        if nonuniform: k0, length0 = .001, .05  # Replaced by native read-only procedures below.
        assert k0 > 0 and length0 > 0
        assert min(e['detailed_spec']['output_times_s']) > 0
    data = base.prepare(job, e)
    p = job/'native/case.sif'; s = p.read_text()
    solver = '''Solver 4
 Equation = Kepsilon
 Procedure = "KESolver" "KESolver"
 Stabilization Method = String Bubbles
 Nonlinear System Max Iterations = 1
 Nonlinear System Convergence Tolerance = 1e-8
 Nonlinear System Relaxation Factor = 0.5
 Linear System Solver = Iterative
 Linear System Iterative Method = BiCGStab
 Linear System Preconditioning = ILU1
 Linear System Max Iterations = 1000
 Linear System Convergence Tolerance = 1e-10
 Steady State Convergence Tolerance = 1e-8
End
'''
    s = s.replace('Equation 1\n', solver+'Equation 1\n', 1)
    s = s.replace('Active Solvers(3) = 1 2 3', 'Active Solvers(4) = 4 1 2 3')
    s = s.replace('Material 1\n', '''Material 1
 Viscosity Model = String ke
 Heat Conductivity Model = String ke
 KE Model = String standard
 KE Cmu = Real 0.09
 KE SigmaK = Real 1
 KE SigmaE = Real 1.3
 KE C1 = Real 1.44
 KE C2 = Real 1.92
 KE Clip = Real 1e-12
 Turbulent Prandtl Number = Real 0.85
''', 1)
    eps = .09**.75 * k0**1.5/length0
    s = s.replace('Initial Condition 1\n', f'Initial Condition 1\nKinetic Energy = Real {k0:.17g}\nKinetic Dissipation = Real {eps:.17g}\n', 1)
    pairs = base.boundary_groups(e['detailed_spec'], data[0])[-1]
    for i in range(len(pairs)):
        s = s.replace(f'Boundary Condition {i+1}\n', f'Boundary Condition {i+1}\nNoslip Wall BC = Logical True\n', 1)
    if nonuniform:
        from native_initial_ke import apply
        s = apply(job, e, data, s)
    put(p, s)
    save(job/'native-closure.json', {'model': 'standard k-epsilon', 'source_commit': COMMIT, 'source_paths': ['fem/src/modules/KESolver.F90', 'fem/src/modules/MaterialModels.F90', 'fem/tests/Step_ke/Step_ke.sif'], 'Pr_t': .85, 'near_wall': 'native Noslip Wall BC; k=0 and native EpsilonWall', 'clip_floor': 1e-12, 'dissipation_closure': 'Native Friction Heat with effective viscosity; modeled Reynolds stress work converted through eddy viscosity, not a separately transported epsilon heat source.', 'pressure': 'native modified pressure minus 2*rho*k/3 then volume-mean-zero static gauge', 'initialization': {'kind': ('physical P0 initial state projected to native P1; see initial-ke-mapping.json' if nonuniform else 'physical constant URANS initial state') if transient else 'steady iteration seed, not a physical initial state', 'k': k0, 'length': length0, 'epsilon': eps, 'initial_reynolds_stress': '2*k/3*I; zero initial mean strain'}, 'numerical_validation': False})
    return data


def convert(job, e, data):
    result = base.convert(job, e, data)
    m = data[0]; x = m['x']; c = m['c']; d = x.shape[1]
    files = sorted((job/'native').rglob('solution*.vtu'))
    transient = e['detailed_spec']['analysis_kind'] == 'transient'
    end_time = (e['detailed_spec']['time_interval_s'] or [0, 1])[1]
    corrections = []
    for time_value in e['detailed_spec']['output_times_s']:
        file = files[round(time_value/end_time*1000)-1] if transient else files[-1]
        tree = ET.parse(file); pos = np.fromstring(tree.find('.//Points/DataArray').text, sep=' ').reshape(-1, 3)[:, :d]
        dist, order = cKDTree(pos).query(x)
        assert dist.max() < max(e['detailed_spec']['geometry']['bounding_lengths'])*1e-7
        arrays = {a.get('Name').lower(): np.fromstring(a.text, sep=' ').reshape(len(x), -1)[order] for a in tree.findall('.//PointData/DataArray')}
        assert 'kinetic energy' in arrays, sorted(arrays)
        k = arrays['kinetic energy'][c].mean(axis=1)
        assert np.isfinite(k).all()
        corrections.append(2*e['detailed_spec']['parameters']['density']['value']*k/3)
    with h5py.File(job/'reference/reference.h5', 'r+') as f:
        p = f['pressure'][...] - np.array(corrections)
        p -= np.sum(p[:, :, 0]*m['volume'], axis=1)[:, None, None]/np.sum(m['volume'])
        f['pressure'][...] = p
    if transient:
        problem_path = job/'input/problem.json'; problem = json.loads(problem_path.read_text())
        with h5py.File(job/'input/input.h5', 'r+') as f:
            for q, unit in [('turbulent_kinetic_energy', 'm2/s2'), ('turbulence_length_scale', 'm')]:
                key = 'initial_'+q
                if (job/'initial-ke-input.npz').exists():
                    with np.load(job/'initial-ke-input.npz') as stored: f[key] = stored[q][None, :, None]
                else: f[key] = np.full((1, len(c), 1), e['detailed_spec']['initial'][q]['expression'], dtype=float)
                field = dict(problem['fields']['initial_temperature'])
                field.update(array=key, quantity=q, unit=unit)
                problem['fields'][key] = field
                problem['conditions'].append({'role': 'initial', 'variable': q, 'operator': 'assign', 'location': 'domain', 'data': {'value': {'field': key}}})
        save(problem_path, problem)
    result.update(reference_sha256=digest(job/'reference/reference.h5'), native_output_frames=len(files), mapping='Unmodified Elmer standard KE + FlowSolver + HeatSolver; native no-slip KE wall treatment, Pr_t=.85, effective-viscosity Friction Heat. Static pressure subtracts 2*rho*k/3 before volume gauge. Simplex means of native P1 fields. No numerical validation.')
    return result


def run(root, e, g):
    job = root/'cases'/e['design_id']; status = job/'status.json'
    if status.exists(): return json.loads(status.read_text())
    job.mkdir(parents=True); save(job/'design.json', e)
    state = {'design_id': e['design_id'], 'status': 'queued'}; save(status, state)
    name = 'ch02thermalrans-'+hashlib.sha256(e['design_id'].encode()).hexdigest()[:12]+'-'+str(time.time_ns())[-9:]
    try:
        with reservation(root, name):
            state['status'] = 'preparing'; save(status, state); data = prepare(job, e)
            command = ['docker', '--host', SOCKET, 'run', '--name', name, '--network', 'none', '--cpus', '1', '--memory', '768m', '--user', f'{os.getuid()}:{os.getgid()}', '-e', 'OMP_NUM_THREADS=1', '-e', 'OPENBLAS_NUM_THREADS=1', '-v', f'{job.resolve()}:/work', '-w', '/work/native', IMAGE, 'ElmerSolver', 'case.sif']
            save(job/'execution.json', {'producer': 'unmodified Elmer standard KE + FlowSolver + HeatSolver', 'image': IMAGE, 'source_commit': COMMIT, 'source_url': f'https://github.com/ElmerCSC/elmerfem/tree/{COMMIT}/fem/src/modules', 'script_sha256': digest(Path(__file__)), 'conversion_script_sha256': digest(Path(base.__file__)), 'command': command, 'start_unix': time.time(), 'numerical_validation': False})
            state.update(status='running', container=name); save(status, state)
            with (job/'solver.log').open('w') as log: cp = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
            assert cp.returncode == 0, f'Elmer exit {cp.returncode}'
            frames = list((job/'native').rglob('solution*.vtu'))
            if e['detailed_spec']['analysis_kind'] == 'steady' and len(frames) >= 300: state['status'] = 'native_iteration_limit'
            else:
                state.update(convert(job, e, data)); save(job/'reference/grading.json', g); state['status'] = 'unvalidated_candidate'
    except Exception as ex: state.update(status='needs_attention', error=repr(ex))
    state['ended_unix'] = time.time(); save(status, state); return state


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--root', type=Path, required=True); ap.add_argument('--snapshot', type=Path, required=True); ap.add_argument('--workers', type=int, default=40); ap.add_argument('--only'); args = ap.parse_args()
    freeze = json.loads((args.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text()); tasks = []
    for p in args.snapshot.glob('qbank/02-fluid-mechanics/*/thermal-rans-3d/author/chapter02-ten-20261020/design.json'):
        assert digest(p) == freeze['designs'][p.relative_to(args.snapshot).as_posix()]
        r = json.loads(p.read_text())
        for e in r['proposed_cases']:
            if args.only and args.only not in e['design_id']: continue
            tasks.append(({**e, 'task': r['task'], 'model': r['model']}, json.loads((p.parents[1]/'grading-template.json').read_text())))
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=min(args.workers, len(tasks))) as pool:
        states = list(pool.map(run, [args.root]*len(tasks), [e for e, g in tasks], [g for e, g in tasks]))
    save(args.root/'maintenance/thermal-rans-summary.json', states)


if __name__ == '__main__': main()
