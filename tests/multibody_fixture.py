"""Disposable metadata/HDF5 plumbing fixtures; not physical benchmark cases."""
from pathlib import Path
import json
import h5py
import numpy as np
from caeoj_ext.multibody import models,shape,labels


def fixture(base,slug):
    base=Path(base);base.mkdir(parents=True,exist_ok=True);cfg=models()[slug];imp=cfg['family']=='impact';modal=cfg['family']=='modal';site='systems' if modal else 'bodies';n=1 if modal else 2
    p={'start_time':0.,'end_time':1.,'mode_count':2,'restitution':.5,'friction':.3}
    arrays={};locs={}
    def loc(name,ids):
        arrays[name+'_ids']=np.array(ids,dtype='int64')
        locs[name]=dict(kind='entities',ids=name+'_ids')
    loc(site,[3] if modal else [3,17])
    axes={'event':'event_times'} if imp else {'initial':'initial_times','response':'response_times','loads':'load_times'}
    arrays.update(event_times=np.array([0.]),initial_times=np.array([0.]),response_times=np.array([0.,.3,1.]),load_times=np.array([0.,.4,1.]))
    if slug=='planar-kinematics':axes.pop('loads')
    m=dict(task=slug,spatial_dimension=cfg['dimension'],data_file='input.h5',geometries={},meshes={},locations=locs,time_axes=axes,fields={},outputs={},physics=dict(model='multibody-'+slug+'-v1',parameters={k:dict(value=p[k],unit=s['unit']) for k,s in cfg['parameters'].items()}),conditions=[])
    def record(op,location,values=None):
        r=cfg['records'][op];data={};values=values or {}
        for key,s in r['data'].items():
            if 'shape' not in s:
                value=values.get(key,0.);data[key]=dict(value=value,unit=s['unit']);continue
            axis='event' if imp else 'loads' if op=='loads' else 'initial';t=len(arrays[axes[axis]]);count=len(arrays[locs[location]['ids']]);sh=shape(s,p)
            a=np.zeros((t,count,*sh))
            if s.get('positive'):a[:]=1.
            if key=='position0' and not modal:a[0,1,0]=2.
            if key=='velocity0' and imp:a[0,:,0]=[1.,-1.]
            if key in ('mass_matrix','stiffness') or (key=='inertia' and cfg['family']=='spatial'):a[:]=np.eye(sh[0])
            if key=='quaternion0':a[:,: ,0]=1.
            if key=='coupling':a[:]=.1
            name=op+'_'+key;array='payload_'+name;arrays[array]=a
            m['fields'][name]=dict(array=array,quantity=key,unit=s['unit'],kind=s.get('kind','scalar'),component_shape=sh,components=labels(s,p),dtype='float64',location=location,time_axis=axis,value_kind='point',sampling=dict(space='uniform',time='linear' if op=='loads' and t>1 else 'constant',extrapolation='forbid'))
            data[key]={'field':name}
        m['conditions'].append(dict(role=r['role'],variable=r['variable'],operator=op,location=location,data=data))
    record('modal_system' if modal else 'body',site)
    if 'loads' in cfg['records']:record('loads',site)
    if 'revolute' in cfg['records']:
        for i,tag in enumerate([3,17]):
            loc('hinge'+str(i),[9]);record('revolute','hinge'+str(i),dict(a=-1,b=tag,ax=float(2*i),ay=0.,bx=0.,by=0.))
    if 'angle_drive' in cfg['records']:
        for i,tag in enumerate([3,17] if slug in ('planar-kinematics','planar-inverse-dynamics') else [3]):
            loc('drive'+str(i),[23]);record('angle_drive','drive'+str(i),dict(body=tag))
    for op in ('spring','contact','collision'):
        if op in cfg['records']:
            loc(op,[5]);record(op,op,dict(a=3,b=17,stiffness=10.,damping=1.,rest_length=2.,friction=.2,slip_speed=.1))
    for q,s in cfg['outputs'].items():
        locations=[site] if s['location']==site else [c['location'] for c in m['conditions'] if c['operator']==s['location']]
        for i,location in enumerate(locations):
            m['outputs']['observation_'+q+str(i)]=dict(array='answer_'+q+str(i),quantity=q,unit=s['unit'],kind=s['kind'],component_shape=shape(s,p),components=labels(s,p),dtype='float64',location=location,time_axis='event' if imp else 'response',value_kind='point')
    used=set(axes.values())|{x[k] for x in locs.values() for k in ('ids',)}|{x['array'] for x in m['fields'].values()}
    with h5py.File(base/'input.h5','w') as h:
        for key in used:h[key]=arrays[key]
    path=base/'problem.json';path.write_text(json.dumps(m));return path,m
