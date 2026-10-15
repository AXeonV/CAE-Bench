"""Checks for protocol structure and opt-in physical declarations.

No value repair, PDE solution validation or answer comparison lives here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from importlib.resources import files
import itertools
import json
import math
from pathlib import Path, PureWindowsPath
import threading
import uuid

import gmsh
import numpy as np
from jsonschema import Draft202012Validator, validators
from .storage import read_arrays

GMSH_LOCK = threading.Lock()
Validator = validators.extend(Draft202012Validator, type_checker=
    Draft202012Validator.TYPE_CHECKER.redefine("integer", lambda _, x: type(x) is int))


def _preview(value):
    if isinstance(value, np.ndarray):
        return {"shape": list(value.shape), "dtype": str(value.dtype)}
    if isinstance(value, np.generic):
        return _preview(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return repr(value)
    if isinstance(value, list):
        return [_preview(x) for x in value[:8]] + (["..."] if len(value) > 8 else [])
    if isinstance(value, dict):
        return {k: _preview(v) for k, v in list(value.items())[:8]}
    return value


def issue(code, path, expected, actual, message):
    return {"code": code, "path": path, "expected": _preview(expected),
            "actual": _preview(actual), "message": message}


def report(errors):
    return {"valid": not errors, "errors": errors}


class ContractError(ValueError):
    def __init__(self, diagnostics):
        self.report = diagnostics
        super().__init__(json.dumps(diagnostics, ensure_ascii=True, allow_nan=False))


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(report([issue("E_DUPLICATE_KEY", "$", "unique JSON keys", key,
                                               "Duplicate JSON key.")]))
        result[key] = value
    return result


def read_json(path):
    def reject(token):
        raise ValueError(f"Nonfinite JSON token: {token}")
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"),
                          object_pairs_hook=_pairs, parse_constant=reject)
    except ContractError:
        raise
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        raise ContractError(report([issue("E_JSON", "$", "UTF-8 JSON", str(exc),
                                          "Cannot read metadata.")])) from exc


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


@lru_cache(maxsize=1)
def _validator():
    schema = json.loads(files("caeoj").joinpath("problem.schema.json").read_text(encoding="utf-8"))
    Validator.check_schema(schema)
    return Validator(schema)


def _path(parts):
    return "$" + "".join(f"[{p}]" if isinstance(p, int) else f".{p}" for p in parts)


def schema_errors(document):
    errors = []
    def scan(value, path):
        if type(value) in (int, float):
            try:
                finite = math.isfinite(value)
            except OverflowError:
                finite = False
            if not finite:
                errors.append(issue("E_FINITE", path, "finite number", str(value), "Invalid metadata number."))
        elif isinstance(value, dict):
            for key, item in value.items():
                scan(item, path + "." + key)
        elif isinstance(value, list):
            for i, item in enumerate(value):
                scan(item, f"{path}[{i}]")
    scan(document, "$")
    errors.extend(issue("E_SCHEMA", _path(e.absolute_path), {e.validator: e.validator_value},
                        e.instance, e.message)
                  for e in sorted(_validator().iter_errors(document), key=lambda e: _path(e.absolute_path)))
    return errors


def resolve_file(base, name, suffixes):
    """Protocol references are package-relative POSIX paths, never CWD-relative."""
    parts = name.split("/")
    if ("\\" in name or PureWindowsPath(name).drive or name.startswith("/") or
            any(part in ("", ".", "..") for part in parts)):
        raise ValueError("Expected a package-relative path with '/' and no '.' or '..' segments.")
    path = (base / name).resolve()
    if not path.is_relative_to(base.resolve()):
        raise ValueError("Referenced file escapes the data package.")
    if path.suffix.lower() not in suffixes:
        raise ValueError(f"Expected extension in {sorted(suffixes)}.")
    if not path.is_file():
        raise ValueError("Referenced file does not exist.")
    return path


def read_hdf5(path):
    try:
        return read_arrays(path)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise ContractError(report([issue("E_HDF5", str(path), "named numeric HDF5 arrays", str(exc),
                                          "Cannot read array payload.")])) from exc


def read_mesh(path, *, geometry=False):
    """Use the official Gmsh reader and element definitions, not a new mesh parser."""
    try:
        with path.open("rb") as stream:
            if stream.readline().strip() != b"$MeshFormat":
                raise ValueError("Missing MSH header.")
            header = stream.readline().split()
            if header != [b"4.1", b"0", b"8"]:
                raise ValueError("Expected Gmsh MSH 4.1 ASCII with header '4.1 0 8'.")
        with GMSH_LOCK:
            owned = not gmsh.isInitialized()
            if owned:
                gmsh.initialize([], readConfigFiles=False)
            previous = gmsh.model.getCurrent()
            terminal = gmsh.option.getNumber("General.Terminal")
            temporary = "caeoj_check_" + uuid.uuid4().hex
            try:
                gmsh.option.setNumber("General.Terminal", 0)
                gmsh.model.add(temporary)
                gmsh.merge(str(path))
                node_tags, coords, _ = gmsh.model.mesh.getNodes()
                if not np.all(np.isfinite(coords)):
                    raise ValueError("Mesh coordinates must be finite.")
                nodes = set(map(int, node_tags))
                elements = {}; connectivity_by_tag = {}
                for dim in range(4):
                    types, tag_blocks, connectivity = gmsh.model.mesh.getElements(dim)
                    ids = set()
                    for typ, tags, conn in zip(types, tag_blocks, connectivity):
                        _, actual_dim, _, arity, _, _ = gmsh.model.mesh.getElementProperties(int(typ))
                        if actual_dim != dim or len(conn) != len(tags) * arity:
                            raise ValueError("Invalid element connectivity shape.")
                        if not set(map(int, conn)).issubset(nodes):
                            raise ValueError("Connectivity references missing nodes.")
                        ids.update(map(int, tags))
                        if geometry:
                            connectivity_by_tag.update({int(tag): (int(typ), tuple(map(int, row)))
                                for tag, row in zip(tags, np.asarray(conn).reshape(-1, arity))})
                    elements[dim] = ids
                all_ids = nodes | set().union(*elements.values())
                if not nodes or any(i <= 0 or i > np.iinfo(np.int64).max for i in all_ids):
                    raise ValueError("Mesh needs positive int64-compatible tags and at least one node.")
                groups = {}
                for dim, tag in gmsh.model.getPhysicalGroups():
                    group_nodes = set(map(int, gmsh.model.mesh.getNodesForPhysicalGroup(dim, tag)[0]))
                    group_elements = set()
                    for entity in gmsh.model.getEntitiesForPhysicalGroup(dim, tag):
                        group_elements.update(int(i) for block in gmsh.model.mesh.getElements(dim, int(entity))[1]
                                              for i in block)
                    groups[(dim, tag)] = {"nodes": group_nodes, "elements": group_elements}
                result = {"nodes": nodes, "elements": elements, "groups": groups,
                        "coordinates": np.asarray(coords).reshape(-1, 3),
                        "dimension": max(dim for dim, ids in elements.items() if ids)}
                if geometry:
                    result.update(node_coordinates={int(tag): xyz for tag, xyz in
                        zip(node_tags, np.asarray(coords).reshape(-1, 3))},
                        connectivity=connectivity_by_tag)
                return result
            finally:
                if owned:
                    gmsh.finalize()
                else:
                    if temporary in gmsh.model.list():
                        gmsh.model.setCurrent(temporary)
                        gmsh.model.remove()
                    if previous in gmsh.model.list():
                        gmsh.model.setCurrent(previous)
                    gmsh.option.setNumber("General.Terminal", terminal)
    except Exception as exc:
        raise ContractError(report([issue("E_MESH", str(path), "Gmsh MSH 4.1 ASCII (4.1 0 8)", str(exc),
                                          "Cannot read mesh structure.")])) from exc


@dataclass
class Problem:
    path: Path
    manifest: dict
    arrays: dict
    meshes: dict = field(default_factory=dict)


class Checker:
    def __init__(self, problem, errors):
        self.problem, self.m, self.errors = problem, problem.manifest, errors
        self.used = set()

    def fail(self, code, path, expected, actual, message):
        self.errors.append(issue(code, path, expected, actual, message))

    def expect(self, actual, expected, path, code="E_METADATA"):
        if actual != expected:
            self.fail(code, path, expected, actual, "Does not match the declared contract.")

    def array(self, key, dtype, shape, path, payload=None):
        self.used.add(key)
        arrays = self.problem.arrays if payload is None else payload
        value = arrays.get(key)
        if value is None:
            self.fail("E_ARRAY", path, key, "missing", "Referenced array is missing.")
            return None
        if value.dtype.name != dtype or value.dtype.fields is not None:
            self.fail("E_DTYPE", path, dtype, str(value.dtype), "Array dtype mismatch; no casting.")
        if shape is not None:
            self.expect(list(value.shape), list(shape), path, "E_SHAPE")
        if value.dtype.kind in "fci" and not np.all(np.isfinite(value)):
            self.fail("E_FINITE", path, "finite array entries", "NaN or Inf", "Nonfinite payload value.")
        return value

    def ids(self, key, path):
        value = self.array(key, "int64", None, path)
        if value is None:
            return None
        if value.ndim != 1 or value.size == 0:
            self.fail("E_SHAPE", path, "nonempty [N]", value, "IDs require one entity axis.")
            return None
        if value.dtype.name != "int64":
            return None
        if np.any(value < 0) or np.any(value[1:] <= value[:-1]):
            self.fail("E_ID", path, "nonnegative strictly increasing int64 IDs", value.tolist(),
                      "IDs must be unique and in the prescribed order.")
        return value

    def locations(self):
        for name, loc in self.m["locations"].items():
            path = "$.locations." + name
            ids = self.ids(loc["ids"], path + ".ids")
            if loc['kind'] == 'aggregate':
                source = self.m['locations'].get(loc['source'])
                if (not source or source['kind'] != 'mesh' or source['entity'] != 'element'):
                    self.fail('E_REFERENCE', path+'.source', 'mesh element location', loc['source'],
                              'Aggregate source must be a mesh element region.')
                if ids is not None and len(ids) != 1:
                    self.fail('E_SHAPE', path+'.ids', 'one aggregate ID', ids, 'Aggregate has one result entity.')
                continue
            if loc["kind"] == "points":
                if ids is not None:
                    self.array(loc["coordinates"], "float64", [len(ids), self.m["spatial_dimension"]],
                               path + ".coordinates")
                continue
            mesh = self.problem.meshes.get(loc["mesh"])
            if mesh is None:
                self.fail("E_REFERENCE", path + ".mesh", "declared readable mesh", loc["mesh"], "Unknown mesh.")
                continue
            if loc["entity"] == "node":
                if "dimension" in loc:
                    self.fail("E_METADATA", path + ".dimension", "absent for nodes", loc["dimension"],
                              "Node selection has no element dimension.")
                known = mesh["nodes"]
            else:
                if "dimension" not in loc:
                    self.fail("E_METADATA", path + ".dimension", "element dimension", "missing", "Required dimension.")
                    continue
                known = mesh["elements"][loc["dimension"]]
            if ids is not None and not set(map(int, ids)).issubset(known):
                self.fail("E_REFERENCE", path + ".ids", "tags of the declared entity table", ids.tolist(),
                          "Selection references unknown mesh tags.")
            if "physical_group" in loc:
                group = loc["physical_group"]
                g = mesh["groups"].get((group["dimension"], group["tag"]))
                if g is None:
                    self.fail("E_REFERENCE", path + ".physical_group", "existing (dimension, tag)", group,
                              "Unknown Physical Group.")
                else:
                    if loc["entity"] == "element":
                        self.expect(loc["dimension"], group["dimension"], path + ".physical_group.dimension")
                    if ids is not None:
                        required = g["nodes" if loc["entity"] == "node" else "elements"]
                        self.expect(ids.tolist(), sorted(required), path + ".ids", "E_ID")

    def times(self):
        for name, key in self.m["time_axes"].items():
            path = "$.time_axes." + name
            a = self.array(key, "float64", None, path)
            if a is not None:
                if a.ndim != 1 or a.size == 0:
                    self.fail("E_SHAPE", path, "nonempty [T]", a, "Time requires one axis.")
                elif a.dtype.kind == "f" and np.any(a[1:] <= a[:-1]):
                    self.fail("E_TIME", path, "strictly increasing seconds", a.tolist(), "Invalid time order.")

    def field_spec(self, spec, path):
        loc = self.m["locations"].get(spec["location"])
        time_key = self.m["time_axes"].get(spec["time_axis"])
        if loc is None or time_key is None:
            self.fail("E_REFERENCE", path, "existing location and time axis", spec, "Unknown field reference.")
            return None
        shape, labels = spec["component_shape"], spec["components"]
        dim = self.m["spatial_dimension"]
        axes = list("xyz"[:dim])
        if spec["kind"] == "scalar":
            self.expect(shape, [1], path + ".component_shape", "E_COMPONENTS")
            self.expect(labels, ["value"], path + ".components", "E_COMPONENTS")
        elif spec["kind"] in ("vector", "tensor"):
            rank = 1 if spec["kind"] == "vector" else 2
            self.expect(shape, [dim] * rank, path + ".component_shape", "E_COMPONENTS")
            self.expect(labels, ["".join(x) for x in itertools.product(axes, repeat=rank)],
                        path + ".components", "E_COMPONENTS")
        self.expect(len(labels), math.prod(shape), path + ".components", "E_COMPONENTS")
        if loc["kind"] == "points" or loc.get("entity") == "node":
            self.expect(spec["value_kind"], "point", path + ".value_kind")
        elif loc['kind'] == 'aggregate':
            self.expect(spec['value_kind'], 'integral' if loc['operation']=='sum' else 'average',
                        path+'.value_kind')
        elif spec["value_kind"] == "point":
            self.fail("E_METADATA", path + ".value_kind", "average or integral", "point",
                      "Element point values require an explicit point location instead.")
        ids, times = self.problem.arrays.get(loc["ids"]), self.problem.arrays.get(time_key)
        if ids is None or times is None or ids.ndim != 1 or times.ndim != 1:
            return None
        return [len(times), len(ids), *shape]

    def fields(self):
        for table in ("fields", "outputs"):
            seen = set()
            for name, spec in self.m[table].items():
                path = f"$.{table}.{name}"
                if spec["array"] in seen:
                    self.fail("E_ARRAY", path + ".array", "unique field array key", spec["array"], "Array aliasing forbidden.")
                seen.add(spec["array"])
                shape = self.field_spec(spec, path)
                if table == "fields":
                    if self.m['locations'].get(spec['location'], {}).get('kind') == 'aggregate':
                        self.fail('E_METADATA', path+'.location', 'non-aggregate input location',
                                  spec['location'], 'Aggregate locations are output-only.')
                    self.array(spec["array"], spec["dtype"], shape, path + ".array")
        support = {loc["ids"] for loc in self.m["locations"].values()} | set(self.m["time_axes"].values())
        support |= {loc["coordinates"] for loc in self.m["locations"].values() if loc["kind"] == "points"}
        # A payload key must have one role; no field can overwrite IDs, times or coordinates.
        for spec in [*self.m["fields"].values(), *self.m["outputs"].values()]:
            if spec["array"] in support:
                self.fail("E_ARRAY", "$.fields/outputs", "field key distinct from support keys", spec["array"],
                          "Field and support arrays cannot share a key.")
        for loc in self.m["locations"].values():
            if loc["ids"] in self.m["time_axes"].values():
                self.fail("E_ARRAY", "$.locations", "distinct ID and time keys", loc["ids"], "Conflicting array roles.")
            if loc["kind"] == "points" and loc["coordinates"] in (
                    {x["ids"] for x in self.m["locations"].values()} | set(self.m["time_axes"].values())):
                self.fail("E_ARRAY", "$.locations", "coordinate key distinct from IDs and times",
                          loc["coordinates"], "Conflicting array roles.")

    def conditions(self):
        for i, condition in enumerate(self.m["conditions"]):
            path = f"$.conditions[{i}]"
            if condition["location"] not in self.m["locations"]:
                self.fail("E_REFERENCE", path + ".location", "declared location", condition["location"], "Unknown location.")
            elif self.m['locations'][condition['location']]['kind'] == 'aggregate':
                self.fail('E_METADATA', path+'.location', 'non-aggregate location', condition['location'],
                          'Aggregates are output observations, not condition locations.')
            for name, value in condition["data"].items():
                if "field" in value:
                    spec = self.m["fields"].get(value["field"])
                    if spec is None:
                        self.fail("E_REFERENCE", path + ".data." + name, "input field", value, "Unknown condition field.")
                    else:
                        compatible = spec['location'] == condition['location']
                        if not compatible and self.m.get('profile') == 'cfd-2.1' and not self.errors:
                            source = self.m['locations'].get(spec['location'], {})
                            target = self.m['locations'].get(condition['location'], {})
                            if (source.get('kind') == target.get('kind') == 'mesh' and
                                source.get('entity') == 'node' and target.get('entity') == 'element' and
                                source['mesh'] == target['mesh']):
                                mesh = self.problem.meshes.get(source['mesh'], {})
                                tags = self.problem.arrays.get(target['ids'], [])
                                connectivity = mesh.get('connectivity', {})
                                nodes = set(n for tag in tags if int(tag) in connectivity
                                            for n in connectivity[int(tag)][1])
                                ids = self.problem.arrays.get(source['ids'], [])
                                compatible = set(map(int, ids)) == nodes and bool(nodes)
                        if not compatible:
                            if self.m.get('profile') == 'cfd-2.1':
                                self.fail('E_REFERENCE', path+'.data.'+name+'.field.location',
                                          'same location or exact CFD region node set', spec['location'],
                                          'Condition field does not cover its geometric region.')
                            else:
                                self.expect(spec['location'], condition['location'],
                                            path+'.data.'+name+'.field.location')
                elif 'location' in value and value['location'] not in self.m['locations']:
                    self.fail('E_REFERENCE', path+'.data.'+name+'.location', 'declared location',
                              value['location'], 'Unknown condition location reference.')


def check_problem(path):
    errors = []
    try:
        path = Path(path).resolve()
        m = read_json(path)
        errors = schema_errors(m)
        if errors:
            return None, report(errors)
        base = path.parent
        arrays = read_hdf5(resolve_file(base, m["data_file"], {".h5"}))
        p = Problem(path, m, arrays)
        for name, geometry in m["geometries"].items():
            suffixes = {"gmsh-geo": {".geo"}, "step": {".step", ".stp"}, "brep": {".brep"}}
            try:
                resolve_file(base, geometry["file"], suffixes[geometry["format"]])
            except ValueError as exc:
                errors.append(issue("E_FILE", "$.geometries." + name, "existing geometry file", str(exc), "Invalid file reference."))
        for name, spec in m["meshes"].items():
            if "geometry" in spec and spec["geometry"] not in m["geometries"]:
                errors.append(issue("E_REFERENCE", "$.meshes." + name + ".geometry", "geometry ID", spec["geometry"], "Unknown geometry."))
            try:
                p.meshes[name] = read_mesh(resolve_file(base, spec["file"], {".msh"}),
                                           geometry=(m.get('profile') == 'cfd-2.1' or
                                                     m.get('physics', {}).get('model', '').startswith(
                                                         ('fluid-energy-', 'fluid-multiphase-', 'fluid-reduced-'))))
                if p.meshes[name]["dimension"] > m["spatial_dimension"]:
                    errors.append(issue("E_DIMENSION", "$.meshes." + name, "topology <= spatial_dimension",
                                        p.meshes[name]["dimension"], "Topology exceeds the declared space."))
                if np.any(p.meshes[name]["coordinates"][:, m["spatial_dimension"]:] != 0):
                    errors.append(issue("E_DIMENSION", "$.meshes." + name, "zero unused Cartesian coordinates",
                                        "nonzero omitted coordinate", "Use spatial_dimension=3 for an embedded mesh."))
            except ContractError as exc:
                errors.extend(exc.report["errors"])
            except ValueError as exc:
                errors.append(issue("E_FILE", "$.meshes." + name, "existing mesh file", str(exc), "Invalid file reference."))
        checker = Checker(p, errors)
        checker.locations()
        checker.times()
        checker.fields()
        checker.conditions()
        if m.get('profile') == 'cfd-2.1' and not errors:
            from .cfd import check_cfd
            check_cfd(p, errors)
        if not errors:
            model = m.get('physics', {}).get('model', '')
            if model.startswith('fluid-energy-'):
                from .fluid_energy import check_fluid_energy
                check_fluid_energy(p, errors)
            elif model.startswith('fluid-multiphase-'):
                from .fluid_multiphase import check_fluid_multiphase
                check_fluid_multiphase(p, errors)
            elif model.startswith('fluid-reduced-'):
                from .fluid_reduced import check_fluid_reduced
                check_fluid_reduced(p, errors)
        checker.expect(sorted(arrays), sorted(checker.used), "$.data_file", "E_ARRAYS")
        return p, report(errors)
    except ContractError as exc:
        return None, exc.report
    except (OSError, ValueError) as exc:
        return None, report([issue("E_FILE", "$", "readable input package", str(exc), "Invalid package reference.")])


def validate_input(path):
    return check_problem(path)[1]


def output_support(problem):
    m = problem.manifest
    return {key for spec in m["outputs"].values()
            for key in (m["locations"][spec["location"]]["ids"], m["time_axes"][spec["time_axis"]])}


def check_result(problem, arrays):
    errors = []
    checker = Checker(problem, errors)
    required = output_support(problem) | {s["array"] for s in problem.manifest["outputs"].values()}
    checker.expect(sorted(arrays), sorted(required), "$h5.keys", "E_ARRAYS")
    for key in sorted(output_support(problem)):
        expected = problem.arrays[key]
        actual = checker.array(key, expected.dtype.name, expected.shape, "$h5." + key, arrays)
        if (actual is not None and actual.dtype.name == expected.dtype.name and
                actual.dtype.fields is None and actual.shape == expected.shape and
                not np.array_equal(actual, expected)):
            checker.fail("E_ORDER", "$h5." + key, "exact input IDs/time values in input order", actual,
                         "Support axis differs from the prescribed axis; no reordering.")
    for name, spec in problem.manifest["outputs"].items():
        shape = checker.field_spec(spec, "$.outputs." + name)
        checker.array(spec["array"], spec["dtype"], shape, "$h5." + spec["array"], arrays)
    return report(errors)


def validate_output(input_path, output_path):
    p, diagnostics = check_problem(input_path)
    if not diagnostics["valid"]:
        return diagnostics
    try:
        return check_result(p, read_hdf5(output_path))
    except ContractError as exc:
        return exc.report
