"""Electromagnetic and circuit declaration checks, without a field/reference solver."""
from functools import lru_cache
from importlib.resources import files
import json,math
import numpy as np


@lru_cache(maxsize=1)
def models():return json.loads(files(__package__).joinpath('models.json').read_text(encoding='utf-8'))


def shape(s,p=None):return s['shape']


def labels(s,p=None):
    if s['kind']=='scalar':return ['value']
    if s['kind']=='vector':return list('xyz'[:s['shape'][0]])
    return ['c'+str(i+1) for i in range(math.prod(s['shape']))]


def check(problem,errors):
    from caeoj.validation import issue
    from .geometry import inspect
    m,a=problem.manifest,problem.arrays;model=m.get('physics',{}).get('model','');slug=model.removeprefix('electromagnetic-').removesuffix('-v1');cfg=models().get(slug)
    def fail(path,expected,actual):
        if isinstance(actual,np.ndarray):actual=actual.tolist() if actual.size<20 else list(actual.shape)
        errors.append(issue('E_ELECTROMAGNETIC',path,expected,actual,'Declaration violates this electromagnetic DATA contract.'))
    if cfg is None or model!='electromagnetic-'+slug+'-v1':fail('$.physics.model','registered electromagnetic model',model);return
    d=cfg['dimension'];circuit=d==0;tr=cfg['transient'];harm=cfg['harmonic'];axis='response' if tr else 'harmonic' if harm else 'steady';static_axis='initial' if tr else axis
    if m['spatial_dimension']!=(1 if circuit else d):fail('$.spatial_dimension',1 if circuit else d,m['spatial_dimension'])
    if 'task' in m and m['task']!=slug:fail('$.task',slug,m['task'])
    if any(k in m for k in ('profile','contract_version','analysis','materials')):fail('$','physics-only declaration','mixed profile')
    p={};params=m['physics'].get('parameters',{})
    if set(params)!=set(cfg['parameters']):fail('$.physics.parameters',list(cfg['parameters']),list(params));return
    for key,s in cfg['parameters'].items():
        v=params[key];x=v.get('value')
        if set(v)!={'value','unit'} or v.get('unit')!=s['unit'] or type(x) not in ((int,) if s.get('integer') else (int,float)):fail('$.physics.parameters.'+key,s,v);continue
        if s.get('positive') and x<=0 or 'lower' in s and x<s['lower']:fail('$.physics.parameters.'+key,s,x)
        p[key]=x
    if errors:return
    locs=m['locations']
    def ids(name):return set(map(int,a[locs[name]['ids']]))
    if circuit:
        if m['meshes'] or m.get('geometries'):fail('$.meshes/geometries','empty objects','spatial geometry')
        for name,limit in [('nodes',33),('branches',64)]:
            if name not in locs or locs[name]['kind']!='entities':fail('$.locations.'+name,'entities','missing or wrong kind');continue
            if not (2 if name=='nodes' else 1)<=len(ids(name))<=limit:fail('$.locations.'+name,'entity count limits',len(ids(name)))
        if errors:return
        nodes=ids('nodes');branches=ids('branches')
        if p['ground_node'] not in nodes:fail('$.physics.parameters.ground_node','a nodes ID',p['ground_node'])
        for name,l in locs.items():
            if l['kind']!='entities' or not (ids(name)<=nodes or ids(name)<=branches):fail('$.locations.'+name,'node or branch subset entities',l)
        geo=None
    else:
        geo=inspect(problem,cfg,fail)
        if errors or geo is None:return
    if tr and p['end_time']<=p['start_time']:fail('$.physics.parameters','tf>t0',p['end_time'])
    required={'initial','response'} if tr else {axis}
    if not required<=set(m['time_axes']):fail('$.time_axes','required '+str(required),list(m['time_axes']));return
    if not tr and set(m['time_axes'])!={axis}:fail('$.time_axes','only '+axis,list(m['time_axes']))
    t0=p['start_time'] if tr else 0.;tf=p['end_time'] if tr else 0.
    if not np.array_equal(a[m['time_axes'][static_axis]],[t0]):fail('$.time_axes.'+static_axis,'single initial/static marker',a[m['time_axes'][static_axis]])
    times=a[m['time_axes'][axis]]
    if times[0]<t0 or times[-1]>tf or slug=='dielectric-relaxation' and times[0]<=t0:fail('$.time_axes.'+axis,'requested physical interval',times)
    if any(len(a[v])>129 for v in m['time_axes'].values()):fail('$.time_axes','<=129 frames','excess')
    refs=set();axes=set(required);counts={};byop={};usedfaces=set();usednodes=set();floatings=set();usedbranches=set();branches_data=[]
    def support(name,where):
        l=locs[name];tags=ids(name)
        if circuit:return name=='nodes' if where=='nodes' else l['kind']=='entities' and tags<=branches
        if where in ('domain','coil'):return name==where
        if l['kind']!='mesh':return False
        if where=='cells':return l['entity']=='element' and l['dimension']==d and tags==geo['cells']
        if where in ('boundary_nodes','floating'):return l['entity']=='node' and tags<=geo['boundary_nodes']
        if where=='facets':return l['entity']=='element' and l['dimension']==d-1 and tags<=set(geo['exterior'])
        return False
    def typed(v,s,location,static,key,path):
        if 'value' in v:
            if set(v)!={'value','unit'} or s['kind']!='scalar' or s.get('dtype')=='int64' or v.get('unit')!=s['unit'] or type(v.get('value')) not in (int,float):fail(path,'typed scalar constant',v);return
            values=np.full((1,len(ids(location)),*s['shape']),v['value'])
        elif set(v)=={'field'}:
            name=v['field'];refs.add(name);fs=m['fields'][name];l=locs[location]
            point=l['kind']=='entities' or l.get('entity')=='node';space='uniform' if l['kind']=='entities' else 'piecewise_linear' if point else 'piecewise_constant'
            expected=dict(quantity=key,unit=s['unit'],kind=s['kind'],component_shape=s['shape'],components=labels(s),dtype=s.get('dtype','float64'),location=location,value_kind='point' if point else 'average')
            for k,x in expected.items():
                if fs.get(k)!=x:fail('$.fields.'+name+'.'+k,x,fs.get(k))
            ta=fs['time_axis'];axes.add(ta);ts=a[m['time_axes'][ta]]
            if static and ta!=static_axis:fail('$.fields.'+name+'.time_axis',static_axis,ta)
            if len(ts)==1 and ts[0]!=t0 or len(ts)>1 and (static or not tr or ts[0]!=t0 or ts[-1]!=tf):fail('$.fields.'+name+'.time_axis','static marker or full loading interval',ts)
            expected_sampling=dict(space=space,time='constant' if len(ts)==1 else 'linear',extrapolation='forbid')
            if fs.get('sampling')!=expected_sampling:fail('$.fields.'+name+'.sampling',expected_sampling,fs.get('sampling'))
            values=a[fs['array']]
        else:fail(path,'field or typed scalar constant',v);return
        if s.get('positive') and np.any(values<=0) or 'lower' in s and np.any(values<s['lower']):fail(path,'allowed value range','out of range')
        return values
    for i,c in enumerate(m['conditions']):
        path=f'$.conditions[{i}]';op=c['operator'];r=cfg['records'].get(op)
        if r is None:fail(path+'.operator',list(cfg['records']),op);continue
        location=c['location'];tags=ids(location);counts[op]=counts.get(op,0)+1
        for k in ('role','variable'):
            if c[k]!=r[k]:fail(path+'.'+k,r[k],c[k])
        if not support(location,r['where']):fail(path+'.location',r['where'],location);continue
        if r['where'] in ('cells','domain','nodes','coil') and counts[op]!=1:fail(path+'.location','one complete record',location)
        if set(c['data'])!=set(r['data']):fail(path+'.data',list(r['data']),list(c['data']));continue
        values={key:typed(c['data'][key],s,location,r['static'] or s.get('static') or not tr,r['variable'] if key=='value' else key,path+'.data.'+key) for key,s in r['data'].items()}
        if any(v is None for v in values.values()):continue
        byop.setdefault(op,[]).append((location,values))
        if circuit and r['where']=='branches':
            if usedbranches&tags:fail(path+'.location','disjoint branch partition',location)
            usedbranches.update(tags)
            for j,tag in enumerate(a[locs[location]['ids']]):
                tail,head=int(values['tail'][0,j,0]),int(values['head'][0,j,0]);branches_data.append((op,int(tag),tail,head))
                if tail==head or tail not in nodes or head not in nodes:fail(path+'.data','distinct existing endpoint IDs',[tail,head])
        if not circuit and r['where'] in ('boundary_nodes','floating','facets'):
            if r['where']=='facets':selected=tags
            else:
                selected={t for t,f in geo['exterior'].items() if set(f)<=tags}
                if {n for t in selected for n in geo['exterior'][t]}!=tags or usednodes&tags:fail(path+'.location','complete disjoint boundary node closure',location)
                usednodes.update(tags)
            if usedfaces&selected:fail(path+'.location','no overlapping boundary faces',location)
            usedfaces.update(selected)
            if op=='floating':
                floatings.add(location);x=values['charge']
                if np.any(x!=x.flat[0]):fail(path+'.data.charge','one total charge per conductor','spatial variation')
                connected=set();stack=[next(iter(selected))] if selected else []
                while stack:
                    tag=stack.pop()
                    if tag not in connected:connected.add(tag);stack.extend(t for t in selected-connected if set(geo['exterior'][t])&set(geo['exterior'][tag]))
                if connected!=selected:fail(path+'.location','connected conductor boundary','disconnected')
    for op,r in cfg['records'].items():
        if r['required'] and not counts.get(op):fail('$.conditions','required '+op,'missing')
    if refs!=set(m['fields']):fail('$.fields','exact referenced fields',sorted(set(m['fields'])-refs))
    if axes!=set(m['time_axes']):fail('$.time_axes','no unused axes',list(m['time_axes']))
    if errors:return
    if slug=='dielectric-relaxation':
        for name in axes-required:
            if np.any(np.isin(times,a[m['time_axes'][name]][1:-1])):fail('$.time_axes.response','not at loading interior corners',times)
    if slug=='coil-circuit' and not np.any(byop['winding'][0][1]['value']!=0):fail('$.fields.winding','nonzero winding density','all zero')
    if circuit:
        if usedbranches!=branches:fail('$.conditions','complete branch partition','missing branches')
        resist={n:set() for n in nodes};voltage_parent={n:n for n in nodes}
        def parent(n):
            while voltage_parent[n]!=n:n=voltage_parent[n]
            return n
        for op,tag,tail,head in branches_data:
            if op=='resistor':resist[tail].add(head);resist[head].add(tail)
            if op=='voltage_source':
                l,r=parent(tail),parent(head)
                if l==r:fail('$.conditions.voltage_source','acyclic voltage-source graph',tag)
                else:voltage_parent[l]=r
        reached=set();stack=[p['ground_node']]
        while stack:
            node=stack.pop()
            if node not in reached:reached.add(node);stack.extend(resist[node]-reached)
        if reached!=nodes:fail('$.conditions.resistor','connected resistor subgraph','unanchored/disconnected nodes')
        if tr:
            row=list(map(int,a[locs['nodes']['ids']])).index(p['ground_node'])
            if byop['initial_voltage'][0][1]['value'][0,row,0]!=0:fail('$.fields.initial_voltage','ground voltage zero','nonzero')
    present=set();floating_outputs=set();total=0
    for name,s in m['outputs'].items():
        q=s['quantity'];os=cfg['outputs'].get(q);path='$.outputs.'+name
        if os is None:fail(path+'.quantity',list(cfg['outputs']),q);continue
        present.add(q);location=s['location'];l=locs[location];w=os['where']
        if w in ('nodes','branches','coil'):ok=location==w
        elif w=='floating':ok=location in floatings;floating_outputs.add(location)
        else:ok=l['kind']=='mesh' and l['entity']=='element' and l['dimension']==d and ids(location)<=geo['cells']
        if not ok:fail(path+'.location',w,location)
        expected=dict(unit=os['unit'],kind=os['kind'],component_shape=os['shape'],components=labels(os),dtype='float64',time_axis=axis,value_kind='average' if w=='cells' else 'point')
        for key,v in expected.items():
            if s.get(key)!=v:fail(path+'.'+key,v,s.get(key))
        if 'sampling' in s:fail(path,'no output sampling',s['sampling'])
        total+=len(a[m['time_axes'][s['time_axis']]])*len(ids(location))*math.prod(s['component_shape'])
    if present!=set(cfg['outputs']):fail('$.outputs','all required quantities',sorted(present))
    if floating_outputs!=floatings:fail('$.outputs','each floating electrode requested',sorted(floating_outputs))
    if max(total,sum(a[s['array']].size for s in m['fields'].values()))>4000000:fail('$.fields/outputs','<=4000000 components each','excess')
