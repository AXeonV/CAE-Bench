"""Disposable I/O declarations, deliberately not formal data or trusted solutions."""
from pathlib import Path
import json
import h5py
import numpy as np
from caeoj_ext.multiphysics import models


def fixture(base, slug):
    base=Path(base);base.mkdir(parents=True,exist_ok=True);c=models()[slug]
    transient=c['mode']=='transient';harmonic=c['mode']=='harmonic'
    p={k:1. for k in c['parameters']}
    p.update({k:v for k,v in dict(length=1.,wall_thickness=.05,young_modulus=100.,alpha=.001,fluid_thermal=.1,heat_capacity=10.,resistivity_slope=.01,piezo_coefficient=-.2,magneto_coefficient=-.2).items() if k in p})
    arrays=dict(domain_ids=np.array([11,37,91],dtype='int64'),domain_coordinates=np.array([[1.],[0.],[.37]]),left_ids=np.array([4],dtype='int64'),right_ids=np.array([4],dtype='int64'))
    arrays.update(dict(load_times=np.array([0.,.2,1.]),response_times=np.array([0.,.07,1.])) if transient else dict(state_times=np.array([0.])))
    locs=dict(domain=dict(kind='points',ids='domain_ids',coordinates='domain_coordinates'),left=dict(kind='entities',ids='left_ids'),right=dict(kind='entities',ids='right_ids'))
    m=dict(task=slug,spatial_dimension=1,data_file='input.h5',geometries={},meshes={},locations=locs,time_axes={'load':'load_times','response':'response_times'} if transient else {'state':'state_times'},physics=dict(model='multiphysics-'+slug+'-v1',parameters={k:dict(value=v,unit=c['parameters'][k]['unit']) for k,v in p.items()}),fields={},outputs={},conditions=[])
    ft=dict(dtype='float64',kind='components' if harmonic else 'scalar',component_shape=[2] if harmonic else [1],components=['real','imag'] if harmonic else ['value'],value_kind='point')
    for side,bc in c['boundaries'].items():
        data={}
        for k,s in bc.items():
            name=side+'_'+k;array='payload_'+name
            v=np.zeros((3 if transient else 1,1,2 if harmonic else 1))
            if transient:v[1:,0,0]=[.003,.01]
            elif k=='temperature':v[:]=1.
            else:v[:]=.01
            arrays[array]=v;m['fields'][name]=dict(ft,array=array,quantity=k,unit=s['unit'],location=side,time_axis='load' if transient else 'state',sampling=dict(space='uniform',time='linear' if transient else 'constant',extrapolation='forbid'));data[k]={'field':name}
        m['conditions'].append(dict(role='boundary',variable='coupled_boundary',operator='prescribed',location=side,data=data))
    for q,s in c['outputs'].items():m['outputs']['observation_'+q]=dict(ft,array='answer_'+q,quantity=q,unit=s['unit'],location=s['location'],time_axis='response' if transient else 'state')
    with h5py.File(base/'input.h5','w') as h:
        for key,value in arrays.items():h[key]=value
    path=base/'problem.json';path.write_text(json.dumps(m));return path,m
