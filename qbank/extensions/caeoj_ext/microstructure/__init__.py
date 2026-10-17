"""Material microstructure declaration checks; no evolution or reference solver."""
from functools import lru_cache
from importlib.resources import files
import json
import math
import numpy as np


@lru_cache(maxsize=1)
def models():
    return json.loads(files(__package__).joinpath('models.json').read_text(encoding='utf-8'))


def state_size(config, parameters):
    return parameters['grain_count'] if config['state_size']=='k' else config['state_size']


def shape(spec, config, parameters):
    return [state_size(config,parameters) if x=='s' else parameters['grain_count'] if x=='k'
            else x for x in spec['shape']]


def labels(spec, config, parameters):
    return ['value'] if spec['kind']=='scalar' else [
        'c'+str(i+1) for i in range(math.prod(shape(spec,config,parameters)))]


def check(problem, errors):
    from caeoj.validation import issue
    m,a=problem.manifest,problem.arrays
    def fail(path, expected, actual):
        if isinstance(actual,np.ndarray):
            actual=actual.tolist() if actual.size<=16 else {'shape':list(actual.shape)}
        errors.append(issue('E_MICROSTRUCTURE',path,expected,actual,
                            'Declaration violates this microstructure DATA contract.'))
    model=m.get('physics',{}).get('model','')
    slug=model.removeprefix('microstructure-').removesuffix('-v1');cfg=models().get(slug)
    if cfg is None or model!='microstructure-'+slug+'-v1':
        fail('$.physics.model','registered microstructure model',model);return
    if m['spatial_dimension']!=2:
        fail('$.spatial_dimension',2,m['spatial_dimension'])
    if 'task' in m and m['task']!=slug:
        fail('$.task',slug,m['task'])
    if any(k in m for k in ('profile','contract_version','analysis','materials')):
        fail('$','physics-only declaration','mixed profile')
    if m['meshes'] or m['geometries']:
        fail('$.meshes/geometries','empty objects','undeclared geometry')
    if set(m['physics'])!={'model','parameters'}:
        fail('$.physics',['model','parameters'],list(m['physics']))
    params=m['physics'].get('parameters',{})
    if set(params)!=set(cfg['parameters']):
        fail('$.physics.parameters',list(cfg['parameters']),list(params));return
    p={}
    for name,s in cfg['parameters'].items():
        v=params[name];x=v.get('value')
        if (set(v)!={'value','unit'} or v.get('unit')!=s['unit'] or
                type(x) not in ((int,) if s.get('integer') else (int,float))):
            fail('$.physics.parameters.'+name,s,v);continue
        if (s.get('positive') and x<=0 or 'lower' in s and x<s['lower'] or
                'upper' in s and x>s['upper'] or 'lower_exclusive' in s and x<=s['lower_exclusive']):
            fail('$.physics.parameters.'+name,s,x)
        p[name]=x
    if errors:return
    axes={'static','requests'} | {r['axis'] for r in cfg['records'].values()}
    if set(m['time_axes'])!=axes:
        fail('$.time_axes',sorted(axes),list(m['time_axes']));return
    if not np.array_equal(a[m['time_axes']['static']],[0.]):
        fail('$.time_axes.static','[0.0]',a[m['time_axes']['static']])
    times=a[m['time_axes']['requests']]
    if len(times)>256 or times[0]<0 or not 0<times[-1]<=1e9:
        fail('$.time_axes.requests','1..256 frames, first>=0, last in (0,1e9]',times)
    if 'control' in axes:
        control=a[m['time_axes']['control']]
        if not 2<=len(control)<=256 or control[0]!=0 or control[-1]!=times[-1]:
            fail('$.time_axes.control','2..256 frames spanning exactly [0,t_end]',control)
    locs=m['locations']
    if set(locs)!={'system','modes','probes'}:
        fail('$.locations',['system','modes','probes'],list(locs));return
    for name,kind,lo,hi in [('system','entities',1,1),('modes','entities',1,32),('probes','points',1,128)]:
        l=locs[name];ids=a[l['ids']]
        if l['kind']!=kind:fail('$.locations.'+name,kind,l['kind'])
        if not lo<=len(ids)<=hi:fail('$.locations.'+name,'count limits',len(ids))
        if name=='system' and not np.array_equal(ids,[0]):fail('$.locations.system','ID [0]',ids)
    if errors:return
    xy=a[locs['probes']['coordinates']]
    if np.any(xy<0) or np.any(xy[:,0]>=p['length_x']) or np.any(xy[:,1]>=p['length_y']):
        fail('$.locations.probes','canonical periodic coordinates [0,Lx)x[0,Ly)',xy)
    counts,refs,values={},set(),{}
    for i,c in enumerate(m['conditions']):
        path=f'$.conditions[{i}]';op=c['operator'];r=cfg['records'].get(op)
        if r is None:
            fail(path+'.operator',list(cfg['records']),op);continue
        counts[op]=counts.get(op,0)+1
        if counts[op]!=1:fail(path,'one record per operator',counts[op])
        for k in ('role','variable','location'):
            if c[k]!=r[k]:fail(path+'.'+k,r[k],c[k])
        if set(c['data'])!=set(r['data']):
            fail(path+'.data',list(r['data']),list(c['data']));continue
        values[op]={}
        for key,s in r['data'].items():
            ref=c['data'][key]
            if set(ref)!={'field'}:
                fail(path+'.data.'+key,'field reference only',ref);continue
            name=ref['field'];refs.add(name);fs=m['fields'][name]
            expected=dict(quantity=r['variable'] if key=='value' else key,unit=s['unit'],
                kind=s['kind'],component_shape=shape(s,cfg,p),components=labels(s,cfg,p),
                dtype='float64',location=r['location'],time_axis=r['axis'],value_kind='point',
                sampling=dict(space='uniform',time='linear' if r['axis']=='control' else 'constant',extrapolation='forbid'))
            for k,v in expected.items():
                if fs.get(k)!=v:fail('$.fields.'+name+'.'+k,v,fs.get(k))
            values[op][key]=a[fs['array']]
    if set(counts)!=set(cfg['records']):fail('$.conditions','all required operators',sorted(counts))
    if refs!=set(m['fields']):fail('$.fields','exactly referenced fields',sorted(set(m['fields'])-refs))
    if errors:return
    wave=values['series']['wave'][0]
    if np.any(abs(wave)>8) or np.any(wave!=np.floor(wave)) or np.any(
            ~((wave[:,0]>0)|((wave[:,0]==0)&(wave[:,1]>0)))):
        fail('$.conditions.series.wave','canonical nonzero integer waves, |component|<=8',wave)
    if len({tuple(row) for row in wave})!=len(wave):
        fail('$.conditions.series.wave','unique wave pairs',wave)
    coeff=values['series']['amplitude'][0];mean=values['offset']['value'][0,0]
    with np.errstate(over='ignore',invalid='ignore'):
        radius=np.hypot(coeff[...,0],coeff[...,1]).sum(axis=0)
    if slug=='ternary-separation':
        invalid=np.any(mean-radius<0) or mean.sum()+radius.sum()>1
    elif slug=='grain-coarsening':
        invalid=np.any(mean-radius<0) or np.any(mean+radius>1)
    else:
        invalid=np.any(abs(mean)+radius>1)
    if not np.all(np.isfinite(radius)) or invalid:
        fail('$.conditions.offset/series','initial-state conservative bounds',dict(mean=mean.tolist(),radius=radius.tolist()))
    if slug=='ternary-separation':
        matrix=values['mobility']['value'][0,0];scale=np.max(abs(matrix))
        scaled=matrix/scale if scale else matrix
        if (matrix[0,1]!=matrix[1,0] or scaled[0,0]<=0 or scaled[1,1]<=0 or
                scaled[0,0]*scaled[1,1]-scaled[0,1]**2<=0):
            fail('$.conditions.mobility','symmetric positive definite matrix',matrix)
    length=min(p['length_x'],p['length_y']);energy=p['energy_scale'];end=times[-1]
    if max(p['length_x'],p['length_y'])/length>4:
        fail('$.physics.parameters.length_x/length_y','aspect ratio <=4','excess')
    with np.errstate(over='ignore',invalid='ignore',divide='ignore'):
        for key in ('gradient','gradient_c','gradient_eta'):
            if key in p:
                ratio=p[key]/(energy*length**2)
                if not .0025<=ratio<=.1:
                    fail('$.physics.parameters.'+key,'kappa/(A length_min^2) in [.0025,.1]',ratio)
        if 'relaxation' in p and p['relaxation']*energy*end>10:
            fail('$.physics.parameters.relaxation','L A t_end <=10','excess')
        if 'mobility' in p:
            limit=.2 if slug=='crystal-density' else 1.
            if p['mobility']*energy*end/length**2>limit:
                fail('$.physics.parameters.mobility','M A t_end/length_min^2 <='+str(limit),'excess')
        if slug=='crystal-density' and not 1/16<=p['length_scale']/length<=1/4:
            fail('$.physics.parameters.length_scale','ell/length_min in [1/16,1/4]',p['length_scale']/length)
        if slug=='coupled-precipitation' and not .1<=p['coupling_energy']/energy<=10:
            fail('$.physics.parameters.coupling_energy','B/A in [.1,10]',p['coupling_energy']/energy)
        if slug=='driven-ordering' and np.any(abs(values['history']['value'])/energy>2):
            fail('$.conditions.history','|b|/A <=2','excess')
        if slug=='ternary-separation':
            eigen=np.linalg.eigvalsh(scaled)*scale
            if eigen[0]<1e-30 or eigen[-1]>1e-6 or eigen[0]<=0 or eigen[-1]/eigen[0]>20:
                fail('$.conditions.mobility','eigenvalues in [1e-30,1e-6] and condition <=20',eigen)
            if eigen[-1]*energy*end/length**2>1:
                fail('$.conditions.mobility','lambda_max A t_end/length_min^2 <=1','excess')
    present,total=set(),0
    for name,fs in m['outputs'].items():
        q=fs['quantity'];s=cfg['outputs'].get(q);path='$.outputs.'+name
        if s is None:fail(path+'.quantity',list(cfg['outputs']),q);continue
        present.add(q)
        expected=dict(unit=s['unit'],kind=s['kind'],component_shape=shape(s,cfg,p),
            components=labels(s,cfg,p),dtype='float64',location='probes',time_axis='requests',value_kind='point')
        for k,v in expected.items():
            if fs.get(k)!=v:fail(path+'.'+k,v,fs.get(k))
        if 'sampling' in fs:fail(path,'no output sampling',fs['sampling'])
        total+=len(a[locs[fs['location']]['ids']])*len(a[m['time_axes'][fs['time_axis']]])*math.prod(fs['component_shape'])
    if present!=set(cfg['outputs']):fail('$.outputs','all required quantities',sorted(present))
    if max(total,sum(a[fs['array']].size for fs in m['fields'].values()))>2000000:
        fail('$.fields/outputs','each total <=2000000 components','excess')
