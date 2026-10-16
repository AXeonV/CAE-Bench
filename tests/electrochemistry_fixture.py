"""Disposable electrochemical declaration fixtures; no numerical reference data."""
from pathlib import Path
import json
import h5py
import numpy as np
from caeoj_ext.electrochemistry import models,shape,labels


def fixture(base,slug):
    base=Path(base);base.mkdir(parents=True,exist_ok=True);cfg=models()[slug]
    defaults=dict(temperature=300.,gas_constant=8.314,faraday=96485.,species_count=2,length=1.,permittivity=1.,applied_current=0.,concentration_scale=1.,diffusivity_reduced=1.,diffusivity_oxidized=2.,electrons=1,alpha=.5,rate=1.,standard_potential=0.,area_resistance=.01,reference_pressure=1.)
    p={k:defaults[k] for k in cfg['parameters']};dynamic=cfg['dynamic'];axis='initial' if dynamic else 'state'
    arrays={'marker':np.array([0.])};axes={axis:'marker'}
    if dynamic:
        arrays.update(requested_times=np.array([0.,.5,1.]),drive_times=np.array([0.,.3,1.]))
        axes.update(observe='requested_times',drive='drive_times')
    locs={}
    for name,s in cfg['locations'].items():
        n=s['minimum'] if s['maximum']==s['minimum'] else 2
        ids=np.arange(2,dtype='int64') if name=='electrodes' else np.array([7] if n==1 else [13,41],dtype='int64')
        arrays[name+'_ids']=ids;locs[name]=dict(kind=s['kind'],ids=name+'_ids')
        if s['kind']=='points':
            x=[0.] if name in ('left','electrode') else [1.] if name=='right' else [0.,1e-5] if 'probes' in name and slug=='particle-battery' else [.25,.75]
            arrays[name+'_coordinates']=np.array(x).reshape(-1,1);locs[name]['coordinates']=name+'_coordinates'
    m=dict(task=slug,spatial_dimension=1,data_file='input.h5',geometries={},meshes={},locations=locs,time_axes=axes,fields={},outputs={},physics=dict(model='electrochemistry-'+slug+'-v1',parameters={k:dict(value=v,unit=cfg['parameters'][k]['unit']) for k,v in p.items()}),conditions=[])
    for op,r in cfg['records'].items():
        loc=r['location'];nt=len(arrays[axes[r['axis']]]);n=len(arrays[locs[loc]['ids']]);data={}
        for key,s in r['data'].items():
            v=np.ones((nt,n,*shape(s,p)))
            if key=='alpha':v[:]=.5
            if key in ('standard_potential','solution_potential') or op in ('left','right','potential_initial','potential'):v[:]=0.
            if key=='charge':v[:]=[1.,-1.]
            if op=='current':v[:]=0.;v[1:]=.1
            if key=='radius':v[:]=1e-5
            if op=='particles' and key=='diffusivity':v[:]=1e-14
            if key=='solid_fraction':v[:]=.5
            if key=='thickness':v[:]=1e-4
            if key=='maximum_concentration':v[:]=30000.
            if key=='ocp':v[0]=[[.1,.2,0.,0.],[4.,-.5,0.,0.]]
            if slug=='particle-battery' and op=='initial':v[:]=.5
            if key=='standard_voltage':v[:]=1.2
            if key=='thermoneutral_voltage':v[:]=1.48
            name=op+'_'+key;key_array='payload_'+name;arrays[key_array]=v
            m['fields'][name]=dict(array=key_array,quantity=r['variable'] if key=='value' else key,unit=s['unit'],location=loc,time_axis=r['axis'],dtype='float64',kind=s['kind'],component_shape=shape(s,p),components=labels(s,p),value_kind='point',sampling=dict(space='uniform',time='linear' if r['axis']=='drive' else 'constant',extrapolation='forbid'))
            data[key]={'field':name}
        m['conditions'].append(dict(role=r['role'],variable=r['variable'],operator=op,location=loc,data=data))
    for q,s in cfg['outputs'].items():m['outputs']['observe_'+q]=dict(array='answer_'+q,quantity=q,unit=s['unit'],location=s['location'],time_axis='observe' if dynamic else 'state',dtype='float64',kind=s['kind'],component_shape=shape(s,p),components=labels(s,p),value_kind='point')
    with h5py.File(base/'input.h5','w') as h:
        for k,v in arrays.items():h[k]=v
    path=base/'problem.json';path.write_text(json.dumps(m));return path,m
