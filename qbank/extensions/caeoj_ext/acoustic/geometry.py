"""Acoustic mesh support and physical receiver checks; no field solver."""
from itertools import combinations
import numpy as np


def receiver_geometry(point,triangles):
    """Return surface distance and absolute closed-surface solid angle."""
    x,y,z=triangles[:,0],triangles[:,1],triangles[:,2]
    nearest=np.full(len(x),np.inf)
    for start,end in ((x,y),(y,z),(z,x)):
        edge=end-start;t=np.clip(np.sum((point-start)*edge,axis=1)/np.sum(edge*edge,axis=1),0,1)
        nearest=np.minimum(nearest,np.linalg.norm(point-start-t[:,None]*edge,axis=1))
    ab=y-x;ac=z-x;n=np.cross(ab,ac);norm=np.linalg.norm(n,axis=1);unit=n/norm[:,None]
    distance=np.sum((point-x)*unit,axis=1);projected=point-distance[:,None]*unit;v=projected-x
    aa=np.sum(ab*ab,axis=1);bb=np.sum(ab*ac,axis=1);cc=np.sum(ac*ac,axis=1);den=aa*cc-bb*bb
    vb=(cc*np.sum(v*ab,axis=1)-bb*np.sum(v*ac,axis=1))/den
    vc=(aa*np.sum(v*ac,axis=1)-bb*np.sum(v*ab,axis=1))/den
    inside=(vb>=0)&(vc>=0)&(vb+vc<=1);nearest=np.where(inside,np.minimum(nearest,abs(distance)),nearest)
    a,b,c=x-point,y-point,z-point;la,lb,lc=[np.linalg.norm(v,axis=1) for v in (a,b,c)]
    numerator=np.sum(a*np.cross(b,c),axis=1)
    denominator=la*lb*lc+np.sum(a*b,axis=1)*lc+np.sum(b*c,axis=1)*la+np.sum(c*a,axis=1)*lb
    omega=abs(np.sum(2*np.arctan2(numerator,denominator)))
    return float(nearest.min()),float(omega)


def inspect(problem,cfg,fail):
    m,a=problem.manifest,problem.arrays;locs=m['locations'];family=cfg['family']
    if set(m['meshes'])!={'main'}:fail('$.meshes','one main mesh',list(m['meshes']));return None
    mesh=problem.meshes['main'];surface=family=='surface';dim=2 if surface else 3;top=mesh['elements'][dim]
    if mesh['dimension']!=dim or not top:fail('$.meshes.main','nonempty dimension '+str(dim),mesh['dimension']);return None
    nodes=set();facets={};owners={};neighbors={t:set() for t in top};triangles=[]
    for tag in top:
        typ,conn=mesh['connectivity'][tag]
        if typ!=(2 if surface else 4):fail('$.meshes.main','first-order triangle/tetrahedron',typ);return None
        nodes.update(conn);x=np.array([mesh['node_coordinates'][n] for n in conn])
        if np.linalg.matrix_rank(x[1:]-x[0])!=dim:fail('$.meshes.main','nondegenerate element',tag);return None
        for face in combinations(conn,dim):facets.setdefault(tuple(sorted(face)),[]).append(tag)
    if surface:
        if any(mesh['elements'][d] for d in (0,1,3)):fail('$.meshes.main','surface triangles only','other elements')
        if any(len(v)!=2 for v in facets.values()):fail('$.meshes.main','closed edge-manifold surface','open/nonmanifold edges');return None
        edges={}
        for tag in top:
            conn=mesh['connectivity'][tag][1];x=np.array([mesh['node_coordinates'][n] for n in conn]);triangles.append(x)
            for start,end in zip(conn,conn[1:]+conn[:1]):edges[(start,end)]=edges.get((start,end),0)+1
        if any(n!=1 or edges.get((b,a))!=1 for (a,b),n in edges.items()):fail('$.meshes.main','oppositely directed adjacent edges','inconsistent orientation')
        triangles=np.array(triangles)
        if np.sum(np.einsum('ij,ij->i',triangles[:,0],np.cross(triangles[:,1],triangles[:,2])))/6<=0:fail('$.meshes.main','positive outward enclosed volume','nonpositive orientation')
        exterior={t:mesh['connectivity'][t][1] for t in top}
    else:
        if mesh['elements'][0] or mesh['elements'][1]:fail('$.meshes.main','tetrahedra and exterior triangles only','lower-dimensional elements')
        if any(len(v)>2 for v in facets.values()):fail('$.meshes.main','manifold facets','nonmanifold');return None
        expected={f for f,v in facets.items() if len(v)==1};exterior={}
        for tag in mesh['elements'][2]:
            typ,conn=mesh['connectivity'][tag];f=tuple(sorted(conn))
            if typ!=2 or f not in expected or f in exterior.values():fail('$.meshes.main','one exported triangle per exterior facet',tag);return None
            exterior[tag]=f;owners[tag]=facets[f][0]
            x=np.array([mesh['node_coordinates'][n] for n in f]);center=x.mean(axis=0);inside=np.mean([mesh['node_coordinates'][n] for n in mesh['connectivity'][owners[tag]][1]],axis=0)
            if np.cross(x[1]-x[0],x[2]-x[0])@(center-inside)<0:x=x[[0,2,1]]
            triangles.append(x)
        if set(exterior.values())!=expected:fail('$.meshes.main','all exterior facets exported',len(exterior));return None
        triangles=np.array(triangles)
    for f,v in facets.items():
        if len(v)==2:neighbors[v[0]].add(v[1]);neighbors[v[1]].add(v[0])
    reached=set();stack=[next(iter(top))]
    while stack:
        tag=stack.pop()
        if tag not in reached:reached.add(tag);stack.extend(neighbors[tag]-reached)
    if reached!=top:fail('$.meshes.main','connected cells/surface','disconnected')
    if nodes!=mesh['nodes']:fail('$.meshes.main','no unused nodes','unused nodes')
    if len(nodes)>9000 or len(top)>(800 if surface else 3000):fail('$.meshes.main','mesh size limits',[len(nodes),len(top)])
    def ids(name):return set(map(int,a[locs[name]['ids']]))
    base='surface' if surface else 'cells'
    for name,entity,tags in [('domain','node',nodes),(base,'element',top)]:
        l=locs.get(name,{})
        if l.get('kind')!='mesh' or l.get('mesh')!='main' or l.get('entity')!=entity or ids(name)!=tags or (entity=='element' and l.get('dimension')!=dim):fail('$.locations.'+name,'complete '+entity+' support',l)
    for name,l in locs.items():
        if name=='receivers' and family in ('surface','source'):
            if l['kind']!='points':fail('$.locations.receivers','points',l);continue
            coords=a[l['coordinates']]
            if len(coords)>128:fail('$.locations.receivers','<=128 points',len(coords))
            scale=np.linalg.norm(np.ptp(mesh['coordinates'],axis=0))
            for p in coords:
                dist,omega=receiver_geometry(p,triangles)
                if dist<1e-8*scale or omega>2*np.pi:fail('$.locations.receivers','strict exterior points with clearance',p)
            continue
        if name=='structure' and m.get('physics',{}).get('model')=='acoustic-modal-vibroacoustics-v1':
            if l['kind']!='entities' or len(ids(name))!=1:fail('$.locations.structure','one entity',l)
            continue
        if l['kind']!='mesh' or l.get('mesh')!='main':fail('$.locations.'+name,'supported mesh location',l);continue
        tags=ids(name)
        ok=tags<=nodes if l['entity']=='node' else l['dimension']==dim and tags<=top or not surface and l['dimension']==2 and tags<=set(exterior)
        if not ok:fail('$.locations.'+name,'nodes/cells/exterior facets',l)
    if family in ('source','surface') and 'receivers' not in locs:fail('$.locations','receivers required',list(locs))
    if surface and set(locs)!={'domain','surface','receivers'}:fail('$.locations','domain/surface/receivers only',list(locs))
    if m.get('physics',{}).get('model')=='acoustic-modal-vibroacoustics-v1' and 'structure' not in locs:fail('$.locations','one structure entity','missing')
    return dict(mesh=mesh,nodes=nodes,cells=top,exterior=exterior,owners=owners,boundary_nodes={n for face in exterior.values() for n in face})
