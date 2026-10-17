"""Mechanical declaration validation. No time integration or reference solver."""
from functools import lru_cache
from importlib.resources import files
import json
import numpy as np


@lru_cache(maxsize=1)
def models():
    return json.loads(files(__package__).joinpath('models.json').read_text(encoding='utf-8'))


def shape(spec, parameters):
    return [int(parameters['mode_count']) if n == 'k' else n for n in spec['shape']]


def labels(spec, parameters):
    sh = shape(spec, parameters)
    kind = spec.get('kind', 'scalar')
    return ['value'] if kind == 'scalar' else list('xyz'[:sh[0]]) if kind == 'vector' else ['c'+str(i+1) for i in range(int(np.prod(sh)))]


def check(problem, errors):
    from caeoj.validation import issue
    m, arrays = problem.manifest, problem.arrays
    slug = m.get('physics', {}).get('model', '').removeprefix('multibody-').removesuffix('-v1')
    cfg = models().get(slug)
    def fail(path, expected, actual):
        if isinstance(actual, np.ndarray): actual = actual.tolist() if actual.size < 10 else list(actual.shape)
        errors.append(issue('E_MULTIBODY',path,expected,actual,'Mechanical declaration violates the task DATA contract.'))
    if cfg is None:
        fail('$.physics.model','registered multibody model',m.get('physics')); return
    if m.get('physics', {}).get('model') != f'multibody-{slug}-v1':
        fail('$.physics.model',f'multibody-{slug}-v1',m.get('physics')); return
    if 'task' in m and m['task'] != slug:fail('$.task',slug,m['task'])
    if m['spatial_dimension'] != cfg['dimension']:fail('$.spatial_dimension',cfg['dimension'],m['spatial_dimension'])
    if any(k in m for k in ('profile','analysis','materials','contract_version')):fail('$','physics-only declaration','mixed profile')
    if m['meshes'] or m['geometries']:fail('$.meshes/geometries','empty objects','mesh geometry')
    p = {}
    def constant(value, spec, path):
        if (set(value) != {'value','unit'} or value.get('unit') != spec['unit'] or
                type(value.get('value')) not in ((int,) if spec.get('integer') else (int,float))):
            fail(path,'typed '+spec['unit']+' constant'+(' integer' if spec.get('integer') else ''),value);return None
        x=value['value']
        if spec.get('lower') is not None and x < spec['lower']:fail(path,'>= '+str(spec['lower']),x)
        if spec.get('upper') is not None and x > spec['upper']:fail(path,'<= '+str(spec['upper']),x)
        return x
    params=m['physics'].get('parameters',{})
    if set(params) != set(cfg['parameters']):fail('$.physics.parameters',list(cfg['parameters']),list(params));return
    for key,s in cfg['parameters'].items():p[key]=constant(params[key],s,'$.physics.parameters.'+key)
    if errors:return
    impulse=cfg['family']=='impact';base='systems' if cfg['family']=='modal' else 'bodies'
    if not impulse and p['end_time'] <= p['start_time']:fail('$.physics.parameters.end_time','> start_time',p['end_time']);return
    locs=m['locations']
    if base not in locs:fail('$.locations','required '+base,list(locs));return
    if len(locs)>129:fail('$.locations','<=129',len(locs))
    for key,l in locs.items():
        n=len(arrays[l['ids']])
        if l['kind']!='entities':fail('$.locations.'+key,'entities',l);continue
        if key==base:
            if not 1<=n<=32:fail('$.locations.'+key,'1..32 IDs',n)
        elif n!=1:fail('$.locations.'+key,'single ID auxiliary',n)
    if errors:return
    ids=set(map(int,arrays[locs[base]['ids']]))
    t0=0. if impulse else p['start_time'];tf=0. if impulse else p['end_time']
    for key,array in m['time_axes'].items():
        t=arrays[array]
        if len(t)>201:fail('$.time_axes.'+key,'<=201 frames',len(t))
    if impulse:
        if set(m['time_axes'])!={'event'}:fail('$.time_axes','event only',list(m['time_axes']));return
        if not np.array_equal(arrays[m['time_axes']['event']],[0.]):fail('$.time_axes.event','[0.0]',arrays[m['time_axes']['event']])
    else:
        if not {'initial','response'}<=set(m['time_axes']):fail('$.time_axes','initial and response',list(m['time_axes']));return
        if not np.array_equal(arrays[m['time_axes']['initial']],[t0]):fail('$.time_axes.initial','[start_time]',arrays[m['time_axes']['initial']])
        t=arrays[m['time_axes']['response']]
        if t[0]<t0 or t[-1]>tf:fail('$.time_axes.response','inside [t0,tf]',t)
    refs=set();used_sites=set();used_axes={'event'} if impulse else {'initial','response'};counts={};records=[];state={};pairs=set()
    def field(ref,s,loc,op,path):
        if set(ref)!={'field'}:fail(path,'field reference',ref);return None
        name=ref['field'];refs.add(name);fs=m['fields'][name]
        expected=dict(unit=s['unit'],dtype='float64',location=loc,kind=s.get('kind','scalar'),component_shape=shape(s,p),components=labels(s,p),value_kind='point')
        # quantity is supplied by caller, independent of field name and array key.
        expected['quantity']=path.rsplit('.',1)[-1]
        for key,val in expected.items():
            if fs.get(key)!=val:fail('$.fields.'+name+'.'+key,val,fs.get(key))
        axis=fs['time_axis'];used_axes.add(axis);t=arrays[m['time_axes'][axis]]
        loading=op=='loads';required_axis='event' if impulse else 'initial'
        if not loading and axis!=required_axis:fail('$.fields.'+name+'.time_axis',required_axis,axis)
        if loading and not impulse:
            if (len(t)==1 and t[0]!=t0) or (len(t)>1 and (t[0]!=t0 or t[-1]!=tf)):
                fail('$.fields.'+name+'.time_axis','constant at t0 or full [t0,tf] axis',t)
        sampling=dict(space='uniform',time='linear' if loading and len(t)>1 else 'constant',extrapolation='forbid')
        if fs.get('sampling')!=sampling:fail('$.fields.'+name+'.sampling',sampling,fs.get('sampling'))
        values=arrays[fs['array']]
        if s.get('positive') and np.any(values<=0):fail(path,'positive values','nonpositive')
        return values
    for i,c in enumerate(m['conditions']):
        op=c['operator'];r=cfg['records'].get(op);path=f'$.conditions[{i}]'
        if r is None:fail(path+'.operator',list(cfg['records']),op);continue
        counts[op]=counts.get(op,0)+1;loc=c['location']
        for key in ('role','variable'):
            if c[key]!=r[key]:fail(path+'.'+key,r[key],c[key])
        if r['location']=='site':
            if loc==base or loc in used_sites:fail(path+'.location','distinct auxiliary site',loc)
            used_sites.add(loc)
        elif loc!=r['location'] or counts[op]!=1:fail(path+'.location','one record on '+r['location'],loc)
        if set(c['data'])!=set(r['data']):fail(path+'.data',list(r['data']),list(c['data']));continue
        values={}
        for key,s in r['data'].items():
            values[key]=field(c['data'][key],s,loc,op,path+'.data.'+key) if 'shape' in s else constant(c['data'][key],s,path+'.data.'+key)
        if any(v is None for v in values.values()):continue
        records.append((op,loc,values))
        if op in ('body','modal_system'):state=values
        if 'a' in values:
            a,b=values['a'],values['b'];allow_ground=op in ('revolute','weld','spring')
            legal=ids|({-1} if allow_ground else set())
            if a not in legal or b not in legal or a==b:fail(path+'.data','distinct valid body IDs', [a,b])
            if op in ('contact','collision'):
                pair=tuple(sorted((a,b)))
                if pair in pairs:fail(path+'.data','unique unordered pair',pair)
                pairs.add(pair)
            for k in ('stiffness','rest_length','slip_speed'):
                if k in values and values[k]<=0 and not (op=='spring' and k=='stiffness'):fail(path+'.data.'+k,'>0',values[k])
        if op=='angle_drive' and values['body'] not in ids:fail(path+'.data.body','movable body ID',values['body'])
    for op,r in cfg['records'].items():
        if r['required'] and not counts.get(op):fail('$.conditions','required '+op,'missing')
    if set(locs)!={base}|used_sites:fail('$.locations','base and exactly used auxiliary sites',list(locs))
    if refs!=set(m['fields']):fail('$.fields','exactly referenced fields',sorted(set(m['fields'])-refs))
    if set(m['time_axes'])!=used_axes:fail('$.time_axes','exactly used axes',list(m['time_axes']))
    if errors:return
    def matrix(a,positive,path):
        for x in a[0]:
            if not np.array_equal(x,x.T):fail(path,'symmetric matrix','nonsymmetric');continue
            try:
                if positive:np.linalg.cholesky(x)
                elif np.linalg.eigvalsh(x).min() < -1e-12*max(1.,np.linalg.norm(x,2)):
                    fail(path,'positive semidefinite','negative eigenvalue')
            except np.linalg.LinAlgError:fail(path,'positive definite','singular/indefinite')
    if cfg['family']=='modal':
        matrix(state['mass_matrix'],True,'$.fields.mass_matrix');matrix(state['stiffness'],True,'$.fields.stiffness');matrix(state['damping'],False,'$.fields.damping')
        if slug=='translating-flexible':
            for i,mass in enumerate(state['carrier_mass'][0,:,0]):
                b=state['coupling'][0,i];massmatrix=np.block([[mass*np.eye(2),b],[b.T,state['mass_matrix'][0,i]]])
                matrix(massmatrix[None,None],True,'$.fields.coupling')
    if cfg['family']=='spatial':
        matrix(state['inertia'],True,'$.fields.inertia')
        for x in state['inertia'][0]:
            e=np.linalg.eigvalsh(x)
            if e[-1]>e[0]+e[1]+1e-12*e[-1]:fail('$.fields.inertia','principal inertia triangle inequality',e)
        if np.any(abs(np.linalg.norm(state['quaternion0'][0],axis=-1)-1)>1e-12):fail('$.fields.quaternion0','unit quaternion','bad norm')
    if impulse:
        used=[];order={tag:i for i,tag in enumerate(arrays[locs[base]['ids']])}
        for op,loc,v in records:
            if op!='collision':continue
            a,b=order[v['a']],order[v['b']];used.extend((v['a'],v['b']))
            d=state['position0'][0,b]-state['position0'][0,a];length=np.linalg.norm(d);r=state['radius'][0,a,0]+state['radius'][0,b,0]
            if length==0 or abs(length-r)>1e-10*max(1,r):fail('$.conditions.'+loc,'externally tangent disks',length)
            elif (state['velocity0'][0,b]-state['velocity0'][0,a]) @ (d/length)>=0:fail('$.conditions.'+loc,'approaching pair','nonnegative normal speed')
        if len(used)!=len(set(used)) or set(used)!=ids:fail('$.conditions','disjoint collision pairs covering bodies',used)
    if cfg['family']=='planar' and slug not in ('normal-contact','regularized-friction'):
        rows=2*counts.get('revolute',0)+3*counts.get('weld',0)+counts.get('angle_drive',0)
        n=3*len(ids)
        if slug in ('planar-kinematics','planar-inverse-dynamics') and rows!=n:fail('$.conditions','3n constraint rows',rows)
        if slug=='prescribed-drive' and rows>=n:fail('$.conditions','fewer than 3n rows',rows)
        if rows>n:fail('$.conditions','no more than 3n independent rows',rows)
    required={(q,base) for q,s in cfg['outputs'].items() if s['location']==base}
    required|={(q,loc) for q,s in cfg['outputs'].items() if s['location']!=base for op,loc,v in records if op==s['location']}
    actual=set();total=0
    for name,s in m['outputs'].items():
        q=s['quantity'];spec=cfg['outputs'].get(q);path='$.outputs.'+name
        if spec is None:fail(path+'.quantity',list(cfg['outputs']),q);continue
        actual.add((q,s['location']))
        expected=dict(unit=spec['unit'],dtype='float64',kind=spec['kind'],component_shape=shape(spec,p),components=labels(spec,p),time_axis='event' if impulse else 'response',value_kind='point')
        for key,val in expected.items():
            if s.get(key)!=val:fail(path+'.'+key,val,s.get(key))
        if 'sampling' in s:fail(path,'no output sampling',s['sampling'])
        total+=len(arrays[m['time_axes'][s['time_axis']]])*len(arrays[locs[s['location']]['ids']])*int(np.prod(s['component_shape']))
    if actual!=required:fail('$.outputs','all required quantity/location pairs',sorted(actual))
    input_total=sum(arrays[s['array']].size for s in m['fields'].values())
    if max(input_total,total)>2000000:fail('$.fields/outputs','<=2000000 components each',[input_total,total])
