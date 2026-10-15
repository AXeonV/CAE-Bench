"""Opt-in finite multiphase declarations, not a multiphase solver.

Public semantics: docs/FLUID-MULTIPHASE.md. Generic structure/reference checks
must succeed before this checker runs. No legacy input is reinterpreted.
"""
import numpy as np

PREFIX = 'fluid-multiphase-'
MODELS = {
    'free-surface': (2, 3), 'immiscible': (2, 3), 'wetting': (2, 3),
    'passive-particles': (3,), 'coupled-particles': (3,),
    'bubbles-droplets': (3,), 'dense-dispersed': (3,),
    'interphase-exchange': (3,), 'evaporation-condensation': (2,),
    'boiling': (3,), 'cavitation': (3,), 'melting-solidification': (2,),
}
DISPERSED = {'passive-particles', 'coupled-particles', 'bubbles-droplets', 'dense-dispersed'}
THERMAL = {'interphase-exchange', 'evaporation-condensation', 'boiling', 'melting-solidification'}
OPEN_REQUIRED = {'evaporation-condensation', 'boiling', 'cavitation'}
# unit, lower bound, whether equality is allowed
BASE_PARAMETERS = {
    'time_start': ('s', None, True), 'time_end': ('s', None, True),
    'density_a': ('kg/m3', 0, False), 'viscosity_a': ('Pa.s', 0, False),
    'pressure_reference': ('Pa', 0, False),
}
PARAMETERS = {
    'free-surface': {},
    'immiscible': {'density_b': ('kg/m3',0,False),'viscosity_b': ('Pa.s',0,False)},
    'wetting': {'density_b': ('kg/m3',0,False),'viscosity_b': ('Pa.s',0,False),
                'surface_tension': ('N/m',0,False),'contact_angle': ('rad',0,False),'slip_length': ('m',0,False)},
    'passive-particles': {'density_b': ('kg/m3',0,False),'relaxation_time': ('s',0,False),'diameter': ('m',0,False)},
    'coupled-particles': {'density_b': ('kg/m3',0,False),'relaxation_time': ('s',0,False),'diameter': ('m',0,False)},
    'bubbles-droplets': {'density_b': ('kg/m3',0,False),'viscosity_b': ('Pa.s',0,False),'relaxation_time': ('s',0,False),'diameter': ('m',0,False)},
    'dense-dispersed': {'density_b': ('kg/m3',0,False),'relaxation_time': ('s',0,False),'diameter': ('m',0,False),
                        'packing_fraction': ('1',0,False),'particle_modulus': ('Pa',0,False)},
    'interphase-exchange': {'density_b': ('kg/m3',0,False),'viscosity_b': ('Pa.s',0,False),
        'heat_capacity_a': ('J/(kg.K)',0,False),'heat_capacity_b': ('J/(kg.K)',0,False),
        'conductivity_a': ('W/(m.K)',0,False),'conductivity_b': ('W/(m.K)',0,False),
        'heat_exchange': ('W/(m3.K)',0,True),'mass_exchange': ('1/s',0,True),
        'diffusivity_a': ('m2/s',0,False),'diffusivity_b': ('m2/s',0,False)},
    'evaporation-condensation': {'density_b': ('kg/m3',0,False),'viscosity_b': ('Pa.s',0,False),
        'heat_capacity_a': ('J/(kg.K)',0,False),'heat_capacity_b': ('J/(kg.K)',0,False),
        'conductivity_a': ('W/(m.K)',0,False),'conductivity_b': ('W/(m.K)',0,False),
        'latent_heat': ('J/kg',0,False),'saturation_temperature': ('K',0,False),
        'interface_mass_coefficient': ('kg/(m2.s.K)',0,False)},
    'boiling': {'density_b': ('kg/m3',0,False),'viscosity_b': ('Pa.s',0,False),
        'heat_capacity_a': ('J/(kg.K)',0,False),'heat_capacity_b': ('J/(kg.K)',0,False),
        'conductivity_a': ('W/(m.K)',0,False),'conductivity_b': ('W/(m.K)',0,False),
        'latent_heat': ('J/kg',0,False),'saturation_temperature': ('K',0,False),
        'evaporation_frequency': ('1/s',0,False),'condensation_frequency': ('1/s',0,False)},
    'cavitation': {'density_b': ('kg/m3',0,False),'viscosity_b': ('Pa.s',0,False),
        'saturation_pressure': ('Pa',0,False),'pressure_rate': ('kg/(m3.s.Pa)',0,False),
        'nuclei_fraction': ('1',0,False)},
    'melting-solidification': {'heat_capacity_a': ('J/(kg.K)',0,False),
        'conductivity_a': ('W/(m.K)',0,False),'latent_heat': ('J/kg',0,False),
        'solidus_temperature': ('K',0,False),'liquidus_temperature': ('K',0,False),
        'mushy_resistance': ('kg/(m3.s)',0,False),'mushy_epsilon': ('1',0,False)},
}
QUANTITIES = {
    'alpha': ('1','scalar'), 'velocity': ('m/s','vector'), 'pressure': ('Pa','scalar'),
    'flux_a': ('m/s','vector'), 'flux_b': ('m/s','vector'),
    'acceleration': ('m/s2','vector'), 'temperature': ('K','scalar'),
    'temperature_a': ('K','scalar'), 'temperature_b': ('K','scalar'),
    'concentration_a': ('kg/m3','scalar'), 'concentration_b': ('kg/m3','scalar'),
    'phase_change_rate': ('kg/(m3.s)','scalar'),
}


def model_kind(problem):
    model = problem.manifest.get('physics', {}).get('model', '')
    if not model.startswith(PREFIX) or not model.endswith('-v1'):
        raise ValueError('Expected a versioned fluid-multiphase model')
    kind = model[len(PREFIX):-3]
    if kind not in MODELS:
        raise ValueError('Unknown fluid-multiphase model')
    return kind


def multiphase_parameters(problem):
    """Read explicit parameters of a validated model; no units/default conversion."""
    model_kind(problem)
    return {key: value['value'] for key, value in problem.manifest['physics']['parameters'].items()}


def multiphase_phase_mass(problem, alpha, cell_measures, phase='a'):
    """Integrate alpha*rho (a) or (1-alpha)*rho (b), last axis = cells.

    Measures are caller-supplied physical cell volumes (areas per unit depth in
    2D); this function does not guess geometry or silently squeeze field axes.
    """
    kind = model_kind(problem)
    if phase not in ('a','b') or (phase == 'b' and kind == 'free-surface'):
        raise ValueError('Unavailable phase')
    a = np.asarray(alpha); w = np.asarray(cell_measures)
    if w.ndim != 1 or a.ndim < 1 or a.shape[-1] != len(w):
        raise ValueError('Expected alpha [...,N] and measures [N]')
    if not np.all(np.isfinite(a)) or np.any((a<0)|(a>1)) or not np.all(np.isfinite(w)) or np.any(w<=0):
        raise ValueError('Invalid fractions or measures')
    p = multiphase_parameters(problem)
    rho = p['density_a'] if phase == 'a' or kind == 'melting-solidification' else p['density_b']
    return np.sum((a if phase == 'a' else 1-a)*w,axis=-1)*rho


def required_initial(kind):
    values = {'alpha', 'flux_a', 'flux_b'} if kind in DISPERSED else {'alpha','velocity'}
    if kind == 'interphase-exchange':
        values |= {'temperature_a','temperature_b','concentration_a','concentration_b'}
    elif kind in THERMAL:
        values.add('temperature')
    if kind == 'melting-solidification':
        values.remove('alpha')  # derived uniquely from initial temperature
    return values


def required_outputs(kind):
    values = required_initial(kind) | {'pressure','alpha'}
    if kind in OPEN_REQUIRED or kind == 'melting-solidification':
        values.add('phase_change_rate')
    return values


def check_fluid_multiphase(problem, errors):
    """Append E_FLUID issues after successful generic checks."""
    from .validation import issue
    from .mesh_geometry import exterior_facets, boundary_geometry
    m = problem.manifest
    model = m.get('physics',{}).get('model','')
    if not model.startswith(PREFIX):
        return
    def fail(path, expected, actual, message='Invalid multiphase declaration.'):
        errors.append(issue('E_FLUID',path,expected,actual,message))
    try:
        kind = model_kind(problem)
    except ValueError as exc:
        fail('$.physics.model',sorted(PREFIX+k+'-v1' for k in MODELS),model,str(exc));return
    if any(k in m for k in ('contract_version','profile','analysis','materials')):
        fail('$','legacy structure plus versioned physics.model','mixed CFD profile');return
    d = m['spatial_dimension']; locs = m['locations']; arrays = problem.arrays
    if d not in MODELS[kind]:
        fail('$.spatial_dimension',MODELS[kind],d)
    expected = BASE_PARAMETERS | PARAMETERS[kind]
    params = m['physics'].get('parameters',{})
    if set(params) != set(expected):
        fail('$.physics.parameters',sorted(expected),sorted(params));return
    for name,(unit,lower,inclusive) in expected.items():
        value = params[name]
        if set(value) != {'value','unit'} or value['unit'] != unit:
            fail('$.physics.parameters.'+name,{'unit':unit},value)
        x = value.get('value')
        if not isinstance(x,(int,float)) or isinstance(x,bool) or not np.isfinite(x) or (lower is not None and (x < lower if inclusive else x <= lower)):
            fail('$.physics.parameters.'+name,('>=' if inclusive else '>')+str(lower),x)
    if errors:return
    p = multiphase_parameters(problem); start,end = p['time_start'],p['time_end']
    if end <= start: fail('$.physics.parameters.time_end','> time_start',end)
    if kind=='wetting' and p['contact_angle']>=np.pi:
        fail('$.physics.parameters.contact_angle','0 < theta < pi',p['contact_angle'])
    if kind=='dense-dispersed' and p['packing_fraction']>=1:
        fail('$.physics.parameters.packing_fraction','0 < alpha_max < 1',p['packing_fraction'])
    if kind=='cavitation' and p['nuclei_fraction']>=1:
        fail('$.physics.parameters.nuclei_fraction','0 < nuclei_fraction < 1',p['nuclei_fraction'])
    if kind=='melting-solidification' and p['liquidus_temperature']<=p['solidus_temperature']:
        fail('$.physics.parameters.liquidus_temperature','> solidus_temperature',p['liquidus_temperature'])
    if len(m['meshes'])!=1:
        fail('$.meshes','exactly one fixed mesh',list(m['meshes']));return
    mesh_name = next(iter(m['meshes'])); mesh = problem.meshes[mesh_name]
    if mesh['dimension']!=d or 'connectivity' not in mesh:
        fail('$.meshes','D-dimensional mesh loaded with geometry',mesh['dimension']);return
    initial = [c for c in m['conditions'] if c['role']=='initial']
    if {c['variable'] for c in initial} != required_initial(kind) or len(initial)!=len(required_initial(kind)):
        fail('$.conditions','exactly one initial condition for '+str(sorted(required_initial(kind))),[c['variable'] for c in initial]);return
    domain = initial[0]['location']; domain_loc = locs[domain]
    def is_cells(location):
        l=locs[location]
        return l.get('kind')=='mesh' and l.get('entity')=='element' and l.get('dimension')==d and l.get('mesh')==mesh_name and set(map(int,arrays[l['ids']]))==mesh['elements'][d]
    if not is_cells(domain):
        fail('$.conditions','initial location covers every full-dimensional cell',domain);return
    if any(c['location']!=domain for c in initial):
        fail('$.conditions','one identical domain location for initial data','different locations')
    consumed = set(); initial_data = {}
    def numeric(data, quantity, location, initial_value=False):
        unit,shape = QUANTITIES[quantity]
        if set(data)=={'value','unit'}:
            if shape!='scalar' or data['unit']!=unit:
                fail('$.conditions.data',f'{quantity} field or scalar {unit}',data);return None
            value = np.asarray([data['value']])
        elif set(data)=={'field'}:
            name=data['field']; consumed.add(name); spec=m['fields'][name]
            if spec['quantity']!=quantity or spec['unit']!=unit or spec['kind']!=shape or spec['dtype']!='float64' or spec['location']!=location or spec['value_kind']!='average':
                fail('$.fields.'+name,f'{quantity}, {unit}, {shape}, float64 cell/facet average at {location}',spec)
            sampling=spec.get('sampling',{})
            if sampling.get('space') not in ('uniform','piecewise_constant') or sampling.get('time') not in ('constant','linear') or sampling.get('extrapolation')!='forbid':
                fail('$.fields.'+name+'.sampling','uniform/piecewise_constant; constant/linear; forbid',sampling)
            t=arrays[m['time_axes'][spec['time_axis']]]; value=arrays[spec['array']]
            if initial_value:
                if len(t)!=1 or t[0]!=start:fail('$.fields.'+name+'.time_axis','singleton time_start',t.tolist())
            elif sampling.get('time')=='constant':
                if len(t)!=1:fail('$.fields.'+name+'.time_axis','singleton for constant throughout interval',t.tolist())
            elif t[0]>start or t[-1]<end:
                fail('$.fields.'+name+'.time_axis','covers [time_start,time_end]',t.tolist())
            if sampling.get('space')=='uniform' and not np.all(value==value[:,:1]):
                fail('$.fields.'+name+'.sampling.space','identical values across location IDs','nonuniform')
        else:
            fail('$.conditions.data','numeric scalar or field',data);return None
        if quantity=='alpha' and np.any((value<0)|(value>1)):
            fail('$.conditions.data.alpha','0 <= alpha <= 1','out of range')
        if quantity.startswith('temperature') and np.any(value<=0):
            fail('$.conditions.data.'+quantity,'positive K','nonpositive')
        if quantity.startswith('concentration') and np.any(value<0):
            fail('$.conditions.data.'+quantity,'nonnegative kg/m3','negative')
        return value
    boundary_keys=set(); source_count=0; reservoir_count=0
    try: exterior = exterior_facets(mesh,d)
    except ValueError as exc:
        fail('$.meshes','first-order facet-connected manifold cells',str(exc));return
    for i,c in enumerate(m['conditions']):
        path=f'$.conditions[{i}]'; role=c['role']; op=c['operator']; data=c['data']; variable=c['variable']; location=c['location']
        if role=='initial':
            if op!='assign' or set(data)!={'value'}:
                fail(path,'initial assign with data.value only',c);continue
            initial_data[variable]=numeric(data['value'],variable,location,True)
        elif role=='source':
            source_count+=1
            if variable!='acceleration' or location!=domain or op!='assign' or set(data)!={'value'}:
                fail(path,'one acceleration source assign at initial domain location',c);continue
            numeric(data['value'],'acceleration',location)
        elif role=='boundary':
            l=locs[location]
            if variable!='flow' or l.get('kind')!='mesh' or l.get('entity')!='element' or l.get('dimension')!=d-1 or l.get('mesh')!=mesh_name:
                fail(path,'flow boundary on exterior facets of main mesh',c);continue
            try:
                boundary_geometry(problem,location)
            except ValueError as exc:
                fail(path,'nondegenerate first-order exterior facets',str(exc));continue
            for tag in arrays[l['ids']]:
                key=frozenset(mesh['connectivity'][int(tag)][1])
                if key in boundary_keys:fail(path,'one boundary condition per exterior facet','overlap')
                boundary_keys.add(key)
            if op=='wall':
                allowed={'mechanical'} | ({'temperature'} if 'temperature' in data else {'thermal'}) if kind in THERMAL else {'mechanical'}
                wanted='navier_wetting' if kind=='wetting' else 'no_slip'
                if set(data)!=allowed or data.get('mechanical')!={'option':wanted}:
                    fail(path,f'wall keys {sorted(allowed)} with mechanical={wanted}',data);continue
                if kind in THERMAL:
                    if 'temperature' in data:
                        if kind=='interphase-exchange':
                            # One thermostat acts on both phase temperatures.
                            numeric(data['temperature'],'temperature',location)
                        else:numeric(data['temperature'],'temperature',location)
                    elif data.get('thermal')!={'option':'adiabatic'}:
                        fail(path+'.data.thermal','option adiabatic',data.get('thermal'))
            elif op=='pressure_reservoir' and kind in OPEN_REQUIRED:
                reservoir_count+=1
                wanted={'alpha'} | ({'temperature'} if kind in THERMAL else set())
                if set(data)!=wanted:
                    fail(path,'reservoir incoming '+str(sorted(wanted)),data);continue
                for q in wanted:
                    values=numeric(data[q],q,location)
                    if kind=='evaporation-condensation' and q=='alpha' and values is not None:
                        # A sharp interface cannot be replaced by a fractional
                        # reservoir mixture or a time-interpolated phase label.
                        if np.any((values!=0)&(values!=1)):
                            fail(path+'.data.alpha','constant pure phase 0 or 1 per boundary facet','fractional reservoir phase')
                        if 'field' in data[q]:
                            spec=m['fields'][data[q]['field']]
                            if spec.get('sampling',{}).get('time')!='constant':
                                fail(path+'.data.alpha','time=constant pure-phase reservoir field',spec.get('sampling',{}))
            else:fail(path+'.operator','wall; pressure_reservoir only for evaporation/boiling/cavitation',op)
        else:fail(path+'.role','initial/source/boundary',role)
    if boundary_keys!=set(exterior):
        fail('$.conditions','exactly all exterior facets','missing or extra boundaries')
    if source_count!=1:fail('$.conditions','exactly one explicit acceleration source',source_count)
    if kind in OPEN_REQUIRED and reservoir_count==0:
        fail('$.conditions','at least one pressure_reservoir for phase volume expansion',0)
    if consumed != set(m['fields']):
        fail('$.fields','only fields referenced by conditions',sorted(set(m['fields'])-consumed))
    alpha=initial_data.get('alpha')
    if alpha is not None:
        if kind in {'free-surface','immiscible','wetting','evaporation-condensation'} and np.any((alpha!=0)&(alpha!=1)):
            fail('$.conditions.initial.alpha','binary cellwise initial sharp phase indicator',alpha.tolist())
        if kind in {'free-surface','immiscible','wetting','evaporation-condensation'} and (not np.any(alpha==0) or not np.any(alpha==1)):
            fail('$.conditions.initial.alpha','both pure phases present in initial mesh','one phase absent')
        if kind in DISPERSED:
            # alpha denotes carrier a; dispersed concentration is 1-alpha.
            maximum = p['packing_fraction'] if kind=='dense-dispersed' else .1
            if np.any(1-alpha>=maximum) or np.any(alpha<=0):
                fail('$.conditions.initial.alpha',f'0 <= dispersed fraction < {maximum}',alpha.tolist())
        if kind in DISPERSED:
            for q,fraction in [('flux_a',alpha),('flux_b',1-alpha)]:
                flux=initial_data.get(q)
                if flux is not None and np.any(np.where(fraction==0,flux,0)!=0):
                    fail('$.conditions.initial.'+q,'zero superficial flux where its phase is absent','nonzero')
        if kind=='interphase-exchange' and np.any((alpha<=0)|(alpha>=1)):
            fail('$.conditions.initial.alpha','strictly mixed 0 < alpha < 1',alpha.tolist())
    output_quantities=[]; axis=None
    for name,spec in m['outputs'].items():
        path='$.outputs.'+name; q=spec['quantity']; output_quantities.append(q)
        if q not in required_outputs(kind):fail(path+'.quantity',sorted(required_outputs(kind)),q);continue
        unit,shape=QUANTITIES[q]
        if spec['unit']!=unit or spec['kind']!=shape or spec['dtype']!='float64' or spec['location']!=domain or spec['value_kind']!='average':
            fail(path,'float64 domain cell-average '+q+' in '+unit,spec)
        if axis is None:axis=spec['time_axis']
        elif spec['time_axis']!=axis:fail(path+'.time_axis','same output time axis',spec['time_axis'])
        t=arrays[m['time_axes'][spec['time_axis']]]
        if t[0]<start or t[-1]!=end:
            fail(path+'.time_axis','within interval, last request=time_end',t.tolist())
    if set(output_quantities)!=required_outputs(kind) or len(output_quantities)!=len(set(output_quantities)):
        fail('$.outputs','exactly one of '+str(sorted(required_outputs(kind))),output_quantities)
