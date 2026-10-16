"""Continuum eigenfunction-series oracle, independent of time-discrete FEM.

Initial values describe the actual continuous P1 field on the supplied mesh.
Integrate that field against rectangular Sturm-Liouville eigenfunctions.
Never solve a mesh-discrete evolution system to construct the reference.
"""
from dataclasses import dataclass
import math

import numpy as np
from scipy.optimize import brentq
from scipy.special import erfc


def impedance(condition, length):
    op = condition['operator']
    if op == 'dirichlet':
        return math.inf
    if op in ('normal_derivative', 'normal_flux'):
        return 0.0
    if op == 'robin':
        return length*condition['data']['alpha']['value']/condition['data']['beta']['value']
    raise ValueError(op)


@dataclass
class Axis:
    frequencies: np.ndarray
    phases: np.ndarray
    norms: np.ndarray

    def values(self, u):
        return np.cos(np.asarray(u)[..., None]*self.frequencies-self.phases)/self.norms


def axis_modes(left, right, length, count):
    a, b = impedance(left, length), impedance(right, length)

    def phase(r, coefficient):
        return math.pi/2 if math.isinf(coefficient) else math.atan2(coefficient, r)

    roots, phases, norms = [], [], []
    for m in range(count):
        if (a == 0 or math.isinf(a)) and (b == 0 or math.isinf(b)):
            r = m*math.pi + (math.pi/2 if math.isinf(a) else 0) + (math.pi/2 if math.isinf(b) else 0)
        else:
            def characteristic(r):
                return r-phase(r, a)-phase(r, b)-m*math.pi
            lo, hi = m*math.pi, (m+1)*math.pi
            r = brentq(characteristic, lo, hi, xtol=2e-14)
        delta = phase(r, a)
        integral = 1.0 if r == 0 else 0.5+(math.sin(2*r-2*delta)+math.sin(2*delta))/(4*r)
        roots.append(r)
        phases.append(delta)
        norms.append(math.sqrt(integral))
    return Axis(np.array(roots), np.array(phases), np.array(norms))


def tail_bound(amplitude, diffusivity, time, lengths, count):
    """Conservative absolute pointwise bound for omitted positive-time modes.

Nonnegative Robin impedances imply r_m >= m*pi. L2-normalized axis
functions have sup norm <= 2; the initial modal coefficient is <= ||T0||2
<= max|nodal T0| on the normalized rectangle. Bound Gaussian sums by
their first term plus an integral. No division by a relative temperature.
"""
    if time <= 0:
        raise ValueError('Series bounds apply only at positive times')
    sums, tails = [], []
    for length in lengths:
        a = diffusivity*time*(math.pi/length)**2
        integral = math.sqrt(math.pi)/(2*math.sqrt(a))
        sums.append(1+integral)
        tails.append(math.exp(-a*count**2)+integral*erfc(count*math.sqrt(a)))
    return float(4*amplitude*(tails[0]*sums[1]+sums[0]*tails[1]))


def coefficients(xy, triangles, initial, axes, origin, lengths, order):
    """Composite Duffy/Gauss integration, bounded temporary storage."""
    z, w = np.polynomial.legendre.leggauss(order)
    z, w = (z+1)/2, w/2
    r, s = np.meshgrid(z, z, indexing='ij')
    bary = np.stack(((1-r)*(1-s), r, (1-r)*s), axis=-1).reshape(-1, 3)
    weights = (w[:, None]*w[None, :]*(1-r)).ravel()
    result = np.zeros((len(axes[0].frequencies), len(axes[1].frequencies)))
    normalized = (xy-origin)/lengths
    for start in range(0, len(triangles), 128):
        tri = triangles[start:start+128]
        vertices = normalized[tri]
        edges = vertices[:, 1:]-vertices[:, :1]
        twice_area = np.abs(edges[:, 0, 0]*edges[:, 1, 1]-edges[:, 0, 1]*edges[:, 1, 0])
        uv = np.einsum('qa,eai->eqi', bary, vertices)
        values = initial[tri]@bary.T
        measure = (twice_area[:, None]*weights*values).ravel()
        px = axes[0].values(uv[:, :, 0].ravel())
        py = axes[1].values(uv[:, :, 1].ravel())
        result += (px*measure[:, None]).T@py
    return result


def evaluate(xy, initial, axes, coeff, origin, lengths, diffusivity, times, dirichlet_nodes):
    uv = (xy-origin)/lengths
    px, py = axes[0].values(uv[:, 0]), axes[1].values(uv[:, 1])
    eigenvalues = (axes[0].frequencies[:, None]/lengths[0])**2 + (axes[1].frequencies[None, :]/lengths[1])**2
    result = np.empty((len(times), len(xy), 1), dtype=np.float64)
    for i, time in enumerate(times):
        if time == 0:
            result[i, :, 0] = initial
        else:
            result[i, :, 0] = np.sum((px@(coeff*np.exp(-diffusivity*time*eigenvalues)))*py, axis=1)
            result[i, dirichlet_nodes, 0] = 0.0
    return result


def reference(problem, xy, elements, *, orders=(4, 6, 8, 10, 12), min_modes=32):
    m = problem.manifest
    p = {key: item['value'] for key, item in m['physics']['parameters'].items()}
    origin = np.array([p['x0'], p['y0']])
    lengths = np.array([p['length_x'], p['length_y']])
    diffusivity = p['conductivity']/p['volumetric_heat_capacity']
    initial_spec = next(c for c in m['conditions'] if c['role'] == 'initial')['data']['value']['field']
    initial = problem.arrays[m['fields'][initial_spec]['array']][0, :, 0]
    times = problem.arrays[m['time_axes'][m['outputs']['temperature']['time_axis']]]
    boundary = {c['location']: c for c in m['conditions'] if c['role'] == 'boundary'}
    cell_tags, cells = elements[2]
    cells = cells[np.searchsorted(cell_tags, problem.arrays['domain_ids'])]
    edge_tags, edges = elements[1]
    fixed = set()
    for side, condition in boundary.items():
        if condition['operator'] == 'dirichlet':
            fixed.update(edges[np.searchsorted(edge_tags, problem.arrays[side+'_ids'])].ravel())
    amplitude = float(np.max(np.abs(initial)))
    count = min_modes
    while tail_bound(amplitude, diffusivity, times[1], lengths, count) > 1e-10:
        count += 16
        if count > 128:
            raise ValueError('Positive output time needs too many reference modes')
    axes = (axis_modes(boundary['left'], boundary['right'], lengths[0], count),
            axis_modes(boundary['bottom'], boundary['top'], lengths[1], count))
    previous = None
    comparisons = []
    # Require two successive refinements to pass, not a single accidental match.
    consecutive = 0
    for order in orders:
        coeff = coefficients(xy, cells, initial, axes, origin, lengths, order)
        result = evaluate(xy, initial, axes, coeff, origin, lengths, diffusivity, times, sorted(fixed))
        if previous is not None:
            difference = float(np.max(np.abs(result-previous)))
            comparisons.append({'quadrature_order': order, 'max_difference_K': difference})
            consecutive = consecutive+1 if difference <= 5e-9 else 0
            if consecutive >= 2:
                break
        previous = result
    else:
        raise ValueError(f'Reference quadrature did not converge: {comparisons}')
    certificate = {'modes_per_axis': count, 'quadrature_order': order,
                   'quadrature_refinements': comparisons,
                   'series_tail_bound_K': tail_bound(amplitude, diffusivity, times[1], lengths, count),
                   'reference_target_K': 1e-8,
                   'axis_frequencies': [a.frequencies.tolist() for a in axes]}
    return result, certificate
