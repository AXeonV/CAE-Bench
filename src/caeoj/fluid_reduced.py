"""Opt-in thin-film, depth-averaged, rarefied and memory-fluid declarations.

This is a contract checker and material SDK, not a flow solver.
"""
import math
import numpy as np

PREFIX = 'fluid-reduced-'
# All parameters are exact sets. Bounds are checked below; units are normative.
BASE = {'reference_pressure':'Pa'}
LIQ = {'density':'kg/m3','viscosity':'Pa.s','reference_pressure':'Pa'}
THERM = {'heat_capacity':'J/(kg.K)','conductivity':'W/(m.K)',
         'reference_temperature':'K','temperature_coefficient':'1/K'}
CARREAU = {'zero_viscosity':'Pa.s','infinite_viscosity':'Pa.s',
           'time_constant':'s','power_index':'1'}
OLDROYD = {'density':'kg/m3','solvent_viscosity':'Pa.s','polymer_viscosity':'Pa.s',
           'relaxation_time':'s','reference_pressure':'Pa'}
GAS = {'molecule_mass':'kg','molecule_diameter':'m','reference_temperature':'K'}
TIME = {'start_time':'s','end_time':'s'}
MODELS = {}
def _model(slug, section, dimension, transient, parameters, domain, outputs, family):
    MODELS[PREFIX+slug+'-v1'] = dict(slug=slug,section=section,dimension=dimension,
        transient=transient,parameters={**parameters,**(TIME if transient else {})},
        domain=domain,outputs=outputs,family=family)

# domain entries: variable -> (role, operator, unit, kind, range).
S = lambda role, op, unit, kind='scalar', bound='finite': (role,op,unit,kind,bound)
FILM = {'gap':S('material','geometry','m',bound='positive'),
        'lower_velocity':S('material','geometry','m/s','vector'),
        'upper_velocity':S('material','geometry','m/s','vector')}
WATER = {'bed':S('material','geometry','m')}
INIT_WATER = {'depth':S('initial','assign','m',bound='positive'),
              'velocity':S('initial','assign','m/s','vector')}
INIT_FLOW = {'velocity':S('initial','assign','m/s','vector')}
INIT_A = {'conformation':S('initial','assign','1','tensor','spd')}
_model('liquid-lubrication','2.8',2,False,{**LIQ,'cavitation_pressure':'Pa'},FILM,
       ['pressure','film_fraction','film_flux','load'],'film_cavitation')
_model('gas-film','2.8',2,True,{'viscosity':'Pa.s','specific_gas_constant':'J/(kg.K)',
       'reference_temperature':'K','reference_pressure':'Pa'},
       {**FILM,'pressure':S('initial','assign','Pa',bound='positive')},
       ['pressure','density','film_flux','load'],'film_gas')
_model('thermal-film','2.8',2,True,{**LIQ,**THERM,'heat_transfer':'W/(m2.K)'},
       {**FILM,'temperature':S('initial','assign','K',bound='positive'),
        'wall_temperature':S('material','geometry','K',bound='positive')},
       ['pressure','temperature','film_flux','load'],'film_thermal')
_model('nonnewtonian-film','2.8',2,False,{'density':'kg/m3','reference_pressure':'Pa',**CARREAU},FILM,
       ['pressure','film_flux','load'],'film_carreau')
for slug,tr,dry in [('fully-wet-steady',False,False),('fully-wet-transient',True,False),('wetting-drying',True,True)]:
    init={**INIT_WATER} if tr else {}
    if dry:init['depth']=S('initial','assign','m',bound='nonnegative')
    _model(slug,'2.9',2,tr,{'density':'kg/m3','gravity':'m/s2','drag_rate':'1/s'},
           {**WATER,**init},['depth','velocity','water_flux','water_volume'],'water_dry' if dry else 'water')
_model('two-layer','2.9',2,True,{'lower_density':'kg/m3','upper_density':'kg/m3','gravity':'m/s2',
       'bottom_drag':'1/s','interface_drag':'kg/(m2.s)'},
       {**WATER,**{f'{layer}_{name}':spec for layer in ['lower','upper'] for name,spec in INIT_WATER.items()}},
       ['lower_depth','upper_depth','lower_velocity','upper_velocity','water_volume'],'water_two')
for slug,thermal in [('isothermal-slip',False),('thermal-slip',True)]:
    _model(slug,'2.10',2,False,{**GAS,'slip_length':'m','temperature_jump_length':'m',
           'reference_pressure':'Pa',**({'heat_conductivity':'W/(m.K)'} if thermal else {})},
           {},['density','velocity','pressure']+(['temperature','heat_flux'] if thermal else [])+['traction'],
           'slip_thermal' if thermal else 'slip')
for slug,collision in [('transition-gas',True),('free-molecular',False)]:
    _model(slug,'2.10',3,False,GAS,{},
           ['density','velocity','temperature','pressure','traction','heat_flux'],
           'kinetic_hs' if collision else 'kinetic_free')
for slug,tr in [('viscoelastic-steady',False),('viscoelastic-transient',True)]:
    _model(slug,'2.11',2,tr,OLDROYD,{**INIT_FLOW,**INIT_A} if tr else {},
           ['velocity','pressure','polymer_stress','conformation','traction'],'oldroyd')
_model('thixotropic-transient','2.11',2,True,{'density':'kg/m3','reference_pressure':'Pa',
       'base_viscosity':'Pa.s','structure_viscosity':'Pa.s','build_time':'s','breakdown':'1'},
       {**INIT_FLOW,'structure':S('initial','assign','1',bound='fraction')},
       ['velocity','pressure','structure','extra_stress','traction'],'thixotropic')
_model('thermal-generalized-newtonian','2.11',3,True,
       {'density':'kg/m3','reference_pressure':'Pa',**CARREAU,**THERM},
       {**INIT_FLOW,'temperature':S('initial','assign','K',bound='positive')},
       ['velocity','pressure','temperature','extra_stress','traction','heat_flux'],'thermal_carreau')
_model('thermal-viscoelastic','2.11',2,True,{**OLDROYD,**THERM},
       {**INIT_FLOW,**INIT_A,'temperature':S('initial','assign','K',bound='positive')},
       ['velocity','pressure','temperature','polymer_stress','conformation','traction','heat_flux'],'thermal_oldroyd')

UNITS = {'pressure':'Pa','density':'kg/m3','temperature':'K','velocity':'m/s',
 'film_fraction':'1','film_flux':'m2/s','depth':'m','lower_depth':'m','upper_depth':'m',
 'lower_velocity':'m/s','upper_velocity':'m/s','water_flux':'m2/s','structure':'1',
 'conformation':'1','polymer_stress':'Pa','extra_stress':'Pa','traction':'Pa','heat_flux':'W/m2',
 'load':'N','water_volume':'m3'}
VECTORS = {'velocity','film_flux','lower_velocity','upper_velocity','water_flux','traction','heat_flux'}
TENSORS = {'conformation','polymer_stress','extra_stress'}

def reduced_parameters(problem):
    """Return declared SI constants, with no defaulting or conversion."""
    return {k:v['value'] for k,v in problem.manifest['physics']['parameters'].items()}

def reduced_viscosity(model, parameters, shear_rate, temperature=None, structure=None):
    """Declared scalar viscosity in Pa.s; shear rate sqrt(2 D:D), in 1/s."""
    cfg=MODELS[model]; p=parameters; g=np.asarray(shear_rate,dtype=float)
    if np.any(~np.isfinite(g)) or np.any(g<0):raise ValueError('Finite nonnegative shear rate required')
    fam=cfg['family']
    if fam=='thixotropic':
        x=np.asarray(structure,dtype=float)
        if np.any(~np.isfinite(x)) or np.any((x<0)|(x>1)):raise ValueError('Structure must lie in [0,1]')
        mu=p['base_viscosity']+p['structure_viscosity']*x
    elif 'carreau' in fam:
        mu=p['infinite_viscosity']+(p['zero_viscosity']-p['infinite_viscosity'])*(1+(p['time_constant']*g)**2)**((p['power_index']-1)/2)
    else:
        if 'viscosity' not in p and 'solvent_viscosity' not in p:raise ValueError('Model has no scalar viscosity helper')
        mu=np.asarray(p.get('viscosity',p.get('solvent_viscosity')),dtype=float)+np.zeros_like(g)
    if 'temperature_coefficient' in p:
        t=np.asarray(temperature,dtype=float)
        if np.any(~np.isfinite(t)) or np.any(t<=0):raise ValueError('Positive absolute temperature required')
        mu=mu*np.exp(-p['temperature_coefficient']*(t-p['reference_temperature']))
    if np.any(~np.isfinite(mu)) or np.any(mu<=0):raise ValueError('Nonpositive/nonfinite viscosity')
    return mu

def maxwellian(number_density, velocity, temperature, molecule_mass, molecular_velocity):
    """3D number distribution f(c), units s3/m6; velocity arguments end in 3."""
    k=1.380649e-23
    if any(not np.isfinite(x) or x<=0 for x in (number_density,temperature,molecule_mass)):
        raise ValueError('Positive finite n,T,m required')
    u=np.asarray(velocity,dtype=float);c=np.asarray(molecular_velocity,dtype=float)
    if u.shape!=(3,) or c.shape[-1:]!=(3,) or not np.all(np.isfinite(u)) or not np.all(np.isfinite(c)):
        raise ValueError('Finite 3D velocities required')
    a=molecule_mass/(2*k*temperature)
    return number_density*(a/math.pi)**1.5*np.exp(-a*np.sum((c-u)**2,axis=-1))


def boundary_rules(cfg):
    """operator -> (variable, data requirements); data unit/kind or option."""
    fam=cfg['family']
    scalar=lambda u,b='finite': ('scalar',u,b)
    vector=lambda u: ('vector',u,'finite')
    if fam.startswith('film'):
        rules={'film_pressure':('pressure',{'value':scalar('Pa','positive')})}
        if fam=='film_cavitation':rules['film_pressure'][1]['fraction']=scalar('1','fraction')
        if fam=='film_thermal':rules['film_pressure'][1]['temperature']=scalar('K','positive')
        return rules
    if fam.startswith('water'):
        if fam=='water_two':return {'layer_wall':('layers',{'mode':('option','impermeable')}),
            'layer_inlet':('layers',{f'{l}_{n}':s for l in ('lower','upper') for n,s in
                [('depth',scalar('m','positive')),('velocity',vector('m/s'))]}),
            'layer_outflow':('layers',{'mode':('option','supercritical_outflow')})}
        return {'water_wall':('water',{'mode':('option','impermeable')}),
                'water_reservoir':('water',{'depth':scalar('m','positive'),'velocity':vector('m/s')})}
    if fam.startswith('kinetic'):
        return {'gas_wall':('gas',{'velocity':vector('m/s'),'temperature':scalar('K','positive'),
                                 'accommodation':scalar('1','fraction')}),
                'gas_reservoir':('gas',{'density':scalar('kg/m3','positive'),'velocity':vector('m/s'),
                                      'temperature':scalar('K','positive')})}
    if fam.startswith('slip'):
        return {'slip_wall':('gas',{'velocity':vector('m/s'),**({'temperature':scalar('K','positive')} if fam=='slip_thermal' else {})}),
                'slip_inlet':('gas',{'velocity':vector('m/s'),
                                       **({'temperature':scalar('K','positive')} if fam=='slip_thermal' else {})}),
                'slip_outlet':('gas',{'pressure':scalar('Pa','positive')})}
    return {'velocity_wall':('velocity',{'value':vector('m/s')}),
            'velocity_inlet':('velocity',{'value':vector('m/s'),
                **({'conformation':('tensor','1','spd')} if 'oldroyd' in fam else {}),
                **({'structure':scalar('1','fraction')} if fam=='thixotropic' else {})}),
            'traction_outlet':('traction',{'value':vector('Pa')})}



def reduced_time_derivative(times, values, time):
    """Linear sample derivative: right trace at knots, left at final endpoint."""
    t=np.asarray(times,dtype=float);v=np.asarray(values,dtype=float)
    if t.ndim!=1 or not len(t) or v.shape[0]!=len(t) or not np.all(np.isfinite(t)) or not np.all(np.isfinite(v)) or not np.isfinite(time):
        raise ValueError('Finite ordered samples with leading time axis required')
    if len(t)==1:return np.zeros_like(v[0])
    if np.any(np.diff(t)<=0) or time<t[0] or time>t[-1]:raise ValueError('Ordered interval coverage required')
    i=min(int(np.searchsorted(t,time,side='right'))-1,len(t)-2)
    return (v[i+1]-v[i])/(t[i+1]-t[i])


def layer_characteristic_speeds(lower_depth, upper_depth, lower_normal_velocity, upper_normal_velocity, gravity, density_ratio):
    """Four normal gravity-wave speeds, plus two tangential advection speeds."""
    hl,hu,vl,vu,g,r=lower_depth,upper_depth,lower_normal_velocity,upper_normal_velocity,gravity,density_ratio
    a=np.array([[vl,0,hl,0],[0,vu,0,hu],[g,r*g,vl,0],[g,g,0,vu]],dtype=float)
    wave=np.linalg.eigvals(a)
    if np.any(np.abs(wave.imag)>1e-10):raise ValueError('Two-layer state is not hyperbolic')
    return np.r_[wave.real,vl,vu]


def check_fluid_reduced(problem, errors):
    """Run after generic structure/reference checks, using loaded mesh geometry."""
    from .validation import issue
    from .mesh_geometry import exterior_facets, boundary_geometry
    m=problem.manifest; model=m.get('physics',{}).get('model','')
    if not model.startswith(PREFIX):return
    def fail(path,expected,actual,message):errors.append(issue('E_FLUID',path,expected,actual,message))
    if model not in MODELS:
        fail('$.physics.model',list(MODELS),model,'Unknown reduced fluid model/version.');return
    initial_errors=len(errors)
    cfg=MODELS[model];d=cfg['dimension'];params=m['physics'].get('parameters',{})
    if any(k in m for k in ('profile','contract_version','analysis','materials')):
        fail('$','physics-only declaration',model,'Cannot combine reduced and CFD profiles.')
    if m['spatial_dimension']!=d:fail('$.spatial_dimension',d,m['spatial_dimension'],'Model dimension mismatch.')
    if set(params)!=set(cfg['parameters']):fail('$.physics.parameters',sorted(cfg['parameters']),sorted(params),'Exact parameter set required.')
    for name,unit in cfg['parameters'].items():
        x=params.get(name,{})
        if set(x)!={'value','unit'} or x.get('unit')!=unit:
            fail('$.physics.parameters.'+name,unit,x,'Explicit SI constant required.');continue
        v=x['value']
        signed=name in ('reference_pressure','cavitation_pressure','start_time','end_time','temperature_coefficient')
        nonnegative=name in ('drag_rate','bottom_drag','interface_drag','heat_transfer','breakdown','temperature_jump_length','slip_length')
        if not signed and (v<0 if nonnegative else v<=0):fail('$.physics.parameters.'+name,'nonnegative' if nonnegative else 'positive',v,'Invalid parameter range.')
    if len(errors)>initial_errors:return
    p={k:x['value'] for k,x in params.items()}
    if cfg['transient'] and p.get('end_time',0)<=p.get('start_time',0):fail('$.physics.parameters','end_time > start_time',p,'Invalid interval.')
    if 'zero_viscosity' in p and p['zero_viscosity']<p.get('infinite_viscosity',0):fail('$.physics.parameters','zero_viscosity >= infinite_viscosity',p,'Carreau ordering invalid.')
    if 'lower_density' in p and p['lower_density']<=p.get('upper_density',0):fail('$.physics.parameters','lower_density > upper_density',p,'Stable density ordering required.')
    if cfg['family'].startswith('slip') and p.get('reference_pressure',0)<=0:fail('$.physics.parameters.reference_pressure','positive',p.get('reference_pressure'),'Positive reference gas pressure required.')
    if cfg['family']=='slip' and p.get('temperature_jump_length')!=0:fail('$.physics.parameters.temperature_jump_length',0,p.get('temperature_jump_length'),'Isothermal model has no temperature jump.')
    if cfg['family']=='film_cavitation' and p.get('cavitation_pressure',0)<=0:fail('$.physics.parameters.cavitation_pressure','positive',p.get('cavitation_pressure'),'Absolute pressure required.')
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
    expected=set(exterior);covered=set(); thermal_covered=set();refs=set();domain_seen=set();rules=boundary_rules(cfg);boundary_ops=set();gas_wall_keys=set()
    thermal=cfg['family'] in ('thermal_carreau','thermal_oldroyd')
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
        if op in ('gas_wall','slip_wall','velocity_wall'):
            key='value' if op=='velocity_wall' else 'velocity'
            if 'field' in data[key]:
                spec=m['fields'][data[key]['field']]
                if spec['kind']=='vector' and spec['component_shape']==[d]:
                    _,normals,_=boundary_geometry(problem,loc)
                    if np.any(np.abs(np.sum(values(key)*normals,axis=-1))>1e-12):fail(path+'.data.'+key,'tangential wall velocity',data[key],'Fixed walls cannot move normally.')
        if op=='layer_inlet':
            axes={m['fields'][x['field']]['time_axis'] for x in data.values() if 'field' in x}
            if len(axes)>1:fail(path+'.data','one shared field time axis',sorted(axes),'Two-layer inlet state samples must be synchronized.')
            valid=len(axes)<=1 and all(('field' not in data[key] or m['fields'][data[key]['field']]['kind']==('vector' if key.endswith('velocity') else 'scalar')) for key in requirements)
            if valid:
                _,normals,_=boundary_geometry(problem,loc)
                vl=values('lower_velocity');vu=values('upper_velocity')
                hl=values('lower_depth');hu=values('upper_depth')
                frames=max(vl.shape[0],vu.shape[0]);count=len(normals)
                hl=np.broadcast_to(hl,(frames,count,1));hu=np.broadcast_to(hu,(frames,count,1))
                for frame in range(frames):
                    for face,n in enumerate(normals):
                        try:
                            speeds=layer_characteristic_speeds(float(hl[frame,face,0]),float(hu[frame,face,0]),
                                float(np.dot(vl[frame,face],n)),float(np.dot(vu[frame,face],n)),p['gravity'],p['upper_density']/p['lower_density'])
                            if np.any(speeds>=0):raise ValueError('Every normal characteristic must enter the domain')
                        except ValueError as exc:fail(path+'.data','strictly supercritical hyperbolic inflow',data,str(exc))
        if op=='film_pressure' and cfg['family']=='film_cavitation':
            v=values('value');theta=values('fraction');pc=p['cavitation_pressure']
            if np.any(v<pc) or np.any((v>pc)&(theta!=1)):fail(path+'.data','p>=pc; full film above pc',data,'Cavitation boundary complementarity violated.')
    if (cfg['family'].startswith('kinetic') and 'gas_reservoir' not in boundary_ops or cfg['family'].startswith('slip') and 'slip_outlet' not in boundary_ops or cfg['family']=='water' and not cfg['transient'] and 'water_reservoir' not in boundary_ops):
        fail('$.conditions','at least one reservoir/outlet',sorted(boundary_ops),'Steady mass/pressure must be fixed by an open boundary.')
    if domain_seen!=set(cfg['domain']):fail('$.conditions',sorted(cfg['domain']),sorted(domain_seen),'Missing domain material or physical initial state.')
    if covered!=expected:fail('$.conditions','complete exterior mechanical/gas/water/film boundary partition',len(covered),'Missing boundary coverage.')
    if thermal and thermal_covered!=expected:fail('$.conditions','complete temperature boundary partition',len(thermal_covered),'Missing thermal coverage.')
    if set(m['fields'])!=refs:fail('$.fields',sorted(refs),sorted(m['fields']),'Every input field must have one declared physical role.')
    present=set()
    for name,spec in m['outputs'].items():
        q=spec['quantity'];path='$.outputs.'+name;present.add(q)
        if q not in cfg['outputs']:fail(path+'.quantity',cfg['outputs'],q,'Unsupported observation.');continue
        kind='vector' if q in VECTORS else 'tensor' if q in TENSORS else 'scalar'
        if spec['unit']!=UNITS[q] or spec['kind']!=kind or spec['dtype']!='float64':fail(path,(UNITS[q],kind),spec,'Output unit/kind mismatch.')
        l=locs[spec['location']]
        if q in ('load','water_volume'):
            valid=l.get('kind')=='aggregate' and l.get('operation')=='sum' and spec['value_kind']=='integral'
            source=locs.get(l.get('source'),{})
            valid=valid and source.get('kind')=='mesh' and source.get('entity')=='element' and source.get('dimension')==d
            if not valid:fail(path+'.location','sum over full domain cells',l,'Domain integrals need real aggregate support.')
            elif set(map(int,problem.arrays[source['ids']]))!=mesh['elements'][d]:fail(path+'.location','all domain cells',source,'Incomplete domain integral.')
        elif q in ('traction','heat_flux'):
            if l.get('kind')!='mesh' or l.get('entity')!='element' or l.get('dimension')!=d-1 or spec['value_kind']!='average':fail(path+'.location','boundary facet average',l,'Exchange observations are boundary averages.')
            else:
                try:
                    boundary_geometry(problem,spec['location'])
                    keys={frozenset(mesh['connectivity'][int(tag)][1]) for tag in problem.arrays[l['ids']]}
                    if cfg['family'].startswith('kinetic') and not keys<=gas_wall_keys:fail(path+'.location','gas_wall support',l,'Kinetic exchanges require wall-frame support.')
                except ValueError as exc:fail(path+'.location','exterior boundary',l,str(exc))
        elif l.get('kind')!='mesh' or l.get('entity')!='node' or spec['value_kind']!='point':fail(path+'.location','mesh node point',l,'State observations use mesh nodes.')
        t=problem.arrays[m['time_axes'][spec['time_axis']]]
        if cfg['transient']:
            if t[0]<p.get('start_time',0) or t[-1]>p.get('end_time',0):fail(path+'.time_axis','within physical interval',t,'Output interval mismatch.')
        elif len(t)!=1 or t[0]!=0:fail(path+'.time_axis','[0]',t,'Steady output time label required.')
    core={'pressure'} if cfg['family'].startswith('film') else {'depth','velocity'} if cfg['family'] in ('water','water_dry') else {'lower_depth','upper_depth','lower_velocity','upper_velocity'} if cfg['family']=='water_two' else {'density','velocity','temperature'} if cfg['family'].startswith('kinetic') else {'velocity','pressure'}
    if 'oldroyd' in cfg['family']:core|={'conformation','polymer_stress'}
    if cfg['family']=='thixotropic':core|={'structure'}
    if cfg['family'] in ('thermal_carreau','thermal_oldroyd','film_thermal','slip_thermal'):core|={'temperature'}
    if cfg['family']=='film_cavitation':core|={'film_fraction'}
    if not core<=present:fail('$.outputs',sorted(core),sorted(present),'Required primary observations missing.')
