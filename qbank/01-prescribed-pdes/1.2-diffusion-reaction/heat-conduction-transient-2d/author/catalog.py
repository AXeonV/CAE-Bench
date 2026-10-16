"""Private initial-field recipes and mesh settings; not solver input."""
from dataclasses import dataclass

import numpy as np

D, N, F, R = 'dirichlet', 'normal_derivative', 'normal_flux', 'robin'
SIDES = ('left', 'right', 'bottom', 'top')


@dataclass(frozen=True)
class Case:
    name: str
    profile: str
    boundaries: tuple = (D, D, D, D)
    nx: int = 48
    ny: int = 48
    origin: tuple = (0.0, 0.0)
    size: tuple = (1.0, 1.0)
    k: float = 1.0
    capacity: float = 1.0
    alpha: tuple = (1.0, 2.0, 0.5, 3.0)
    beta: tuple = (1.0, 0.7, 1.5, 0.8)
    epochs: tuple = (0.0, 0.003, 0.007, 0.016, 0.035, 0.08)
    unstructured: bool = False
    sparse: bool = False


CASES = [
    Case('01-zero', 'zero', nx=2, ny=2),
    Case('02-insulated-constant', 'constant', (N, N, N, N), nx=12, ny=12),
    Case('03-smooth-cooling', 'sine'),
    Case('04-polynomial-bump', 'bubble'),
    Case('05-two-hotspots', 'lobes'),
    Case('06-localized-hotspot', 'narrow', nx=64, ny=64),
    Case('07-signed-pattern', 'signed'),
    Case('08-short-wavelength', 'wave', nx=64, ny=64,
         epochs=(0.0, 0.003, 0.004, 0.006, 0.009, 0.013, 0.019, 0.028, 0.04, 0.055, 0.07, 0.09)),
    Case('09-dirichlet-neumann', 'lobes', (D, N, D, N)),
    Case('10-reversed-natural', 'signed', (N, D, N, D)),
    Case('11-one-insulated-axis', 'bubble', (D, D, N, N)),
    Case('12-other-insulated-axis', 'sine', (F, F, D, D)),
    Case('13-four-robin', 'lobes', (R, R, R, R)),
    Case('14-dirichlet-robin', 'bubble', (D, R, D, R)),
    Case('15-four-operators', 'signed', (D, N, F, R)),
    Case('16-robin-flux', 'lobes', (F, R, R, F)),
    Case('17-weak-robin', 'constant', (R, R, R, R),
         alpha=(0.1, 0.2, 0.1, 0.3), beta=(10.0, 20.0, 15.0, 10.0)),
    Case('18-fast-diffusion', 'bubble', (R, D, F, N), k=20.0, capacity=0.5),
    Case('19-slow-diffusion', 'signed', (N, R, D, F), k=0.05, capacity=20.0),
    Case('20-shifted-rectangle', 'lobes', (D, F, R, N),
         origin=(-1.5, 2.0), size=(2.0, 0.8), nx=64, ny=32),
    Case('21-sparse-tags', 'bubble', (F, D, N, R),
         nx=32, ny=40, sparse=True),
    Case('22-unstructured', 'lobes', (R, N, F, D), unstructured=True),
    Case('23-initial-boundary-layer', 'plate', nx=88, ny=88),
    Case('24-insulated-gradient', 'gradient', (N, F, F, N),
         epochs=(0.0, 0.003, 0.011, 0.027, 0.06, 0.12)),
]


def initial_values(case, xy):
    u, v = ((xy - case.origin) / case.size).T
    if case.profile == 'zero':
        result = np.zeros(len(xy))
    elif case.profile == 'constant':
        result = np.full(len(xy), 2.5)
    elif case.profile == 'sine':
        result = 4 * np.sin(np.pi * u) * np.sin(np.pi * v)
    elif case.profile == 'bubble':
        result = 48 * u * (1-u) * v * (1-v)
    elif case.profile == 'lobes':
        result = (3*np.exp(-((u-0.3)**2/0.0225+(v-0.4)**2/0.04)) +
                  2*np.exp(-((u-0.72)**2/0.0324+(v-0.68)**2/0.0196)))
    elif case.profile == 'narrow':
        result = 4*np.exp(-((u-0.43)**2+(v-0.57)**2)/0.0081)
    elif case.profile == 'signed':
        result = 2*np.cos(3*np.pi*u)*np.sin(2*np.pi*v) + 0.7*(u-v)
    elif case.profile == 'wave':
        result = 2*np.sin(4*np.pi*u)*np.sin(3*np.pi*v)
    elif case.profile == 'plate':
        result = np.ones(len(xy))
    elif case.profile == 'gradient':
        result = 2*u-v-0.3
    else:
        raise ValueError(case.profile)
    for side, op in zip(SIDES, case.boundaries):
        if op == D:
            coordinate = u if side in ('left', 'right') else v
            value = 0.0 if side in ('left', 'bottom') else 1.0
            result[np.isclose(coordinate, value, atol=1e-10, rtol=0)] = 0.0
    return result.astype(np.float64)
