"""Independent P1 FEM baseline: public input only, no analytic oracle."""
import argparse
from pathlib import Path

import gmsh
import numpy as np
from scipy.sparse import coo_matrix, bmat, csr_matrix
from scipy.sparse.linalg import spsolve

from caeoj.sdk import load_problem, write_result
from caeoj.validation import GMSH_LOCK


def read_geometry(problem):
    ids = problem.arrays["node_ids"]
    with GMSH_LOCK:
        gmsh.initialize([], readConfigFiles=False)
        try:
            gmsh.option.setNumber("General.Terminal", 0)
            gmsh.open(str(problem.path.parent / problem.manifest["meshes"]["main"]["file"]))
            tags, coordinates, _ = gmsh.model.mesh.getNodes()
            coordinates = coordinates.reshape(-1, 3)[np.argsort(tags), :2]
            assert np.array_equal(np.sort(tags), ids)
            elements = {}
            for dim, width, expected in ((1, 2, 1), (2, 3, 2)):
                types, tag_blocks, connectivity = gmsh.model.mesh.getElements(dim)
                assert all(int(t) == expected for t in types)
                tags = np.concatenate(tag_blocks)
                connections = np.concatenate([block.reshape(-1, width) for block in connectivity])
                order = np.argsort(tags)
                elements[dim] = (tags[order], np.searchsorted(ids, connections[order]))
            return coordinates, elements
        finally:
            gmsh.finalize()


def solve(problem):
    coordinates, elements = read_geometry(problem)
    p = {key: item["value"] for key, item in problem.manifest["physics"]["parameters"].items()}
    k = p["conductivity"]
    origin, lengths = np.array([p["x0"], p["y0"]]), np.array([p["length_x"], p["length_y"]])
    n = len(coordinates)
    tags, all_cells = elements[2]
    cells = all_cells[np.searchsorted(tags, problem.arrays["domain_ids"])]
    vertices = coordinates[cells]
    affine = np.concatenate([np.ones((*vertices.shape[:2], 1)), vertices], axis=2)
    area = np.abs(np.linalg.det(affine)) / 2
    gradients = np.linalg.inv(affine)[:, 1:, :].transpose(0, 2, 1)
    local = k * area[:, None, None] * np.einsum("eik,ejk->eij", gradients, gradients)
    rows, cols = [np.repeat(cells, 3, axis=1).ravel()], [np.tile(cells, (1, 3)).ravel()]
    values = [local.ravel()]
    rhs, mean_weights = np.zeros(n), np.zeros(n)
    np.add.at(mean_weights, cells.ravel(), np.repeat(area / 3, 3))
    # Product Gauss quadrature mapped to a triangle by the Duffy transform.
    z, w = np.polynomial.legendre.leggauss(4)
    z, w = (z + 1) / 2, w / 2
    r, t = np.meshgrid(z, z, indexing="ij")
    weights = (w[:, None] * w[None, :] * (1 - r)).ravel()
    bary = np.stack(((1 - r) * (1 - t), r, (1 - r) * t), axis=-1).reshape(-1, 3)
    uv = (np.einsum("qa,eai->eqi", bary, vertices) - origin) / lengths
    source = next(c for c in problem.manifest["conditions"] if c["role"] == "source")
    field = source["data"]["coefficients"]["field"]
    coeff = problem.arrays[problem.manifest["fields"][field]["array"]][0]
    q = sum(coeff[:, i, j, None] * uv[:, :, 0]**i * uv[:, :, 1]**j for i in range(3) for j in range(3))
    loads = 2 * area[:, None] * np.einsum("eq,q,qa->ea", q, weights, bary)
    np.add.at(rhs, cells.ravel(), loads.ravel())
    prescribed = {}
    z, weights = np.polynomial.legendre.leggauss(3)
    z, weights = (z + 1) / 2, weights / 2
    edge_basis = np.stack((1 - z, z), axis=1)
    tags, all_edges = elements[1]
    for condition in problem.manifest["conditions"]:
        if condition["role"] != "boundary":
            continue
        location = condition["location"]
        ids = problem.arrays[problem.manifest["locations"][location]["ids"]]
        edges = all_edges[np.searchsorted(tags, ids)]
        verts = coordinates[edges]
        length = np.linalg.norm(verts[:, 1] - verts[:, 0], axis=1)
        field = condition["data"]["coefficients"]["field"]
        coeff = problem.arrays[problem.manifest["fields"][field]["array"]][0]
        axis = 1 if location in ("left", "right") else 0
        s_end = (verts[:, :, axis] - origin[axis]) / lengths[axis]
        operator = condition["operator"]
        if operator == "dirichlet":
            g = sum(coeff[:, i, None] * s_end**i for i in range(5))
            for node, value in zip(edges.ravel(), g.ravel()):
                if int(node) in prescribed and not np.isclose(prescribed[int(node)], value, atol=1e-10, rtol=0):
                    raise ValueError("Conflicting Dirichlet corner values")
                prescribed[int(node)] = float(value)
            continue
        s = s_end @ edge_basis.T
        g = sum(coeff[:, i, None] * s**i for i in range(5))
        if operator == "normal_flux":
            factor = -1.0
        elif operator == "normal_derivative":
            factor = k
        elif operator == "robin":
            alpha, beta = (condition["data"][key]["value"] for key in ("alpha", "beta"))
            factor = k / beta
            mass = factor * alpha * length[:, None, None] / 6 * np.array([[2, 1], [1, 2]])
            rows.append(np.repeat(edges, 2, axis=1).ravel())
            cols.append(np.tile(edges, (1, 2)).ravel())
            values.append(mass.ravel())
        else:
            raise ValueError(f"Unknown boundary operator {operator}")
        loads = factor * length[:, None] * np.einsum("eq,q,qa->ea", g, weights, edge_basis)
        np.add.at(rhs, edges.ravel(), loads.ravel())
    matrix = coo_matrix((np.concatenate(values), (np.concatenate(rows), np.concatenate(cols))), shape=(n, n)).tocsr()
    temperature = np.zeros(n)
    if prescribed:
        fixed = np.array(sorted(prescribed), dtype=np.int64)
        temperature[fixed] = [prescribed[int(i)] for i in fixed]
        free = np.setdiff1d(np.arange(n), fixed)
        temperature[free] = spsolve(matrix[free][:, free], rhs[free] - matrix[free][:, fixed] @ temperature[fixed])
    elif "mean_temperature" in p:
        column = csr_matrix(mean_weights[:, None])
        augmented = bmat([[matrix, column], [column.T, None]], format="csr")
        temperature = spsolve(augmented, np.r_[rhs, p["mean_temperature"] * area.sum()])[:-1]
    else:
        temperature = spsolve(matrix, rhs)
    return temperature[None, :, None]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Local P1 finite-element verification baseline")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    problem = load_problem(args.input)
    write_result(args.output, problem, {"temperature": solve(problem)})
