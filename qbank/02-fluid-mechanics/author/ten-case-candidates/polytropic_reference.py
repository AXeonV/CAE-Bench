"""Evaluate a published hydrostatic formula; this is not a PDE solver.

Chandrashekar & Zenk, arXiv:1511.08739v2, section 2.1.2:
K*gamma/(gamma-1)*rho**(gamma-1)+Phi=C. The same conservative-potential
relation is evaluated in 2D/3D; it is not the paper's DG implementation.
No refinement, error estimate or independent validation is performed.
"""
from __future__ import annotations
import argparse
import hashlib
import itertools
import json
import math
import time
from pathlib import Path
import h5py
import numpy as np
from scipy.optimize import brentq

def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def mesh(spec):
    g=spec['geometry'];d=g['dimension'];L=np.array(g['bounding_lengths']);div=spec['mesh_recipe']['base_divisions']
    assert g['operation']=='box'
    points=np.array(list(itertools.product(*(np.linspace(0,l,n+1) for l,n in zip(L,div)))))
    shape=tuple(n+1 for n in div)
    def tag(a):return np.ravel_multi_index(tuple(a),shape)
    conn=[]
    for idx in itertools.product(*(range(n) for n in div)):
        centre=(np.array(idx)+.5)*L/div
        if any(all(np.array(h['xy_corners'][0])<centre[:2]) and all(centre[:2]<np.array(h['xy_corners'][1])) for h in g['holes']):continue
        for perm in itertools.permutations(range(d)):
            a=np.array(idx);c=[tag(a)]
            for axis in perm:a=a.copy();a[axis]+=1;c.append(tag(a))
            conn.append(c)
    conn=np.array(conn,dtype=np.int64);active=np.unique(conn);new=np.full(len(points),-1);new[active]=np.arange(len(active));points=points[active];conn=new[conn]
    x=points[conn];A=x[:,1:,:]-x[:,:1,:];det=np.linalg.det(A)
    neg=det<0;conn[neg,1],conn[neg,2]=conn[neg,2].copy(),conn[neg,1].copy()
    volumes=np.abs(det)/math.factorial(d)
    counts={}
    for c in conn:
        for j in range(d+1):
            f=tuple(sorted(np.delete(c,j)));counts[f]=counts.get(f,0)+1
    boundary=np.array([f for f,n in counts.items() if n==1],dtype=np.int64)
    assert len(conn)<=25000
    return points,conn,boundary,volumes

def gmsh(p,xyz,conn,boundary,d):
    n=len(xyz);nc=len(conn);nb=len(boundary);xyz3=np.pad(xyz,((0,0),(0,3-d)));bb=' '.join(map(str,[*xyz3.min(axis=0),*xyz3.max(axis=0)]))
    rows=['$MeshFormat','4.1 0 8','$EndMeshFormat','$Entities',f'0 {1 if d==2 else 0} 1 {1 if d==3 else 0}']
    rows += [f'2 {bb} 1 2 0',f'1 {bb} 1 1 0'] if d==2 else [f'2 {bb} 1 2 0',f'1 {bb} 1 1 0']
    rows += ['$EndEntities','$Nodes',f'1 {n} 1 {n}',f'{d} 1 0 {n}',*map(str,range(1,n+1)),*(' '.join(map(str,x)) for x in xyz3),'$EndNodes','$Elements',f'2 {nc+nb} 1 {nc+nb}',f'{d} 1 {2 if d==2 else 4} {nc}']
    rows += [f'{j+1} '+' '.join(map(str,c+1)) for j,c in enumerate(conn)]
    rows += [f'{d-1} 2 {1 if d==2 else 2} {nb}']
    rows += [f'{nc+j+1} '+' '.join(map(str,c+1)) for j,c in enumerate(boundary)]
    rows += ['$EndElements'];p.write_text('\n'.join(rows)+'\n')

def potential(x,L,i):
    delta=x-.5*L
    if i==0:return 3000*x[:,1]
    if i==1:return 2000*x[:,0]
    if i==2:return x@np.array([1500,3000,1000][:len(L)])
    if i==3:return 5000*x[:,1]
    if i==4:return 2500*np.sum(delta**2,axis=1)
    if i==5:return .5*np.sum(np.array([3000,6000,9000][:len(L)])*delta**2,axis=1)
    if i==6:return 3000*np.sum((x-.4*L)**2,axis=1)
    if i==7:return 3000*np.abs(x[:,0]-.5*L[0])
    if i==8:
        X=x[:,0]/L[0];return 200000*(X-.25)**2*(X-.75)**2
    M=np.array([[2,.3],[.3,1]]) if len(L)==2 else np.array([[2,.3,.1],[.3,1,.2],[.1,.2,1.5]])
    return .5*6000*np.einsum('ni,ij,nj->n',delta,M,delta)

def quadrature(d):
    z,w=np.polynomial.legendre.leggauss(8);z=(z+1)/2;w=w/2;bary=[];weights=[]
    for ids in itertools.product(range(8),repeat=d):
        a=z[list(ids)];weight=np.prod(w[list(ids)])
        if d==2:
            r,s=a;bary.append([1-r,r*(1-s),r*s]);weights.append(weight*2*r)
        else:
            r,s,t=a;bary.append([1-r,r*(1-s),r*s*(1-t),r*s*t]);weights.append(weight*6*r*r*s)
    return np.array(bary),np.array(weights)

def descriptor(q,c,unit,location,output=False):
    x={'array':q,'quantity':q,'location':location,'time_axis':'steady','dtype':'float64','kind':'vector' if c>1 else 'scalar','component_shape':[c],'components':list('xyz'[:c]) if c>1 else ['value'],'unit':unit,'value_kind':'average'}
    if not output:x['sampling']={'space':'piecewise_constant','time':'constant','extrapolation':'forbid'}
    return x

def run_one(root,record,e,grading,source):
    job=root/'cases'/e['design_id']
    if (job/'status.json').exists():return json.loads((job/'status.json').read_text())
    job.mkdir(parents=True,exist_ok=False);start=time.time();save(job/'design.json',e)
    spec=e['detailed_spec'];d=e['spatial_dimension'];i=int(e['design_id'].split('-')[-2])-1;L=np.array(spec['geometry']['bounding_lengths']);params={k:v['value'] for k,v in spec['parameters'].items()}
    x,c,b,vol=mesh(spec);phi=potential(x,L,i);pc=phi[c]
    A=x[c][:,1:]-x[c][:,:1];force=-np.linalg.solve(A,(pc[:,1:]-pc[:,:1])[...,None])[...,0]
    bary,w=quadrature(d);gamma=params['heat_capacity_ratio'];R=params['specific_gas_constant'];K=R*params['reference_temperature']/params['isentropic_reference_density']**(gamma-1);factor=(gamma-1)/(K*gamma)
    # Chunk integration to keep the 3D quadrature working set bounded.
    def integrate(C,all_fields=False):
        vals=[]
        for a in range(0,len(c),512):
            ph=pc[a:a+512]@bary.T;rho=(factor*(C-ph))**(1/(gamma-1));p=K*rho**gamma;T=p/(rho*R)
            vals.append(np.column_stack([rho@w,p@w,T@w]) if all_fields else rho@w)
        return np.concatenate(vals)
    lower=float(phi.max())+1.;upper=lower+1e6
    def mass(C):return np.dot(vol,integrate(C))/vol.sum()-params['mean_density']
    assert mass(lower)<0 and mass(upper)>0
    C=brentq(mass,lower,upper,xtol=1e-9);values=integrate(C,True)
    if not np.isfinite(values).all():raise ValueError('nonfinite formula output')
    inp=job/'input';ref=job/'reference';inp.mkdir();ref.mkdir();gmsh(inp/'mesh.msh',x,c,b,d)
    nc=len(c);nb=len(b)
    with h5py.File(inp/'input.h5','w') as f:
        f['cells']=np.arange(1,nc+1,dtype=np.int64);f['boundary']=np.arange(nc+1,nc+nb+1,dtype=np.int64);f['time']=np.array([0.]);f['acceleration']=force[None]
    def loc(key,dim):return {'kind':'mesh','mesh':'main','entity':'element','dimension':dim,'ids':key}
    problem={'task':record['task'],'spatial_dimension':d,'physics':{'model':record['model'],'parameters':spec['parameters']},'data_file':'input.h5','geometries':{},'meshes':{'main':{'file':'mesh.msh'}},'locations':{'domain':loc('cells',d),'walls':loc('boundary',d-1)},'time_axes':{'steady':'time'},'fields':{'acceleration':descriptor('acceleration',d,'m/s2','domain')},'conditions':[{'role':'source','variable':'acceleration','operator':'assign','location':'domain','data':{'value':{'field':'acceleration'}}},{'role':'boundary','variable':'velocity','operator':'slip_wall','location':'walls','data':{'impermeable':{'option':'yes'}}}],'outputs':{q:descriptor(q,cc,u,'domain',True) for q,cc,u in [('velocity',d,'m/s'),('pressure',1,'Pa'),('temperature',1,'K'),('density',1,'kg/m3')]}}
    save(inp/'problem.json',problem);save(ref/'grading.json',grading)
    with h5py.File(ref/'reference.h5','w') as f:
        f['cells']=np.arange(1,nc+1,dtype=np.int64);f['time']=np.array([0.]);f['velocity']=np.zeros((1,nc,d));f['density']=values[None,:,0:1];f['pressure']=values[None,:,1:2];f['temperature']=values[None,:,2:3]
    producer={'producer':'published analytic formula evaluation, not the paper DG solver or OpenFOAM','source':source,'formula':spec['analytic_producer_candidate'],'potential':spec['definitions']['Phi_nodes'],'normalization_constant_C':C,'quadrature':{'points_per_dimension':8,'type':'Gauss Legendre, Duffy simplex transform'},'script_sha256':sha(Path(__file__)),'start_unix':start,'finish_unix':time.time(),'native_physics_extension':False,'numerical_validation':'not_performed'}
    save(job/'producer.json',producer)
    state={'design_id':e['design_id'],'status':'unvalidated_candidate','producer':producer['producer'],'cells':nc,'output_quantities':list(problem['outputs']),'output_frames':1,'reference_sha256':sha(ref/'reference.h5'),'input_sha256':{p.name:sha(p) for p in inp.iterdir()},'limitations':['No numerical/independent validation.','3D uses the dimension-independent published hydrostatic relation, not a reproduced 3D case from the paper.','Quadrature averages have no error certification.']}
    save(job/'status.json',state);return state

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);args=ap.parse_args()
    base=args.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates';frozen=json.loads((base/'design-freeze.json').read_text());assert frozen['design_complete']
    sourcepath=args.root/'maintenance/sources/arxiv-1511.08739v2.pdf'
    assert sourcepath.is_file(),'Archive the exact published source before evaluation.'
    source={'url':'https://arxiv.org/pdf/1511.08739v2','file':str(sourcepath.relative_to(args.root)),'sha256':sha(sourcepath),'sections':['2.1.2','3.1']}
    states=[]
    for rel,want in frozen['designs'].items():
        path=args.snapshot/rel;assert hashlib.sha256(path.read_text().encode()).hexdigest()==want
        record=json.loads(path.read_text())
        if record['family']!='euler_equilibrium':continue
        grading=json.loads((path.parents[1]/'grading-template.json').read_text())
        for e in record['proposed_cases']:
            states.append(run_one(args.root,record,e,grading,source))
    assert len(states)==20;save(args.root/'maintenance/polytropic-summary.json',states)
    print(json.dumps({'formula_candidates':len(states),'validated':0}))

if __name__=='__main__':main()
