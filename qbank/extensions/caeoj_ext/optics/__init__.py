"""Optical declaration validation; no propagation, eigenmode or reference solver."""
from functools import lru_cache
from importlib.resources import files
import json,math
import numpy as np


@lru_cache(maxsize=1)
def models():return json.loads(files(__package__).joinpath('models.json').read_text())


def shape(s,p):return [p['wave_count'] if x=='w' else p['mode_count'] if x=='m' else x for x in s['shape']]


def labels(s,p):
    return ['value'] if s['kind']=='scalar' else ['x','y','z'] if s['kind']=='vector' else ['c'+str(i+1) for i in range(math.prod(shape(s,p)))]


def check(problem,errors):
    from caeoj.validation import issue
    m,a=problem.manifest,problem.arrays;model=m.get('physics',{}).get('model','');slug=model.removeprefix('optics-').removesuffix('-v1');cfg=models().get(slug)
    def fail(path,expected,actual):
        if isinstance(actual,np.ndarray):actual=actual.tolist() if actual.size<16 else list(actual.shape)
        errors.append(issue('E_OPTICS',path,expected,actual,'Declaration violates this optical DATA contract.'))
    if cfg is None or model!='optics-'+slug+'-v1':fail('$.physics.model','registered optical model',model);return
    if m['spatial_dimension']!=cfg['spatial_dimension']:fail('$.spatial_dimension',cfg['spatial_dimension'],m['spatial_dimension'])
    if 'task' in m and m['task']!=slug:fail('$.task',slug,m['task'])
    if any(k in m for k in ('profile','contract_version','analysis','materials')):fail('$','physics-only declaration','mixed profile')
    params=m['physics'].get('parameters',{});p={}
    if set(params)!=set(cfg['parameters']):fail('$.physics.parameters',list(cfg['parameters']),list(params));return
    for key,s in cfg['parameters'].items():
        v=params[key];x=v.get('value')
        if set(v)!={'value','unit'} or v.get('unit')!=s['unit'] or type(x) not in ((int,) if s.get('integer') else (int,float)):fail('$.physics.parameters.'+key,s,v);continue
        if s.get('positive') and x<=0 or 'lower' in s and x<s['lower'] or 'upper' in s and x>s['upper'] or 'upper_exclusive' in s and x>=s['upper_exclusive']:fail('$.physics.parameters.'+key,s,x)
        p[key]=x
    locs=m['locations'];axis='steady' if slug=='layered-rays' else 'optical'
    if set(m['time_axes'])!={axis}:fail('$.time_axes','single '+axis+' axis',list(m['time_axes']));return
    if not np.array_equal(a[m['time_axes'][axis]],[0.]):fail('$.time_axes.'+axis,'single [0.0] marker',a[m['time_axes'][axis]])
    if set(locs)!=set(cfg['locations']):fail('$.locations',list(cfg['locations']),list(locs));return
    for name,s in cfg['locations'].items():
        l=locs[name]
        if l['kind']!=s['kind']:fail('$.locations.'+name+'.kind',s['kind'],l['kind']);continue
        if s['kind']=='mesh':
            expected=dict(mesh='main',entity=s['entity'])
            if s['entity']=='element':expected['dimension']=2
            for k,v in expected.items():
                if l.get(k)!=v:fail('$.locations.'+name+'.'+k,v,l.get(k))
        else:
            n=len(a[l['ids']])
            if not s['minimum']<=n<=s['maximum']:fail('$.locations.'+name,'object count limits',n)
    if errors:return
    if cfg['mesh']:
        if set(m['meshes'])!={'main'}:fail('$.meshes','one main aperture mesh',list(m['meshes']));return
        mesh=problem.meshes['main'];top=mesh['elements'][2];nodes=set()
        if mesh['dimension']!=2 or not top or any(mesh['elements'][v] for v in (0,1,3)):fail('$.meshes.main','triangles only','wrong topology');return
        if np.any(mesh['coordinates'][:,2]!=0):fail('$.meshes.main','z=0 aperture','nonzero z')
        for tag in top:
            typ,conn=mesh['connectivity'][tag]
            if typ!=2:fail('$.meshes.main','first order triangles',typ);continue
            nodes.update(conn);x=np.array([mesh['node_coordinates'][n] for n in conn])
            if np.linalg.matrix_rank(x[1:]-x[0])!=2:fail('$.meshes.main','nondegenerate triangles',tag)
        if nodes!=mesh['nodes'] or len(nodes)>4000 or len(top)>800:fail('$.meshes.main','no unused nodes and size limits',[len(nodes),len(top)])
        for name,tags in [('domain',nodes),('aperture',top)]:
            if set(map(int,a[locs[name]['ids']]))!=tags:fail('$.locations.'+name,'complete support','subset')
        if slug=='fresnel-aperture':
            z=a[locs['receivers']['coordinates']][:,2];clearance=1e-8*np.linalg.norm(np.ptp(mesh['coordinates'],axis=0))
            if np.any(z<=0) or np.any(z<clearance):fail('$.locations.receivers','z>0 and clearance',z)
    elif m['meshes'] or m.get('geometries'):fail('$.meshes/geometries','empty objects','spatial geometry')
    for name,key in [('waves','wave_count'),('modes','mode_count')]:
        if name in locs and not np.array_equal(a[locs[name]['ids']],np.arange(p[key])):fail('$.locations.'+name,'IDs exactly 0..'+str(p[key]-1),a[locs[name]['ids']])
    if slug=='slab-modes' and np.any(a[locs['receivers']['coordinates']][:,1:]!=0):fail('$.locations.receivers','(x,0,0)','nonzero y/z')
    refs=set();byop={};counts={}
    def typed(v,s,location,key,path):
        if 'value' in v:
            if set(v)!={'value','unit'} or s['kind']!='scalar' or v.get('unit')!=s['unit'] or type(v.get('value')) not in (int,float):fail(path,'typed scalar constant',v);return
            values=np.full((1,len(a[locs[location]['ids']]),*shape(s,p)),v['value'])
        elif set(v)=={'field'}:
            name=v['field'];refs.add(name);fs=m['fields'][name];l=locs[location];element=l['kind']=='mesh' and l['entity']=='element'
            expected=dict(quantity=key,unit=s['unit'],kind=s['kind'],component_shape=shape(s,p),components=labels(s,p),dtype='float64',location=location,time_axis=axis,value_kind='average' if element else 'point',sampling=dict(space='piecewise_constant' if element else 'uniform',time='constant',extrapolation='forbid'))
            for k,x in expected.items():
                if fs.get(k)!=x:fail('$.fields.'+name+'.'+k,x,fs.get(k))
            values=a[fs['array']]
        else:fail(path,'field or typed scalar constant',v);return
        if s.get('positive') and np.any(values<=0):fail(path,'positive values','nonpositive')
        return values
    for i,c in enumerate(m['conditions']):
        path=f'$.conditions[{i}]';op=c['operator'];r=cfg['records'].get(op)
        if r is None:fail(path+'.operator',list(cfg['records']),op);continue
        counts[op]=counts.get(op,0)+1
        for k in ('role','variable','location'):
            if c[k]!=r[k]:fail(path+'.'+k,r[k],c[k])
        if c['location']!=r['location']:continue
        if counts[op]!=1:fail(path,'one complete record',counts[op])
        if set(c['data'])!=set(r['data']):fail(path+'.data',list(r['data']),list(c['data']));continue
        v={key:typed(c['data'][key],s,r['location'],r['variable'] if key=='value' else key,path+'.data.'+key) for key,s in r['data'].items()}
        if not any(x is None for x in v.values()):byop[op]=v
    for op in cfg['records']:
        if not counts.get(op):fail('$.conditions','required '+op,'missing')
    if refs!=set(m['fields']):fail('$.fields','exact referenced fields',sorted(set(m['fields'])-refs))
    if errors:return
    directions=[]
    if slug=='layered-rays':
        launch=byop['launch'];direction=launch['direction'][0];directions.append(direction)
        if np.any(launch['origin'][...,2]!=0) or np.any(direction[:,2]<1e-4):fail('$.conditions.launch','z=0 origins and forward d_z>=1e-4','invalid launch')
        target=np.r_[byop['layers']['index'].ravel(),p['output_index']]
        with np.errstate(over='ignore',invalid='ignore',divide='ignore'):
            ratio=np.square((p['input_index']/target)[None,:]*np.linalg.norm(direction[:,:2],axis=1)[:,None])
        if np.any(abs(ratio-1)<1e-8):fail('$.conditions.launch','critical incidence margin','near critical')
    if 'waves' in byop:directions.append(byop['waves']['direction'][0])
    if slug=='farfield-aperture':
        direction=byop['directions']['value'][0];directions.append(direction)
        if np.any(direction[:,2]<1e-4):fail('$.conditions.directions','s_z>=1e-4','backward/grazing')
    for direction in directions:
        if np.any(abs(np.linalg.norm(direction,axis=-1)-1)>1e-12):fail('$.fields.direction','unit vectors to 1e-12','bad norm')
    if slug=='partial-coherence':
        raw=byop['coherence']['value'][0,0];scale=max(1.,np.max(abs(raw)));scaled=raw/scale;z=scaled[...,0]+1j*scaled[...,1];tol=1e-12*max(1/scale,np.linalg.norm(z))
        if np.max(abs(z-z.conj().T))>tol:fail('$.fields.covariance','Hermitian matrix','nonsymmetric')
        elif np.linalg.eigvalsh((z+z.conj().T)/2).min() < -tol:fail('$.fields.covariance','positive semidefinite','negative eigenvalue')
    if slug=='jones-chain':
        raw=byop['elements']['value'][0];z=raw[...,0]+1j*raw[...,1]
        if np.any(np.linalg.svd(z,compute_uv=False)>1+1e-12):fail('$.fields.jones_matrix','passive operator norm <=1','gain')
    if slug=='thin-film':
        indices=np.r_[byop['layers']['index'].ravel(),p['output_index']]
        with np.errstate(over='ignore',invalid='ignore',divide='ignore'):
            ratio=np.square((p['input_index']/indices)*p['incidence_sine'])
        if np.any(ratio>1-1e-8):fail('$.conditions.layers','propagating noncritical layers and exit','evanescent/critical')
    if slug=='slab-modes' and byop['layers']['index'].max()<=max(p['left_index'],p['right_index']):fail('$.conditions.layers','index above both claddings','no guiding contrast')
    present=set();total=0
    for name,s in m['outputs'].items():
        q=s['quantity'];os=cfg['outputs'].get(q);path='$.outputs.'+name
        if os is None:fail(path+'.quantity',list(cfg['outputs']),q);continue
        present.add(q);expected=dict(unit=os['unit'],kind=os['kind'],component_shape=shape(os,p),components=labels(os,p),dtype='float64',location=os['location'],time_axis=axis,value_kind='point')
        for key,v in expected.items():
            if s.get(key)!=v:fail(path+'.'+key,v,s.get(key))
        if 'sampling' in s:fail(path,'no output sampling',s['sampling'])
        total+=len(a[locs[s['location']]['ids']])*math.prod(s['component_shape'])
    if present!=set(cfg['outputs']):fail('$.outputs','all required quantities',sorted(present))
    if max(total,sum(a[s['array']].size for s in m['fields'].values()))>2000000:fail('$.fields/outputs','<=2000000 components each','excess')
