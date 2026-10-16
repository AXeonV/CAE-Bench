"""Mesh and support declarations for electromagnetic models; no mesher/solver."""
from itertools import combinations
import numpy as np


def inspect(problem,cfg,fail):
    m,a=problem.manifest,problem.arrays;d=cfg['dimension'];locs=m['locations']
    if set(m['meshes'])!={'main'}:fail('$.meshes','one main mesh',list(m['meshes']));return
    mesh=problem.meshes['main'];top=mesh['elements'][d]
    if mesh['dimension']!=d or not top:fail('$.meshes.main','nonempty dimension '+str(d),mesh['dimension']);return
    if any(mesh['elements'][v] for v in range(d-1)):fail('$.meshes.main','top cells and exterior facets only','lower elements')
    if d==2 and np.any(mesh['coordinates'][:,2]!=0):fail('$.meshes.main','xy plane z=0','nonzero z')
    nodes=set();faces={};neighbors={t:set() for t in top}
    for tag in top:
        typ,conn=mesh['connectivity'][tag]
        if typ!=(2 if d==2 else 4):fail('$.meshes.main','first order simplices',typ);return
        x=np.array([mesh['node_coordinates'][n] for n in conn]);nodes.update(conn)
        if np.linalg.matrix_rank(x[1:]-x[0])!=d:fail('$.meshes.main','nondegenerate cell',tag);return
        for f in combinations(conn,d):faces.setdefault(tuple(sorted(f)),[]).append(tag)
    if any(len(v)>2 for v in faces.values()):fail('$.meshes.main','manifold faces','nonmanifold');return
    expected={f for f,v in faces.items() if len(v)==1};exterior={}
    for tag in mesh['elements'][d-1]:
        typ,conn=mesh['connectivity'][tag];f=tuple(sorted(conn))
        if typ!=(1 if d==2 else 2) or f not in expected or f in exterior.values():fail('$.meshes.main','one export per exterior facet',tag);return
        exterior[tag]=f
    if set(exterior.values())!=expected:fail('$.meshes.main','all exterior facets exported',len(exterior));return
    for owners in faces.values():
        if len(owners)==2:neighbors[owners[0]].add(owners[1]);neighbors[owners[1]].add(owners[0])
    reached=set();stack=[next(iter(top))]
    while stack:
        t=stack.pop()
        if t not in reached:reached.add(t);stack.extend(neighbors[t]-reached)
    if reached!=top:fail('$.meshes.main','face-connected domain','disconnected')
    if nodes!=mesh['nodes']:fail('$.meshes.main','no unused nodes','unused nodes')
    if len(nodes)>6000 or len(top)>(1800 if d==3 else 5000):fail('$.meshes.main','size limits',[len(nodes),len(top)])
    def ids(name):return set(map(int,a[locs[name]['ids']]))
    for name,entity,tags in [('domain','node',nodes),('cells','element',top)]:
        l=locs.get(name,{})
        if l.get('kind')!='mesh' or l.get('mesh')!='main' or l.get('entity')!=entity or ids(name)!=tags or entity=='element' and l.get('dimension')!=d:fail('$.locations.'+name,'complete '+entity,l)
    coil=m.get('physics',{}).get('model')=='electromagnetic-coil-circuit-v1'
    for name,l in locs.items():
        if coil and name=='coil':
            if l['kind']!='entities' or len(ids(name))!=1:fail('$.locations.coil','one entity',l)
            continue
        if l['kind']!='mesh' or l.get('mesh')!='main':fail('$.locations.'+name,'main mesh support',l);continue
        tags=ids(name);ok=tags<=nodes if l['entity']=='node' else l['dimension']==d and tags<=top or l['dimension']==d-1 and tags<=set(exterior)
        if not ok:fail('$.locations.'+name,'nodes/cells/exterior facets',l)
    if coil and 'coil' not in locs:fail('$.locations','coil entity required','missing')
    return dict(mesh=mesh,nodes=nodes,cells=top,exterior=exterior,boundary_nodes={n for f in exterior.values() for n in f})
