"""Temporary protocol fixtures only; no benchmark data or trusted reference."""
from itertools import combinations
import json
from pathlib import Path
import gmsh
import h5py
import numpy as np
from caeoj_ext.solid import models


def fixture(base, slug):
    base=Path(base);base.mkdir(parents=True,exist_ok=True);cfg=models()[slug];d=cfg['dimension'];top=cfg['topology'];hist=cfg['mode']=='history'
    arrays={};locs={};mesh={};coords={};conns={};exterior={};taglist=[]
    def location(name,tags,entity,dimension=None):
        key=name+'_ids';arrays[key]=np.array(sorted(tags),dtype='int64')
        locs[name]=dict(kind='mesh',mesh='main',entity=entity,ids=key)
        if dimension is not None:locs[name]['dimension']=dimension
    if top:
        if top==3:
            xy=[[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]]
            c=[[0,1,2,6],[0,2,3,6],[0,3,7,6],[0,7,4,6],[0,4,5,6],[0,5,1,6]]
        elif top==2:
            xy=[[0,0,0],[1,0,0],[1,1,0],[0,1,0]];c=[[0,1,2],[0,2,3]]
            if slug=='cohesive-interface':
                xy=[[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,1,0],[1,1,0],[1,2,0],[0,2,0]]
                c=[[0,1,2],[0,2,3],[4,5,6],[4,6,7]]
        else:
            if slug=='elastic-truss':xy=[[0,0,0],[1,0,0],[0,1,0]];c=[[0,1],[1,2],[2,0]]
            else:xy=[[0,0,0],[1,0,0],[2,0,0]];c=[[0,1],[1,2]]
        tags=[11+12*i for i in range(len(xy))];coords=dict(zip(tags,xy));conns={101+i:tuple(tags[n] for n in conn) for i,conn in enumerate(c)}
        faces={}
        for conn in conns.values():
            for face in combinations(conn,top):
                face=tuple(sorted(face));faces[face]=faces.get(face,0)+1
        exterior={201+i:face for i,(face,count) in enumerate(faces.items()) if count==1}
        if slug=='elastic-truss':exterior={201+i:(tag,) for i,tag in enumerate(tags)}
        gmsh.initialize([],readConfigFiles=False)
        try:
            gmsh.option.setNumber('General.Terminal',0);gmsh.model.add('solid_fixture')
            e=gmsh.model.addDiscreteEntity(top);gmsh.model.mesh.addNodes(top,e,tags,np.array(xy).ravel())
            gmsh.model.mesh.addElementsByType(e,{1:1,2:2,3:4}[top],list(conns),np.array(list(conns.values())).ravel())
            for tag,conn in exterior.items():
                e=gmsh.model.addDiscreteEntity(top-1);gmsh.model.mesh.addElementsByType(e,{1:15,2:1,3:2}[top],[tag],list(conn))
            gmsh.option.setNumber('Mesh.MshFileVersion',4.1);gmsh.option.setNumber('Mesh.Binary',0);gmsh.write(str(base/'mesh.msh'))
        finally:gmsh.finalize()
        mesh={'main':{'file':'mesh.msh'}}
        location('domain',tags,'node');location('cells',conns,'element',top);location('boundary',exterior,'element',top-1)
        if top==3:
            fixed=[t for t,x in coords.items() if x[2]==0]
            contact=[t for t,conn in exterior.items() if all(coords[n][2]==1 for n in conn)]
        elif top==2:
            fixed=[t for t,x in coords.items() if x[0]==0]
            if slug=='cohesive-interface':fixed=[t for t,x in coords.items() if x[1] in (0,2)]
            contact=[]
        else:fixed=[tags[0]];contact=[]
        location('fixed_nodes',fixed,'node')
        if contact:location('contact',contact,'element',top-1)
        if slug=='elastic-beam':location('free_end',[tags[-1]],'node')
        if slug=='cohesive-interface':
            minus=[t for t,conn in exterior.items() if set(conn)=={tags[2],tags[3]}]
            plus=[t for t,conn in exterior.items() if set(conn)=={tags[4],tags[5]}]
            location('minus',minus,'element',1);location('plus',plus,'element',1)
        arrays['whole_ids']=np.array([0],dtype='int64')
        locs['whole_sum']=dict(kind='aggregate',source='cells',ids='whole_ids',operation='sum')
        locs['whole_mean']=dict(kind='aggregate',source='cells',ids='whole_ids',operation='mean')
    else:
        arrays.update(sites_ids=np.array([0,4],dtype='int64'),sites_coordinates=np.array([[0.,0.],[1.,0.]]))
        locs['sites']=dict(kind='points',ids='sites_ids',coordinates='sites_coordinates')
    arrays.update(steady_times=np.array([0.]),initial_times=np.array([0.]),response_times=np.array([0.,.5,1.]),load_times=np.array([0.,.5,1.]))
    axes={'response':'response_times','initial':'initial_times','loads':'load_times'} if hist else {'steady':'steady_times'}
    params={k:dict(value=1.,unit=x['unit']) for k,x in cfg['parameters'].items()}
    defaults={'young_modulus':1000000.,'poisson_ratio':.25,'start_time':0.,'end_time':1.,'mode_count':3,'normal_x':0.,'normal_y':1. if d==2 else 0.,'normal_z':1.,'plane_offset':1.,'residual_stiffness':.01,'initial_length':.1,'width':10.,'reference_intensity_squared':1e14,'critical_intensity_squared':1e16,'ultimate_strength':1e8,'geometry_linear':0.,'geometry_quadratic':0.}
    for k,val in defaults.items():
        if k in params:params[k]['value']=val
    m=dict(task=slug,spatial_dimension=d,data_file='input.h5',geometries={},meshes=mesh,locations=locs,time_axes=axes,fields={},outputs={},physics=dict(model=cfg['model'],parameters=params),conditions=[])
    def field(name,spec,loc,initial=False,zero=False):
        kind=spec['kind'];shape=[d] if kind=='vector' else [d,d] if kind=='tensor' else [1]
        labels=list('xyz'[:d]) if kind=='vector' else [a+b for a in 'xyz'[:d] for b in 'xyz'[:d]] if kind=='tensor' else ['value']
        axis='initial' if initial else 'loads' if hist else 'steady';t=arrays[axes[axis]];n=len(arrays[locs[loc]['ids']])
        values=np.zeros((len(t),n,*shape))
        if spec['quantity'] in ('area','rigidity'):values[:]=1.
        if spec['quantity']=='crack_length':values[:]=.1
        space='uniform' if top==0 else 'piecewise_linear' if locs[loc].get('entity')=='node' else 'piecewise_constant'
        time='constant' if initial or not hist else 'previous' if not top else 'linear'
        arrays['payload_'+name]=values
        m['fields'][name]=dict(array='payload_'+name,quantity=spec['quantity'],unit=spec['unit'],kind=kind,component_shape=shape,components=labels,dtype='float64',location=loc,time_axis=axis,value_kind='point' if space!='piecewise_constant' else 'average',sampling=dict(space=space,time=time,extrapolation='forbid'))
        return dict(field=name)
    for op,(role,var,where,data,desc) in cfg['rules'].items():
        if op in ('traction','end_load','nodal_force') or op.startswith('traction_'):continue
        if role=='boundary':
            loc='minus' if op=='cohesive_pair' else 'contact' if op=='rigid_plane' else 'boundary' if op=='plate_clamp' else 'fixed_nodes'
        elif where=='sites':loc='sites'
        elif role=='initial':loc='domain'
        else:loc='cells'
        dv={}
        for k,s in data.items():
            if 'option' in s:dv[k]={'option':s['option']}
            elif 'location' in s:dv[k]={'location':'plus'}
            else:dv[k]=field(op+'_'+k,s,loc,role=='initial')
        m['conditions'].append(dict(role=role,variable=var,operator=op,location=loc,data=dv))
    for q,s in cfg['output_specs'].items():
        where=s['where'];loc={'nodes':'domain','cells':'cells','sum':'whole_sum','mean':'whole_mean','sites':'sites','contact':'contact','interface':'minus'}[where]
        kind=s['kind'];shape=[d] if kind=='vector' else [d,d] if kind=='tensor' else [params['mode_count']['value']] if kind=='spectrum' else [1]
        labels=list('xyz'[:d]) if kind=='vector' else [a+b for a in 'xyz'[:d] for b in 'xyz'[:d]] if kind=='tensor' else ['f'+str(i+1) for i in range(shape[0])] if kind=='spectrum' else ['value']
        m['outputs']['observation_'+q]=dict(array='answer_'+q,quantity=q,unit=s['unit'],kind='components' if kind=='spectrum' else kind,component_shape=shape,components=labels,dtype='float64',location=loc,time_axis='response' if hist else 'steady',value_kind='integral' if where=='sum' else 'point' if where in ('nodes','sites') else 'average')
    used={loc['ids'] for loc in locs.values()}|{loc['coordinates'] for loc in locs.values() if loc['kind']=='points'}|set(axes.values())|{f['array'] for f in m['fields'].values()}
    with h5py.File(base/'input.h5','w') as f:
        for key in used:f.create_dataset(key,data=arrays[key])
    path=base/'problem.json';path.write_text(json.dumps(m));return path,m
