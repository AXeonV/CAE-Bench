"""Author-only exact solutions. Never needed by a submitted solver."""
from dataclasses import dataclass

import numpy as np
from numpy.polynomial import polynomial as poly

SIDES = ("left", "right", "bottom", "top")
NORMALS = ((-1, 0), (1, 0), (0, -1), (0, 1))
D, N, F, R = "dirichlet", "normal_derivative", "normal_flux", "robin"


@dataclass(frozen=True)
class Case:
    name: str
    terms: dict
    boundaries: tuple = (D, D, D, D)
    origin: tuple = (0.0, 0.0)
    size: tuple = (1.0, 1.0)
    k: float = 1.0
    nx: int = 32
    ny: int = 28
    alpha: float = 2.0
    beta_ratio: float = 1.0
    unstructured: bool = False
    sparse_ids: bool = False

    @property
    def temperature(self):
        a = np.zeros((5, 5), dtype=np.float64)
        for (i, j), c in self.terms.items():
            a[i, j] = c
        return a


AFFINE = {(0, 0): 2.0, (1, 0): 1.3, (0, 1): -0.7}
QUADRATIC = {(0, 0): 1.0, (2, 0): 2.0, (0, 2): -0.8, (1, 1): 0.6}
CUBIC = {(0, 0): -0.3, (3, 0): 1.5, (0, 3): -0.9, (2, 1): 0.7, (1, 2): -0.4}
BUBBLE = {(1, 1): 8.0, (2, 1): -8.0, (1, 2): -8.0, (2, 2): 8.0}
QUARTIC = {(0, 0): 0.4, (4, 0): 1.2, (0, 4): -0.7, (3, 1): 0.5, (1, 3): -0.8, (2, 2): 0.9}

CASES = [
    Case("01-constant-dirichlet", {(0, 0): 4.0}, nx=2, ny=2),
    Case("02-affine-shifted", AFFINE, origin=(-1.2, 0.7), size=(2.0, 0.8)),
    Case("03-bilinear-dirichlet", {(0, 0): 0.2, (1, 1): 3.0}, size=(0.8, 1.7)),
    Case("04-quadratic-source", {(2, 0): 1.0, (0, 2): 1.0}),
    Case("05-anisotropic-quadratic", QUADRATIC, size=(2.4, 0.7), k=7.5),
    Case("06-cubic-source", CUBIC, origin=(0.4, -1.5), k=0.3),
    Case("07-zero-boundary-bubble", BUBBLE),
    Case("08-harmonic-quartic", {(4, 0): 1.0, (2, 2): -6.0, (0, 4): 1.0}),
    Case("09-dirichlet-derivative", QUADRATIC, (D, N, D, N), size=(1.4, 0.9)),
    Case("10-insulated-sides", {(0, 0): 1.0, (1, 0): 2.0, (2, 0): -1.0}, (D, D, F, F)),
    Case("11-signed-heat-flux", QUADRATIC, (F, D, F, D), k=3.2, size=(0.6, 1.8)),
    Case("12-cubic-derivative", CUBIC, (N, D, N, D), k=0.15),
    Case("13-dirichlet-robin", QUADRATIC, (D, R, D, R), alpha=0.6, beta_ratio=1.7),
    Case("14-four-operators", CUBIC, (D, N, F, R), size=(1.8, 0.8), k=2.3),
    Case("15-pure-robin-constant", {(0, 0): -2.0}, (R, R, R, R), alpha=0.4),
    Case("16-pure-robin-quadratic", QUADRATIC, (R, R, R, R), alpha=3.5, beta_ratio=0.6),
    Case("17-pure-flux-affine-mean", AFFINE, (F, F, F, F), k=0.4, origin=(-0.5, -0.8)),
    Case("18-pure-flux-source-mean", QUADRATIC, (F, F, F, F), k=4.0, size=(1.5, 0.7)),
    Case("19-pure-derivative-mean", CUBIC, (N, N, N, N), size=(0.8, 1.3)),
    Case("20-robin-flux-no-dirichlet", QUARTIC, (R, F, R, F), alpha=1.3),
    Case("21-robin-derivative-large-k", CUBIC, (N, R, N, R), k=20.0, alpha=10.0),
    Case("22-small-k-flux", QUADRATIC, (D, F, D, F), k=0.05),
    Case("23-long-shifted-domain", CUBIC, (F, D, R, N), origin=(2.5, -2.0), size=(3.0, 0.5), nx=48, ny=24),
    Case("24-quartic-four-operators", QUARTIC, (R, F, N, D), k=1.7, beta_ratio=2.0),
    Case("25-zero-solution", {}),
    Case("26-small-temperature", {(2, 0): 0.04, (0, 2): -0.025, (1, 1): 0.015}, (R, D, F, N)),
    Case("27-sparse-tags", AFFINE, (D, R, N, F), size=(1.2, 0.6), nx=12, ny=10, sparse_ids=True),
    Case("28-unstructured-quadratic", QUADRATIC, (D, F, R, N), unstructured=True, k=1.4),
    Case("29-bubble-coarser", BUBBLE, nx=16, ny=14),
    Case("30-bubble-refined", BUBBLE, nx=48, ny=42),
    Case("31-quartic-pure-flux", QUARTIC, (F, F, F, F), nx=40, ny=36, size=(1.1, 0.9)),
    Case("32-rotated-boundary-roles", CUBIC, (N, R, D, F), k=0.8, origin=(-2.0, 1.0)),
]


def source_coefficients(case):
    a = case.temperature
    source = np.zeros((5, 5), dtype=np.float64)
    for axis, length in enumerate(case.size):
        derivative = poly.polyder(a, m=2, axis=axis) / length**2
        source[:derivative.shape[0], :derivative.shape[1]] -= case.k * derivative
    assert not np.any(source[3:, :]) and not np.any(source[:, 3:])
    return source[:3, :3]


def trace(a, side):
    """Edge parameter increases with global y (vertical) or x (horizontal)."""
    if side == "left":
        return a[0, :]
    if side == "right":
        return a.sum(axis=0)
    if side == "bottom":
        return a[:, 0]
    return a.sum(axis=1)


def boundary_coefficients(case, side, operator):
    a = case.temperature
    index = SIDES.index(side)
    axis = 0 if index < 2 else 1
    d = poly.polyder(a, axis=axis) * NORMALS[index][axis] / case.size[axis]
    padded = np.zeros_like(a)
    padded[:d.shape[0], :d.shape[1]] = d
    t, normal = trace(a, side), trace(padded, side)
    if operator == D:
        return t
    if operator == N:
        return normal
    if operator == F:
        return -case.k * normal
    return case.alpha * t + case.k * case.beta_ratio * normal


def exact_mean(case):
    return float(sum(c / ((i + 1) * (j + 1)) for (i, j), c in case.terms.items()))


def equation(a, variables=("u", "v")):
    terms = []
    for index in np.ndindex(a.shape):
        coefficient = a[index]
        if coefficient == 0:
            continue
        factors = [f"{x}^{power}" if power > 1 else x for x, power in zip(variables, index) if power]
        terms.append(f"{coefficient:.12g}" + ("*" + "*".join(factors) if factors else ""))
    return " + ".join(terms).replace("+ -", "- ") or "0"
