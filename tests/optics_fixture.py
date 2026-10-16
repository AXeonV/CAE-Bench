"""Disposable optical I/O fixtures; not formal cases or numerical references."""
from pathlib import Path
import json
import gmsh
import h5py
import numpy as np
from caeoj_ext.optics import models,shape,labels


def fixture(base,slug):
    base=Path(base);base.mkdir(parents=True,exist_ok=True);cfg=models()[slug];arrays={'marker':np.array([0.])};locs={};meshes={}
    defaults=dict(wavelength=1.,refractive_index=1.,impedance=2.,input_index=1.,output_index=1.,wave_count=2,vacuum_impedance=2.,incidence_sine=.2,polarization=0,left_index=1.,right_index=1.,mode_count=2)
    p={k:defaults[k] for k in cfg['parameters']};axis='steady' if slug=='layered-rays' else 'optical'
    for name,s in cfg['locations'].items():
        if s['kind']=='mesh':continue
        n=1 if s['maximum']==1 else 3 if name=='receivers' else 2
        arrays[name+'_ids']=np.arange(n,dtype='int64');locs[name]=dict(kind=s['kind'],ids=name+'_ids')
        if s['kind']=='points':
            coords=np.array([[-1.],[.5],[3.]]) if slug=='slab-modes' else np.array([[0.,0.,1.],[1.,0.,2.],[0.,1.,2.]])
            arrays[name+'_coordinates']=coords;locs[name]['coordinates']=name+'_coordinates'
    if cfg['mesh']:
        tags=[13,31,59,83];xyz=np.array([[0.,0.,0.],[1.,0.,0.],[1.,1.,0.],[0.,1.,0.]]);celltags=[101,149];conn=[13,31,59,13,59,83]
        gmsh.initialize([],readConfigFiles=False)
        try:
            gmsh.option.setNumber('General.Terminal',0);gmsh.model.add('optical_protocol_fixture');e=gmsh.model.addDiscreteEntity(2);gmsh.model.mesh.addNodes(2,e,tags,xyz.ravel());gmsh.model.mesh.addElementsByType(e,2,celltags,conn)
            gmsh.option.setNumber('Mesh.MshFileVersion',4.1);gmsh.option.setNumber('Mesh.Binary',0);gmsh.write(str(base/'mesh.msh'))
        finally:gmsh.finalize()
        meshes={'main':{'file':'mesh.msh'}};arrays['domain_ids']=np.array(tags,dtype='int64');arrays['aperture_ids']=np.array(celltags,dtype='int64')
        locs['domain']=dict(kind='mesh',mesh='main',entity='node',ids='domain_ids');locs['aperture']=dict(kind='mesh',mesh='main',entity='element',dimension=2,ids='aperture_ids')
    m=dict(task=slug,spatial_dimension=cfg['spatial_dimension'],data_file='input.h5',geometries={},meshes=meshes,locations=locs,time_axes={axis:'marker'},fields={},outputs={},physics=dict(model='optics-'+slug+'-v1',parameters={k:dict(value=v,unit=cfg['parameters'][k]['unit']) for k,v in p.items()}),conditions=[])
    for op,r in cfg['records'].items():
        location=r['location'];n=len(arrays[locs[location]['ids']]);data={}
        for key,s in r['data'].items():
            values=np.zeros((1,n,*shape(s,p)))
            if s.get('positive'):values[:]=1.
            if op=='layers' and key=='index':values[:]=[[[1.5],[1.4]]]
            if key=='direction' or op=='directions':values[:]=[0.,0.,1.]
            if op=='coherence':values[0,0,:,:,0]=np.eye(p['wave_count'])
            if op=='elements':values[:,:,:,:,0]=np.eye(2);values[0,1,1,1,0]=0.
            if op=='states':values[0,:,0,0]=1.
            name=op+'_'+key;array='payload_'+name;arrays[array]=values;l=locs[location];element=l['kind']=='mesh'
            m['fields'][name]=dict(array=array,quantity=r['variable'] if key=='value' else key,unit=s['unit'],kind=s['kind'],component_shape=shape(s,p),components=labels(s,p),dtype='float64',location=location,time_axis=axis,value_kind='average' if element else 'point',sampling=dict(space='piecewise_constant' if element else 'uniform',time='constant',extrapolation='forbid'))
            data[key]={'field':name}
        m['conditions'].append(dict(role=r['role'],variable=r['variable'],operator=op,location=location,data=data))
    for q,s in cfg['outputs'].items():m['outputs']['observation_'+q]=dict(array='answer_'+q,quantity=q,unit=s['unit'],kind=s['kind'],component_shape=shape(s,p),components=labels(s,p),dtype='float64',location=s['location'],time_axis=axis,value_kind='point')
    with h5py.File(base/'input.h5','w') as h:
        for key,value in arrays.items():h[key]=value
    path=base/'problem.json';path.write_text(json.dumps(m));return path,m
