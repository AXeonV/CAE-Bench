"""Thermal declaration checks and local material maps; no field solver."""
from functools import lru_cache
from importlib.resources import files
from itertools import combinations
import json
import math
import numpy as np
SIGMA=5.670374419e-8


@lru_cache(maxsize=1)
def models():return json.loads(files(__package__).joinpath('models.json').read_text(encoding='utf-8'))


def shape(spec,parameters):return [int(parameters['patch_count']) if n=='p' else n for n in spec['shape']]


def labels(spec,parameters):
    sh=shape(spec,parameters);k=spec['kind']
    if k=='scalar':return ['value']
    if k=='vector':return list('xyz'[:sh[0]])
    if k=='tensor':return [a+b for a in 'xyz'[:sh[0]] for b in 'xyz'[:sh[0]]]
    return ['c'+str(i+1) for i in range(math.prod(sh))]


def phase_state(enthalpy,capacity,latent_heat,solidus,liquidus=None):
    """Return temperature and liquid fraction for the explicitly given local law."""
    h,c,l=np.broadcast_arrays(np.asarray(enthalpy,dtype=float),np.asarray(capacity,dtype=float),np.asarray(latent_heat,dtype=float))
    if not all(np.all(np.isfinite(a)) for a in (h,c,l)) or np.any(c<=0) or np.any(l<=0):raise ValueError('finite H, C>0 and L>0 required')
    if not np.isfinite(solidus):raise ValueError('finite phase temperature required')
    if liquidus is None:
        return solidus+np.minimum(h,0)/c+np.maximum(h-l,0)/c,np.clip(h/l,0,1)
    if not np.isfinite(liquidus) or liquidus<=solidus:raise ValueError('liquidus must exceed solidus')
    delta=liquidus-solidus;hl=c*delta+l
    t=np.where(h<0,solidus+h/c,np.where(h<=hl,solidus+h/(c+l/delta),liquidus+(h-hl)/c))
    return t,np.clip((t-solidus)/delta,0,1)


def check(problem,errors):
    from caeoj.validation import issue
    m,a=problem.manifest,problem.arrays
    model=m.get('physics',{}).get('model','');slug=model.removeprefix('thermal-').removesuffix('-v1');cfg=models().get(slug)
    def fail(path,expected,actual):
        if isinstance(actual,np.ndarray):actual=actual.tolist() if actual.size<12 else list(actual.shape)
        errors.append(issue('E_THERMAL',path,expected,actual,'Thermal declaration does not match this task DATA.'))
    if cfg is None or model!='thermal-'+slug+'-v1':fail('$.physics.model','registered thermal model',model);return
    if 'task' in m and m['task']!=slug:fail('$.task',slug,m['task'])
    if m['spatial_dimension']!=cfg['dimension']:fail('$.spatial_dimension',cfg['dimension'],m['spatial_dimension'])
    if any(k in m for k in ('profile','contract_version','analysis','materials')):fail('$','physics-only declaration','mixed profile')
    ps=m['physics'].get('parameters',{});p={}
    if set(ps)!=set(cfg['parameters']):fail('$.physics.parameters',list(cfg['parameters']),list(ps));return
    for key,s in cfg['parameters'].items():
        v=ps[key];x=v.get('value')
        if set(v)!={'value','unit'} or v.get('unit')!=s['unit'] or type(x) not in ((int,) if s.get('integer') else (int,float)):
            fail('$.physics.parameters.'+key,s,v);continue
        if (s.get('positive') and x<=0) or ('lower' in s and x<s['lower']) or ('upper' in s and x>s['upper']):fail('$.physics.parameters.'+key,s,x)
        p[key]=x
    if errors:return
    low,high=p['temperature_min'],p['temperature_max'];steady=cfg['steady'];gray=cfg['topology']==0;top=cfg['topology']
    if high<=low:fail('$.physics.parameters','Tmax>Tmin',[low,high])
    if not steady and p['end_time']<=p['start_time']:fail('$.physics.parameters','tf>t0',p['end_time'])
    if 'temperature_reference' in p and not low<=p['temperature_reference']<=high:fail('$.physics.parameters.temperature_reference','inside operating range',p['temperature_reference'])
    if slug=='mushy-enthalpy' and not low<p['solidus']<p['liquidus']<high:fail('$.physics.parameters','Tmin<Ts<Tl<Tmax',p)
    if slug=='isothermal-stefan' and not low<p['melting_temperature']<high:fail('$.physics.parameters','Tmin<Tm<Tmax',p)
    if errors:return
    locs=m['locations'];mesh=None;cells=set();nodes=set();exterior={};owners={};boundary_nodes=set()
    def ids(name):return set(map(int,a[locs[name]['ids']]))
    if gray:
        if m['meshes'] or m['geometries'] or set(locs)!={'enclosure'} or locs.get('enclosure',{}).get('kind')!='entities':
            fail('$.locations','one enclosure entity without mesh/geometry',list(locs));return
        if len(ids('enclosure'))!=1:fail('$.locations.enclosure','one entity',len(ids('enclosure')))
    else:
        if set(m['meshes'])!={'main'}:fail('$.meshes','one main mesh',list(m['meshes']));return
        mesh=problem.meshes['main'];cells=mesh['elements'][top]
        if any(mesh['elements'][d] for d in range(top-1)):fail('$.meshes.main','only top-dimensional and exterior facet elements','extra lower-dimensional elements')
        if mesh['dimension']!=top or not cells:fail('$.meshes.main','nonempty declared dimension',mesh['dimension']);return
        facets={};cell_links={tag:set() for tag in cells}
        for tag in cells:
            typ,conn=mesh['connectivity'][tag]
            if typ!={2:2,3:4}[top]:fail('$.meshes.main','first-order simplices',typ);continue
            nodes.update(conn);x=np.array([mesh['node_coordinates'][n][:top] for n in conn])
            if np.linalg.matrix_rank(x[1:]-x[0])!=top:fail('$.meshes.main','nondegenerate simplex',tag)
            for face in combinations(conn,top):facets.setdefault(tuple(sorted(face)),[]).append(tag)
        if any(len(v)>2 for v in facets.values()):fail('$.meshes.main','manifold facets','nonmanifold')
        for face,v in facets.items():
            if len(v)==2:cell_links[v[0]].add(v[1]);cell_links[v[1]].add(v[0])
        expected={face for face,v in facets.items() if len(v)==1}
        for tag in mesh['elements'][top-1]:
            typ,conn=mesh['connectivity'][tag];face=tuple(sorted(conn))
            if typ!={2:1,3:2}[top] or face not in expected or face in exterior.values():fail('$.meshes.main','unique exterior first-order facets',tag);continue
            exterior[tag]=face;owners[tag]=facets[face][0]
        if set(exterior.values())!=expected:fail('$.meshes.main','all exterior facets exported',len(exterior))
        boundary_nodes={n for f in exterior.values() for n in f}
        if nodes!=mesh['nodes']:fail('$.meshes.main','no unused mesh nodes','unused nodes')
        if len(nodes)>10000 or len(cells)>4000:fail('$.meshes.main','<=10000 nodes and 4000 cells',[len(nodes),len(cells)])
        for name,entity,tags in [('domain','node',nodes),('cells','element',cells)]:
            l=locs.get(name,{})
            if l.get('kind')!='mesh' or l.get('mesh')!='main' or l.get('entity')!=entity or ids(name)!=tags or (entity=='element' and l.get('dimension')!=top):fail('$.locations.'+name,'complete '+entity+' support',l)
        if slug!='thermal-contact' and cells:
            reached=set();stack=[next(iter(cells))]
            while stack:
                tag=stack.pop()
                if tag not in reached:reached.add(tag);stack.extend(cell_links[tag]-reached)
            if reached!=cells:fail('$.meshes.main','face-connected domain','disconnected cells')
        for name,l in locs.items():
            if l.get('kind')!='mesh' or l.get('mesh')!='main':fail('$.locations.'+name,'mesh support on main',l);continue
            tags=ids(name)
            if l['entity']=='node':ok=tags<=nodes
            else:ok=(l['dimension']==top and tags<=cells) or (l['dimension']==top-1 and tags<=set(exterior))
            if not ok:fail('$.locations.'+name,'nodes/cells/exterior facets',l)
    if errors:return
    for name,key in m['time_axes'].items():
        if len(a[key])>101:fail('$.time_axes.'+name,'<=101 frames',len(a[key]))
    output_axis='steady' if steady else 'response';static_axis='steady' if steady else 'initial';t0=0. if steady else p['start_time'];tf=0. if steady else p['end_time']
    required_axes={'steady'} if steady else {'initial','response'}
    if not required_axes<=set(m['time_axes']):fail('$.time_axes','required '+str(required_axes),list(m['time_axes']));return
    if steady and set(m['time_axes'])!={'steady'}:fail('$.time_axes','steady only',list(m['time_axes']))
    if not np.array_equal(a[m['time_axes'][static_axis]],[t0]):fail('$.time_axes.'+static_axis,'single t0',a[m['time_axes'][static_axis]])
    times=a[m['time_axes'][output_axis]]
    if times[0]<t0 or times[-1]>tf or (cfg['phase'] and times[0]<=t0):fail('$.time_axes.'+output_axis,'valid response interval',times)
    used_axes=set(required_axes);refs=set();counts={};boundary_used=set();dir_nodes=set();dir_faces=set();contact_sides=set();minus_sites=set();values_by_op={}
    def support(name,where):
        if gray:return name=='enclosure'
        l=locs[name];tags=ids(name)
        if where=='domain':return name=='domain'
        if where=='cells':return l['entity']=='element' and l['dimension']==top and tags<=cells
        if where=='nodes':return l['entity']=='node' and tags<=boundary_nodes
        if where=='facets':return l['entity']=='element' and l['dimension']==top-1 and tags<=set(exterior)
        return False
    def typed(value,s,location,static,key,path):
        shape_expected=shape(s,p);kind=s['kind'];n=len(ids(location))
        if 'value' in value:
            if set(value)!={'value','unit'} or kind!='scalar' or s.get('dtype')=='int64' or value.get('unit')!=s['unit'] or type(value.get('value')) not in (int,float):fail(path,'typed scalar constant',value);return None
            values=np.full((1,n,1),value['value'])
        elif set(value)=={'field'}:
            name=value['field'];refs.add(name);fs=m['fields'][name]
            expected=dict(quantity=key,unit=s['unit'],kind=kind,component_shape=shape_expected,components=labels(s,p),dtype=s.get('dtype','float64'),location=location,value_kind='point' if gray or locs[location]['entity']=='node' else 'average')
            for k,v in expected.items():
                if fs.get(k)!=v:fail('$.fields.'+name+'.'+k,v,fs.get(k))
            axis=fs['time_axis'];used_axes.add(axis);t=a[m['time_axes'][axis]]
            if static and axis!=static_axis:fail('$.fields.'+name+'.time_axis',static_axis,axis)
            if (len(t)==1 and t[0]!=t0) or (len(t)>1 and (static or t[0]!=t0 or t[-1]!=tf)):
                fail('$.fields.'+name+'.time_axis','static t0 or full loading interval',t)
            space='uniform' if gray else 'piecewise_linear' if locs[location]['entity']=='node' else 'piecewise_constant'
            expected_sampling=dict(space=space,time='constant' if len(t)==1 else 'linear',extrapolation='forbid')
            if fs.get('sampling')!=expected_sampling:fail('$.fields.'+name+'.sampling',expected_sampling,fs.get('sampling'))
            values=a[fs['array']]
        else:fail(path,'constant or field',value);return None
        if s.get('positive') and np.any(values<=0):fail(path,'strictly positive values','nonpositive')
        if 'lower' in s and np.any(values<s['lower']):fail(path,'>= '+str(s['lower']),'below bound')
        if 'upper' in s and np.any(values>s['upper']):fail(path,'<= '+str(s['upper']),'above bound')
        if s['unit']=='K' and (np.any(values<low) or np.any(values>high)):fail(path,'inside [Tmin,Tmax]','outside temperature range')
        return values
    for i,c in enumerate(m['conditions']):
        path=f'$.conditions[{i}]';op=c['operator'];r=cfg['records'].get(op)
        if r is None:fail(path+'.operator',list(cfg['records']),op);continue
        counts[op]=counts.get(op,0)+1;location=c['location'];tags=ids(location)
        for k in ('role','variable'):
            if c[k]!=r[k]:fail(path+'.'+k,r[k],c[k])
        if not support(location,r['where']):fail(path+'.location',r['where'],location);continue
        if r['where'] in ('cells','domain','enclosure') and (counts[op]!=1 or (r['where']=='cells' and tags!=cells)):
            fail(path+'.location','one complete record',location)
        if set(c['data'])!=set(r['data']):fail(path+'.data',list(r['data']),list(c['data']));continue
        vals={}
        for key,s in r['data'].items():
            ref=c['data'][key]
            if 'location' in s:
                if set(ref)!={'location'} or not support(ref['location'],'facets'):fail(path+'.data.'+key,'partner exterior facets',ref);continue
                vals[key]=ref['location'];continue
            q=key
            if key=='value':q={'heat_source':'heat_source','power':'power','initial_enthalpy':'enthalpy','prescribed_velocity':'velocity','heat_flux':'heat_flux'}.get(op,'temperature')
            vals[key]=typed(ref,s,location,r['static'] or steady,q,path+'.data.'+key)
        if any(v is None for v in vals.values()) or set(vals)!=set(r['data']):continue
        values_by_op.setdefault(op,[]).append((location,vals))
        if not gray and r['where'] in ('nodes','facets'):
            if r['where']=='nodes':
                selected={tag for tag,f in exterior.items() if set(f)<=tags}
                if {n for tag in selected for n in exterior[tag]}!=tags or dir_nodes&tags:fail(path+'.location','complete nonoverlapping temperature face union',location)
                dir_nodes.update(tags);dir_faces.update(selected)
            else:selected=tags
            if boundary_used&selected:fail(path+'.location','no complete-face boundary overlap',location)
            boundary_used.update(selected)
            if op=='thermal_pair':
                partner=vals['partner'];right=ids(partner)
                if boundary_used&right or right&selected:fail(path+'.data.partner','unused distinct plus side',partner)
                boundary_used.update(right);contact_sides.update(selected|right);minus_sites.add(location)
                def signatures(tags):
                    return {tuple(sorted(tuple(mesh['node_coordinates'][n]) for n in exterior[tag])):tag for tag in tags}
                leftmap,rightmap=signatures(selected),signatures(right)
                if set(leftmap)!=set(rightmap) or len(leftmap)!=len(selected) or len(rightmap)!=len(right):fail(path+'.data.partner','bijective coincident faces',partner)
                elif {n for t in selected for n in exterior[t]}&{n for t in right for n in exterior[t]}:fail(path+'.data.partner','distinct side node IDs',partner)
                else:
                    for sig,tleft in leftmap.items():
                        tright=rightmap[sig];x=np.array(sig);normal=np.cross(x[1]-x[0],x[2]-x[0]);center=x.mean(axis=0)
                        ca=np.mean([mesh['node_coordinates'][n] for n in mesh['connectivity'][owners[tleft]][1]],axis=0)
                        cb=np.mean([mesh['node_coordinates'][n] for n in mesh['connectivity'][owners[tright]][1]],axis=0)
                        if ((ca-center)@normal)*((cb-center)@normal)>=0:fail(path+'.data.partner','adjacent solids on opposite sides',partner)
    for op,r in cfg['records'].items():
        if r['required'] and not counts.get(op):fail('$.conditions','required '+op,'missing')
    if refs!=set(m['fields']):fail('$.fields','exactly referenced fields',sorted(set(m['fields'])-refs))
    if set(m['time_axes'])!=used_axes:fail('$.time_axes','no unused loading axes',list(m['time_axes']))
    if errors:return
    if gray:
        v=values_by_op['enclosure'][0][1];area=v['area'][0,0];f=v['view_factors'][0,0]
        if np.any(abs(f.sum(axis=1)-1)>1e-10):fail('$.fields.view_factors','row sums = 1','bad sums')
        exchange=area[:,None]*f;tol=1e-10*np.maximum(1,np.maximum(area[:,None],area[None,:]))
        if np.any(abs(exchange-exchange.T)>tol):fail('$.fields.view_factors','area reciprocity','not reciprocal')
    else:
        material=values_by_op['material'][0][1]
        if slug=='anisotropic-conduction':
            for k in material['conductivity'][0]:
                if not np.array_equal(k,k.T):fail('$.fields.conductivity','symmetric tensor','nonsymmetric');continue
                try:np.linalg.cholesky(k)
                except np.linalg.LinAlgError:fail('$.fields.conductivity','positive definite tensor','not SPD')
        if slug=='nonlinear-conductivity':
            beta=material['beta'];ref=p['temperature_reference']
            if np.any(np.maximum(abs(beta*(low-ref)),abs(beta*(high-ref)))>20):fail('$.fields.beta','bounded exponent <=20','excess exponent')
        if slug=='nonlinear-capacity':
            gamma=material['gamma'];ref=p['temperature_reference']
            if np.any(1+gamma*(low-ref)<=0) or np.any(1+gamma*(high-ref)<=0):fail('$.fields.gamma','positive capacity throughout operating range','nonpositive capacity')
        if cfg['phase']:
            h=values_by_op['initial_enthalpy'][0][1]['value'];t,_=phase_state(h,material['capacity'],material['latent_heat'],p.get('solidus',p.get('melting_temperature')),p.get('liquidus'))
            if np.any(t<low) or np.any(t>high):fail('$.fields.enthalpy','initial temperature inside operating range','outside range')
        if steady:
            anchor=bool(dir_faces) or any(np.any(v['coefficient']>0) for l,v in values_by_op.get('convection',[]))
            if not anchor:fail('$.conditions','absolute temperature anchor','pure Neumann')
        if cfg['advection']:
            velocity=values_by_op['prescribed_velocity'][0][1]['value'][0];order={int(tag):i for i,tag in enumerate(a[locs['domain']['ids']])};vnode={tag:velocity[i] for tag,i in order.items()};capacity=material['capacity'][0,:,0]
            cellorder={int(tag):i for i,tag in enumerate(a[locs['cells']['ids']])}
            medium=material.get('medium',np.ones((1,len(cells),1),dtype='int64'))[0,:,0]
            if slug=='conjugate-prescribed-flow' and (set(medium)!={0,1}):fail('$.fields.medium','both 0 solid and 1 fluid',np.unique(medium))
            fluid=medium==1
            if fluid.any() and np.any(capacity[fluid]!=capacity[fluid][0]):fail('$.fields.capacity','constant fluid capacity','varying fluid C')
            for tag in cells:
                conn=mesh['connectivity'][tag][1];x=np.array([mesh['node_coordinates'][n][:3] for n in conn]);v=np.array([vnode[n] for n in conn]);isfluid=medium[cellorder[tag]]==1
                if not isfluid and np.any(v!=0):fail('$.fields.velocity','zero velocity at solid nodes','nonzero solid velocity')
                if isfluid:
                    gradient=np.linalg.solve(x[1:]-x[0],v[1:]-v[0])
                    if abs(np.trace(gradient))>1e-10*max(1,np.linalg.norm(gradient)):fail('$.fields.velocity','divergence-free P1','nonzero divergence')
            for tag,conn in exterior.items():
                x=np.array([mesh['node_coordinates'][n] for n in conn]);normal=np.cross(x[1]-x[0],x[2]-x[0]);center=x.mean(axis=0);inside=np.mean([mesh['node_coordinates'][n] for n in mesh['connectivity'][owners[tag]][1]],axis=0)
                normal/=np.linalg.norm(normal)
                if normal@(center-inside)<0:normal=-normal
                v=np.array([vnode[n] for n in conn]);dots=v@normal;eps=1e-12*max(1,np.linalg.norm(v,axis=1).max())
                if dots.min() < -eps:
                    if dots.max()>eps:fail('$.fields.velocity','no sign-changing boundary normal speed',tag)
                    if tag not in dir_faces:fail('$.conditions','temperature on every inflow face',tag)
    present=set();actual_pairs=set();total=0
    for name,s in m['outputs'].items():
        path='$.outputs.'+name;q=s['quantity'];os=cfg['outputs'].get(q)
        if os is None:fail(path+'.quantity',list(cfg['outputs']),q);continue
        present.add(q);location=s['location'];where=os['where']
        ok=location=='enclosure' if gray else location in minus_sites if where=='interface' else support(location,'cells')
        if not ok:fail(path+'.location',where,location)
        if where=='interface':actual_pairs.add(location)
        expected=dict(unit=os['unit'],kind=os['kind'],dtype='float64',component_shape=shape(os,p),components=labels(os,p),time_axis=output_axis,value_kind='point' if gray else 'average')
        for k,v in expected.items():
            if s.get(k)!=v:fail(path+'.'+k,v,s.get(k))
        if 'sampling' in s:fail(path,'no output sampling',s['sampling'])
        total+=len(a[m['time_axes'][s['time_axis']]])*len(ids(location))*math.prod(s['component_shape'])
    if present!=set(cfg['outputs']):fail('$.outputs','all required quantities',sorted(present))
    if actual_pairs!=minus_sites:fail('$.outputs','each thermal_pair minus-side flux',sorted(actual_pairs))
    input_total=sum(a[s['array']].size for s in m['fields'].values())
    if max(input_total,total)>3000000:fail('$.fields/outputs','<=3000000 components each',[input_total,total])
