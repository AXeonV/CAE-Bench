"""Disposable declaration fixtures, no DEM or population-balance references."""
from pathlib import Path
import json
import h5py
import numpy as np
from caeoj_ext.granular import models,shape,labels


def fixture(base,slug):
    base=Path(base);base.mkdir(parents=True,exist_ok=True);cfg=models()[slug]
    defaults=dict(stiffness=1.,normal_damping=0.,friction=.5,slip_speed=.01,
                  cohesive_force=.001,interaction_range=.001,box_length=1.,bin_count=3,monomer_volume=1e-9)
    p={k:defaults[k] for k in cfg['parameters']}
    arrays={'marker':np.array([0.]),'observations':np.array([0.,.01])}
    axes=dict(static='marker',initial='marker',observe='observations')
    if not cfg['population']:
        axes['drive']='drive_times';arrays['drive_times']=np.array([0.,.004,.01])
    locs={}
    for name in cfg['locations']:
        ids=np.array([1,2,3],dtype='int64') if name=='bins' else np.array([7],dtype='int64') if name=='system' else np.array([7,31,93],dtype='int64')
        locs[name]=dict(kind='entities',ids=name+'_ids');arrays[name+'_ids']=ids
    m=dict(task=slug,spatial_dimension=cfg['dimension'],data_file='input.h5',geometries={},meshes={},
           locations=locs,time_axes=axes,fields={},outputs={},conditions=[],physics=dict(model=slug+'-v1',parameters={k:dict(value=v,unit=cfg['parameters'][k]['unit']) for k,v in p.items()}))
    for q,s in cfg['inputs'].items():
        t,n=len(arrays[axes[s['axis']]]),len(arrays[locs[s['location']]['ids']])
        values=np.zeros((t,n,*shape(s,p)))
        if q in ('mass','radius'):values[:]=.01
        if q=='initial_position':values[0]=[[.1,.1,.1],[.3,.1,.1],[.6,.1,.1]]
        if q=='initial_density':values[0,:,0]=[1000.,2000.,0.]
        if q=='collision_kernel':values[:]=1e-6
        if q=='breakage_rate':values[0,:,0]=[0.,1.,2.]
        if q=='daughter_count':values[0,0]=[[0.,2.,1.],[0.,0.,1.],[0.,0.,0.]]
        name,key='given_'+q,'payload_'+q;arrays[key]=values
        m['fields'][name]=dict(array=key,quantity=q,location=s['location'],time_axis=s['axis'],dtype='float64',kind=s['kind'],component_shape=shape(s,p),components=labels(s,p),unit=s['unit'],value_kind='point',sampling=dict(space='uniform',time='linear' if s['axis']=='drive' else 'constant',extrapolation='forbid'))
        m['conditions'].append(dict(role='initial' if s['axis']=='initial' else 'source' if s['axis']=='drive' else 'material',variable=q,location=s['location'],operator='prescribed',data={'value':{'field':name}}))
    for q,s in cfg['outputs'].items():m['outputs']['observed_'+q]=dict(array='answer_'+q,quantity=q,location=s['location'],time_axis='observe',dtype='float64',kind=s['kind'],component_shape=shape(s,p),components=labels(s,p),unit=s['unit'],value_kind='point')
    with h5py.File(base/'input.h5','w') as h:
        for key,v in arrays.items():h[key]=v
    path=base/'problem.json';path.write_text(json.dumps(m),encoding='utf-8')
    return path,m
