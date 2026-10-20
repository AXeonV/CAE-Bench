"""Native OpenFOAM blockMesh configuration for frozen rectangular cutouts."""
import itertools
import numpy as np
from native_closed_cavity import header,put,vector
from elmer_flow_mesh import select


def write(native,s):
    geo=s['geometry'];assert geo['operation']=='box';d=geo['dimension'];L=geo['bounding_lengths'];assert d==2
    xs={0.,L[0]};ys={0.,L[1]}
    for h in geo['holes']:
        a,b=h['xy_corners'];xs.update([a[0],b[0]]);ys.update([a[1],b[1]])
    # These are actual boundary partition endpoints in the frozen experiments.
    for bc in s['boundaries']:
        if 'x<Lx/2' in bc['selection'] or 'x>Lx/2' in bc['selection']:xs.add(L[0]/2)
        if '1/3' in bc['selection'] or '2/3' in bc['selection']:xs.update([L[0]/3,2*L[0]/3])
    xs=sorted(xs);ys=sorted(ys);zs=[0.,.05];verts=[];lookup={}
    def vertex(i,j,k):
        key=i,j,k
        if key not in lookup:lookup[key]=len(verts);verts.append([xs[i],ys[j],zs[k]])
        return lookup[key]
    active=set()
    for i,j in itertools.product(range(len(xs)-1),range(len(ys)-1)):
        mid=np.array([.5*(xs[i]+xs[i+1]),.5*(ys[j]+ys[j+1])])
        if not any(np.all(mid>h['xy_corners'][0]) and np.all(mid<h['xy_corners'][1]) for h in geo['holes']):active.add((i,j))
    patches={f'bc{i}':[] for i in range(len(s['boundaries']))};patches.update(front=[],back=[]);blocks=[];counts=s['mesh_recipe']['base_divisions']
    def part(mid):
        out=0
        for i,bc in enumerate(s['boundaries'][1:],1):
            if select(s,bc['selection'],np.array([mid]))[0]:out=i
        return f'bc{out}'
    for i,j in sorted(active):
        ids=[vertex(i,j,0),vertex(i+1,j,0),vertex(i+1,j+1,0),vertex(i,j+1,0),vertex(i,j,1),vertex(i+1,j,1),vertex(i+1,j+1,1),vertex(i,j+1,1)]
        nn=[max(1,round(counts[0]*(xs[i+1]-xs[i])/L[0])),max(1,round(counts[1]*(ys[j+1]-ys[j])/L[1])),1];blocks.append('hex '+vector(ids)+' '+vector(nn)+' simpleGrading (1 1 1)')
        for other,local in [((i-1,j),[0,4,7,3]),((i+1,j),[1,2,6,5]),((i,j-1),[0,1,5,4]),((i,j+1),[3,7,6,2])]:
            if other in active:continue
            face=[ids[k] for k in local];mid=np.array([verts[k][:2] for k in face]).mean(axis=0);patches[part(mid)].append(face)
        patches['front'].append([ids[k] for k in [0,3,2,1]]);patches['back'].append([ids[k] for k in [4,5,6,7]])
    patches={k:v for k,v in patches.items() if v};text=header('dictionary','blockMeshDict')+'scale 1;\nvertices (\n'+'\n'.join(vector(v) for v in verts)+'\n);\nblocks (\n'+'\n'.join(blocks)+'\n);\nedges ();\nboundary (\n'
    for name,faces in patches.items():text+=name+' { type '+('empty' if name in ('front','back') else 'wall')+'; faces ('+' '.join(vector(f) for f in faces)+'); }\n'
    text+=');\nmergePatchPairs ();\n';put(native/'system/blockMeshDict',text);return patches
