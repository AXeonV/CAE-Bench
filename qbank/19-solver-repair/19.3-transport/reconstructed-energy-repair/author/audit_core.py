"""Independent NumPy evaluation of edge interpolation and thermodynamic definitions.

This audit reads completed references; it is never imported by the driver.
The interpolation is evaluated as a batched affine map, separately from the
upstream C++ SIMD implementation. Stored enthalpy is advanced by its exact
constant-Cp/kinetic-energy increment, including any original stage offset.
"""
from pathlib import Path
import json
import numpy as np
from caeoj.sdk import load_problem, load_result

Q = Path(__file__).resolve().parents[1]


def expected(problem):
    a = problem.arrays
    p = {k: v['value'] for k, v in problem.manifest['physics']['parameters'].items()}
    d = problem.manifest['spatial_dimension']
    before = np.concatenate([a['temperature'][0], a['velocity'][0], a['pressure'][0]], axis=1)
    after = before.copy()
    old_h = a['enthalpy'][0, :, 0]
    density = a['density'][0, :, 0].copy()
    enthalpy = old_h.copy()
    reverted = np.zeros(len(before)//2, dtype=bool)
    if p['muscl']:
        gradients = np.concatenate([a['gradient_temperature'][0, :, None, :],
                                    a['gradient_velocity'][0].reshape(-1, d, d),
                                    a['gradient_pressure'][0, :, None, :]], axis=1)
        grad_projection = np.einsum('evd,ed->ev', gradients,
                                     np.repeat(a['displacement'][0], 2, axis=0))
        delta = np.repeat(before[1::2]-before[::2], 2, axis=0)
        increment = p['relax']*((1-p['kappa'])*grad_projection+p['kappa']*delta)
        if p['limiter'] == 1:
            regularized_delta2 = delta**2+1e-6
            increment *= (regularized_delta2+increment*delta)/(increment**2+regularized_delta2)
        elif p['limiter'] == 2:
            increment *= a['limiters'][0]
        after += np.tile([.5, -.5], len(before)//2)[:, None]*increment
        density = after[:, -1]/(p['gas_constant']*after[:, 0])
        cp = p['gamma']*p['gas_constant']/(p['gamma']-1)
        enthalpy = old_h + cp*(after[:, 0]-before[:, 0])
        enthalpy += .5*np.sum(after[:, 1:1+d]**2-before[:, 1:1+d]**2, axis=1)
        # Test positivity of the Roe averaged enthalpy above kinetic energy.
        ratio = np.sqrt(abs(density[1::2]/density[::2]))
        roe_h = (ratio*enthalpy[1::2]+enthalpy[::2])/(ratio+1)
        roe_u = (ratio[:, None]*after[1::2, 1:1+d]+after[::2, 1:1+d])/(ratio+1)[:, None]
        reverted = np.any(after.reshape(-1, 2, d+2)[:, :, -1] < 0, axis=1)
        reverted |= np.any(density.reshape(-1, 2) < 0, axis=1)
        reverted |= roe_h < .5*np.sum(roe_u**2, axis=1)
        select = np.repeat(reverted, 2)
        after[select] = before[select]
        density[select] = a['density'][0, select, 0]
        enthalpy[select] = old_h[select]
    result = {'temperature': after[:, :1], 'velocity': after[:, 1:1+d],
              'pressure': after[:, -1:], 'density': density[:, None], 'enthalpy': enthalpy[:, None],
              'momentum': density[:, None]*after[:, 1:1+d],
              'energy': (density*enthalpy-after[:, -1])[:, None]}
    return {k: v[None] for k, v in result.items()}, reverted


if __name__ == '__main__':
    rows = []
    for path in sorted((Q/'cases').glob('*/problem.json')):
        problem = load_problem(path)
        if problem.manifest['physics']['parameters']['operation']['value'] != 0:
            continue
        actual = load_result(problem, Q/'reference'/path.parent.name/'reference.h5')
        target, reverted = expected(problem)
        errors = {k: float(np.max(abs(actual[k]-v))) for k, v in target.items()}
        for key, value in target.items():
            np.testing.assert_allclose(actual[key], value, atol=1e-8, rtol=1e-12)
        rows.append({'case': path.parent.name, 'passed': True,
                     'max_abs_errors': errors, 'fallback_edges': reverted.tolist()})
    (Q/'author/data-evidence/full-core-independent-audit.json').write_text(json.dumps(rows, indent=2)+'\n')
    print(json.dumps({'cases': len(rows), 'passed': all(row['passed'] for row in rows)}))
