"""Validate only public declarations; never evaluate solver outputs or repair derivatives."""
import numpy as np
LOGICAL=['phi','eta0','eta1','eta2','eta3']
PROPERTIES=['void_minimum','solid_minimum','void_response','solid_response']
def description(name,quantity,unit,components):
    return {'array':name,'quantity':quantity,'unit':unit,'location':'programs','time_axis':'instant','dtype':'float64','kind':'scalar' if len(components)==1 else 'components','component_shape':[len(components)],'components':components,'value_kind':'point'}
def inputs():
    records={name:description(name,q,u,c) for name,q,u,c in [('phi','void_order_parameter','1',['value']),('eta','grain_order_parameters','1',['eta0','eta1','eta2','eta3']),('potential','chemical_potential','J',['value']),('temperature','temperature','K',['value']),('concentration','total_concentration','1',['value'])]}
    for v in records.values():v['sampling']={'space':'uniform','time':'constant','extrapolation':'forbid'}
    return records
def outputs():
    result={}
    for i,name in enumerate(PROPERTIES):
        stem='phase_concentration' if i<2 else name;unit='1' if i<2 else '1/J'
        for suffix,quantity,components in [('',stem+'_coefficient',['value']),('_gradient',stem+'_gradient',LOGICAL),('_hessian',stem+'_hessian',[a+'_'+b for a in LOGICAL for b in LOGICAL])]:result[name+suffix]=description(name+suffix,quantity,unit,components)
    for name,q,u,c in [('void_number_density','number_density','1/m3',['value']),('solid_number_density','number_density','1/m3',['value']),('void_grand_potential','grand_potential_density','J/m3',['value']),('solid_grand_potential','grand_potential_density','J/m3',['value']),('constraint_residual','concentration_constraint_residual','m',['left','right']),('constraint_state_jacobian','constraint_state_jacobian','m',[v+'_'+r+'_'+c for v in LOGICAL for r in ['left','right'] for c in ['left','right']]),('constraint_potential_jacobian','constraint_potential_jacobian','m/J',[r+'_'+c for r in ['left','right'] for c in ['left','right']]),('constraint_concentration_jacobian','constraint_concentration_jacobian','m',[r+'_'+c for r in ['left','right'] for c in ['left','right']])]:result[name]=description(name,q,u,c)
    return result
def parameter_units():
    p={'grain_count':'1','strict_mass_conservation':'1','variable_name_set':'1','atomic_volume':'m3','void_energy_coefficient':'J/m3','solid_energy_coefficient':'J/m3','surface_energy':'J/m2','grainboundary_energy':'J/m2','interface_width':'m','surface_switch_value':'1','probe_length':'m','equilibrium_constant':'1'}
    p.update({f'equilibrium_linear_{i}':'1' for i in range(4)});p.update({f'equilibrium_hessian_{i}{j}':'1' for i in range(4) for j in range(i,4)});return p
def check(problem,errors):
    from caeoj.validation import issue
    m=problem.manifest;a=problem.arrays
    def fail(path,expected,actual):errors.append(issue('E_GRAND_POTENTIAL',path,expected,str(actual),'Outside the public grand-potential material-program contract.'))
    if m.get('task')!='grand-potential-derivatives-repair' or m['spatial_dimension']!=1 or m['geometries'] or m['meshes'] or m['conditions'] or m.get('physics',{}).get('model')!='grand-potential-material-programs-v1':fail('$','declared model, 1D programs, no input mesh/geometry/conditions',m.get('physics'));return
    if m['locations']!={'programs':{'kind':'entities','ids':'program_ids'}} or m['time_axes']!={'instant':'times'} or not np.array_equal(a['times'],[0.]):fail('$.locations/time_axes','program identities and one zero instant',m['locations']);return
    if m['fields']!=inputs() or m['outputs']!=outputs():fail('$.fields/outputs','exact DATA input/output declarations',m['fields']);return
    p=m['physics']['parameters'];units=parameter_units()
    if set(p)!=set(units) or any(set(p[k])!={'value','unit'} or p[k]['unit']!=u for k,u in units.items()):fail('$.physics.parameters','exact DATA scalar parameters and units',p);return
    p={k:v['value'] for k,v in p.items()};n=p['grain_count'];ids=a['program_ids']
    if n!=int(n) or not 1<=n<=4 or p['strict_mass_conservation'] not in [0,1] or p['variable_name_set'] not in [0,1] or not 1<=len(ids)<=8 or np.any(ids<=0):fail('$.physics.parameters','grain_count1..4, two binary settings, 1..8 positive program identities',p);return
    n=int(n)
    bounds={'atomic_volume':(1e-30,1e-28),'void_energy_coefficient':(1e8,1e11),'solid_energy_coefficient':(1e8,1e11),'surface_energy':(.01,5.),'grainboundary_energy':(.01,5.),'interface_width':(1e-10,1e-8),'surface_switch_value':(.1,.9),'probe_length':(.25,4.),'equilibrium_constant':(.05,.8)}
    if any(not low<=p[k]<=high for k,(low,high) in bounds.items()):fail('$.physics.parameters','DATA finite scalar bounds',p);return
    linear=np.array([p[f'equilibrium_linear_{i}'] for i in range(4)]);hessian=np.zeros((4,4))
    for i in range(4):
        for j in range(i,4):hessian[i,j]=hessian[j,i]=p[f'equilibrium_hessian_{i}{j}']
    if np.any(abs(linear)>.15) or np.any(abs(hessian)>.1) or np.any(linear[n:]!=0) or np.any(hessian[n:,:]!=0) or np.any(hessian[:,n:]!=0):fail('$.physics.parameters','bounded polynomial coefficients and zero inactive padding',p);return
    phi=a['phi'][0,:,0];eta=a['eta'][0];temperature=a['temperature'][0,:,0];potential=a['potential'][0,:,0];concentration=a['concentration'][0,:,0]
    if np.any((phi<-.1)|(phi>1.1)) or np.any((eta<0)|(eta>1)) or np.any(eta[:,n:]!=0) or np.any((temperature<250)|(temperature>2000)) or np.any((concentration<0)|(concentration>1)):fail('$.fields','DATA state ranges and zero inactive eta padding','state range');return
    ceq=p['equilibrium_constant']+eta@linear+.5*np.einsum('ni,ij,nj->n',eta,hessian,eta)
    bound=.1*p['atomic_volume']*np.minimum(p['solid_energy_coefficient']*ceq,p['void_energy_coefficient'])
    if np.any((ceq<.02)|(ceq>.95)) or np.any(abs(potential)>bound):fail('$.fields','physical ceq range and DATA chemical-potential bound',{'ceq':ceq.tolist(),'potential':potential.tolist()})
