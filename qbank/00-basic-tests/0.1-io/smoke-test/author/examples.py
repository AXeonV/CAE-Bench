"""Real Gmsh mesh/HDF5 fixtures with asymmetric values."""
from caeoj.storage import write_hdf5
from pathlib import Path

import gmsh
import numpy as np

from caeoj.validation import GMSH_LOCK, read_mesh, write_json

CASE_NAMES = ["01-line-1d", "02-triangle-2d", "03-quad-2d", "04-tetra-3d",
              "05-mixed-blocks", "06-noncontiguous-ids",
              "08-scalars-and-dtypes", "09-vector-2d", "10-full-tensor",
              "11-field-locations", "12-time-series"]


def generate_mesh(path, dimension=2, quads=False, mixed=False, sparse=False):
    """Geometry, meshing and element numbering all use the official Gmsh API."""
    path = Path(path)
    with GMSH_LOCK:
        gmsh.initialize([], readConfigFiles=False)
        try:
            gmsh.option.setNumber("General.Terminal", 0)
            gmsh.model.add("fixture")
            geo = gmsh.model.geo
            if dimension == 1:
                a, b = geo.addPoint(0, 0, 0, 0.5), geo.addPoint(2, 0, 0, 0.5)
                line = geo.addLine(a, b)
                geo.synchronize()
                gmsh.model.addPhysicalGroup(1, [line], tag=1, name="domain")
                gmsh.model.addPhysicalGroup(0, [a], tag=2, name="left")
            elif dimension == 3:
                volume = gmsh.model.occ.addBox(-0.5, 0, 0, 2, 1, 1.5)
                gmsh.model.occ.synchronize()
                gmsh.option.setNumber("Mesh.MeshSizeMin", 0.8)
                gmsh.option.setNumber("Mesh.MeshSizeMax", 0.8)
                gmsh.model.addPhysicalGroup(3, [volume], tag=1, name="domain")
                surfaces = [tag for _, tag in gmsh.model.getBoundary([(3, volume)], oriented=False)]
                gmsh.model.addPhysicalGroup(2, [surfaces[0]], tag=2, name="boundary")
            else:
                p = [geo.addPoint(x, y, 0, 0.7) for x, y in [(0, 0), (2, 0), (2, 1), (0, 1)]]
                curves = [geo.addLine(p[i], p[(i+1) % 4]) for i in range(4)]
                surface = geo.addPlaneSurface([geo.addCurveLoop(curves)])
                surfaces = [surface]
                if mixed:
                    # A second triangle-meshed surface retains mixed element types.
                    q = [geo.addPoint(x, y, 0, 0.7) for x, y in [(3, 0), (4, 0), (3, 1)]]
                    lines = [geo.addLine(q[i], q[(i+1) % 3]) for i in range(3)]
                    surfaces.append(geo.addPlaneSurface([geo.addCurveLoop(lines)]))
                geo.synchronize()
                for curve in curves:
                    gmsh.model.mesh.setTransfiniteCurve(curve, 3)
                gmsh.model.mesh.setTransfiniteSurface(surface)
                if quads or mixed:
                    gmsh.model.mesh.setRecombine(2, surface)
                gmsh.model.addPhysicalGroup(2, surfaces, tag=1, name="domain")
                gmsh.model.addPhysicalGroup(1, [curves[3]], tag=2, name="left")
                gmsh.model.addPhysicalGroup(1, curves, tag=3, name="boundary")
            gmsh.model.mesh.generate(dimension)
            if sparse:
                tags = gmsh.model.mesh.getNodes()[0]
                gmsh.model.mesh.renumberNodes(tags, np.arange(1, len(tags)+1, dtype=np.uint64) * 11 + 7)
            gmsh.option.setNumber("Mesh.MshFileVersion", 4.1)
            gmsh.option.setNumber("Mesh.SaveAll", 1)
            gmsh.option.setNumber("Mesh.Binary", 0)
            # Keep the generated .geo as the optional geometry artifact in 1D/2D cases.
            if dimension != 3:
                gmsh.write(str(path.with_suffix(".geo_unrolled")))
                path.with_suffix(".geo_unrolled").replace(path.with_suffix(".geo"))
            gmsh.write(str(path))
        finally:
            gmsh.finalize()


def base(dimension):
    return {"task": "smoke-test", "spatial_dimension": dimension,
            "data_file": "input.h5", "geometries": {}, "meshes": {"main": {"file": "mesh.msh"}},
            "locations": {"nodes": {"kind": "mesh", "mesh": "main", "entity": "node", "ids": "node_ids"}},
            "time_axes": {"steady": "times"}, "fields": {}, "outputs": {}, "conditions": []}


def add_field(m, arrays, name, location="nodes", kind="scalar", dtype="float64", time_axis="steady",
              value_kind="point", components=None, component_shape=None, unit="1"):
    axes = list("xyz"[:m["spatial_dimension"]])
    if kind == "scalar":
        component_shape, components = [1], ["value"]
    elif kind == "vector":
        component_shape, components = [len(axes)], axes
    elif kind == "tensor":
        component_shape, components = [len(axes), len(axes)], [a+b for a in axes for b in axes]
    spec = {"array": name, "quantity": name, "location": location, "time_axis": time_axis,
            "dtype": dtype, "kind": kind, "component_shape": component_shape,
            "components": components, "unit": unit, "value_kind": value_kind}
    m["fields"][name] = spec
    m["outputs"][name] = dict(spec)
    n = len(arrays[m["locations"][location]["ids"]])
    t = len(arrays[m["time_axes"][time_axis]])
    shape = (t, n, *component_shape)
    data = np.arange(np.prod(shape), dtype=np.int64).reshape(shape) * 7 + 3
    if dtype == "bool":
        data = data % 2 == 0
    else:
        data = data.astype(dtype)
        if dtype == "float64":
            data = data * 0.125 - 4.5
    arrays[name] = data


def make_cases(destination):
    destination = Path(destination)
    for name in CASE_NAMES:
        index = int(name.split("-", 1)[0])
        directory = destination / name
        directory.mkdir(parents=True, exist_ok=True)
        dim = 1 if index == 1 else 3 if index == 4 else 2
        mesh_path = directory / "mesh.msh"
        generate_mesh(mesh_path, dim, quads=index == 3, mixed=index == 5,
                      sparse=index == 6)
        mesh = read_mesh(mesh_path)
        m = base(dim)
        if dim != 3:
            m["geometries"]["shape"] = {"file": "mesh.geo", "format": "gmsh-geo"}
            m["meshes"]["main"]["geometry"] = "shape"
        arrays = {"node_ids": np.array(sorted(mesh["nodes"]), dtype=np.int64),
                  "times": np.array([0.0], dtype=np.float64)}
        if index == 5:
            m["locations"]["cells"] = {"kind": "mesh", "mesh": "main", "entity": "element",
                                         "dimension": dim, "ids": "cell_ids"}
            arrays["cell_ids"] = np.array(sorted(mesh["elements"][dim]), dtype=np.int64)
            add_field(m, arrays, "cell_temperature", "cells", value_kind="average", unit="K")
        elif index == 8:
            add_field(m, arrays, "temperature", unit="K")
            add_field(m, arrays, "region_label", dtype="int64")
            add_field(m, arrays, "mask", dtype="bool")
        elif index in (4, 9):
            add_field(m, arrays, "velocity", kind="vector", unit="m/s")
            if index == 4:
                m["locations"]["faces"] = {"kind": "mesh", "mesh": "main", "entity": "element",
                    "dimension": 2, "ids": "face_ids", "physical_group": {"dimension": 2, "tag": 2}}
                arrays["face_ids"] = np.array(sorted(mesh["groups"][(2, 2)]["elements"]), dtype=np.int64)
                add_field(m, arrays, "face_pressure", "faces", value_kind="average", unit="Pa")
        elif index == 10:
            add_field(m, arrays, "stress", kind="tensor", unit="Pa")
            add_field(m, arrays, "species", kind="components", component_shape=[3],
                      components=["A", "B", "C"])
        elif index == 11:
            add_field(m, arrays, "temperature", unit="K")
            m["locations"]["left"] = {"kind": "mesh", "mesh": "main", "entity": "node", "ids": "left_ids",
                                        "physical_group": {"dimension": 1, "tag": 2}}
            arrays["left_ids"] = np.array(sorted(mesh["groups"][(1, 2)]["nodes"]), dtype=np.int64)
            m["locations"]["edges"] = {"kind": "mesh", "mesh": "main", "entity": "element",
                                         "dimension": 1, "ids": "edge_ids", "physical_group": {"dimension": 1, "tag": 3}}
            arrays["edge_ids"] = np.array(sorted(mesh["groups"][(1, 3)]["elements"]), dtype=np.int64)
            m["locations"]["probes"] = {"kind": "points", "ids": "probe_ids", "coordinates": "probe_coordinates"}
            arrays["probe_ids"] = np.array([5, 808], dtype=np.int64)
            arrays["probe_coordinates"] = np.array([[0.2, 0.1], [0.4, 0.3]], dtype=np.float64)
            add_field(m, arrays, "left_temperature", "left", unit="K")
            add_field(m, arrays, "edge_flux", "edges", value_kind="integral", unit="W")
            add_field(m, arrays, "probe_temperature", "probes", unit="K")
            m["physics"] = {"model": "identity", "parameters": {"conductivity": {"value": 1.0, "unit": "W/(m.K)"}}}
            m["conditions"] = [
                {"role": "boundary", "variable": "temperature", "location": "left", "operator": "dirichlet",
                 "data": {"value": {"field": "left_temperature"}}},
                {"role": "initial", "variable": "temperature", "location": "nodes", "operator": "assign",
                 "data": {"value": {"value": 100.0, "unit": "K"}}},
                {"role": "source", "variable": "heat_source", "location": "nodes", "operator": "assign",
                 "data": {"value": {"value": 0.0, "unit": "W/m3"}}},
                {"role": "material", "variable": "conductivity", "location": "nodes", "operator": "assign",
                 "data": {"value": {"value": 1.0, "unit": "W/(m.K)"}}},
            ]
        elif index == 12:
            arrays["times"] = np.array([-0.25, 0.125, 2.0], dtype=np.float64)
            add_field(m, arrays, "velocity", kind="vector", unit="m/s")
        else:
            add_field(m, arrays, "temperature", unit="K")
        write_hdf5(directory / 'input.h5', arrays)
        write_json(directory / "problem.json", m)
    return len(CASE_NAMES)
