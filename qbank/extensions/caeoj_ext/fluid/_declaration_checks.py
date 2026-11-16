"""Shared typed-declaration mechanics parameterized by physical extensions."""
import numpy as np

def check_declaration(problem, errors, models, parameter_check, boundary_check):
    """Run after generic structure/reference checks, using loaded mesh geometry."""
    from caeoj.validation import issue
    from ._geometry import exterior_facets, boundary_geometry
    m=problem.manifest; model=m.get('physics',{}).get('model','')
    def fail(path,expected,actual,message):errors.append(issue('E_FLUID',path,expected,actual,message))
    if model not in models:
        fail('$.physics.model',list(models),model,'Unknown reduced fluid model/version.');return
    initial_errors=len(errors)
    cfg=models[model];d=cfg['dimension'];params=m['physics'].get('parameters',{})
    if any(k in m for k in ('profile','contract_version','analysis','materials')):
        fail('$','physics-only declaration',model,'Cannot combine reduced and CFD profiles.')
    if m['spatial_dimension']!=d:fail('$.spatial_dimension',d,m['spatial_dimension'],'Model dimension mismatch.')
    if set(params)!=set(cfg['parameters']):fail('$.physics.parameters',sorted(cfg['parameters']),sorted(params),'Exact parameter set required.')
    for name,unit in cfg['parameters'].items():
        x=params.get(name,{})
        if set(x)!={'value','unit'} or x.get('unit')!=unit:
            fail('$.physics.parameters.'+name,unit,x,'Explicit SI constant required.');continue
        v=x['value']
        signed=name in cfg['signed_parameters']
        nonnegative=name in cfg['nonnegative_parameters']
        if not signed and (v<0 if nonnegative else v<=0):fail('$.physics.parameters.'+name,'nonnegative' if nonnegative else 'positive',v,'Invalid parameter range.')
    if len(errors)>initial_errors:return
    p={k:x['value'] for k,x in params.items()}
    if cfg['transient'] and p.get('end_time',0)<=p.get('start_time',0):fail('$.physics.parameters','end_time > start_time',p,'Invalid interval.')
    parameter_check(cfg, p, fail)
    locs=m['locations'];domain=locs.get('domain',{})
    if domain.get('kind')!='mesh' or domain.get('entity')!='node':
        fail('$.locations.domain','mesh node location covering domain',domain,'Explicit full domain node support required.');return
    mesh=problem.meshes[domain['mesh']]
    if set(map(int,problem.arrays[domain['ids']]))!=mesh['nodes']:
        fail('$.locations.domain','all mesh nodes',domain,'Domain must include all nodes.')
    if len(m['meshes'])!=1 or mesh['dimension']!=d:fail('$.meshes','one full-dimensional mesh',list(m['meshes']),'One connected domain required.')
    if any(typ not in ((1,2,15) if d==2 else (2,4,15)) for typ,_ in mesh['connectivity'].values()):
        fail('$.meshes','linear simplex mesh',model,'Only triangles/tetrahedra and their facets are supported.')
    try: exterior=exterior_facets(mesh,d)
    except ValueError as exc:fail('$.meshes','connected manifold mesh',model,str(exc));return
    expected=set(exterior);covered=set(); thermal_covered=set();refs=set();domain_seen=set();rules=cfg['boundary_rules'];boundary_ops=set();gas_wall_keys=set()
    thermal=cfg['thermal_boundary']
    def check_field(spec,path,unit,kind,bound,initial=False):
        if spec['unit']!=unit or spec['kind']!=kind or spec['dtype']!='float64':
            fail(path,(unit,kind,'float64'),spec,'Unit/component declaration mismatch.');return
        loc=locs[spec['location']]; sampling=spec.get('sampling',{})
        if loc.get('kind')=='mesh' and loc.get('entity')=='node': space='piecewise_linear';vk='point'
        else:space='piecewise_constant';vk='average'
        if spec['value_kind']!=vk or sampling.get('space')!=space:fail(path+'.sampling',space,sampling,'Explicit reconstruction required.')
        t=problem.arrays[m['time_axes'][spec['time_axis']]];v=problem.arrays[spec['array']]
        if initial:
            if len(t)!=1 or t[0]!=p.get('start_time'):fail(path+'.time_axis','single start_time',t,'Physical initial state required.')
            time='constant'
        else:time='linear' if cfg['transient'] and len(t)>1 else 'constant'
        if sampling!={'space':space,'time':time,'extrapolation':'forbid'}:fail(path+'.sampling',dict(space=space,time=time,extrapolation='forbid'),sampling,'Sampling declaration mismatch.')
        if time=='constant' and len(t)!=1:fail(path+'.time_axis','single frame',t,'Constant samples require one frame.')
        if time=='linear' and (t[0]>p['start_time'] or t[-1]<p['end_time']):fail(path+'.time_axis','covers physical interval',t,'Insufficient temporal coverage.')
        if not cfg['transient'] and (len(t)!=1 or t[0]!=0):fail(path+'.time_axis','[0]',t,'Steady time label must be zero.')
        if bound=='positive' and np.any(v<=0) or bound=='nonnegative' and np.any(v<0) or bound=='fraction' and np.any((v<0)|(v>1)):
            fail(path+'.array',bound,v,'Field values outside declared range.')
        if bound=='spd' and (not np.allclose(v,np.swapaxes(v,-1,-2),rtol=0,atol=1e-12) or np.any(np.linalg.eigvalsh(v)<=0)):
            fail(path+'.array','symmetric positive definite',v,'Conformation must be SPD.')
    def data_value(x,req,path,location,initial=False,quantity=None):
        if req[0]=='option':
            if x!={'option':req[1]}:fail(path,{'option':req[1]},x,'Invalid option.')
            return
        kind,unit,bound=req
        if set(x)=={'field'}:
            name=x['field'];refs.add(name);spec=m['fields'][name]
            if spec['quantity']!=quantity:fail('$.fields.'+name+'.quantity',quantity,spec['quantity'],'Condition field quantity must match physical role.')
            if spec['location']!=location:fail(path+'.field',location,spec['location'],'Exact condition support required.')
            check_field(spec,'$.fields.'+name,unit,kind,bound,initial)
        elif set(x)=={'value','unit'} and kind=='scalar' and x['unit']==unit and not initial:
            value=x['value']
            if bound=='positive' and value<=0 or bound=='nonnegative' and value<0 or bound=='fraction' and not 0<=value<=1:
                fail(path,bound,value,'Constant outside declared range.')
        else:fail(path,'explicit field (or scalar SI constant outside initial state)',x,'Invalid typed condition data.')
    for i,c in enumerate(m['conditions']):
        path=f'$.conditions[{i}]';op=c['operator'];var=c['variable'];loc=c['location'];data=c['data']
        if var in cfg['domain'] and (c['role'],op)==cfg['domain'][var][:2]:
            role,_,unit,kind,bound=cfg['domain'][var]
            if loc!='domain' or var in domain_seen:fail(path,'one condition per domain variable',c,'Duplicate/wrong domain condition.')
            domain_seen.add(var)
            if set(data)!={'value'}:fail(path+'.data',['value'],data,'Exact parameter set required.');continue
            data_value(data['value'],(kind,unit,bound),path+'.data.value',loc,role=='initial',var);continue
        is_thermal=thermal and c['role']=='boundary' and var=='temperature' and op=='temperature_wall'
        if c['role']!='boundary' or not (op in rules or is_thermal):
            fail(path,sorted(rules),c,'Unsupported condition.');continue
        target,requirements=('temperature',{'value':('scalar','K','positive')}) if is_thermal else rules[op]
        if var!=target or set(data)!=set(requirements):fail(path,(target,sorted(requirements)),c,'Condition variable/parameter mismatch.');continue
        l=locs[loc]
        if l.get('kind')!='mesh' or l.get('entity')!='element' or l.get('dimension')!=d-1 or l.get('mesh')!=domain['mesh']:
            fail(path+'.location','boundary facet element support',l,'Boundary support mismatch.');continue
        try:
            boundary_geometry(problem,loc)
            keys={frozenset(mesh['connectivity'][int(tag)][1]) for tag in problem.arrays[l['ids']]}
        except ValueError as exc:fail(path+'.location','exterior boundary',loc,str(exc));continue
        boundary_ops.add(op)
        if op=='gas_wall':gas_wall_keys.update(keys)
        bucket=thermal_covered if is_thermal else covered
        if bucket & keys:fail(path+'.location','disjoint boundary partitions',loc,'Overlapping boundary declarations.')
        bucket.update(keys)
        for key,req in requirements.items():data_value(data[key],req,path+'.data.'+key,loc,quantity=var if key=='value' else key)
        def values(key):
            x=data[key]
            return problem.arrays[m['fields'][x['field']]['array']] if 'field' in x else np.asarray(x.get('value'))
        if op in cfg['wall_velocity_keys']:
            key=cfg['wall_velocity_keys'][op]
            if 'field' in data[key]:
                spec=m['fields'][data[key]['field']]
                if spec['kind']=='vector' and spec['component_shape']==[d]:
                    _,normals,_=boundary_geometry(problem,loc)
                    if np.any(np.abs(np.sum(values(key)*normals,axis=-1))>1e-12):fail(path+'.data.'+key,'tangential wall velocity',data[key],'Fixed walls cannot move normally.')
        boundary_check(cfg, p, op, data, values, problem, loc, requirements, fail, path)
    if cfg['required_open_ops'] and not set(cfg['required_open_ops']) & boundary_ops:
        fail('$.conditions','at least one reservoir/outlet',sorted(boundary_ops),'Steady mass/pressure must be fixed by an open boundary.')
    if domain_seen!=set(cfg['domain']):fail('$.conditions',sorted(cfg['domain']),sorted(domain_seen),'Missing domain material or physical initial state.')
    if covered!=expected:fail('$.conditions','complete exterior mechanical/gas/water/film boundary partition',len(covered),'Missing boundary coverage.')
    if thermal and thermal_covered!=expected:fail('$.conditions','complete temperature boundary partition',len(thermal_covered),'Missing thermal coverage.')
    if set(m['fields'])!=refs:fail('$.fields',sorted(refs),sorted(m['fields']),'Every input field must have one declared physical role.')
    present=set()
    for name,spec in m['outputs'].items():
        q=spec['quantity'];path='$.outputs.'+name;present.add(q)
        if q not in cfg['outputs']:fail(path+'.quantity',cfg['outputs'],q,'Unsupported observation.');continue
        unit,kind=cfg['output_specs'][q]
        if spec['unit']!=unit or spec['kind']!=kind or spec['dtype']!='float64':fail(path,(unit,kind),spec,'Output unit/kind mismatch.')
        l=locs[spec['location']]
        if q in cfg['integral_outputs']:
            valid=l.get('kind')=='aggregate' and l.get('operation')=='sum' and spec['value_kind']=='integral'
            source=locs.get(l.get('source'),{})
            valid=valid and source.get('kind')=='mesh' and source.get('entity')=='element' and source.get('dimension')==d
            if not valid:fail(path+'.location','sum over full domain cells',l,'Domain integrals need real aggregate support.')
            elif set(map(int,problem.arrays[source['ids']]))!=mesh['elements'][d]:fail(path+'.location','all domain cells',source,'Incomplete domain integral.')
        elif q in cfg['boundary_outputs']:
            if l.get('kind')!='mesh' or l.get('entity')!='element' or l.get('dimension')!=d-1 or spec['value_kind']!='average':fail(path+'.location','boundary facet average',l,'Exchange observations are boundary averages.')
            else:
                try:
                    boundary_geometry(problem,spec['location'])
                    keys={frozenset(mesh['connectivity'][int(tag)][1]) for tag in problem.arrays[l['ids']]}
                    if cfg['exchange_wall_only'] and not keys<=gas_wall_keys:fail(path+'.location','gas_wall support',l,'Kinetic exchanges require wall-frame support.')
                except ValueError as exc:fail(path+'.location','exterior boundary',l,str(exc))
        elif l.get('kind')!='mesh' or l.get('entity')!='node' or spec['value_kind']!='point':fail(path+'.location','mesh node point',l,'State observations use mesh nodes.')
        t=problem.arrays[m['time_axes'][spec['time_axis']]]
        if cfg['transient']:
            if t[0]<p.get('start_time',0) or t[-1]>p.get('end_time',0):fail(path+'.time_axis','within physical interval',t,'Output interval mismatch.')
        elif len(t)!=1 or t[0]!=0:fail(path+'.time_axis','[0]',t,'Steady output time label required.')
    core=set(cfg['required_outputs'])
    if not core<=present:fail('$.outputs',sorted(core),sorted(present),'Required primary observations missing.')
