"""Disposable system declaration fixtures, not formal cases or reference solutions."""
from pathlib import Path
import json
import h5py
import numpy as np
from caeoj_ext.systems import models


def fixture(base,slug):
    base=Path(base);base.mkdir(parents=True,exist_ok=True);c=models()[slug]
    arrays=dict(static_times=np.array([0.]),load_times=np.array([0.,.2,1.]),response_times=np.array([0.,.07,1.]))
    locations={}
    if c['network']:
        arrays.update(node_ids=np.array([11,41,103],dtype='int64'),edge_ids=np.array([7,11,59],dtype='int64'))
        locations=dict(nodes=dict(kind='entities',ids='node_ids'),edges=dict(kind='entities',ids='edge_ids'))
    else:
        arrays['system_ids']=np.array([7,31],dtype='int64');locations=dict(systems=dict(kind='entities',ids='system_ids'))
    axes={k:k+'_times' for k in ('static','load','response')}
    if c.get('control'):
        arrays['control_times']=np.array([0.,.1,.6,1.]);axes['control']='control_times'
    m=dict(task=slug,spatial_dimension=1,data_file='input.h5',geometries={},meshes={},locations=locations,time_axes=axes,physics=dict(model='systems-'+slug+'-v1',parameters={k:dict(value=287. if k=='gas_constant' else 300.,unit=s['unit']) for k,s in c['parameters'].items()}),fields={},outputs={},conditions=[])
    for op,r in c['records'].items():
        data={};loc=r['location'];n=len(arrays[locations[loc]['ids']]);nt=len(arrays[axes[r['axis']]])
        for key,s in r['data'].items():
            name=op+'_'+key;array='payload_'+name;v=np.full((nt,n,*s['shape']),1. if s['positive'] else 0.,dtype=s['dtype'])
            if key=='endpoints':v[0]=[[103,11],[11,41],[41,103]]
            elif key=='ratio':v[0,:,0]=[-2.,.5,1.]
            elif 'temperature' in key:v[:]=300.
            elif r['axis']=='load':v[:, :, 0]=np.array([0.,.01,.03])[:,None]
            arrays[array]=v
            m['fields'][name]=dict(array=array,quantity=key,unit=s['unit'],dtype=s['dtype'],kind='scalar' if s['shape']==[1] else 'components',component_shape=s['shape'],components=s['labels'],location=loc,time_axis=r['axis'],value_kind='point',sampling=dict(space='uniform',time={'static':'constant','load':'linear','control':'previous'}[r['axis']],extrapolation='forbid'))
            data[key]={'field':name}
        m['conditions'].append(dict(role=r['role'],variable='system_data',operator=op,location=loc,data=data))
    for q,s in c['outputs'].items():
        m['outputs']['observation_'+q]=dict(array='answer_'+q,quantity=q,unit=s['unit'],dtype='float64',kind='scalar' if s['shape']==[1] else 'components',component_shape=s['shape'],components=s['labels'],location=s['location'],time_axis='response',value_kind='point')
    with h5py.File(base/'input.h5','w') as h:
        for k,v in arrays.items():h[k]=v
    path=base/'problem.json';path.write_text(json.dumps(m));return path,m
