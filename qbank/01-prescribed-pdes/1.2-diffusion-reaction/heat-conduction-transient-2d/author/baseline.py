"""Standalone consistent-mass P1 FEM baseline; reads only public input.

Fixed: Crank-Nicolson with two initial backward-Euler half steps.
Adaptive: step doubling and local error control; no explicit CFL assumption.
"""
import argparse
from collections import OrderedDict
import json
import math
from pathlib import Path

import gmsh
import numpy as np
from scipy.sparse import coo_matrix, diags
from scipy.sparse.linalg import splu

from caeoj.sdk import load_problem, read_constant, read_field, write_result
from caeoj.validation import GMSH_LOCK


def read_geometry(problem):
    ids = problem.arrays['node_ids']
    with GMSH_LOCK:
        gmsh.initialize([], readConfigFiles=False)
        try:
            gmsh.option.setNumber('General.Terminal', 0)
            gmsh.open(str(problem.path.parent/problem.manifest['meshes']['main']['file']))
            tags, xyz, _ = gmsh.model.mesh.getNodes()
            order = np.argsort(tags)
            if not np.array_equal(tags[order], ids):
                raise ValueError('Node IDs do not cover the mesh')
            coordinates = xyz.reshape(-1, 3)[order, :2]
            elements = {}
            for dim, expected, width in ((1, 1, 2), (2, 2, 3)):
                types, tag_blocks, connections = gmsh.model.mesh.getElements(dim)
                if any(t != expected for t in types):
                    raise ValueError('Unsupported element type')
                tags = np.concatenate(tag_blocks)
                conn = np.concatenate([c.reshape(-1, width) for c in connections])
                order = np.argsort(tags)
                elements[dim] = (tags[order], np.searchsorted(ids, conn[order]))
            return coordinates, elements
        finally:
            gmsh.finalize()


def assemble(problem):
    xy, elements = read_geometry(problem)
    p = {name: read_constant(data) for name, data in problem.manifest['physics']['parameters'].items()}
    tags, cells = elements[2]
    cells = cells[np.searchsorted(tags, problem.arrays['domain_ids'])]
    vertices = xy[cells]
    affine = np.concatenate([np.ones((*vertices.shape[:2], 1)), vertices], axis=2)
    area = np.abs(np.linalg.det(affine))/2
    gradients = np.linalg.inv(affine)[:, 1:, :].transpose(0, 2, 1)
    local_k = p['conductivity']*area[:, None, None]*np.einsum('eik,ejk->eij', gradients, gradients)
    local_m = p['volumetric_heat_capacity']*area[:, None, None]/12*(np.ones((3, 3))+np.eye(3))
    rows, cols = [np.repeat(cells, 3, axis=1).ravel()], [np.tile(cells, (1, 3)).ravel()]
    stiffness = [local_k.ravel()]
    n = len(xy)
    mass = coo_matrix((local_m.ravel(), (rows[0], cols[0])), shape=(n, n)).tocsr()
    fixed = set()
    edge_tags, all_edges = elements[1]
    for condition in problem.manifest['conditions']:
        if condition['role'] != 'boundary':
            continue
        location = condition['location']
        ids = problem.arrays[problem.manifest['locations'][location]['ids']]
        edges = all_edges[np.searchsorted(edge_tags, ids)]
        op = condition['operator']
        if read_constant(condition['data']['value']) != 0:
            raise ValueError('This task has homogeneous boundary data')
        if op == 'dirichlet':
            fixed.update(map(int, edges.ravel()))
        elif op == 'robin':
            alpha, beta = (read_constant(condition['data'][key]) for key in ('alpha', 'beta'))
            length = np.linalg.norm(xy[edges[:, 1]]-xy[edges[:, 0]], axis=1)
            robin = p['conductivity']*alpha/beta*length[:, None, None]/6*np.array([[2, 1], [1, 2]])
            rows.append(np.repeat(edges, 2, axis=1).ravel())
            cols.append(np.tile(edges, (1, 2)).ravel())
            stiffness.append(robin.ravel())
        elif op not in ('normal_derivative', 'normal_flux'):
            raise ValueError(op)
    stiffness = coo_matrix((np.concatenate(stiffness), (np.concatenate(rows), np.concatenate(cols))), shape=(n, n)).tocsr()
    free = np.ones(n, dtype=bool)
    free[list(fixed)] = False
    initial = next(c for c in problem.manifest['conditions'] if c['role'] == 'initial')
    values = read_field(problem, initial['data']['value'])[0, :, 0].copy()
    if np.any(values[list(fixed)] != 0):
        raise ValueError('Initial Dirichlet nodes must be zero')
    return mass, stiffness, free, values, xy, cells


class Stepper:
    def __init__(self, mass, stiffness):
        self.mass, self.stiffness = mass, stiffness
        self.cache = OrderedDict()
        self.factorizations = 0

    def step(self, values, dt, theta):
        key = (float(dt), float(theta))
        if key not in self.cache:
            self.cache[key] = splu((self.mass+theta*dt*self.stiffness).tocsc())
            self.factorizations += 1
            if len(self.cache) > 4:
                self.cache.popitem(last=False)
        self.cache.move_to_end(key)
        rhs = self.mass@values-(1-theta)*dt*(self.stiffness@values)
        return self.cache[key].solve(rhs)


def solve(problem, *, time_mode='fixed', dt=None, atol=2e-5, rtol=2e-5):
    if time_mode not in ('fixed', 'adaptive'):
        raise ValueError('Unknown time mode')
    if dt is not None and (not math.isfinite(dt) or dt <= 0):
        raise ValueError('dt must be finite and positive')
    if atol <= 0 or rtol < 0 or not math.isfinite(atol+rtol):
        raise ValueError('Invalid local time-error tolerances')
    mass, stiffness, free, initial, xy, cells = assemble(problem)
    p = {name: read_constant(data) for name, data in problem.manifest['physics']['parameters'].items()}
    diffusivity = p['conductivity']/p['volumetric_heat_capacity']
    times = problem.arrays[problem.manifest['time_axes'][problem.manifest['outputs']['temperature']['time_axis']]]
    if not np.any(free):
        # A valid coarse rectangle may contain only Dirichlet boundary nodes.
        return np.zeros((len(times), len(initial), 1), dtype=np.float64), {
            'time_mode': time_mode, 'accepted_steps': 0, 'rejected_steps': 0,
            'smallest_step_s': None, 'largest_step_s': None, 'factorizations': 0,
            'nodes': len(initial), 'triangles': len(cells),
            'lumped_explicit_stable_step_bound_s': None, 'explicit_steps_at_bound': 0}
    natural_scale = min(p['length_x'], p['length_y'])**2/diffusivity
    max_step = dt if dt is not None else 1e-4*natural_scale
    stepper = Stepper(mass[free][:, free], stiffness[free][:, free])
    values = initial[free].copy()
    output = np.zeros((len(times), len(initial), 1), dtype=np.float64)
    output[0, :, 0] = initial
    accepted = rejected = 0
    smallest, largest = math.inf, 0.0
    first = True
    current = float(times[0])
    proposal = max_step
    for i, target in enumerate(times[1:], 1):
        if time_mode == 'fixed':
            steps = max(1, math.ceil((target-current)/max_step))
            interval = target-current
            for j in range(steps):
                step = max_step if j < steps-1 else interval-max_step*(steps-1)
                if first:
                    values = stepper.step(stepper.step(values, step/2, 1.0), step/2, 1.0)
                    first = False
                else:
                    values = stepper.step(values, step, 0.5)
                accepted += 1
                smallest, largest = min(smallest, step), max(largest, step)
            current = float(target)
        else:
            while current < target:
                step = min(proposal, target-current)
                if current+step == current or accepted+rejected > 100000:
                    raise RuntimeError('Time integration cannot make progress')
                theta = 1.0 if first else 0.5
                coarse = stepper.step(values, step, theta)
                fine = stepper.step(stepper.step(values, step/2, theta), step/2, theta)
                divisor = 1.0 if first else 3.0
                error = float(np.max(np.abs(fine-coarse)/(divisor*(atol+rtol*np.maximum(np.abs(values), np.abs(fine))))))
                exponent = 0.5 if first else 1/3
                if error <= 1.0:
                    values = fine
                    current = float(target) if step == target-current else current+step
                    first = False
                    accepted += 1
                    smallest, largest = min(smallest, step/2), max(largest, step/2)
                else:
                    rejected += 1
                proposal = step*min(2.0, max(0.2, 0.9*max(error, 1e-12)**(-exponent)))
        output[i, free, 0] = values
    # Stability budget for a DIFFERENT explicit, mass-lumped discretization.
    # Gershgorin bounds its largest eigenvalue; this is not an implicit limit.
    lumped = np.asarray(mass.sum(axis=1)).ravel()[free]
    scale = diags(1/np.sqrt(lumped))
    symmetric = scale@stiffness[free][:, free]@scale
    eigenvalue_upper = float(np.max(np.asarray(abs(symmetric).sum(axis=1))))
    explicit_bound = 2/eigenvalue_upper
    stats = {'time_mode': time_mode, 'accepted_steps': accepted, 'rejected_steps': rejected,
             'smallest_step_s': smallest, 'largest_step_s': largest,
             'factorizations': stepper.factorizations, 'nodes': len(initial), 'triangles': len(cells),
             'lumped_explicit_stable_step_bound_s': explicit_bound,
             'explicit_steps_at_bound': math.ceil(float(times[-1])/explicit_bound)}
    return output, stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--time-mode', choices=('fixed', 'adaptive'), default='fixed')
    parser.add_argument('--dt', type=float)
    parser.add_argument('--atol', type=float, default=2e-5)
    parser.add_argument('--rtol', type=float, default=2e-5)
    args = parser.parse_args()
    problem = load_problem(args.input)
    temperature, stats = solve(problem, time_mode=args.time_mode, dt=args.dt, atol=args.atol, rtol=args.rtol)
    write_result(args.output, problem, {'temperature': temperature})
    print(json.dumps(stats, allow_nan=False))


if __name__ == '__main__':
    main()
