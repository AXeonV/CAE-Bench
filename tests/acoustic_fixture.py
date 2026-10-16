"""Disposable acoustic I/O fixtures, without a solver or physical reference."""
from pathlib import Path
from itertools import combinations
import json
import gmsh
import h5py
import numpy as np
from caeoj_ext.acoustic import models,shape,labels


def fixture(base,slug):
    base=Path(base);base.mkdir(parents=True,exist_ok=True);cfg=models()[slug];surface=cfg['family']=='surface';tr=cfg['transient'];arrays={};locs={}
    def loc(name,tags,entity,dim=None):
        arrays[name+'_ids']=np.array(sorted(tags),dtype='int64');locs[name]=dict(kind='mesh',mesh='main',entity=entity,ids=name+'_ids')
        if dim is not None:locs[name]['dimension']=dim
    if surface:
        xyz=np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]])
        cells={}
        for i,face in enumerate(combinations(range(4),3)):
            face=list(face);x=xyz[face]
            if np.cross(x[1]-x[0],x[2]-x[0])@(x.mean(axis=0)-xyz.mean(axis=0))<0:face=face[::-1]
            cells[301+i]=face
    else:
        xyz=np.array([[0.,0.,0.],[1.,0.,0.],[1.,1.,0.],[0.,1.,0.],[0.,0.,1.],[1.,0.,1.],[1.,1.,1.],[0.,1.,1.]])
        cells={101+i:c for i,c in enumerate([[0,1,2,6],[0,2,3,6],[0,3,7,6],[0,7,4,6],[0,4,5,6],[0,5,1,6]])}
    tags=[11+12*i for i in range(len(xyz))];cells={tag:tuple(tags[j] for j in c) for tag,c in cells.items()};coord=dict(zip(tags,xyz));boundary={}
    if not surface:
        faces={}
        for c in cells.values():
            for f in combinations(c,3):f=tuple(sorted(f));faces[f]=faces.get(f,0)+1
        boundary={301+i:f for i,(f,n) in enumerate(faces.items()) if n==1}
    gmsh.initialize([],readConfigFiles=False)
    try:
        gmsh.option.setNumber('General.Terminal',0);gmsh.model.add('acoustic_protocol_fixture');dim=2 if surface else 3;e=gmsh.model.addDiscreteEntity(dim)
        gmsh.model.mesh.addNodes(dim,e,tags,xyz.ravel());gmsh.model.mesh.addElementsByType(e,2 if surface else 4,list(cells),np.array(list(cells.values())).ravel())
        for tag,c in boundary.items():
            e=gmsh.model.addDiscreteEntity(2);gmsh.model.mesh.addElementsByType(e,2,[tag],list(c))
        gmsh.option.setNumber('Mesh.MshFileVersion',4.1);gmsh.option.setNumber('Mesh.Binary',0);gmsh.write(str(base/'mesh.msh'))
    finally:gmsh.finalize()
    loc('domain',tags,'node');loc('surface' if surface else 'cells',cells,'element',dim)
    if cfg['family'] in ('surface','source'):
        arrays['receiver_ids']=np.array([0,7],dtype='int64');arrays['receiver_coordinates']=np.array([[2.,2.,2.],[3.,1.,1.]])
        locs['receivers']=dict(kind='points',ids='receiver_ids',coordinates='receiver_coordinates')
    if not surface:
        first=next(iter(boundary));loc('wall',[first],'element',2);loc('boundary_nodes',tags,'node')
    if slug=='uniform-flow-acoustics':
        for j,axis in enumerate('xyz'):
            for side,v in [('minus',0.),('plus',1.)]:loc(axis+'_'+side,[t for t,c in boundary.items() if all(coord[n][j]==v for n in c)],'element',2)
    if slug=='modal-vibroacoustics':
        arrays['structure_ids']=np.array([19],dtype='int64');locs['structure']=dict(kind='entities',ids='structure_ids')
    arrays.update(harmonic_times=np.array([0.]),initial_times=np.array([0.]),response_times=np.array([0.,.5,1.]),load_times=np.array([0.,.4,1.]))
    axes={'initial':'initial_times','response':'response_times','loads':'load_times'} if tr else {'harmonic':'harmonic_times'}
    defaults=dict(start_time=0.,end_time=1.,frequency=2.,density=1.,sound_speed=2.,direction_x=1.,direction_y=0.,direction_z=0.,reference_x=0.,reference_y=0.,reference_z=0.,amplitude_real=1.,amplitude_imag=0.,temperature=300.,gas_constant=287.,gamma=1.4,viscosity=.001,bulk_viscosity=0.,conductivity=.01,mean_x=.1,mean_y=0.,mean_z=0.,mode_count=1)
    params={k:defaults[k] for k in cfg['parameters']}
    m=dict(task=slug,spatial_dimension=3,data_file='input.h5',geometries={},meshes={'main':{'file':'mesh.msh'}},locations=locs,time_axes=axes,fields={},outputs={},physics=dict(model='acoustic-'+slug+'-v1',parameters={k:dict(value=v,unit=cfg['parameters'][k]['unit']) for k,v in params.items()}),conditions=[])
    def record(op,location,partner=None):
        r=cfg['records'][op];data={}
        for key,s in r['data'].items():
            if 'location' in s:data[key]={'location':partner};continue
            if 'option' in s:data[key]={'option':s['option']};continue
            axis='harmonic' if not tr else 'initial' if r['static'] or s.get('static') else 'loads';n=len(arrays[locs[location]['ids']]);nt=len(arrays[axes[axis]])
            val=np.zeros((nt,n,*shape(s,params)))
            if s.get('positive'):val[:]=1.
            if op=='material' and s['kind']=='components':val[...,0]=1.;val[...,1]=-.1
            if op=='structure' and key in ('mass','stiffness'):val[:]=np.eye(params['mode_count'])
            if op=='modal_wall':val[:]=1.
            name=op+'_'+key;name=name if partner is None else name+'_'+location;array='payload_'+name;arrays[array]=val
            l=locs[location];space='uniform' if l['kind']=='entities' else 'piecewise_linear' if l['entity']=='node' else 'piecewise_constant'
            m['fields'][name]=dict(array=array,quantity=r['variable'] if key=='value' else key,unit=s['unit'],kind=s['kind'],component_shape=shape(s,params),components=labels(s,params),dtype='float64',location=location,time_axis=axis,value_kind='average' if space=='piecewise_constant' else 'point',sampling=dict(space=space,time='constant' if nt==1 else 'linear',extrapolation='forbid'))
            data[key]={'field':name}
        m['conditions'].append(dict(role=r['role'],variable=r['variable'],operator=op,location=location,data=data))
    for op,r in cfg['records'].items():
        if not r['required']:continue
        if op=='periodic':
            for axis in 'xyz':record(op,axis+'_minus',axis+'_plus')
        else:record(op,dict(domain='domain',cells='cells',surface='surface',structure='structure',boundary_nodes='boundary_nodes',facets='wall')[r['where']])
    for q,s in cfg['outputs'].items():
        location='wall' if s['where'] in ('resonator','modal_wall') else s['where']
        m['outputs']['observation_'+q]=dict(array='answer_'+q,quantity=q,unit=s['unit'],kind=s['kind'],component_shape=shape(s,params),components=labels(s,params),dtype='float64',location=location,time_axis='response' if tr else 'harmonic',value_kind='point' if location in ('receivers','structure') else 'average')
    used=set(axes.values())|{l['ids'] for l in locs.values()}|{l['coordinates'] for l in locs.values() if 'coordinates' in l}|{f['array'] for f in m['fields'].values()}
    with h5py.File(base/'input.h5','w') as h:
        for key in used:h[key]=arrays[key]
    path=base/'problem.json';path.write_text(json.dumps(m));return path,m
