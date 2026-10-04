"""Uniform Cartesian Gmsh triangles; numbering and encoding remain Gmsh's."""
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
            gmsh.model.add(case.name)
            geo = gmsh.model.geo
            x, y = case.origin
            lx, ly = case.size
            p = [geo.addPoint(a, b, 0) for a, b in ((x,y),(x+lx,y),(x+lx,y+ly),(x,y+ly))]
            curves = [geo.addLine(p[i], p[(i+1)%4]) for i in range(4)]
            surface = geo.addPlaneSurface([geo.addCurveLoop(curves)])
            geo.synchronize()
            for curve in curves:
                gmsh.model.mesh.setTransfiniteCurve(curve, case.n+1)
            gmsh.model.mesh.setTransfiniteSurface(surface, 'AlternateLeft')
            gmsh.model.addPhysicalGroup(2, [surface], 1, 'domain')
            for tag, name, curve in zip(range(2,6), ('left','right','bottom','top'),
                                        (curves[3],curves[1],curves[0],curves[2])):
                gmsh.model.addPhysicalGroup(1, [curve], tag, name)
            if case.family == 'periodic' or case.family == 'channel' and case.axis == 0:
                gmsh.model.mesh.setPeriodic(1,[curves[1]],[curves[3]],
                    [1,0,0,lx, 0,1,0,0, 0,0,1,0, 0,0,0,1])
            if case.family == 'periodic' or case.family == 'channel' and case.axis == 1:
                gmsh.model.mesh.setPeriodic(1,[curves[2]],[curves[0]],
                    [1,0,0,0, 0,1,0,ly, 0,0,1,0, 0,0,0,1])
            gmsh.model.mesh.generate(2)
            # Remove Gmsh's tiny transfinite roundoff so every nominal grid row
            # represents exactly the same transverse coordinate/profile sample.
            tags,xyz,_=gmsh.model.mesh.getNodes()
            for tag,point in zip(tags,xyz.reshape(-1,3)):
                i=int(round((point[0]-x)/lx*case.n));j=int(round((point[1]-y)/ly*case.n))
                gmsh.model.mesh.setNode(int(tag),[x+lx*i/case.n,y+ly*j/case.n,0],[])
            if case.sparse:
                tags = gmsh.model.mesh.getNodes()[0]
                gmsh.model.mesh.renumberNodes(tags, 101+13*np.arange(len(tags),dtype=np.uint64))
            gmsh.option.setNumber('Mesh.MshFileVersion', 4.1)
            gmsh.option.setNumber('Mesh.Binary', int(case.binary))
            gmsh.write(str(directory/'mesh.msh'))
            gmsh.write(str(directory/'mesh.geo_unrolled'))
            (directory/'mesh.geo_unrolled').replace(directory/'mesh.geo')
            ids, xyz, _ = gmsh.model.mesh.getNodes()
            order = np.argsort(ids)
            groups = {}
            for dim, tag in gmsh.model.getPhysicalGroups():
                tags, _ = gmsh.model.mesh.getNodesForPhysicalGroup(dim,tag)
                groups[(dim,tag)] = np.sort(tags.astype(np.int64))
            return ids[order].astype(np.int64), xyz.reshape(-1,3)[order,:2], groups
        finally:
            gmsh.finalize()
