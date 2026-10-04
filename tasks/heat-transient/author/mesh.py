"""Gmsh rectangle writer and tag-based reader for author tools."""
from pathlib import Path

import gmsh
import numpy as np

from caeoj.validation import GMSH_LOCK


def generate_mesh(case, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    with GMSH_LOCK:
        gmsh.initialize([], readConfigFiles=False)
        try:
            gmsh.option.setNumber('General.Terminal', 0)
            gmsh.option.setNumber('Mesh.RandomSeed', 1)
            gmsh.model.add(case.name)
            geo = gmsh.model.geo
            x, y = case.origin
            lx, ly = case.size
            h = min(lx/case.nx, ly/case.ny)
            points = [geo.addPoint(a, b, 0, h) for a, b in
                      ((x, y), (x+lx, y), (x+lx, y+ly), (x, y+ly))]
            curves = [geo.addLine(points[i], points[(i+1) % 4]) for i in range(4)]
            surface = geo.addPlaneSurface([geo.addCurveLoop(curves)])
            geo.synchronize()
            if not case.unstructured:
                for i, curve in enumerate(curves):
                    gmsh.model.mesh.setTransfiniteCurve(curve, (case.nx if i % 2 == 0 else case.ny)+1)
                gmsh.model.mesh.setTransfiniteSurface(surface, 'AlternateLeft')
            gmsh.model.addPhysicalGroup(2, [surface], 1, 'domain')
            for tag, name, curve in zip(range(2, 6), ('left', 'right', 'bottom', 'top'),
                                        (curves[3], curves[1], curves[0], curves[2])):
                gmsh.model.addPhysicalGroup(1, [curve], tag, name)
            gmsh.model.mesh.generate(2)
            if case.sparse:
                tags = gmsh.model.mesh.getNodes()[0]
                gmsh.model.mesh.renumberNodes(tags, 101+13*np.arange(len(tags), dtype=np.uint64))
                tags = np.concatenate(gmsh.model.mesh.getElements()[1])
                gmsh.model.mesh.renumberElements(tags, 211+17*np.arange(len(tags), dtype=np.uint64))
            gmsh.option.setNumber('Mesh.MshFileVersion', 4.1)
            gmsh.option.setNumber('Mesh.Binary', int(case.binary))
            gmsh.option.setNumber('Mesh.SaveAll', 1)
            gmsh.write(str(directory/'mesh.geo_unrolled'))
            (directory/'mesh.geo_unrolled').replace(directory/'mesh.geo')
            gmsh.write(str(directory/'mesh.msh'))
        finally:
            gmsh.finalize()


def read_mesh(path, node_ids=None):
    with GMSH_LOCK:
        gmsh.initialize([], readConfigFiles=False)
        try:
            gmsh.option.setNumber('General.Terminal', 0)
            gmsh.open(str(Path(path)))
            tags, xyz, _ = gmsh.model.mesh.getNodes()
            order = np.argsort(tags)
            tags, xyz = tags[order].astype(np.int64), xyz.reshape(-1, 3)[order, :2]
            if node_ids is not None and not np.array_equal(tags, node_ids):
                raise ValueError('Input node IDs must cover the mesh in tag order')
            elements = {}
            for dim, typ, width in ((1, 1, 2), (2, 2, 3)):
                types, blocks, conn = gmsh.model.mesh.getElements(dim)
                if any(t != typ for t in types):
                    raise ValueError('Only first-order triangles and lines are supported')
                element_tags = np.concatenate(blocks).astype(np.int64)
                connectivity = np.concatenate([c.reshape(-1, width) for c in conn])
                order = np.argsort(element_tags)
                elements[dim] = (element_tags[order], np.searchsorted(tags, connectivity[order]))
            groups = {}
            for dim, group in gmsh.model.getPhysicalGroups():
                ids = [np.concatenate(gmsh.model.mesh.getElements(dim, int(e))[1])
                       for e in gmsh.model.getEntitiesForPhysicalGroup(dim, group)]
                groups[dim, group] = np.sort(np.concatenate(ids).astype(np.int64))
            return tags, xyz, elements, groups
        finally:
            gmsh.finalize()
