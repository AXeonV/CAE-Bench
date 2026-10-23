"""Generate actual Gmsh inputs and analytic (not numerical-solver) references."""
from caeoj.storage import write_hdf5
import argparse
import json
from pathlib import Path
import shutil

import gmsh
import numpy as np
from numpy.polynomial.polynomial import polyval2d

from caeoj.sdk import load_problem, write_result
from caeoj_tools.format_examples import randomize_example
from caeoj_tools.grading_policy import materialize_references, author_case_grading
from caeoj.validation import GMSH_LOCK, write_json
from catalog import Case, CASES, SIDES, D, R, N, F, source_coefficients, boundary_coefficients, exact_mean, equation

TASK_ROOT = Path(__file__).resolve().parents[1]


def publish_sample(destination):
    """Publish random format examples using two representative inputs."""
    name = "01-constant-dirichlet"
    sample = destination / "samples" / "01"
    input_dir = sample / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    for filename in ("problem.json", "input.h5", "mesh.msh", "mesh.geo"):
        shutil.copyfile(destination / "cases" / name / filename, input_dir / filename)
    randomize_example(sample, seed=1)
    publish_mixed_sample(destination)


def publish_mixed_sample(destination):
    """Publish a small input with all four boundary operators."""
    case = Case("sample-02-mixed-boundaries", {(0, 0): 1.0, (1, 0): 1.0, (0, 1): 1.0},
                (D, N, F, R), nx=2, ny=2, alpha=1.0, beta_ratio=1.0)
    sample = Path(destination) / "samples/02"
    generate_case(case, sample/'input', None)
    randomize_example(sample, seed=2)


def mesh(case, path):
    with GMSH_LOCK:
        gmsh.initialize([], readConfigFiles=False)
        try:
            gmsh.option.setNumber("General.Terminal", 0)
            gmsh.option.setNumber("Mesh.RandomSeed", 1)
            gmsh.model.add(case.name)
            geo = gmsh.model.geo
            x, y = case.origin
            lx, ly = case.size
            h = min(lx / case.nx, ly / case.ny)
            points = [geo.addPoint(px, py, 0, h) for px, py in
                      ((x, y), (x + lx, y), (x + lx, y + ly), (x, y + ly))]
            curves = [geo.addLine(points[i], points[(i + 1) % 4]) for i in range(4)]
            surface = geo.addPlaneSurface([geo.addCurveLoop(curves)])
            geo.synchronize()
            if not case.unstructured:
                for i, curve in enumerate(curves):
                    gmsh.model.mesh.setTransfiniteCurve(curve, (case.nx if i % 2 == 0 else case.ny) + 1)
                gmsh.model.mesh.setTransfiniteSurface(surface, "AlternateLeft")
            gmsh.model.addPhysicalGroup(2, [surface], tag=1, name="domain")
            for tag, side, curve in zip(range(2, 6), SIDES, (curves[3], curves[1], curves[0], curves[2])):
                gmsh.model.addPhysicalGroup(1, [curve], tag=tag, name=side)
            gmsh.model.mesh.generate(2)
            if case.sparse_ids:
                tags = gmsh.model.mesh.getNodes()[0]
                gmsh.model.mesh.renumberNodes(tags, np.arange(len(tags), dtype=np.uint64) * 13 + 101)
                _, blocks, _ = gmsh.model.mesh.getElements()
                tags = np.concatenate(blocks)
                gmsh.model.mesh.renumberElements(tags, np.arange(len(tags), dtype=np.uint64) * 17 + 211)
            gmsh.option.setNumber("Mesh.MshFileVersion", 4.1)
            gmsh.option.setNumber("Mesh.Binary", 0)
            gmsh.option.setNumber("Mesh.SaveAll", 1)
            gmsh.write(str(path.with_suffix(".geo_unrolled")))
            path.with_suffix(".geo_unrolled").replace(path.with_suffix(".geo"))
            gmsh.write(str(path))
            tags, coordinates, _ = gmsh.model.mesh.getNodes()
            order = np.argsort(tags)
            return tags[order].astype(np.int64), coordinates.reshape(-1, 3)[order, :2]
        finally:
            gmsh.finalize()


def field(name, location, shape, labels, unit):
    return {"array": name, "quantity": name, "location": location, "time_axis": "steady",
            "dtype": "float64", "kind": "components", "component_shape": shape,
            "components": labels, "unit": unit, "value_kind": "average"}


def generate_case(case, directory, reference_dir):
    """Use the same data contract for scoring cases and public examples."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    ids, coordinates = mesh(case, directory / "mesh.msh")
    # Let the existing structural loader enumerate mesh entities/groups.
    from caeoj.validation import read_mesh
    topology = read_mesh(directory / "mesh.msh")
    manifest = {"task": "heat-conduction-steady-2d", "spatial_dimension": 2, "data_file": "input.h5",
                "geometries": {"rectangle": {"file": "mesh.geo", "format": "gmsh-geo"}},
                "meshes": {"main": {"file": "mesh.msh", "geometry": "rectangle"}},
                "locations": {"nodes": {"kind": "mesh", "mesh": "main", "entity": "node", "ids": "node_ids"}},
                "time_axes": {"steady": "times"}, "fields": {}, "outputs": {}, "conditions": [],
                "physics": {"model": "steady_heat_conduction", "parameters": {}}}
    parameters = manifest["physics"]["parameters"]
    for name, value, unit in [("conductivity", case.k, "W/(m.K)"), ("x0", case.origin[0], "m"),
                              ("y0", case.origin[1], "m"), ("length_x", case.size[0], "m"),
                              ("length_y", case.size[1], "m")]:
        parameters[name] = {"value": value, "unit": unit}
    arrays = {"node_ids": ids, "times": np.array([0.0], dtype=np.float64)}
    for name, dim, tag in [("domain", 2, 1)] + [(side, 1, tag) for side, tag in zip(SIDES, range(2, 6))]:
        key = name + "_ids"
        arrays[key] = np.array(sorted(topology["groups"][(dim, tag)]["elements"]), dtype=np.int64)
        manifest["locations"][name] = {"kind": "mesh", "mesh": "main", "entity": "element",
            "dimension": dim, "ids": key, "physical_group": {"dimension": dim, "tag": tag}}
    source = source_coefficients(case)
    arrays["source_coefficients"] = np.broadcast_to(source, (1, len(arrays["domain_ids"]), 3, 3)).copy()
    manifest["fields"]["source_coefficients"] = field("source_coefficients", "domain", [3, 3],
        [f"c{i}{j}" for i in range(3) for j in range(3)], "W/m3")
    manifest["conditions"].append({"role": "source", "variable": "temperature", "location": "domain",
        "operator": "polynomial", "data": {"coefficients": {"field": "source_coefficients"}}})
    boundaries = {}
    for side, operator in zip(SIDES, case.boundaries):
        key = side + "_coefficients"
        coeff = boundary_coefficients(case, side, operator)
        arrays[key] = np.broadcast_to(coeff, (1, len(arrays[side + "_ids"]), 5)).copy()
        unit = "K/m" if operator == N else "W/m2" if operator in (F, R) else "K"
        manifest["fields"][key] = field(key, side, [5], [f"c{i}" for i in range(5)], unit)
        data = {"coefficients": {"field": key}}
        if operator == R:
            data |= {"alpha": {"value": case.alpha, "unit": "W/(m2.K)"},
                     "beta": {"value": case.k * case.beta_ratio, "unit": "W/(m.K)"}}
        manifest["conditions"].append({"role": "boundary", "variable": "temperature", "location": side,
                                         "operator": operator, "data": data})
        boundaries[side] = {"operator": operator, "coefficients": coeff.tolist(), "g": equation(coeff, ("s",))}
    if all(op in (N, F) for op in case.boundaries):
        parameters["mean_temperature"] = {"value": exact_mean(case), "unit": "K"}
    manifest["outputs"]["temperature"] = {"array": "temperature", "quantity": "temperature", "location": "nodes",
        "time_axis": "steady", "dtype": "float64", "kind": "scalar", "component_shape": [1],
        "components": ["value"], "unit": "K", "value_kind": "point"}
    write_hdf5(directory / 'input.h5', arrays, compression="gzip")
    write_json(directory / "problem.json", manifest)
    problem = load_problem(directory / "problem.json")
    if reference_dir is not None:
        uv = (coordinates - case.origin) / case.size
        temperature = polyval2d(uv[:, 0], uv[:, 1], case.temperature)[None, :, None]
        write_result(Path(reference_dir) / "reference.h5", problem, {"temperature": temperature})
    record = {"case": case.name, "temperature_coefficients": case.temperature.tolist(),
              "temperature": equation(case.temperature), "source": equation(source), "boundaries": boundaries,
              "mean_temperature": exact_mean(case), "node_count": len(ids), "cell_count": len(arrays["domain_ids"])}
    return record, coordinates


def generate(destination=TASK_ROOT):
    destination = Path(destination)
    descriptions = ["# 热传导测试点与解析解（出题材料）", "",
                    "本目录的解析公式和 `reference/` 不应进入后续 Agent 开发环境。",
                    "所有公式使用题面的 u、v、s；温度单位 K。D/N/F/R 分别表示定温、法向导数、向外热流、Robin。",
                    "源项由 `q=-k(T_uu/Lx²+T_vv/Ly²)` 得到，边界右端由各算子作用于同一个 T 得到。", "",
                    "| 测试点 | T(u,v) | 左/右/下/上 | k | 域 (x0,y0; Lx,Ly) | 网格 |",
                    "|---|---|---|---|---|---|"]
    symbols = {"dirichlet": "D", N: "N", F: "F", R: "R"}
    records = []
    for case in CASES:
        record, _ = generate_case(case, destination / "cases" / case.name,
                                  destination / "reference" / case.name)
        write_json(destination/"author/data-evidence/reference"/case.name/"analytic.json", record)
        records.append(record)
        boundaries_short = "/".join(symbols[op] for op in case.boundaries)
        mesh_label = "非结构" if case.unstructured else f"{case.nx}×{case.ny}"
        if case.sparse_ids:
            mesh_label += "，稀疏 tags"
        descriptions.append(f"| {case.name} | `{record['temperature']}` | {boundaries_short} | {case.k:g} | {case.origin}; {case.size} | {mesh_label} |")
    descriptions += ["", "## 每例源项、边界方程及唯一性", "",
                     "边界方程中 N 为 ∂T/∂n=g，F 为 −k∂T/∂n=g，R 为 αT+β∂T/∂n=g。法向均指向域外。"]
    for case, record in zip(CASES, records):
        descriptions += ["", f"### {case.name}", "", f"`T = {record['temperature']}`；`q = {record['source']}`。", ""]
        for side, item in record["boundaries"].items():
            operator = item["operator"]
            lhs = "T" if operator == "dirichlet" else "∂T/∂n" if operator == N else f"−{case.k:g}∂T/∂n" if operator == F else f"{case.alpha:g}T + {case.k * case.beta_ratio:g}∂T/∂n"
            descriptions.append(f"- {side}：`{lhs} = {item['g']}`。")
        if all(op in (N, F) for op in case.boundaries):
            descriptions += ["", f"另给定域平均温度 `{record['mean_temperature']:.12g} K`。"]
    (destination / "TEST-CASES.md").write_text("\n".join(descriptions) + "\n", encoding="utf-8")
    materialize_references(destination, case_config=author_case_grading(TASK_ROOT))
    publish_sample(destination)
    return len(CASES)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=TASK_ROOT)
    args = parser.parse_args()
    print(f"Generated {generate(args.output)} analytic heat-conduction-steady-2d cases in {args.output}")
