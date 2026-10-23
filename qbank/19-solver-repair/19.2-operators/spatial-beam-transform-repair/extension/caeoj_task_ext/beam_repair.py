INPUTS={
 'endpoints':('endpoints','m',[f'{node}_{axis}' for node in ['root','tip'] for axis in 'xyz']),
 'section_axis':('section_reference_axis','1',list('xyz')),
 'young_modulus':('young_modulus','Pa',['value']), 'poisson_ratio':('poisson_ratio','1',['value']),
 'area':('cross_section_area','m^2',['value']), 'inertia_y':('second_moment_y','m^4',['value']),
 'inertia_z':('second_moment_z','m^4',['value']), 'torsion_constant':('torsion_constant','m^4',['value']),
 'shear_area_y':('effective_shear_area_y','m^2',['value']), 'shear_area_z':('effective_shear_area_z','m^2',['value']),
 'density':('density','kg/m^3',['value']), 'body_acceleration':('body_acceleration','m/s^2',list('xyz')),
 'tip_load':('normalized_generalized_force','N',['fx','fy','fz','mx_over_L','my_over_L','mz_over_L'])}
OUTPUTS={'lhs_combined':('normalized_stiffness','N/m',[f'row_{i}_col_{j}' for i in range(12) for j in range(12)]),
 'lhs_separate':('normalized_stiffness','N/m',[f'row_{i}_col_{j}' for i in range(12) for j in range(12)]),
 'rhs_combined':('normalized_generalized_force','N',[f'dof_{i}' for i in range(12)]),
 'rhs_separate':('normalized_generalized_force','N',[f'dof_{i}' for i in range(12)]),
 'tip_displacement':('normalized_displacement','m',['ux','uy','uz','L_rx','L_ry','L_rz'])}

def spec(name,description,output=False):
    quantity,unit,components=description
    d={'array':name,'quantity':quantity,'unit':unit,'location':'beams','time_axis':'instant','dtype':'float64',
       'kind':'scalar' if len(components)==1 else 'components','component_shape':[len(components)],'components':components,'value_kind':'point'}
    if not output:d['sampling']={'space':'uniform','time':'constant','extrapolation':'forbid'}
    return d




def check(problem,errors):
    import numpy as np
    from caeoj.validation import issue
    m=problem.manifest;a=problem.arrays
    def fail(path,expected,actual):errors.append(issue('E_BEAM',path,expected,str(actual),'Outside the public spatial beam DATA contract.'))
    if m.get('task')!='spatial-beam-transform-repair' or m['spatial_dimension']!=3 or m.get('physics')!={'model':'linear-timoshenko-spatial-beam-v1','parameters':{}} or m['geometries'] or m['meshes'] or m['conditions']:
        fail('$','3D independent beam declaration',m.get('physics'));return
    if m['locations']!={'beams':{'kind':'entities','ids':'beam_ids'}} or not 1<=len(a.get('beam_ids',[]))<=16 or np.any(a.get('beam_ids',np.array([]))<=0):
        fail('$.locations','1..16 beam identities',m['locations']);return
    if m['time_axes']!={'instant':'times'} or not np.array_equal(a.get('times'),[0.]):fail('$.time_axes','one zero instant',m['time_axes'])
    for group,descriptions,output in [('fields',INPUTS,False),('outputs',OUTPUTS,True)]:
        if set(m[group])!=set(descriptions):fail('$.'+group,'exact DATA field set',list(m[group]));return
        for name,description in descriptions.items():
            if m[group][name]!=spec(name,description,output):fail('$.'+group+'.'+name,str(spec(name,description,output)),m[group][name]);return
    endpoints=a['endpoints'][0];delta=endpoints[:,3:]-endpoints[:,:3];length=np.linalg.norm(delta,axis=1)
    if np.any(np.abs(endpoints)>100) or np.any(length<.1) or np.any(length>20):fail('$.fields.endpoints','coordinates<=100m and length .1..20m',endpoints);return
    axis=a['section_axis'][0];mag=np.linalg.norm(axis,axis=1);t=delta/length[:,None]
    projection=axis-(axis*t).sum(axis=1)[:,None]*t
    if np.any(mag<.1) or np.any(mag>10) or np.any(np.linalg.norm(projection,axis=1)<.1*mag):fail('$.fields.section_axis','magnitude .1..10 and nonparallel projection>=.1 norm',axis)
    ranges={'young_modulus':(1e9,3e11),'poisson_ratio':(0,.45),'area':(1e-4,.1),'inertia_y':(1e-8,1e-3),'inertia_z':(1e-8,1e-3),'torsion_constant':(1e-8,1e-3),'density':(100,2e4),'body_acceleration':(-20,20),'tip_load':(-1e4,1e4)}
    for name,(lo,hi) in ranges.items():
        if np.any(a[name]<lo) or np.any(a[name]>hi):fail('$.fields.'+name,f'{lo}..{hi}',a[name])
    for name in ['shear_area_y','shear_area_z']:
        if np.any(a[name]<1e-5*a['area']) or np.any(a[name]>a['area']):fail('$.fields.'+name,'1e-5*A..A',a[name])

