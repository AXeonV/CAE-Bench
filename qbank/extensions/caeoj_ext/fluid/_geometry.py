"""Fluid-domain restrictions layered on neutral mesh primitives."""
from caeoj.mesh_geometry import FACETS, boundary_geometry, periodic_face_pairs
from caeoj.mesh_geometry import exterior_facets as _exterior_facets


def exterior_facets(mesh, dimension):
    """Exterior facets of exactly one facet-connected fluid domain."""
    result = _exterior_facets(mesh, dimension)
    parent = {tag: tag for tag in mesh['elements'][dimension]}
    def root(tag):
        while parent[tag] != tag:
            parent[tag] = parent[parent[tag]]
            tag = parent[tag]
        return tag
    owner = {}
    for tag in parent:
        typ, nodes = mesh['connectivity'][tag]
        for local in FACETS[typ]:
            facet = frozenset(nodes[i] for i in local)
            if facet in owner:
                parent[root(tag)] = root(owner[facet])
            owner[facet] = tag
    if len({root(tag) for tag in parent}) != 1:
        raise ValueError('One facet-connected fluid domain is required')
    return result
