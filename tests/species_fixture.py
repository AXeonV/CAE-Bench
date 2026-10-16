"""Temporary protocol fixtures, never formal data or chemical references."""
from pathlib import Path
import json
import h5py
import numpy as np
from caeoj_ext.species import models, shape, labels


def fixture(base, slug):
    base=Path(base);base.mkdir(parents=True,exist_ok=True);cfg=models()[slug]
    defaults=dict(species_count=2,length=1.,temperature=300.,electric_field=1.,gas_constant=8.314,faraday=96485.,capacity=1.,porosity=.3,solid_density=2000.,solid_loading=100.,reaction_count=2,concentration_scale=1.,velocity=.1,reference_temperature=298.15)
    p={key:defaults[key] for key in cfg['parameters']}
    arrays={'initial_time':np.array([0.]),'requested_times':np.array([0.,.5,1.])};locs={}
    for name,s in cfg['locations'].items():
        n=1 if s['maximum']==1 else 3 if name=='knots' else 2
        ids=np.array([17,41] if name=='vessels' else [13,31,59] if name=='knots' else [7] if n==1 else [23,67],dtype='int64')
        arrays[name+'_identity']=ids;locs[name]=dict(kind=s['kind'],ids=name+'_identity')
        if s['kind']=='points':
            x=[0.,.5,1.] if name=='knots' else [0.] if name=='left' else [1.] if name=='right' else [.25,.75]
            arrays[name+'_coordinates']=np.array(x).reshape(-1,1);locs[name]['coordinates']=name+'_coordinates'
    axes={'initial':'initial_time','observe':'requested_times'}
    if cfg['transport']:
        arrays['boundary_times']=np.array([0.,.3,1.]);axes['boundary']='boundary_times'
    m=dict(task=slug,spatial_dimension=1,data_file='input.h5',geometries={},meshes={},locations=locs,time_axes=axes,fields={},outputs={},physics=dict(model='species-'+slug+'-v1',parameters={k:dict(value=v,unit=cfg['parameters'][k]['unit']) for k,v in p.items()}),conditions=[])
    for op,r in cfg['records'].items():
        data={};loc=r['location'];axis=r['axis'];n=len(arrays[locs[loc]['ids']]);nt=len(arrays[axes[axis]])
        for key,s in r['data'].items():
            v=np.ones((nt,n,*shape(s,p)))
            if op=='initial_loading':v[:]=.2
            if op=='kinetics' and key in ('reactants','products'):
                v[:]=0.;v[0,:,0 if key=='reactants' else 1]=1.
            if op=='thermal_initial':v[:]=300.
            if key=='activation':v[:]=1000.
            if key=='heat_capacity':v[:]=20.
            if key=='reference_energy':v[:]=[1000.,0.]
            if key=='charge':v[:]=[1.,-1.]
            if op=='links' and key=='origin':v[:]=17.
            if op=='links' and key=='destination':v[:]=41.
            name=op+'_'+key;array='payload_'+name;arrays[array]=v
            m['fields'][name]=dict(array=array,quantity=r['variable'] if key=='value' else key,unit=s['unit'],location=loc,time_axis=axis,dtype='float64',kind=s['kind'],component_shape=shape(s,p),components=labels(s,p),value_kind='point',sampling=dict(space='piecewise_linear' if loc=='knots' else 'uniform',time='linear' if axis=='boundary' else 'constant',extrapolation='forbid'))
            data[key]={'field':name}
        m['conditions'].append(dict(role=r['role'],variable=r['variable'],operator=op,location=loc,data=data))
    for q,s in cfg['outputs'].items():
        m['outputs']['observe_'+q]=dict(array='answer_'+q,quantity=q,unit=s['unit'],location=s['location'],time_axis='observe',dtype='float64',kind=s['kind'],component_shape=shape(s,p),components=labels(s,p),value_kind='point')
    with h5py.File(base/'input.h5','w') as h:
        for key,v in arrays.items():h[key]=v
    path=base/'problem.json';path.write_text(json.dumps(m));return path,m
