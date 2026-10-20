"""Convert native DSMC moments and diagnostic collision records to DATA.

No particle transport, collision, reflection or continuum PDE is solved here.
The wall force/heat are measured event integrals in the prescribed wall frame.
"""
import itertools
import json
from pathlib import Path
import h5py
import numpy as np
from scipy.spatial import cKDTree
from elmer_flow_mesh import generate, select
from native_closed_cavity import save, digest
from polytropic_reference import gmsh


def dump(path):
    lines=path.read_text().splitlines();i=max(j for j,line in enumerate(lines) if line.startswith('ITEM:') and 'id' in line.split());columns=lines[i].split()[2:];a=np.loadtxt(lines[i+1:],ndmin=2);assert a.shape[1]==len(columns);return columns,a


def groups(s,m):
    mid=m['x'][m['b']].mean(axis=1);assigned=np.zeros(len(mid),dtype=int)
    for i,bc in enumerate(s['boundaries'][1:],1):
        name=bc['selection'];name=s['geometry']['ports']['bottom' if name.startswith('bottom') else 'top'] if name.startswith(('bottom','top')) else name;take=select(s,name,mid);assigned[take]=i
    return assigned


def select_observations(m,assignment,s):
    x=m['x'];c=m['c'];b=m['b'];normal=m['normal'];n=len(x);boundary=set(np.unique(b).tolist());incident=[[] for _ in x]
    for i,face in enumerate(b):
        for v in face:incident[v].append(i)
    singular=set()
    for v,faces in enumerate(incident):
        if not faces:continue
        if not np.allclose(normal[faces],normal[faces[0]],atol=1e-8,rtol=0) or len({assignment[i] for i in faces})>1:singular.add(v)
    excluded=set(singular)
    for _ in range(2):
        touch=np.any(np.isin(c,list(excluded)),axis=1);excluded.update(c[touch].ravel().tolist())
    observed=np.array(sorted(set(range(n))-boundary-excluded),dtype=int);assert len(observed)>0,'no valid interior nodes under frozen observation rule'
    wall=np.array([s['boundaries'][i]['operator']=='gas_wall' for i in assignment]);traces=np.flatnonzero(wall&~np.any(np.isin(b,list(singular)),axis=1));assert len(traces)>0
    return observed,traces


def locate(points,triangles,x,axis):
    """Map diagnostic wall impacts to actual public triangles on one plane."""
    axes=[j for j in range(3) if j!=axis];verts=x[triangles][:,:,axes];origin=verts[:,0];mat=np.stack((verts[:,1]-origin,verts[:,2]-origin),axis=2);inverse=np.linalg.inv(mat);scale=max(np.ptp(x,axis=0));query=points[:,axes];tree=cKDTree(verts.mean(axis=1));result=np.full(len(points),-1,dtype=int)
    for k in (16,128,len(triangles)):
        missing=np.flatnonzero(result<0)
        if not len(missing):break
        _,near=tree.query(query[missing],k=min(k,len(triangles)));near=near[:,None] if near.ndim==1 else near;uv=np.einsum('nkij,nkj->nki',inverse[near],query[missing,None,:]-origin[near]);inside=(uv.min(axis=2)>=-1e-8)&(uv.sum(axis=2)<=1+1e-8);found=inside.any(axis=1);result[missing[found]]=near[found,np.argmax(inside[found],axis=1)]
    assert np.all(result>=0),f'{np.sum(result<0)} wall events outside public triangles (scale {scale})';return result


def boundary_moments(job,s,m,assignment,sample):
    path=job/'sampling';x=m['x'];b=m['b'];mid=x[b].mean(axis=1);L=np.array(s['geometry']['bounding_lengths']);nb=len(b);force=np.zeros((nb,3));heat=np.zeros(nb);counts=np.zeros(nb,dtype=np.int64);axis=np.argmax(np.abs(m['normal']),axis=1);wall_velocity=np.array([s['boundaries'][i]['data']['velocity']['expression'] for i in assignment]);mass=s['parameters']['molecule_mass']['value'];fnum=sample['real_molecules_per_particle'];dt=sample['native_dt_s'];number=sample['sample_steps']//sample['sampling_stride'];duration=number*dt
    # Native bounding-box collisions carry positions and pre/post velocities.
    events=path/'boundary-events.dat';blocks={}
    for iface in range(6):
        ax=iface//2;side=iface%2;ids=np.flatnonzero((axis==ax)&np.isclose(mid[:,ax],side*L[ax],atol=max(L)*1e-9,rtol=0))
        if len(ids):blocks[iface]=ids
    import itertools as it
    with events.open() as stream:
        while True:
            lines=list(it.islice(stream,50000))
            if not lines:break
            a=np.loadtxt(lines,ndmin=2);assert a.shape[1]==12 and np.isfinite(a).all()
            for iface in np.unique(a[:,1].astype(int)):
                row=a[a[:,1]==iface];ids=blocks[int(iface)];which=ids[locate(row[:,2:5],b[ids],x,int(iface)//2)];vw=wall_velocity[which];weight=row[:,11]*mass*fnum;dv=row[:,8:11]-row[:,5:8];de=.5*(np.sum((row[:,5:8]-vw)**2,axis=1)-np.sum((row[:,8:11]-vw)**2,axis=1));np.add.at(force,which,dv*weight[:,None]);np.add.at(heat,which,de*weight);np.add.at(counts,which,1)
    traction=force/(duration*m['measure'][:,None]);flux=m['normal']*(heat/(duration*m['measure']))[:,None]
    # The existing native surface tally handles all internal gas walls.
    old=job/'native-input-mesh.npz'
    if old.exists() and (path/'surface-moments.dat').exists():
        native=dict(np.load(old));assert np.array_equal(native['b'],b) and np.allclose(native['x'],x,atol=0,rtol=0);outside=np.any(np.all(np.isclose(x[b],0,atol=max(L)*1e-9),axis=1)|np.all(np.isclose(x[b],L,atol=max(L)*1e-9),axis=1),axis=1);inner=np.flatnonzero(~outside);columns,a=dump(path/'surface-moments.dat');assert a.shape[1]==5 and len(a)==len(inner);order=np.argsort(a[:,0]);assert np.array_equal(a[order,0],np.arange(1,len(inner)+1));value=a[order,1:];traction[inner]=-value[:,:3]/m['measure'][inner,None];flux[inner]=m['normal'][inner]*value[:,3,None]
    return traction,flux,{'logged_box_collisions':int(counts.sum()),'sampled_event_duration_s':duration,'unsampled_bbox_triangles':int(np.sum(counts==0)),'native_internal_surface_tally':(path/'surface-moments.dat').exists(),'accuracy_assessed':False}


def package(job,e):
    s=e['detailed_spec'];sample=json.loads((job/'sampling-plan.json').read_text());path=job/'sampling';source=job/'native-input-mesh.npz';m=dict(np.load(source)) if source.exists() else generate(s);np.savez(path/'public-geometry.npz',**m);assignment=groups(s,m);observed,traces=select_observations(m,assignment,s);x=m['x'];c=m['c'];b=m['b'];nc=len(c);n=len(x)
    columns,a=dump(path/'moments.grid');assert a.shape[1]==19;centres=a[:,1:4];values=a[:,4:];valid=np.isfinite(values).all(axis=1)&(values[:,0]>0);assert valid.any();centres=centres[valid];values=values[valid];distance,near=cKDTree(centres).query(x[observed],k=min(8,len(centres)));distance=distance[:,None] if distance.ndim==1 else distance;near=near[:,None] if near.ndim==1 else near;weights=1/np.maximum(distance,max(s['geometry']['bounding_lengths'])*1e-12)**2;weights/=weights.sum(axis=1)[:,None];recovered=np.einsum('nk,nkj->nj',weights,values[near]);traction,heat,wall_record=boundary_moments(job,s,m,assignment,sample)
    inp=job/'input';ref=job/'reference';inp.mkdir(exist_ok=True);ref.mkdir(exist_ok=True);gmsh(inp/'mesh.msh',x,c,b,3);arrays={'domain_nodes':np.arange(1,n+1,dtype=np.int64),'observed_nodes':(observed+1).astype(np.int64),'traces':(nc+traces+1).astype(np.int64),'requested':np.array(s['output_times_s']),'history':np.array([0.])};locations={'domain':{'kind':'mesh','mesh':'main','entity':'node','dimension':3,'ids':'domain_nodes'},'observed':{'kind':'mesh','mesh':'main','entity':'node','dimension':3,'ids':'observed_nodes'},'traces':{'kind':'mesh','mesh':'main','entity':'element','dimension':2,'ids':'traces'}};fields={};conditions=[]
    def descriptor(key,q,where,unit,num,axis='requested',average=False,input=False):
        z={'array':key,'quantity':q,'location':where,'time_axis':axis,'dtype':'float64','kind':'scalar' if num==1 else 'vector','component_shape':[num],'components':['value'] if num==1 else list('xyz'),'unit':unit,'value_kind':'average' if average else 'point'}
        if input:z['sampling']={'space':'piecewise_constant','time':'constant','extrapolation':'forbid'}
        return z
    for i,bc in enumerate(s['boundaries']):
        ids=np.flatnonzero(assignment==i)
        if not len(ids):continue
        key=f'boundary{i}';arrays[key]=(nc+ids+1).astype(np.int64);locations[key]={'kind':'mesh','mesh':'main','entity':'element','dimension':2,'ids':key};fk=key+'_velocity';arrays[fk]=np.tile(bc['data']['velocity']['expression'],(1,len(ids),1));fields[fk]=descriptor(fk,'velocity',key,'m/s',3,'history',True,True);data={'velocity':{'field':fk},'temperature':{'value':bc['data']['temperature_K'],'unit':'K'}}
        if bc['operator']=='gas_wall':data['accommodation']={'value':bc['data']['accommodation'],'unit':'1'}
        else:data['density']={'value':bc['data']['density_kg_m3'],'unit':'kg/m3'}
        conditions.append({'role':'boundary','variable':'gas','operator':bc['operator'],'location':key,'data':data})
    outputs={q:descriptor(q,q,'traces' if q in ('traction','heat_flux') else 'observed',unit,num,average=q in ('traction','heat_flux')) for q,unit,num in [('density','kg/m3',1),('velocity','m/s',3),('temperature','K',1),('pressure','Pa',1),('traction','Pa',3),('heat_flux','W/m2',3)]}
    save(inp/'problem.json',{'task':e['task'],'spatial_dimension':3,'physics':{'model':e['model'],'parameters':s['parameters']},'data_file':'input.h5','geometries':{},'meshes':{'main':{'file':'mesh.msh'}},'locations':locations,'time_axes':{'requested':'requested','history':'history'},'fields':fields,'conditions':conditions,'outputs':outputs})
    with h5py.File(inp/'input.h5','w') as f:
        for k,v in arrays.items():f[k]=v
    result={'density':recovered[:,0:1],'velocity':recovered[:,1:4],'temperature':recovered[:,4:5],'pressure':recovered[:,5:6],'traction':traction[traces],'heat_flux':heat[traces]}
    assert len(arrays['requested'])==1
    with h5py.File(ref/'reference.h5','w') as f:
        for k in ('observed_nodes','traces','requested'):f[k]=arrays[k]
        for k,v in result.items():assert np.isfinite(v).all();f[k]=v[None]
    save(path/'wall-conversion.json',wall_record)
    return {'reference_sha256':digest(ref/'reference.h5'),'nodes':n,'cells':nc,'observed_nodes':len(observed),'observed_wall_triangles':len(traces),'frames':1,'mapping':'Native DSMC pooled cell moments recovered to actual interior nodes by inverse-distance interpolation. Wall traction is recorded post-minus-pre particle momentum / actual triangle area / sampled event time. Wall-frame energy loss uses the prescribed wall velocity; vector heat flux is outward normal times this scalar. Internal walls use existing native per-triangle surface force/energy tallies. No stationarity, statistical, discretization or accuracy assessment. Original burn-in is resumed with a newly declared native RNG seed, not claimed bitwise identical to the earlier sample.'}
