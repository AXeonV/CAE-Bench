"""Opt-in single-phase flow profile declarations and material/condition checks; never a CFD solver."""
import numpy as np

from .._geometry import boundary_geometry, exterior_facets
from caeoj.mesh_geometry import periodic_face_pairs
from caeoj.sdk import read_constant, sample_field, id_to_row

DENSITY = {
    'constant': {'density':'kg/m3'},
    'isothermal_ideal_gas': {'specific_gas_constant':'J/(kg.K)'},
    'linear_barotropic': {'reference_density':'kg/m3','reference_pressure':'Pa','sound_speed':'m/s'},
}
VISCOSITY = {
    'newtonian': {'dynamic_viscosity':'Pa.s'},
    'power_law': {'reference_viscosity':'Pa.s','reference_shear_rate':'1/s','power_index':'1',
                  'minimum_shear_rate':'1/s','maximum_shear_rate':'1/s'},
    'cross': {'zero_shear_viscosity':'Pa.s','infinite_shear_viscosity':'Pa.s','relaxation_time':'s','cross_exponent':'1'},
    'carreau': {'zero_shear_viscosity':'Pa.s','infinite_shear_viscosity':'Pa.s','relaxation_time':'s','power_index':'1'},
    'carreau_yasuda': {'zero_shear_viscosity':'Pa.s','infinite_shear_viscosity':'Pa.s','relaxation_time':'s','power_index':'1','transition_index':'1'},
}


def material_density(material, pressure, temperature):
    """Absolute pressure in Pa and temperature in K; return density in kg/m3."""
    law=material['density'];p={k:v['value'] for k,v in law['parameters'].items()}
    pressure=np.asarray(pressure,dtype=float)
    if np.any(~np.isfinite(pressure)):raise ValueError('Pressure must be finite')
    if law['kind']!='constant' and np.any(pressure<=0):raise ValueError('Compressible absolute pressure must be positive')
    if law['kind']=='constant':result=np.full_like(pressure,p['density'])
    elif law['kind']=='isothermal_ideal_gas':result=pressure/(p['specific_gas_constant']*temperature)
    else:result=p['reference_density']+(pressure-p['reference_pressure'])/p['sound_speed']/p['sound_speed']
    if np.any(~np.isfinite(result)) or np.any(result<=0):raise ValueError('State has nonpositive/nonfinite density')
    return result


def material_viscosity(material, shear_rate):
    """Dynamic viscosity in Pa.s; shear_rate=sqrt(2 D:D), nonnegative in 1/s."""
    law=material['viscosity'];p={k:v['value'] for k,v in law['parameters'].items()}
    g=np.asarray(shear_rate,dtype=float)
    if np.any(~np.isfinite(g)) or np.any(g<0):raise ValueError('Shear rate must be finite and nonnegative')
    with np.errstate(over='raise',invalid='raise',divide='raise'):
        if law['kind']=='newtonian':mu=np.full_like(g,p['dynamic_viscosity'])
        elif law['kind']=='power_law':
            g=np.clip(g,p['minimum_shear_rate'],p['maximum_shear_rate'])
            mu=p['reference_viscosity']*(g/p['reference_shear_rate'])**(p['power_index']-1)
        else:
            x=p['relaxation_time']*g
            if law['kind']=='cross':factor=1/(1+x**p['cross_exponent'])
            else:
                a=p.get('transition_index',2.)
                factor=(1+x**a)**((p['power_index']-1)/a)
            mu=p['infinite_shear_viscosity']+(p['zero_shear_viscosity']-p['infinite_shear_viscosity'])*factor
    if np.any(~np.isfinite(mu)) or np.any(mu<=0):raise ValueError('Material has nonpositive/nonfinite viscosity')
    return mu


def check_cfd(problem, errors):
    """Check declared units, ranges, coverage, references and compatibility.

    Does not establish mesh quality, well-posedness, absence of outlet backflow,
    laminar validity, existence of a steady solution or numerical accuracy.
    """
    from caeoj.validation import issue
    m=problem.manifest;a=m['analysis'];d=m['spatial_dimension'];locs=m['locations']
    def fail(path,expected,actual,message):errors.append(issue('E_CFD',path,expected,actual,message))
    def constant(value,unit,path,positive=False):
        if set(value)!={'value','unit'}:
            fail(path,'scalar constant',value,'Expected a constant.');return None
        if value['unit']!=unit:fail(path+'.unit',unit,value['unit'],'CFD units are canonical; no conversion.')
        v=value['value']
        if positive and v<=0:fail(path,'positive value',v,'Invalid material/state parameter.')
        return v
    def region(name,dimension,path):
        loc=locs.get(name)
        if not loc or loc['kind']!='mesh' or loc['entity']!='element' or loc['dimension']!=dimension:
            fail(path,f'mesh element region of dimension {dimension}',name,'Invalid region.');return None
        return loc
    if 'physics' in m:fail('$.physics','analysis and materials only',m['physics'],'Avoid conflicting physical declarations in the CFD profile.')
    if d not in (2,3):fail('$.spatial_dimension','2 or 3',d,'single-phase flow profile supports planar 2D and full 3D.');return
    if len(m['meshes'])!=1:fail('$.meshes','one fluid mesh',list(m['meshes']),'single-phase flow profile uses one fixed mesh.');return
    mesh_name=next(iter(m['meshes']));mesh=problem.meshes[mesh_name]
    if mesh['dimension']!=d:fail('$.meshes','full-dimensional fluid cells',mesh['dimension'],'Missing fluid volume.');return
    try:exterior=exterior_facets(mesh,d)
    except ValueError as exc:fail('$.meshes','supported first-order manifold cells',str(exc),'Invalid CFD topology.');return
    temperature=constant(a['temperature'],'K','$.analysis.temperature',True)
    pressure=a['pressure'];offset=0.
    if pressure['representation']=='gauge':
        if 'reference_pressure' not in pressure:fail('$.analysis.pressure','reference_pressure in Pa',pressure,'Gauge pressure needs an absolute reference.')
        else:offset=constant(pressure['reference_pressure'],'Pa','$.analysis.pressure.reference_pressure',True)
    elif 'reference_pressure' in pressure:fail('$.analysis.pressure','no reference_pressure for absolute representation',pressure,'Avoid ambiguous pressure references.')
    transient=a['type']=='transient';window=a.get('time_interval')
    if transient:
        if not window or window['end']<=window['start']:
            fail('$.analysis.time_interval','start < end, in seconds',window,'Transient interval required.');return
        start,end=window['start'],window['end']
    else:
        if window:fail('$.analysis.time_interval','absent for steady analysis',window,'Steady state has no physical integration interval.')
        start=end=0.
    material=next(iter(m['materials'].values()));mat_path='$.materials.'+next(iter(m['materials']))
    domain=region(material['region'],d,mat_path+'.region')
    if domain and (domain['mesh']!=mesh_name or set(map(int,problem.arrays[domain['ids']]))!=mesh['elements'][d]):
        fail(mat_path+'.region','all fluid cells exactly once',material['region'],'Single material must cover the fluid domain.')
    for key,specs in (('density',DENSITY),('viscosity',VISCOSITY)):
        law=material[key];params=law['parameters'];expected=dict(specs[law['kind']])
        if key=='viscosity' and law['kind']=='newtonian' and a['compressibility']=='isothermal_compressible':expected['bulk_viscosity']='Pa.s'
        if set(params)!=set(expected):fail(mat_path+'.'+key+'.parameters',sorted(expected),sorted(params),'Exact parameter set required.');continue
        for name,unit in expected.items():
            v=constant(params[name],unit,mat_path+'.'+key+'.parameters.'+name,name!='bulk_viscosity')
            if name=='bulk_viscosity' and v<0:fail(mat_path+'.viscosity.parameters.bulk_viscosity','nonnegative',v,'Invalid bulk viscosity.')
    visc=material['viscosity'];vp={k:v['value'] for k,v in visc['parameters'].items()}
    if visc['kind']=='power_law' and all(k in vp for k in VISCOSITY['power_law']):
        if not vp['minimum_shear_rate']<=vp['reference_shear_rate']<=vp['maximum_shear_rate']:
            fail(mat_path+'.viscosity','min <= reference <= max shear rate',vp,'Inconsistent physical cutoff range.')
    if visc['kind'] in ('carreau','carreau_yasuda') and vp.get('power_index',1)>1:
        fail(mat_path+'.viscosity.parameters.power_index','0 < n <= 1',vp['power_index'],'Plateau response in this profile is shear-thinning.')
    if 'zero_shear_viscosity' in vp and 'infinite_shear_viscosity' in vp and vp['zero_shear_viscosity']<vp['infinite_shear_viscosity']:
        fail(mat_path+'.viscosity','mu_zero >= mu_infinite',vp,'This profile supports shear-thinning plateau laws.')
    compressible=a['compressibility']=='isothermal_compressible'
    if compressible:
        if material['density']['kind']=='constant':fail(mat_path+'.density','compressible density response','constant','Compressible flow needs a density response.')
        if visc['kind']!='newtonian':fail(mat_path+'.viscosity','newtonian',visc['kind'],'Non-Newtonian compressible flow is outside the isothermal single-phase contract.')
        if 'pressure_gauge' in a:fail('$.analysis.pressure_gauge','absent',a['pressure_gauge'],'Compressible pressure is fixed by physical state.')
    elif material['density']['kind']!='constant':fail(mat_path+'.density','constant',material['density']['kind'],'Incompressible material has constant density.')
    for name,spec in m['fields'].items():
        path='$.fields.'+name;sampling=spec.get('sampling');loc=locs[spec['location']]
        if not sampling:fail(path+'.sampling','explicit sampling',None,'Input samples need continuous interpretation.');continue
        t=problem.arrays[m['time_axes'][spec['time_axis']]];values=problem.arrays[spec['array']]
        if sampling['space']=='uniform' and not np.all(values==values[:,:1]):fail(path+'.sampling.space','spatially uniform samples',name,'Uniform samples disagree.')
        if sampling['space']=='piecewise_constant' and (loc['kind']!='mesh' or loc['entity']!='element'):
            fail(path+'.sampling.space','element region',loc,'Piecewise constant data are entity averages.')
        if sampling['space']=='piecewise_linear' and (loc['kind']!='mesh' or loc['entity']!='node'):
            fail(path+'.sampling.space','mesh nodes',loc,'Piecewise linear data need mesh connectivity.')
        if sampling['space']=='piecewise_linear':
            if any(typ not in (1,2,4,15) for typ,conn in mesh['connectivity'].values()):
                fail(path+'.sampling.space','linear simplex mesh',name,'Use uniform/cell data for non-simplex meshes.')
        if sampling['time']=='constant':
            if len(t)!=1 or t[0]!=start:fail(path+'.time_axis',f'one sample at {start}',t,'Constant data apply throughout the interval.')
        else:
            if sampling['time']=='linear' and spec['dtype']!='float64':fail(path+'.dtype','float64 for linear interpolation',spec['dtype'],'Do not interpolate categorical/integer data.')
            if not transient or len(t)<2:fail(path+'.sampling.time','transient with >=2 samples',t,'Invalid temporal reconstruction.')
            if sampling['extrapolation']=='forbid' and (t[0]>start or t[-1]<end):fail(path+'.time_axis','coverage of analysis interval',t,'No extrapolation is allowed.')
    def density_state(value,path):
        law=material['density']
        if value is None or law['kind']!='linear_barotropic':return
        dp={k:v['value'] for k,v in law['parameters'].items()}
        if set(dp)!=set(DENSITY['linear_barotropic']):return
        with np.errstate(over='ignore',invalid='ignore'):
            absolute=dp['reference_pressure']+((np.asarray(value)-dp['reference_density'])*dp['sound_speed'])*dp['sound_speed']
        if np.any(~np.isfinite(absolute)) or np.any(absolute<=0):fail(path,'positive finite absolute pressure',value,'Density lies outside the material response domain.')

    # Data access validates physical quantity shapes and canonical units.
    def data(value,unit,kind,location,path,positive=False):
        if 'value' in value:
            if kind!='scalar':fail(path,'explicit vector field',value,'Vectors use HDF5 fields.');return None
            v=constant(value,unit,path,positive)
            if unit=='kg/m3':density_state(v,path)
            return np.asarray(v)
        if 'field' not in value:fail(path,'constant or field',value,'Expected numerical condition data.');return None
        spec=m['fields'][value['field']]
        if spec['unit']!=unit or spec['kind']!=kind or spec['dtype']!='float64':fail(path,f'float64 {kind} in {unit}',spec,'Invalid CFD condition field.')
        loc=locs[spec['location']]
        expected_value_kind='point' if loc.get('entity')=='node' else 'average'
        if spec['value_kind']!=expected_value_kind:fail(path,expected_value_kind,spec['value_kind'],'Condition data are physical values, not entity integrals.')
        values=problem.arrays[spec['array']]
        if unit=='kg/m3':density_state(values,path)
        if positive and np.any(values<=0):fail(path,'positive values',value,'Nonpositive physical data.')
        return values
    def keys(actual,required,optional,path):
        if not set(required)<=set(actual) or set(actual)-set(required)-set(optional):
            fail(path,{'required':required,'optional':optional},list(actual),'Invalid condition parameters.');return False
        return True
    boundary_seen=set();facet_seen=set();initial=set();anchored=False;density_anchored=False;periodic={}
    for i,c in enumerate(m['conditions']):
        path=f'$.conditions[{i}]';name=c['location'];role=c['role'];op=c['operator'];values=c['data']
        if role=='material':fail(path,'material table only',c,'Do not duplicate material declarations.');continue
        if role in ('initial','source'):
            loc=region(name,d,path+'.location')
            if loc and set(map(int,problem.arrays[loc['ids']]))!=mesh['elements'][d]:fail(path+'.location','full fluid domain',name,'Initial/source fields cover the domain.')
            if role=='source':
                if c['variable']!='velocity' or op!='acceleration':fail(path,'source/velocity/acceleration',c,'Unsupported source.');continue
                if keys(values,['value'],[],path+'.data'):data(values['value'],'m/s2','vector',name,path+'.data.value')
                continue
            if not transient or op!='assign' or c['variable'] not in (('velocity','density') if compressible else ('velocity',)):
                fail(path,'transient initial velocity (and compressible density)',c,'Pressure is not an independent initial condition.');continue
            if c['variable'] in initial:fail(path,'one initial condition per quantity',c['variable'],'Duplicate initial state.')
            initial.add(c['variable'])
            if keys(values,['value'],[],path+'.data'):
                variable=c['variable'];value=data(values['value'],'m/s' if variable=='velocity' else 'kg/m3','vector' if variable=='velocity' else 'scalar',name,path+'.data.value',variable=='density')
                if 'field' in values['value']:
                    spec=m['fields'][values['value']['field']];t=problem.arrays[m['time_axes'][spec['time_axis']]]
                    if len(t)!=1 or t[0]!=start:fail(path,'one initial sample at start',t,'Initial data are not an evolving boundary condition.')
            continue
        if role!='boundary':fail(path,'supported CFD role',role,'Unsupported condition.');continue
        loc=region(name,d-1,path+'.location')
        if not loc:continue
        ids=problem.arrays[loc['ids']]
        if name in boundary_seen:fail(path,'one boundary declaration per location',name,'Duplicate boundary.')
        boundary_seen.add(name)
        try:
            boundary_geometry(problem,name)
            for tag in ids:
                key=frozenset(mesh['connectivity'][int(tag)][1])
                if key in facet_seen:fail(path,'non-overlapping exterior facets',int(tag),'Boundary regions overlap.')
                facet_seen.add(key)
        except ValueError as exc:fail(path+'.location','valid exterior boundary',str(exc),'Invalid boundary geometry.')
        if c['variable']!='flow':fail(path+'.variable','flow',c['variable'],'CFD boundaries jointly describe the flow condition.')
        if op in ('no_slip','slip','symmetry'):
            keys(values,[],[],path+'.data')
        elif op in ('velocity','moving_wall'):
            required=['velocity']+(['density'] if compressible and op=='velocity' else [])
            if keys(values,required,[],path+'.data'):
                velocity=data(values['velocity'],'m/s','vector',name,path+'.data.velocity')
                if op=='moving_wall' and velocity is not None:
                    try:
                        from . import condition_values
                        _,normal,_=boundary_geometry(problem,name)
                        spec=m['fields'][values['velocity']['field']]
                        times=problem.arrays[m['time_axes'][spec['time_axis']]]
                        for time in times:
                            v=condition_values(problem,c,'velocity',float(time))
                            if not np.allclose(np.sum(v*normal,axis=-1),0.,rtol=0,atol=1e-12):fail(path+'.data.velocity','tangential velocity on fixed geometry',values['velocity'],'Normal wall motion needs moving geometry, outside single-phase flow profile.')
                    except (ValueError,KeyError):pass
                if compressible and op=='velocity':
                    density_anchored=True
                    data(values['density'],'kg/m3','scalar',name,path+'.data.density',True)
        elif op=='pressure_outlet':
            anchored=True
            if keys(values,['pressure','backflow'],[],path+'.data'):
                if values['backflow']!={'option':'forbid'}:fail(path+'.data.backflow',{'option':'forbid'},values['backflow'],'Only outflow-only outlets in single-phase flow profile.')
                p=data(values['pressure'],'Pa','scalar',name,path+'.data.pressure')
                if compressible and p is not None:
                    try:material_density(material,p+offset,temperature)
                    except (ValueError,KeyError) as exc:fail(path,'valid density response',str(exc),'Invalid outlet state.')
                    if np.any(p+offset<=0):fail(path,'positive absolute pressure',p,'Invalid compressible pressure.')
        elif op=='traction':
            anchored=True
            if keys(values,['traction'],[],path+'.data'):data(values['traction'],'Pa','vector',name,path+'.data.traction')
            if compressible:fail(path,'pressure_outlet for compressible open boundary',op,'Traction-only compressible open state is outside this profile.')
        elif op=='flow_rate':
            if keys(values,['rate','shape']+(['density'] if compressible else []),[],path+'.data'):
                data(values['rate'],'m2/s' if d==2 else 'm3/s','scalar',name,path+'.data.rate',True)
                if 'field' in values['rate'] and m['fields'][values['rate']['field']].get('sampling',{}).get('space')!='uniform':fail(path+'.data.rate','uniform rate over the region',values['rate'],'A global flow rate cannot vary spatially.')
                data(values['shape'],'1','scalar',name,path+'.data.shape',True)
                if compressible:
                    density_anchored=True
                    data(values['density'],'kg/m3','scalar',name,path+'.data.density',True)
        elif op=='periodic':
            required=['partner']+[f'translation_{x}' for x in 'xyz'[:d]]
            if keys(values,required,[],path+'.data'):
                if set(values['partner'])!={'location'}:fail(path+'.data.partner','location reference',values['partner'],'Periodic boundary needs another region.');continue
                periodic[name]=values['partner']['location']
                for x in 'xyz'[:d]:constant(values[f'translation_{x}'],'m',path+'.data.translation_'+x)
        else:fail(path+'.operator','registered CFD boundary operator',op,'Unknown CFD boundary.')
    if facet_seen!=set(exterior):fail('$.conditions','exact coverage of exterior facets',len(facet_seen),'Missing or invalid exterior boundary coverage.')
    if transient and initial!=({'velocity','density'} if compressible else {'velocity'}):fail('$.conditions','complete initial state',sorted(initial),'Missing initial conditions.')
    for name,partner in periodic.items():
        if partner==name or periodic.get(partner)!=name:fail('$.conditions','reciprocal periodic partners',{'region':name,'partner':partner},'Periodic pair is incomplete.');continue
        records={c['location']:c for c in m['conditions'] if c['role']=='boundary'}
        try:
            delta=np.array([records[name]['data'][f'translation_{x}']['value'] for x in 'xyz'[:d]])
            other=np.array([records[partner]['data'][f'translation_{x}']['value'] for x in 'xyz'[:d]])
            if not np.allclose(delta,-other,rtol=0,atol=1e-12):raise ValueError('Periodic translations must be opposite')
            periodic_face_pairs(problem,name,partner,delta)
        except (ValueError,KeyError) as exc:fail('$.conditions','matching translational periodic facets',str(exc),'Invalid periodic map.')
    inventory=a.get('mean_density')
    needs_inventory=compressible and not transient and not (anchored or density_anchored)
    if needs_inventory:
        if inventory is None:
            fail('$.analysis.mean_density','positive mean density in kg/m3',None,
                 'Closed/periodic compressible steady flow needs physical mass inventory.')
        else:
            mean_density=constant(inventory,'kg/m3','$.analysis.mean_density',True)
            if mean_density is not None and material['density']['kind']=='linear_barotropic':
                parameters=material['density']['parameters']
                if all(k in parameters for k in DENSITY['linear_barotropic']):
                    dp={k:v['value'] for k,v in parameters.items()}
                    mean_pressure=dp['reference_pressure']+(mean_density-dp['reference_density'])*float(dp['sound_speed'])*float(dp['sound_speed'])
                    if not np.isfinite(mean_pressure) or mean_pressure<=0:
                        fail('$.analysis.mean_density','mean state with positive absolute pressure',mean_density,
                             'Mean density is outside the linear material response domain.')
    elif inventory is not None:
        fail('$.analysis.mean_density','absent for incompressible/transient/open-anchored flow',inventory,
             'Do not duplicate the pressure/density boundary state or transient mass inventory.')
    gauge=a.get('pressure_gauge')
    if not compressible:
        if anchored and gauge:fail('$.analysis.pressure_gauge','absent with pressure/traction boundary',gauge,'Do not overconstrain pressure.')
        if not anchored and not gauge:fail('$.analysis.pressure_gauge','explicit pressure constraint',None,'Closed/velocity-driven flow needs a pressure gauge.')
        if gauge:
            constant(gauge['value'],'Pa','$.analysis.pressure_gauge.value')
            if gauge['kind']=='mean':
                if gauge['location']!=material['region']:fail('$.analysis.pressure_gauge.location','fluid material region',gauge['location'],'Mean is a volume/area mean.')
            else:
                g=locs.get(gauge['location'])
                if not g or g['kind']!='points' or len(problem.arrays[g['ids']])!=1:fail('$.analysis.pressure_gauge.location','one independent probe',gauge['location'],'Point gauge needs an explicit point.')
    units={'velocity':'m/s','pressure':'Pa','density':'kg/m3','dynamic_viscosity':'Pa.s','shear_rate':'1/s','traction':'Pa',
           'force':'N/m' if d==2 else 'N','volume_flow':'m2/s' if d==2 else 'm3/s','mass_flow':'kg/(m.s)' if d==2 else 'kg/s'}
    for name,spec in m['outputs'].items():
        path='$.outputs.'+name;q=spec['quantity'];loc=locs[spec['location']]
        if q not in units:fail(path+'.quantity',list(units),q,'Unknown CFD observation.');continue
        if spec['unit']!=units[q] or spec['dtype']!='float64':fail(path,f'float64 in {units[q]}',spec,'Invalid CFD output representation.')
        kind='vector' if q in ('velocity','traction','force') else 'scalar'
        if spec['kind']!=kind:fail(path+'.kind',kind,spec['kind'],'Invalid output components.')
        if q in ('force','volume_flow','mass_flow'):
            if loc['kind']!='aggregate' or loc['operation']!='sum':fail(path+'.location','sum aggregate on boundary',loc,'Integrated engineering quantity needs aggregate region.')
            elif not region(loc['source'],d-1,path+'.location.source'):pass
            else:
                try:boundary_geometry(problem,loc['source'])
                except ValueError as exc:fail(path+'.location.source','exterior facets',str(exc),'Invalid observation boundary.')
        elif loc['kind']=='aggregate':
            if q not in ('pressure','velocity','density','dynamic_viscosity','shear_rate') or loc['operation']!='mean':fail(path+'.location','mean aggregate for intensive quantities',loc,'Invalid aggregate observation.')
        if q not in ('force','volume_flow','mass_flow') and loc['kind']=='mesh' and loc['entity']=='element' and spec['value_kind']!='average':fail(path+'.value_kind','average',spec['value_kind'],'Intensive quantities are not entity integrals.')
        if q=='traction' and not region(spec['location'],d-1,path+'.location'):pass
        t=problem.arrays[m['time_axes'][spec['time_axis']]]
        if transient:
            if t[0]<start or t[-1]>end:fail(path+'.time_axis','within analysis interval',t,'Output times outside physical interval.')
        elif len(t)!=1 or t[0]!=0:fail(path+'.time_axis','[0] steady sentinel',t,'Steady output uses one nonphysical sentinel time.')


def absolute_pressure(problem, pressure):
    """Convert CFD profile pressure values to absolute Pa, preserving shape."""
    spec = problem.manifest['analysis']['pressure']
    offset = spec['reference_pressure']['value'] if spec['representation']=='gauge' else 0.
    return np.asarray(pressure) + offset



def fluid_material(problem):
    """Return the single material description of a validated single-phase flow profile problem."""
    if problem.manifest.get('profile') != 'cfd-2.1':
        raise ValueError('Expected cfd-2.1 profile')
    return next(iter(problem.manifest['materials'].values()))



def density_at_pressure(problem, pressure):
    """Evaluate declared material response; input follows profile pressure representation."""
    return material_density(fluid_material(problem), absolute_pressure(problem, pressure),
                            problem.manifest['analysis']['temperature']['value'])



def dynamic_viscosity(problem, shear_rate):
    """Evaluate declared dynamic viscosity at sqrt(2 D:D) in inverse seconds."""
    return material_viscosity(fluid_material(problem), shear_rate)



def condition_values(problem, condition, parameter, time):
    """Read numerical CFD condition data on its region's element rows.

    Scalars stay scalars. Nodal input is averaged over each linear simplex;
    uniform nodal data also work on other supported first-order cells. This is
    the exact entity average of the declared linear/uniform reconstruction.
    """
    value=condition['data'][parameter]
    if 'value' in value:return read_constant(value)
    if set(value)!={'field'}:raise TypeError('Expected a numerical condition value')
    spec=problem.manifest['fields'][value['field']]
    sampled=sample_field(problem,value['field'],time)
    if spec['location']==condition['location']:return sampled
    source=problem.manifest['locations'][spec['location']]
    target=problem.manifest['locations'][condition['location']]
    if (source['kind']!='mesh' or source['entity']!='node' or target['kind']!='mesh'
            or target['entity']!='element' or source['mesh']!=target['mesh']):
        raise ValueError('Condition requires the exact nodes of its element region')
    rows=id_to_row(problem.arrays[source['ids']]);mesh=problem.meshes[source['mesh']]
    return np.array([np.mean([sampled[rows[n]] for n in mesh['connectivity'][int(tag)][1]],axis=0)
                     for tag in problem.arrays[target['ids']]])



def periodic_condition_pairs(problem, condition):
    """Return (this-side facet ID, partner facet ID) pairs for a periodic condition."""
    from caeoj.mesh_geometry import periodic_face_pairs as pair
    if condition['operator']!='periodic':raise ValueError('Expected a periodic boundary')
    d=problem.manifest['spatial_dimension'];data=condition['data']
    return pair(problem,condition['location'],data['partner']['location'],
                [read_constant(data['translation_'+x]) for x in 'xyz'[:d]])



def check(problem, errors):
    if problem.manifest.get("profile") == "cfd-2.1":
        check_cfd(problem, errors)


def condition_location_compatible(problem, condition, spec):
    """Accept exactly the nodes of a declared element-region condition."""
    if spec['location'] == condition['location']:
        return True
    locations = problem.manifest['locations']
    source = locations.get(spec['location'], {})
    target = locations.get(condition['location'], {})
    if not (source.get('kind') == target.get('kind') == 'mesh' and
            source.get('entity') == 'node' and target.get('entity') == 'element' and
            source['mesh'] == target['mesh']):
        return False
    mesh = problem.meshes.get(source['mesh'], {})
    tags = problem.arrays.get(target['ids'], [])
    connectivity = mesh.get('connectivity', {})
    nodes = {node for tag in tags if int(tag) in connectivity
             for node in connectivity[int(tag)][1]}
    ids = problem.arrays.get(source['ids'], [])
    return set(map(int, ids)) == nodes and bool(nodes)
