"""Geometry and storage adapters for native Elmer. No PDE solver."""
import math
import re
from pathlib import Path
import numpy as np


def generate(spec):
    import gmsh
    geo=spec['geometry'];d=geo['dimension'];L=geo['bounding_lengths']
    gmsh.initialize();gmsh.option.setNumber('General.Terminal',0)
    gmsh.option.setNumber('Mesh.Algorithm',6);gmsh.option.setNumber('Mesh.Algorithm3D',1)
    occ=gmsh.model.occ
    def polygon(vertices):
        pts=[occ.addPoint(x,y,0) for x,y in vertices]
        edges=[occ.addLine(pts[i],pts[(i+1)%len(pts)]) for i in range(len(pts))]
        return (2,occ.addPlaneSurface([occ.addCurveLoop(edges)]))
    if geo['operation']=='box':surfaces=[(2,occ.addRectangle(0,0,0,L[0],L[1]))]
    elif geo['operation'].startswith('polygon'):surfaces=[polygon(geo['xy_vertices'])]
    elif geo['operation'].startswith('union'):
        rects=[(2,occ.addRectangle(a[0],a[1],0,b[0]-a[0],b[1]-a[1])) for a,b in geo['xy_rectangles']]
        surfaces=occ.fuse(rects[:1],rects[1:])[0]
    else:raise ValueError(geo['operation'])
    if d==3:
        bodies=[q for q in occ.extrude(surfaces,0,0,L[2]) if q[0]==3]
        holes=[(3,occ.addBox(a[0],a[1],0,b[0]-a[0],b[1]-a[1],L[2])) for h in geo['holes'] for a,b in [h['xy_corners']]]
    else:
        bodies=surfaces;holes=[(2,occ.addRectangle(a[0],a[1],0,b[0]-a[0],b[1]-a[1])) for h in geo['holes'] for a,b in [h['xy_corners']]]
    if holes:bodies=occ.cut(bodies,holes)[0]
    occ.synchronize();size=spec['mesh_recipe']['bulk_size_m']
    for attempt in range(4):
        gmsh.model.mesh.clear();gmsh.model.mesh.setSize(gmsh.model.getEntities(0),size)
        gmsh.model.mesh.generate(d);types,_,allc=gmsh.model.mesh.getElements(d)
        assert list(types)==[2 if d==2 else 4]
        if len(allc[0])//(d+1)<=25000:break
        size*=1.3
    else:raise ValueError('mesh exceeds fixed element cap')
    tags,xx,_=gmsh.model.mesh.getNodes();x=np.asarray(xx).reshape(-1,3)[:,:d]
    lut={int(t):i for i,t in enumerate(tags)}
    c=np.array([[lut[int(t)] for t in row] for row in np.asarray(allc[0]).reshape(-1,d+1)],dtype=np.int64)
    _,_,faces=gmsh.model.mesh.getElements(d-1)
    b=np.array([[lut[int(t)] for t in row] for arr in faces for row in np.asarray(arr).reshape(-1,d)],dtype=np.int64)
    gmsh.finalize()
    A=x[c][:,1:]-x[c][:,:1];det=np.linalg.det(A);neg=det<0
    c[neg,1],c[neg,2]=c[neg,2].copy(),c[neg,1].copy()
    volume=np.abs(det)/math.factorial(d)
    parents={tuple(sorted(np.delete(row,j))):i for i,row in enumerate(c) for j in range(d+1)}
    parent=np.array([parents[tuple(sorted(row))] for row in b],dtype=np.int64)
    centres=x[b].mean(axis=1);cell_centres=x[c].mean(axis=1)
    if d==2:
        tangent=x[b[:,1]]-x[b[:,0]];measure=np.linalg.norm(tangent,axis=1)
        normal=np.column_stack([tangent[:,1],-tangent[:,0]])/measure[:,None]
    else:
        v=np.cross(x[b[:,1]]-x[b[:,0]],x[b[:,2]]-x[b[:,0]])
        measure=np.linalg.norm(v,axis=1)/2;normal=v/(2*measure[:,None])
    normal[np.einsum('ij,ij->i',normal,centres-cell_centres[parent])<0]*=-1
    return dict(x=x,c=c,b=b,volume=volume,parent=parent,normal=normal,measure=measure,size=size)


def select(spec,selection,mid):
    d=mid.shape[1];L=spec['geometry']['bounding_lengths'];tol=max(L)*1e-8
    if selection=='all':return np.ones(len(mid),bool)
    if 'complement' in selection:return None
    if selection in ('inlet','outlet'):selection=spec['geometry']['ports'][selection]
    clauses=selection.replace(' and ',',').split(',');mask=np.ones(len(mid),bool)
    for clause in clauses:
        clause=clause.strip()
        chained=re.fullmatch(r'([^<>]+)<([XYZxyz])<([^<>]+)',clause)
        if chained:
            lo,a,hi=chained.groups();axis='xyz'.index(a.lower());q=mid[:,axis]/L[axis] if a.isupper() else mid[:,axis]
            values={'Lx':L[0],'Ly':L[1],**({'Lz':L[2]} if d==3 else {})}
            mask &= (q>eval(lo,{'__builtins__':{}},values)) & (q<eval(hi,{'__builtins__':{}},values));continue
        if '=' in clause:
            a,v=clause.split('=');axis='xyz'.index(a.strip());value=0. if v.strip()=='0' else L[axis]
            mask &= np.abs(mid[:,axis]-value)<tol
        elif '<' in clause or '>' in clause:
            op='<' if '<' in clause else '>';a,v=clause.split(op);axis='xyz'.index(a.strip().lower())
            value=eval(v,{'__builtins__':{}},{'Lx':L[0],'Ly':L[1],**({'Lz':L[2]} if d==3 else {})})
            q=mid[:,axis]/L[axis] if a.strip().isupper() else mid[:,axis]
            mask &= q<float(value) if op=='<' else q>float(value)
        else:raise ValueError('unsupported boundary selector '+selection)
    return mask


def partitions(spec,m):
    mid=m['x'][m['b']].mean(axis=1);assignment=np.full(len(mid),-1,dtype=int);fallback=None
    for i,bc in enumerate(spec['boundaries']):
        selected=select(spec,bc['selection'],mid)
        if selected is None:fallback=i;continue
        assert not np.any(assignment[selected]>=0),'overlapping physical partitions'
        assignment[selected]=i
    if fallback is not None:assignment[assignment<0]=fallback
    assert np.all(assignment>=0),'unassigned boundary'
    return assignment


def write_native(path,m,groups,pin):
    path.mkdir(parents=True,exist_ok=True);x=m['x'];c=m['c'];b=m['b'];d=x.shape[1]
    n=len(x);nc=len(c);nb=len(b);ct=303 if d==2 else 504;bt=202 if d==2 else 303
    (path/'mesh.header').write_text(f'{n} {nc} {nb+int(pin)}\n{2+int(pin)}\n{ct} {nc}\n{bt} {nb}\n'+('101 1\n' if pin else ''))
    (path/'mesh.nodes').write_text('\n'.join(f'{i+1} -1 '+' '.join(map(str,list(v)+([0.] if d==2 else []))) for i,v in enumerate(x))+'\n')
    (path/'mesh.elements').write_text('\n'.join(f'{i+1} 1 {ct} '+' '.join(map(str,row+1)) for i,row in enumerate(c))+'\n')
    rows=[f'{i+1} {groups[i]+1} {m["parent"][i]+1} 0 {bt} '+' '.join(map(str,row+1)) for i,row in enumerate(b)]
    if pin:rows.append(f'{nb+1} {groups.max()+2} 1 0 101 {c[0,0]+1}')
    (path/'mesh.boundary').write_text('\n'.join(rows)+'\n')
