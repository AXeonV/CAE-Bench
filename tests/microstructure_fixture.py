"""Disposable protocol declarations, not phase-field solutions or benchmark cases."""
from pathlib import Path
import json
import h5py
import numpy as np
from caeoj_ext.microstructure import models, shape, labels, state_size


def fixture(base, slug, grain_count=3):
    base=Path(base);base.mkdir(parents=True,exist_ok=True);cfg=models()[slug]
    defaults=dict(length_x=1e-6,length_y=2e-6,energy_scale=1.,gradient=1e-14,
        gradient_c=1e-14,gradient_eta=1e-14,mobility=1e-13,mobility_contrast=1.,
        relaxation=1.,grain_count=grain_count,competition=2.,coupling_energy=2.,reference=0.,
        partition=.5,length_scale=1e-7,undercooling=-.5)
    p={key:defaults[key] for key in cfg['parameters']}
    arrays={'static_times':np.array([0.]),'request_times':np.array([0.,.5,1.]),
            'system_ids':np.array([0],dtype='int64'),'mode_ids':np.array([7,29],dtype='int64'),
            'probe_ids':np.array([3,11,23],dtype='int64'),
            'probe_coordinates':np.array([[0.,0.],[.8e-6,1.8e-6],[.2e-6,.3e-6]])}
    axes=dict(static='static_times',requests='request_times')
    if slug=='driven-ordering':
        arrays['control_times']=np.array([0.,.25,1.]);axes['control']='control_times'
    locations=dict(system=dict(kind='entities',ids='system_ids'),modes=dict(kind='entities',ids='mode_ids'),
        probes=dict(kind='points',ids='probe_ids',coordinates='probe_coordinates'))
    m=dict(task=slug,spatial_dimension=2,data_file='input.h5',geometries={},meshes={},
        locations=locations,time_axes=axes,fields={},outputs={},conditions=[],
        physics=dict(model='microstructure-'+slug+'-v1',parameters={
            k:dict(value=v,unit=cfg['parameters'][k]['unit']) for k,v in p.items()}))
    for op,r in cfg['records'].items():
        n=len(arrays[locations[r['location']]['ids']]);t=len(arrays[axes[r['axis']]]);data={}
        for key,s in r['data'].items():
            v=np.zeros((t,n,*shape(s,cfg,p)))
            if op=='offset':
                v[:]=.3 if slug=='ternary-separation' else .5 if slug=='grain-coarsening' else 0.
            if op=='series' and key=='wave':v[0]=[[1.,-1.],[0.,2.]]
            if op=='series' and key=='amplitude':v[:]=.01
            if op=='mobility':v[0,0]=[[1e-13,-2e-14],[-2e-14,1e-13]]
            if op=='history':v[:,0,0]=[-.1,.2,-.1]
            name=op+'_'+key;array='payload_'+name;arrays[array]=v
            m['fields'][name]=dict(array=array,quantity=r['variable'] if key=='value' else key,
                unit=s['unit'],kind=s['kind'],component_shape=shape(s,cfg,p),components=labels(s,cfg,p),
                dtype='float64',location=r['location'],time_axis=r['axis'],value_kind='point',
                sampling=dict(space='uniform',time='linear' if r['axis']=='control' else 'constant',extrapolation='forbid'))
            data[key]={'field':name}
        m['conditions'].append(dict(operator=op,role=r['role'],variable=r['variable'],location=r['location'],data=data))
    for q,s in cfg['outputs'].items():
        m['outputs']['observation_'+q]=dict(array='answer_'+q,quantity=q,unit=s['unit'],kind=s['kind'],
            component_shape=shape(s,cfg,p),components=labels(s,cfg,p),dtype='float64',location='probes',
            time_axis='requests',value_kind='point')
    with h5py.File(base/'input.h5','w') as h:
        for key,v in arrays.items():h[key]=v
    path=base/'problem.json';path.write_text(json.dumps(m),encoding='utf-8');return path,m
