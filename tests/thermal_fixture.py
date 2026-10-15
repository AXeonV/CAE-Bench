"""Disposable mesh/HDF5 contract fixtures; no thermal solver or trusted reference."""
from pathlib import Path
from itertools import combinations
import json
import gmsh
import h5py
import numpy as np
from caeoj_ext.thermal import models,shape,labels


def fixture(base,slug):
    base=Path(base);base.mkdir(parents=True,exist_ok=True);cfg=models()[slug];gray=cfg['topology']==0;d=cfg['dimension'];steady=cfg['steady']
    arrays={};locs={};meshes={};coord={};conn={};boundary={}
    def loc(name,tags,entity,dim=None):
        arrays[name+'_ids']=np.array(sorted(tags),dtype='int64');locs[name]=dict(kind='mesh',mesh='main',entity=entity,ids=name+'_ids')
        if dim is not None:locs[name]['dimension']=dim
    if gray:
        arrays['enclosure_ids']=np.array([19],dtype='int64');locs['enclosure']=dict(kind='entities',ids='enclosure_ids')
    else:
        if d==2:
            xy=[[0.,0.,0.],[1.,0.,0.],[1.,1.,0.],[0.,1.,0.]];cell=[[0,1,2],[0,2,3]]
        else:
            # Two pyramidal tetrahedra sharing z=0; contact duplicates its three vertices.
            xy=[[0.,0.,0.],[1.,0.,0.],[0.,1.,0.],[0.,0.,-1.],[0.,0.,1.]];cell=[[0,1,2,3],[0,1,2,4]]
            if slug=='thermal-contact':xy += [[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]];cell=[[0,1,2,3],[5,6,7,4]]
        tags=[13+11*i for i in range(len(xy))];coord=dict(zip(tags,xy));conn={101+i:tuple(tags[j] for j in c) for i,c in enumerate(cell)}
        counts={}
        for c in conn.values():
            for f in combinations(c,d):f=tuple(sorted(f));counts[f]=counts.get(f,0)+1
        boundary={301+i:f for i,(f,n) in enumerate(counts.items()) if n==1}
        gmsh.initialize([],readConfigFiles=False)
        try:
            gmsh.option.setNumber('General.Terminal',0);gmsh.model.add('thermal_protocol_fixture');e=gmsh.model.addDiscreteEntity(d);gmsh.model.mesh.addNodes(d,e,tags,np.array(xy).ravel());gmsh.model.mesh.addElementsByType(e,2 if d==2 else 4,list(conn),np.array(list(conn.values())).ravel())
            for tag,c in boundary.items():
                e=gmsh.model.addDiscreteEntity(d-1);gmsh.model.mesh.addElementsByType(e,1 if d==2 else 2,[tag],list(c))
            gmsh.option.setNumber('Mesh.MshFileVersion',4.1);gmsh.option.setNumber('Mesh.Binary',0);gmsh.write(str(base/'mesh.msh'))
        finally:gmsh.finalize()
        meshes['main']=dict(file='mesh.msh');loc('domain',tags,'node');loc('cells',conn,'element',d);loc('boundary',boundary,'element',d-1)
        if slug=='thermal-contact':
            minus=[tag for tag,c in boundary.items() if set(c)=={tags[0],tags[1],tags[2]}];plus=[tag for tag,c in boundary.items() if set(c)=={tags[5],tags[6],tags[7]}]
            loc('minus',minus,'element',2);loc('plus',plus,'element',2)
        # Fix one outside face (closure exactly that face), leaving contact sides unused.
        target=next(c for c in boundary.values() if len(c)==d and any(coord[n][d-1]<0 for n in c)) if d==3 else next(iter(boundary.values()))
        loc('temperature_nodes',target,'node')
        rad=[tag for tag,c in boundary.items() if not set(c)<=set(target)]
        loc('exchange',rad[:1],'element',d-1)
    arrays.update(steady_times=np.array([0.]),initial_times=np.array([0.]),response_times=np.array([.1,.5,1.]),load_times=np.array([0.,.4,1.]))
    axes={'steady':'steady_times'} if steady else {'initial':'initial_times','response':'response_times','loads':'load_times'}
    values=dict(start_time=0.,end_time=1.,temperature_min=200.,temperature_max=600.,temperature_reference=300.,patch_count=2,solidus=300.,liquidus=310.,melting_temperature=300.)
    p={k:values[k] for k in cfg['parameters']}
    m=dict(task=slug,spatial_dimension=d,data_file='input.h5',geometries={},meshes=meshes,locations=locs,time_axes=axes,fields={},outputs={},physics=dict(model='thermal-'+slug+'-v1',parameters={k:dict(value=v,unit=cfg['parameters'][k]['unit']) for k,v in p.items()}),conditions=[])
    def record(op,location):
        r=cfg['records'][op];data={}
        for key,s in r['data'].items():
            if 'location' in s:data[key]=dict(location='plus');continue
            axis='steady' if steady else 'initial' if r['static'] else 'loads';n=len(arrays[locs[location]['ids']]);t=len(arrays[axes[axis]]);sh=shape(s,p)
            val=np.zeros((t,n,*sh),dtype=s.get('dtype','float64'))
            if s.get('positive'):val[:]=1.
            if s['unit']=='K':val[:]=300.
            if key=='conductivity' and s['kind']=='tensor':val[:]=np.eye(3)
            if key=='capacity':val[:]=2.
            if key=='latent_heat':val[:]=100.
            if key=='view_factors':val[:]=[[0.,1.],[1.,0.]]
            if key=='emissivity':val[:]=.8
            if key=='medium':val[0,:,0]=[0,1]
            if op=='initial_enthalpy':val[:]=0.
            name=op+'_'+key;array='payload_'+name;arrays[array]=val
            q=key if key!='value' else dict(heat_source='heat_source',power='power',initial_enthalpy='enthalpy',prescribed_velocity='velocity',heat_flux='heat_flux').get(op,'temperature')
            space='uniform' if gray else 'piecewise_linear' if locs[location]['entity']=='node' else 'piecewise_constant'
            m['fields'][name]=dict(array=array,quantity=q,unit=s['unit'],kind=s['kind'],component_shape=sh,components=labels(s,p),dtype=s.get('dtype','float64'),location=location,time_axis=axis,value_kind='point' if space!='piecewise_constant' else 'average',sampling=dict(space=space,time='constant' if t==1 else 'linear',extrapolation='forbid'))
            data[key]=dict(field=name)
        m['conditions'].append(dict(role=r['role'],variable=r['variable'],operator=op,location=location,data=data))
    for op,r in cfg['records'].items():
        if not r['required'] and op!='temperature':continue
        location=dict(domain='domain',cells='cells',enclosure='enclosure',nodes='temperature_nodes',facets='minus' if op=='thermal_pair' else 'exchange')[r['where']]
        record(op,location)
    for q,s in cfg['outputs'].items():
        location='enclosure' if gray else 'minus' if s['where']=='interface' else 'cells'
        m['outputs']['observation_'+q]=dict(array='answer_'+q,quantity=q,unit=s['unit'],kind=s['kind'],component_shape=shape(s,p),components=labels(s,p),dtype='float64',location=location,time_axis='steady' if steady else 'response',value_kind='point' if gray else 'average')
    used=set(axes.values())|{l['ids'] for l in locs.values()}|{f['array'] for f in m['fields'].values()}
    with h5py.File(base/'input.h5','w') as h:
        for key in used:h[key]=arrays[key]
    path=base/'problem.json';path.write_text(json.dumps(m));return path,m
