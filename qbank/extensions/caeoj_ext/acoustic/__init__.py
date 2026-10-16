"""Acoustic declarations and a free-space kernel, not a reference field solver."""
from functools import lru_cache
from importlib.resources import files
import json,math
import numpy as np


@lru_cache(maxsize=1)
def models():return json.loads(files(__package__).joinpath('models.json').read_text(encoding='utf-8'))


def shape(s,p):return [int(p['mode_count']) if n=='m' else n for n in s['shape']]


def labels(s,p):
    if s['kind']=='scalar':return ['value']
    if s['kind']=='vector':return ['x','y','z']
    return ['c'+str(i+1) for i in range(math.prod(shape(s,p)))]


def helmholtz_hessian(displacement,wavenumber):
    """Hessian of exp(-ikr)/(4*pi*r), matching exp(+i*omega*t)."""
    x=np.asarray(displacement,dtype=float);k=wavenumber
    if x.shape[-1:]!=(3,) or not np.all(np.isfinite(x)) or not np.isfinite(k) or k<0:raise ValueError('finite [...,3] displacement and k>=0 required')
    r=np.asarray(np.linalg.norm(x,axis=-1))
    if np.any(r==0):raise ValueError('nonzero source-receiver distance required')
    n=x/r[...,None];g=np.asarray(np.exp(-1j*k*r)/(4*np.pi*r))
    return g[...,None,None]*((np.asarray(-k*k+3j*k/r+3/r**2)[...,None,None])*n[..., :,None]*n[...,None,:]+np.asarray(-1j*k/r-1/r**2)[...,None,None]*np.eye(3))


def check(problem,errors):
    from caeoj.validation import issue
    from caeoj.mesh_geometry import boundary_geometry,periodic_face_pairs
    from .geometry import inspect
    m,a=problem.manifest,problem.arrays;model=m.get('physics',{}).get('model','');slug=model.removeprefix('acoustic-').removesuffix('-v1');cfg=models().get(slug)
    def fail(path,expected,actual):
        if isinstance(actual,np.ndarray):actual=actual.tolist() if actual.size<16 else list(actual.shape)
        errors.append(issue('E_ACOUSTIC',path,expected,actual,'Acoustic declaration violates the public DATA contract.'))
    if cfg is None or model!='acoustic-'+slug+'-v1':fail('$.physics.model','registered acoustic model',model);return
    if m['spatial_dimension']!=3:fail('$.spatial_dimension',3,m['spatial_dimension'])
    if 'task' in m and m['task']!=slug:fail('$.task',slug,m['task'])
    if any(k in m for k in ('profile','contract_version','analysis','materials')):fail('$','physics-only declaration','mixed profile')
    params=m['physics'].get('parameters',{});p={}
    if set(params)!=set(cfg['parameters']):fail('$.physics.parameters',list(cfg['parameters']),list(params));return
    for key,s in cfg['parameters'].items():
        v=params[key];x=v.get('value')
        if set(v)!={'value','unit'} or v.get('unit')!=s['unit'] or type(x) not in ((int,) if s.get('integer') else (int,float)):
            fail('$.physics.parameters.'+key,s,v);continue
        if s.get('positive') and x<=0 or 'lower' in s and x<s['lower'] or 'upper' in s and x>s['upper'] or 'lower_exclusive' in s and x<=s['lower_exclusive']:fail('$.physics.parameters.'+key,s,x)
        p[key]=x
    if errors:return
    tr=cfg['transient'];family=cfg['family'];modal=slug=='modal-vibroacoustics'
    if tr and p['end_time']<=p['start_time']:fail('$.physics.parameters','tf>t0',p['end_time'])
    if slug=='rigid-scattering' and abs(np.linalg.norm([p['direction_'+v] for v in 'xyz'])-1)>1e-12:fail('$.physics.parameters','unit direction','bad norm')
    if slug=='uniform-flow-acoustics' and np.linalg.norm([p['mean_'+v] for v in 'xyz'])>=.5*p['sound_speed']:fail('$.physics.parameters','Mach < .5','excess mean speed')
    if errors:return
    geo=inspect(problem,cfg,fail)
    if errors or geo is None:return
    mesh=geo['mesh'];locs=m['locations'];cells=geo['cells'];nodes=geo['nodes'];exterior=geo['exterior'];bnodes=geo['boundary_nodes']
    def ids(name):return set(map(int,a[locs[name]['ids']]))
    for key,arr in m['time_axes'].items():
        if len(a[arr])>101:fail('$.time_axes.'+key,'<=101 frames',len(a[arr]))
    static_axis='initial' if tr else 'harmonic';outaxis='response' if tr else 'harmonic';required_axes={'initial','response'} if tr else {'harmonic'};t0=p['start_time'] if tr else 0.;tf=p['end_time'] if tr else 0.
    if not required_axes<=set(m['time_axes']):fail('$.time_axes','required '+str(required_axes),list(m['time_axes']));return
    if not tr and set(m['time_axes'])!={'harmonic'}:fail('$.time_axes','harmonic only',list(m['time_axes']))
    if not np.array_equal(a[m['time_axes'][static_axis]],[t0]):fail('$.time_axes.'+static_axis,'single t0/0 marker',a[m['time_axes'][static_axis]])
    times=a[m['time_axes'][outaxis]]
    if times[0]<t0 or times[-1]>tf:fail('$.time_axes.'+outaxis,'inside [t0,tf]',times)
    refs=set();axes=set(required_axes);counts={};usedfaces=set();pnodes=set();byop={};special_sites={};periodic_nodes=[]
    def support(name,where):
        l=locs[name];tags=ids(name)
        if where in ('domain','surface','structure'):return name==where
        if where=='cells':return l['kind']=='mesh' and l['entity']=='element' and l['dimension']==3 and tags<=cells
        if where=='facets':return l['kind']=='mesh' and l['entity']=='element' and l['dimension']==2 and tags<=set(exterior)
        if where in ('nodes','boundary_nodes'):return l['kind']=='mesh' and l['entity']=='node' and (tags==bnodes if where=='boundary_nodes' else tags<=bnodes)
        return False
    def typed(v,s,location,static,key,path):
        n=len(ids(location));sh=shape(s,p)
        if 'value' in v:
            if set(v)!={'value','unit'} or s['kind']!='scalar' or v.get('unit')!=s['unit'] or type(v.get('value')) not in (int,float):fail(path,'typed scalar constant',v);return None
            values=np.full((1,n,*sh),v['value'])
        elif set(v)=={'field'}:
            name=v['field'];refs.add(name);fs=m['fields'][name];l=locs[location]
            expected=dict(quantity=key,unit=s['unit'],kind=s['kind'],component_shape=sh,components=labels(s,p),dtype='float64',location=location,value_kind='point' if l['kind']=='entities' or l.get('entity')=='node' else 'average')
            for k,x in expected.items():
                if fs.get(k)!=x:fail('$.fields.'+name+'.'+k,x,fs.get(k))
            axis=fs['time_axis'];axes.add(axis);t=a[m['time_axes'][axis]]
            if static and axis!=static_axis:fail('$.fields.'+name+'.time_axis',static_axis,axis)
            if len(t)==1 and t[0]!=t0 or len(t)>1 and (static or not tr or t[0]!=t0 or t[-1]!=tf):fail('$.fields.'+name+'.time_axis','static t0 or full loading interval',t)
            space='uniform' if l['kind']=='entities' else 'piecewise_linear' if l['entity']=='node' else 'piecewise_constant'
            sampling=dict(space=space,time='constant' if len(t)==1 else 'linear',extrapolation='forbid')
            if fs.get('sampling')!=sampling:fail('$.fields.'+name+'.sampling',sampling,fs.get('sampling'))
            values=a[fs['array']]
        else:fail(path,'field or typed constant',v);return None
        if s.get('positive') and np.any(values<=0):fail(path,'positive values','nonpositive')
        if 'lower' in s and np.any(values<s['lower']):fail(path,'>= '+str(s['lower']),'below bound')
        return values
    for i,c in enumerate(m['conditions']):
        path=f'$.conditions[{i}]';op=c['operator'];r=cfg['records'].get(op)
        if r is None:fail(path+'.operator',list(cfg['records']),op);continue
        counts[op]=counts.get(op,0)+1;location=c['location'];tags=ids(location)
        for k in ('role','variable'):
            if c[k]!=r[k]:fail(path+'.'+k,r[k],c[k])
        if not support(location,r['where']):fail(path+'.location',r['where'],location);continue
        if r['where'] in ('domain','cells','surface','structure','boundary_nodes') and (counts[op]!=1 or r['where']=='cells' and tags!=cells):fail(path+'.location','one complete record',location)
        if set(c['data'])!=set(r['data']):fail(path+'.data',list(r['data']),list(c['data']));continue
        values={}
        for key,s in r['data'].items():
            v=c['data'][key]
            if 'location' in s:
                if set(v)!={'location'} or not support(v['location'],'facets'):fail(path+'.data.'+key,'partner facets',v);continue
                values[key]=v['location']
            elif 'option' in s:
                if v!={'option':s['option']}:fail(path+'.data.'+key,s,v)
                values[key]=s['option']
            else:values[key]=typed(v,s,location,r['static'] or s.get('static') or not tr,r['variable'] if key=='value' else key,path+'.data.'+key)
        if any(v is None for v in values.values()) or set(values)!=set(r['data']):continue
        byop.setdefault(op,[]).append((location,values))
        if r['where'] in ('facets','nodes','boundary_nodes'):
            if r['where'] in ('nodes','boundary_nodes'):
                selected={tag for tag,conn in exterior.items() if set(conn)<=tags}
                if {n for t in selected for n in exterior[t]}!=tags or pnodes&tags:fail(path+'.location','complete nonoverlapping boundary node union',location)
                pnodes.update(tags)
            else:selected=tags
            if usedfaces&selected:fail(path+'.location','no boundary face overlap',location)
            usedfaces.update(selected)
            if op in ('resonator','modal_wall'):special_sites.setdefault(op,set()).add(location)
            if op=='periodic':
                partner=values['partner'];right=ids(partner)
                if usedfaces&right or right&selected:fail(path+'.data.partner','unused distinct side',partner)
                usedfaces.update(right)
                leftcoords=np.array([mesh['node_coordinates'][n] for tag in tags for n in exterior[tag]]);rightcoords=np.array([mesh['node_coordinates'][n] for tag in right for n in exterior[tag]])
                lo=mesh['coordinates'].min(axis=0);hi=mesh['coordinates'].max(axis=0);candidates=[axis for axis in range(3) if np.all(leftcoords[:,axis]==lo[axis]) and np.all(rightcoords[:,axis]==hi[axis])]
                if len(candidates)!=1:fail(path+'.data.partner','min-to-max opposite box faces',partner);continue
                shift=np.zeros(3);axis=candidates[0];shift[axis]=hi[axis]-lo[axis]
                try:pairs=periodic_face_pairs(problem,location,partner,shift)
                except ValueError as exc:fail(path+'.data.partner','translated matching triangulation',str(exc));continue
                ln={n for tag in tags for n in exterior[tag]};rn={n for tag in right for n in exterior[tag]}
                for n in ln:
                    x=np.array(mesh['node_coordinates'][n])+shift;matched=[j for j in rn if np.allclose(mesh['node_coordinates'][j],x,rtol=0,atol=1e-10*np.linalg.norm(hi-lo))]
                    if len(matched)!=1:fail(path+'.data.partner','bijective boundary nodes',n)
                    else:periodic_nodes.append((n,matched[0]))
    for op,r in cfg['records'].items():
        if r['required'] and not counts.get(op):fail('$.conditions','required '+op,'missing')
    if refs!=set(m['fields']):fail('$.fields','exactly referenced fields',sorted(set(m['fields'])-refs))
    if axes!=set(m['time_axes']):fail('$.time_axes','no unused loading axes',list(m['time_axes']))
    if errors:return
    if slug=='equivalent-fluid':
        values=byop['material'][0][1]
        for key in ('density','compressibility'):
            z=values[key]
            if np.any(z[...,0]<=0) or np.any(z[...,1]>0):fail('$.fields.'+key,'positive real, nonpositive imaginary','active/nonphysical sign')
    for location,v in byop.get('impedance',[]):
        if not tr and (np.any(v['impedance'][...,0]<0) or np.any(np.linalg.norm(v['impedance'],axis=-1)==0)):fail('$.conditions.impedance','passive nonzero impedance','invalid Z')
    if slug=='lighthill-radiation':
        x=byop['lighthill_tensor'][0][1]['value']
        if not np.array_equal(x,np.swapaxes(x,2,3)):fail('$.fields.stress','symmetric ij for real and imaginary parts','nonsymmetric')
    if slug=='uniform-flow-acoustics':
        if counts.get('periodic')!=3 or usedfaces!=set(exterior):fail('$.conditions','three pairs covering all box faces','incomplete periodicity')
        row={int(tag):i for i,tag in enumerate(a[locs['domain']['ids']])}
        for op in ('initial_pressure','initial_velocity'):
            values=byop[op][0][1]['value'][0]
            for left,right in periodic_nodes:
                if not np.allclose(values[row[left]],values[row[right]],rtol=1e-12,atol=1e-12):fail('$.conditions.'+op,'periodic-compatible initial values',[left,right])
    if modal:
        v=byop['structure'][0][1]
        for key in ('mass','damping','stiffness'):
            x=v[key][0,0]
            if not np.array_equal(x,x.T):fail('$.fields.'+key,'symmetric matrix','nonsymmetric');continue
            try:
                if key!='damping':np.linalg.cholesky(x)
                elif np.linalg.eigvalsh(x).min() < -1e-12*max(1,np.linalg.norm(x)):fail('$.fields.damping','positive semidefinite','negative eigenvalue')
            except np.linalg.LinAlgError:fail('$.fields.'+key,'positive definite','not SPD')
        gram=np.zeros((p['mode_count'],p['mode_count']))
        for location,v in byop['modal_wall']:
            _,_,area=boundary_geometry(problem,location);phi=v['shape'][0];gram+=phi.T@(area[:,None]*phi)
        try:np.linalg.cholesky(gram)
        except np.linalg.LinAlgError:fail('$.fields.shape','independent shapes on wall union','rank deficient')
    present=set();wall_output={op:set() for op in special_sites};total=0
    for name,s in m['outputs'].items():
        q=s['quantity'];os=cfg['outputs'].get(q);path='$.outputs.'+name;location=s['location']
        if os is None:fail(path+'.quantity',list(cfg['outputs']),q);continue
        present.add(q);where=os['where']
        if where in ('receivers','structure'):ok=location==where
        elif where=='cells':ok=support(location,'cells')
        else:ok=location in special_sites.get(where,set());wall_output[where].add((q,location))
        if not ok:fail(path+'.location',where,location)
        expected=dict(unit=os['unit'],kind=os['kind'],component_shape=shape(os,p),components=labels(os,p),dtype='float64',time_axis=outaxis,value_kind='point' if where in ('receivers','structure') else 'average')
        for k,v in expected.items():
            if s.get(k)!=v:fail(path+'.'+k,v,s.get(k))
        if 'sampling' in s:fail(path,'no output sampling',s['sampling'])
        total+=len(a[m['time_axes'][s['time_axis']]])*len(ids(location))*math.prod(s['component_shape'])
    if present!=set(cfg['outputs']):fail('$.outputs','all required quantities',sorted(present))
    for op,sites in special_sites.items():
        expected={(q,loc) for q,s in cfg['outputs'].items() if s['where']==op for loc in sites}
        if wall_output[op]!=expected:fail('$.outputs','all local wall quantities on every record',sorted(wall_output[op]))
    inp=sum(a[s['array']].size for s in m['fields'].values())
    if max(inp,total)>3000000:fail('$.fields/outputs','<=3000000 components each',[inp,total])
