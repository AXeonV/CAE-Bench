"""Finite input/reference assembly from an already completed native run."""
import argparse
import json
from pathlib import Path
import h5py
import numpy as np
from native_closed_cavity import save,digest,field
from native_pyclaw_closed_flat import descriptor
from native_shallow_obstacle import CASE

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);a=ap.parse_args();j=a.root/'cases'/CASE
    state=json.loads((j/'status.json').read_text());assert state['status']=='native_complete_pending_conversion'
    e=json.loads((j/'design.json').read_text());s=e['detailed_spec'];z=np.load(j/'mesh-input-identity.npz');x,c,b,q,area=[z[k] for k in ['x','c','b','quads','area']];n=len(x);nc=len(q)
    keep=np.ones(n,bool);keep[np.unique(b)]=False
    for _ in range(2):keep[np.unique(c[np.any(~keep[c],axis=1)])]=False
    ids=np.flatnonzero(keep);assert len(ids)>0
    arrays={'nodes':np.arange(1,n+1,dtype=np.int64),'observed':ids.astype(np.int64)+1,'cells':np.arange(1,len(c)+1,dtype=np.int64),'wall':np.arange(1,len(b)+1,dtype=np.int64)+len(c),'integral':np.array([1],dtype=np.int64),'initial':np.array([0.]),'constant':np.array([0.]),'requested':np.array(s['output_times_s']),'bed':z['bed'][None,:,None],'depth0':z['initial_depth'][None,:,None],'velocity0':z['initial_velocity'][None]}
    locations={'domain':{'kind':'mesh','mesh':'main','entity':'node','ids':'nodes'},'observed':{'kind':'mesh','mesh':'main','entity':'node','ids':'observed'},'area':{'kind':'mesh','mesh':'main','entity':'element','dimension':2,'ids':'cells'},'wall':{'kind':'mesh','mesh':'main','entity':'element','dimension':1,'ids':'wall'},'volume':{'kind':'aggregate','source':'area','ids':'integral','operation':'sum'}}
    fields={};conditions=[]
    for key,quantity,role,op,axis,unit,dim in [('bed','bed','material','geometry','constant','m',1),('depth0','depth','initial','assign','initial','m',1),('velocity0','velocity','initial','assign','initial','m/s',2)]:
        fields[key]=descriptor(quantity,'domain',axis,unit,dim,input=True);fields[key]['array']=key;conditions.append({'role':role,'variable':quantity,'operator':op,'location':'domain','data':{'value':{'field':key}}})
    conditions.append({'role':'boundary','variable':'water','operator':'water_wall','location':'wall','data':{'mode':{'option':'impermeable'}}})
    outputs={v:descriptor(v,'volume' if v=='water_volume' else 'observed','requested',unit,dim,integral=v=='water_volume') for v,unit,dim in [('depth','m',1),('velocity','m/s',2),('water_flux','m2/s',2),('water_volume','m3',1)]}
    save(j/'input/problem.json',{'task':e['task'],'physics':{'model':e['model'],'parameters':s['parameters']},'spatial_dimension':2,'data_file':'input.h5','geometries':{},'meshes':{'main':{'file':'mesh.msh'}},'locations':locations,'time_axes':{'initial':'initial','constant':'constant','requested':'requested'},'fields':fields,'conditions':conditions,'outputs':outputs})
    with h5py.File(j/'input/input.h5','w') as f:
        for k,v in arrays.items():f[k]=v
    weights=np.zeros(n)
    for k in range(4):np.add.at(weights,q[:,k],area)
    assert np.all(weights>0)
    def recover(v):
        out=np.zeros((n,v.shape[1]))
        for k in range(4):np.add.at(out,q[:,k],v*area[:,None])
        return out/weights[:,None]
    result={v:[] for v in outputs}
    for t in s['output_times_s']:
        folder=j/'native'/format(t,'.12g');h=field(folder/'h',1,nc);hu=field(folder/'hU',3,nc)[:,:2];assert np.min(h)>0 and np.isfinite(h).all() and np.isfinite(hu).all()
        result['depth'].append(recover(h)[ids]);result['velocity'].append(recover(hu/h)[ids]);result['water_flux'].append(recover(hu)[ids]);result['water_volume'].append(np.array([[np.dot(area,h[:,0])]]))
    ref=j/'reference';ref.mkdir()
    with h5py.File(ref/'reference.h5','w') as f:
        for k in ['observed','requested','integral']:f[k]=arrays[k]
        for k,v in result.items():f[k]=np.array(v)
    save(ref/'grading.json',json.loads((j/'grading-template.json').read_text()))
    state.pop('remaining',None);state.update(status='unvalidated_candidate',reference_sha256=digest(ref/'reference.h5'),input_sha256=digest(j/'input/input.h5'),nodes=n,cells=len(c),frames=len(s['output_times_s']),conversion_script_sha256=digest(Path(__file__)),mapping='Native shallowWaterFoam FV on exact rectangular-hole domain. Public quad split triangles; exact P1 initial-depth means. Interior real-node outputs use area-weighted cell-to-node recovery, an approximate point reconstruction. Water volume is native FV integral over horizontal areas, no extrusion multiplier. No accuracy validation.');save(j/'status.json',state);print(json.dumps(state))
if __name__=='__main__':main()
