"""Disposable electromagnetic declaration fixtures, no physical references."""
from pathlib import Path
from itertools import combinations
import json
import gmsh
import h5py
import numpy as np
from caeoj_ext.electromagnetic import models,labels


def fixture(base,slug):
    base=Path(base);base.mkdir(parents=True,exist_ok=True);cfg=models()[slug];d=cfg['dimension'];tr=cfg['transient'];harm=cfg['harmonic'];arrays={};locs={};meshes={}
    def entity(name,ids):arrays[name+'_ids']=np.array(ids,dtype='int64');locs[name]=dict(kind='entities',ids=name+'_ids')
    def loc(name,tags,entity,dim=None):
        arrays[name+'_ids']=np.array(sorted(tags),dtype='int64');locs[name]=dict(kind='mesh',mesh='main',entity=entity,ids=name+'_ids')
        if dim is not None:locs[name]['dimension']=dim
    if d==0:
        entity('nodes',[0,7,23]);entity('branches',[11,29,47,65,83,101]);entity('resistors',[11,29])
        for op,tag in [('capacitor',47),('inductor',65),('voltage_source',83),('current_source',101)]:entity(op,[tag])
    else:
        xyz=np.array([[0.,0.,0.],[1.,0.,0.],[1.,1.,0.],[0.,1.,0.]]) if d==2 else np.array([[0.,0.,0.],[1.,0.,0.],[1.,1.,0.],[0.,1.,0.],[0.,0.,1.],[1.,0.,1.],[1.,1.,1.],[0.,1.,1.]])
        cells=[[0,1,2],[0,2,3]] if d==2 else [[0,1,2,6],[0,2,3,6],[0,3,7,6],[0,7,4,6],[0,4,5,6],[0,5,1,6]]
        tags=[13+17*i for i in range(len(xyz))];coord=dict(zip(tags,xyz));conn={101+i:tuple(tags[j] for j in c) for i,c in enumerate(cells)};counts={}
        for c in conn.values():
            for f in combinations(c,d):f=tuple(sorted(f));counts[f]=counts.get(f,0)+1
        boundary={301+i:f for i,(f,n) in enumerate(counts.items()) if n==1}
        gmsh.initialize([],readConfigFiles=False)
        try:
            gmsh.option.setNumber('General.Terminal',0);gmsh.model.add('electromagnetic_protocol_fixture');e=gmsh.model.addDiscreteEntity(d);gmsh.model.mesh.addNodes(d,e,tags,xyz.ravel());gmsh.model.mesh.addElementsByType(e,2 if d==2 else 4,list(conn),np.array(list(conn.values())).ravel())
            for tag,c in boundary.items():
                e=gmsh.model.addDiscreteEntity(d-1);gmsh.model.mesh.addElementsByType(e,1 if d==2 else 2,[tag],list(c))
            gmsh.option.setNumber('Mesh.MshFileVersion',4.1);gmsh.option.setNumber('Mesh.Binary',0);gmsh.write(str(base/'mesh.msh'))
        finally:gmsh.finalize()
        meshes={'main':{'file':'mesh.msh'}};loc('domain',tags,'node');loc('cells',conn,'element',d)
        loc('fixed',[n for n,x in coord.items() if x[0]==0.],'node');loc('floating',[n for n,x in coord.items() if x[0]==1.],'node')
        loc('flux',[next(t for t,c in boundary.items() if all(coord[n][1]==0 for n in c))],'element',d-1)
        if slug=='coil-circuit':entity('coil',[19])
    arrays.update(initial_times=np.array([0.]),response_times=np.array([.25,.75,1.]),load_times=np.array([0.,.5,1.]),marker=np.array([0.]))
    axis='response' if tr else 'harmonic' if harm else 'steady';axes={'initial':'initial_times','response':'response_times','loads':'load_times'} if tr else {axis:'marker'}
    defaults=dict(start_time=0.,end_time=1.,frequency=10.,ground_node=0,length=.4,resistance=1.,inductance=.01,capacitance=.001)
    p={k:defaults[k] for k in cfg['parameters']}
    m=dict(task=slug,spatial_dimension=d or 1,data_file='input.h5',geometries={},meshes=meshes,locations=locs,time_axes=axes,fields={},outputs={},physics=dict(model='electromagnetic-'+slug+'-v1',parameters={k:dict(value=v,unit=cfg['parameters'][k]['unit']) for k,v in p.items()}),conditions=[])
    def record(op,location):
        r=cfg['records'][op];data={};n=len(arrays[locs[location]['ids']])
        for key,s in r['data'].items():
            ta='initial' if tr and (r['static'] or s.get('static')) else 'loads' if tr else axis;nt=len(arrays[axes[ta]]);values=np.zeros((nt,n,*s['shape']),dtype=s.get('dtype','float64'))
            if s.get('positive') or op=='winding':values[:]=1.
            if key in ('tail','head'):
                ends={'resistor':[(0,7),(7,23)],'capacitor':[(0,7)],'inductor':[(7,23)],'voltage_source':[(0,23)],'current_source':[(7,23)]}
                values[0,:,0]=[pair[0 if key=='tail' else 1] for pair in ends[op]]
            name=op+'_'+key;array='payload_'+name;arrays[array]=values;l=locs[location];space='uniform' if l['kind']=='entities' else 'piecewise_linear' if l['entity']=='node' else 'piecewise_constant'
            m['fields'][name]=dict(array=array,quantity=r['variable'] if key=='value' else key,unit=s['unit'],kind=s['kind'],component_shape=s['shape'],components=labels(s),dtype=s.get('dtype','float64'),location=location,time_axis=ta,value_kind='average' if space=='piecewise_constant' else 'point',sampling=dict(space=space,time='constant' if nt==1 else 'linear',extrapolation='forbid'))
            data[key]={'field':name}
        m['conditions'].append(dict(role=r['role'],variable=r['variable'],operator=op,location=location,data=data))
    for op,r in cfg['records'].items():
        if not r['required'] and d!=0:continue
        where=r['where'];location='resistors' if op=='resistor' else op if where=='branches' else 'fixed' if where=='boundary_nodes' else 'floating' if where=='floating' else where
        record(op,location)
    for q,s in cfg['outputs'].items():
        location='floating' if s['where']=='floating' else s['where']
        m['outputs']['observation_'+q]=dict(array='answer_'+q,quantity=q,unit=s['unit'],kind=s['kind'],component_shape=s['shape'],components=labels(s),dtype='float64',location=location,time_axis=axis,value_kind='average' if location=='cells' else 'point')
    used=set(axes.values())|{l['ids'] for l in locs.values()}|{f['array'] for f in m['fields'].values()}
    with h5py.File(base/'input.h5','w') as h:
        for key in used:h[key]=arrays[key]
    path=base/'problem.json';path.write_text(json.dumps(m));return path,m
