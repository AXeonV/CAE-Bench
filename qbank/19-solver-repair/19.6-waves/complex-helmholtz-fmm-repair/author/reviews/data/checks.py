"""Independent complete-array audit. Never invokes native numerical pipeline."""
from pathlib import Path
import copy, hashlib, importlib.util, json, subprocess, tarfile
import h5py
import numpy as np
from caeoj.sdk import load_problem, load_result
from caeoj.validation import read_mesh
from caeoj.case_grading import grade_case

ROOT=Path(__file__).resolve().parents[3]
TASK=ROOT/'qbank/19-solver-repair/19.6-waves/complex-helmholtz-fmm-repair'
DATA=ROOT/'work/repair-22/bempp-20/dataset-v2'
OUT=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('decl',TASK/'extension/caeoj_task_ext/helmholtz.py'); ext=importlib.util.module_from_spec(sp);sp.loader.exec_module(ext)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def compare(a,b):
    a=np.asarray(a);b=np.asarray(b); ratio=abs(a-b)/(1e-6+1e-5*abs(b))
    return dict(max_abs=float(abs(a-b).max()),max_tolerance_fraction=float(ratio.max()),passed=bool(np.all(ratio<=1)))
def split(a):
    a=np.asarray(a)
    if a.ndim==1:a=a[:,None]
    return np.stack((a.real,a.imag),axis=-1).reshape(len(a),-1)
def cx(a):
    a=np.asarray(a);return a[:,0::2]+1j*a[:,1::2]
def mesh_data(p):
    m=read_mesh(p.path.parent/'surface.msh',geometry=True)
    ids=p.arrays['node_ids'];ind={int(x):i for i,x in enumerate(ids)}
    v=np.array([m['node_coordinates'][int(x)] for x in ids]);tri=np.array([[ind[x] for x in row[1]] for _,row in sorted(m['connectivity'].items())])
    return m,v,tri
def external(v,t,rho,x,k,n):
    # Reference triangle y=a+u(b-a)+(1-u)*v(c-a), explicit Jacobian.
    nodes,weights=np.polynomial.legendre.leggauss(n);nodes=(nodes+1)/2;weights=weights/2
    u,w=np.meshgrid(nodes,nodes,indexing='ij');bary=np.stack((1-u-(1-u)*w,u,(1-u)*w),-1).reshape(-1,3)
    weight=(np.outer(weights,weights)*(1-u)).ravel()
    tv=v[t];cr=np.cross(tv[:,1]-tv[:,0],tv[:,2]-tv[:,0]);a2=np.linalg.norm(cr,axis=1);normal=cr/a2[:,None]
    y=bary@tv;density=np.einsum('qj,ej->eq',bary,rho[t]);delta=x[:,None,None,:]-y[None,:,:,:];r=np.linalg.norm(delta,axis=-1)
    g=np.exp(1j*k*r)/(4*np.pi*r);dg=g*(1/r-1j*k)*np.einsum('teqc,ec->teq',delta,normal)/r
    return {name:np.einsum('teq,eq,q,e->t',ker,density,weight,a2) for name,ker in [('single_layer',g),('double_layer',dg)]}

report={'documents':{str(p.relative_to(ROOT)):sha(p) for p in [TASK/'DATA.md',TASK/'instruction.md',ROOT/'docs/CONTRACT.md',TASK/'extension/caeoj_task_ext/helmholtz.py']},'cases':[],'variants':[]}
scope=[(p,p.parent.name,DATA/'reference'/p.parent.name) for p in sorted((DATA/'cases').glob('*/problem.json'))]
scope += [(p,'sample-'+p.parents[1].name,p.parents[1]/'reference') for p in sorted((TASK/'samples').glob('*/input/problem.json'))]
for path,name,refdir in scope:
    p=load_problem(path);err=[];ext.check(p,err);r=load_result(p,refdir/'reference.h5');m=p.manifest;a=p.arrays
    op=m['physics']['parameters']['operation']['value'];k=complex(*[m['physics']['parameters'][x]['value'] for x in ['wavenumber_real','wavenumber_imag']])
    row=dict(name=name,operation=op,wavenumber=[k.real,k.imag],extension_errors=err,inputs={},outputs={},hashes={str(q.relative_to(ROOT)):sha(q) for q in [path,path.parent/'input.h5',refdir/'reference.h5',refdir/'grading.json']})
    for key,val in a.items():row['inputs'][key]=dict(shape=list(val.shape),dtype=str(val.dtype),min=float(val.min()),max=float(val.max()),zeros=int(np.count_nonzero(val==0)),negative=int(np.count_nonzero(val<0)))
    for key,val in r.items():row['outputs'][key]=dict(shape=list(val.shape),dtype=str(val.dtype),min=float(val.min()),max=float(val.max()))
    row['self_grade']=grade_case(path,refdir/'reference.h5',refdir/'grading.json')
    config=json.loads((refdir/'grading.json').read_text());policy=config['checks'][0]['policy']['quantities'];row['policy_matches']=all(policy[s['quantity']]=={'unit':s['unit'],'rule':{'metric':'pointwise','time':'per_time','components':'per_component','atol':1e-6,'rtol':1e-5}} for s in m['outputs'].values())
    if op==0:
        y=a['source_coordinates'];x=a['target_coordinates'];q=cx(a['strength'][0]).ravel();d=x[:,None,:]-y[None,:,:];dist=np.linalg.norm(d,axis=-1);g=np.exp(1j*k*dist)/(4*np.pi*dist)
        potential=g@q;grad=np.einsum('ts,tsc,s->tc',g*(1j*k-1/dist)/dist,d,q)
        row['analytic']={key:compare(r[key][0],split(grad if 'gradient' in key else potential)) for key in m['outputs']}
        row['geometry']={'source_box_diagonal':float(np.linalg.norm(np.ptp(y,axis=0))),'source_target_min':float(dist.min()),'shared_ids':len(set(a['source_ids'])&set(a['target_ids']))}
    else:
        mm,v,t=mesh_data(p);rho=cx(a['density'][0]).ravel();payload=json.loads((DATA/'cases'/name/'native-payload.json').read_text()) if not name.startswith('sample') else None
        cr=np.cross(v[t[:,1]]-v[t[:,0]],v[t[:,2]]-v[t[:,0]]);a2=np.linalg.norm(cr,axis=1);mass=np.zeros((len(v),len(v)))
        for ids,jac in zip(t,a2):mass[np.ix_(ids,ids)]+=jac/24*(np.eye(3)+np.ones((3,3)))
        row['geometry']={'vertices':len(v),'triangles':len(t),'area_min':float(a2.min()/2),'box_diagonal':float(np.linalg.norm(np.ptp(v,axis=0))),'volume':float(np.einsum('tc,tc->',v[t[:,0]],np.cross(v[t[:,1]],v[t[:,2]]))/6),'mass_condition':float(np.linalg.cond(mass)),'mesh_storage_ids_sorted':list(mm['node_coordinates'])==a['node_ids'].tolist()}
        quad={n:external(v,t,rho,a['target_coordinates'],k,n) for n in [14,22]};row['quadrature']={key:compare(r['potential_'+key][0],split(val)) for key,val in quad[22].items()};row['quadrature_convergence']={key:float(abs(quad[22][key]-quad[14][key]).max()) for key in quad[22]}
        if payload:
            row['payload_matches_input']=bool(np.array_equal(v,payload['vertices']) and np.array_equal(t,payload['triangles']) and np.array_equal(a['density'][0],payload['density']) and np.array_equal(a['target_coordinates'],payload['targets']))
            dense=json.loads((ROOT/'runs/authoring/repair-22/bempp-formal-boundary-audit'/name/'stdout.json').read_text());row['dense_weak_mass']={key:compare(r[key][0],split(np.linalg.solve(mass,cx(dense[key])))) for key in m['outputs'] if key.startswith('boundary_')}
    # Grade both sides for each scalar component of every output: one changed entry.
    row['grading_boundary']=[]
    temp=OUT/'perturbed.h5'
    for key,spec in m['outputs'].items():
        for c in range(spec['component_shape'][0]):
            for factor in [.99,1.01]:
                rr={kk:vv.copy() for kk,vv in r.items()};v0=rr[key][0,0,c];rr[key][0,0,c]+=factor*(1e-6+1e-5*abs(v0))
                with h5py.File(temp,'w') as h:
                    for kk,vv in rr.items():h[kk]=vv
                result=grade_case(path,temp,refdir/'grading.json');row['grading_boundary'].append({'field':key,'component':c,'factor':factor,'result':result})
    temp.unlink()
    report['cases'].append(row);print(name,'loaded and independently checked',flush=True)
(OUT/'evidence.json').write_text(json.dumps(report,indent=2)+'\n')
