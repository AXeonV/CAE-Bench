"""Geometry of first-order CFD cells; independent of mesh tag ordering."""
from collections import Counter, defaultdict
from itertools import product

import numpy as np

# Gmsh first-order types, local facet vertices in the Gmsh node convention.
FACETS = {
    2: ((0,1),(1,2),(2,0)),
    3: ((0,1),(1,2),(2,3),(3,0)),
    4: ((0,1,2),(0,3,1),(1,3,2),(2,3,0)),
    5: ((0,1,2,3),(4,5,6,7),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)),
    6: ((0,1,2),(3,4,5),(0,3,4,1),(1,4,5,2),(2,5,3,0)),
    7: ((0,1,2,3),(0,4,1),(1,4,2),(2,4,3),(3,4,0)),
}


def exterior_facets(mesh, dimension):
    """Return exterior facet node sets and their unique adjacent volume cell."""
    counts = Counter(); owner = {}; parent={tag:tag for tag in mesh['elements'][dimension]}
    def root(tag):
        while parent[tag]!=tag:
            parent[tag]=parent[parent[tag]];tag=parent[tag]
        return tag
    for tag in mesh['elements'][dimension]:
        typ, conn = mesh['connectivity'][tag]
        if typ not in FACETS:
            raise ValueError('CFD profile requires first-order triangle/quad/tet/hex/prism/pyramid cells')
        for local in FACETS[typ]:
            key = frozenset(conn[i] for i in local)
            if key in owner:parent[root(tag)]=root(owner[key])
            counts[key] += 1; owner[key] = tag
    if len({root(tag) for tag in parent})!=1:
        raise ValueError('CFD 2.1 requires one facet-connected fluid domain')
    if any(n > 2 for n in counts.values()):
        raise ValueError('Nonmanifold cell facets are not supported')
    return {key:owner[key] for key,n in counts.items() if n == 1}


def boundary_geometry(problem, location):
    """Return facet centroids, outward normals and measures in location ID order.

    In 2D measures are edge lengths; integrated flow/force is per unit depth.
    Triangulates planar quad facets; rejects degenerate/nonplanar facets.
    """
    loc = problem.manifest['locations'][location]
    d = problem.manifest['spatial_dimension']
    if loc['kind'] != 'mesh' or loc['entity'] != 'element' or loc['dimension'] != d-1:
        raise ValueError('Expected a codimension-one element location')
    mesh = problem.meshes[loc['mesh']]; exterior = exterior_facets(mesh,d)
    centers=[]; normals=[]; measures=[]
    for tag in problem.arrays[loc['ids']]:
        typ,conn = mesh['connectivity'][int(tag)]
        if typ not in ((1,) if d == 2 else (2,3)):
            raise ValueError('Expected first-order boundary edges/triangles/quads')
        key = frozenset(conn)
        if key not in exterior: raise ValueError('Boundary facet is not exterior')
        points=np.array([mesh['node_coordinates'][i][:d] for i in conn])
        center=points.mean(axis=0)
        cell=mesh['connectivity'][exterior[key]][1]
        inside=np.mean([mesh['node_coordinates'][i][:d] for i in cell],axis=0)
        if d == 2:
            tangent=points[1]-points[0];measure=np.linalg.norm(tangent)
            normal=np.array([tangent[1],-tangent[0]])
        else:
            cross=np.cross(points[1]-points[0],points[2]-points[0])
            length=np.linalg.norm(cross)
            if not length:raise ValueError('Degenerate boundary facet')
            normal=cross/length;measure=length/2
            if len(points)==4:
                scale=max(np.max(np.linalg.norm(points-center,axis=1)),np.finfo(float).tiny)
                if abs(np.dot(points[3]-points[0],normal)) > 1e-10*scale:
                    raise ValueError('CFD profile requires planar quad boundary facets')
                other=np.cross(points[2]-points[0],points[3]-points[0])
                if np.dot(cross,other)<=0:raise ValueError('Folded quad boundary facet')
                other_area=np.linalg.norm(other)/2
                center=(measure*points[:3].mean(axis=0)+other_area*points[[0,2,3]].mean(axis=0))/(measure+other_area)
                measure+=other_area
        if measure<=0 or not np.isfinite(measure):raise ValueError('Degenerate boundary facet')
        normal=normal/np.linalg.norm(normal)
        if np.dot(normal,center-inside)<0:normal=-normal
        if np.dot(normal,center-inside)<=0:raise ValueError('Ambiguous outward boundary normal')
        centers.append(center);normals.append(normal);measures.append(measure)
    return np.array(centers),np.array(normals),np.array(measures)


def periodic_face_pairs(problem, location, partner, translation):
    """Match translated exterior facets with opposite normals, independent of IDs.

    Uses spatial bins of facet centroids, then verifies every vertex. Ambiguous
    coincident facets and non-bijective maps are rejected.
    """
    locs=problem.manifest['locations'];d=problem.manifest['spatial_dimension']
    mesh=problem.meshes[locs[location]['mesh']]
    if locs[partner]['mesh']!=locs[location]['mesh']:raise ValueError('Periodic faces require the same mesh')
    left=problem.arrays[locs[location]['ids']];right=problem.arrays[locs[partner]['ids']]
    if len(left)!=len(right):raise ValueError('Periodic sides have different facet counts')
    ca,na,_=boundary_geometry(problem,location);cb,nb,_=boundary_geometry(problem,partner)
    delta=np.asarray(translation,dtype=float)
    if delta.shape!=(d,) or not np.all(np.isfinite(delta)):raise ValueError('Invalid periodic translation')
    scale=np.max(np.ptp(mesh['coordinates'][:,:d],axis=0))
    tolerance=1e-10*scale+8*np.finfo(float).eps*np.max(np.abs(mesh['coordinates']))
    if tolerance<=0:raise ValueError('Degenerate periodic geometry')
    origin=cb.min(axis=0);bins=defaultdict(list)
    def key(x):return tuple(np.floor((x-origin)/tolerance).astype('int64'))
    for j,x in enumerate(cb):bins[key(x)].append(j)
    def vertices(tag):return np.array([mesh['node_coordinates'][n][:d] for n in mesh['connectivity'][int(tag)][1]])
    used=set();pairs=[]
    for i,tag in enumerate(left):
        point=ca[i]+delta;bucket=key(point);candidates=[];a=vertices(tag)+delta
        for offset in product((-1,0,1),repeat=d):
            for j in bins.get(tuple(x+y for x,y in zip(bucket,offset)),()):
                if not np.allclose(point,cb[j],rtol=0,atol=tolerance):continue
                b=vertices(right[j])
                if len(a)!=len(b):continue
                match=np.max(np.abs(a[:,None,:]-b[None,:,:]),axis=-1)<=tolerance
                if np.all(match.sum(axis=0)==1) and np.all(match.sum(axis=1)==1):candidates.append(j)
        if len(candidates)!=1 or candidates[0] in used:raise ValueError('Periodic facet map is missing, ambiguous or non-bijective')
        j=candidates[0]
        if not np.allclose(na[i],-nb[j],rtol=0,atol=1e-8):raise ValueError('Periodic outward normals must be opposite')
        used.add(j);pairs.append((int(tag),int(right[j])))
    return pairs
