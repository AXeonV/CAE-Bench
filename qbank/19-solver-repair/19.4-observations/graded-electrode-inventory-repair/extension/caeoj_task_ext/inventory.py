"""Validate the declared finite-volume input domain, without producing answers."""
import numpy as np
from caeoj.validation import issue


def declarations(parameters):
    fields={};outputs={}
    for d in ['n','p']:
        x=parameters['x_count_'+d];r=parameters['r_count_'+d]
        xc=[f'x_{j}' for j in range(x)]
        fields['epsilon_'+d]=('active_material_fraction','1',xc)
        fields['concentration_'+d]=('concentration','mol.m-3',[f'x_{j}_r_{i}' for j in range(x) for i in range(r)])
        fields['thickness_'+d]=('length','m',['value'])
        fields['cmax_'+d]=('concentration','mol.m-3',['value'])
        outputs['radial_'+d]=('concentration','mol.m-3',xc)
        outputs['volume_'+d]=('concentration','mol.m-3',['value'])
        outputs['stoichiometry_'+d]=('stoichiometry','1',['value'])
        outputs['inventory_'+d]=('amount_of_substance','mol',['value'])
    fields['area']=('area','m2',['value'])
    outputs['total_inventory']=('amount_of_substance','mol',['value'])
    return fields,outputs


def field_spec(name,description,output=False):
    quantity,unit,components=description
    spec={'array':name,'quantity':quantity,'unit':unit,'location':'states','time_axis':'instant',
          'dtype':'float64','kind':'scalar' if len(components)==1 else 'components',
          'component_shape':[len(components)],'components':components,'value_kind':'point'}
    if not output:spec['sampling']={'space':'uniform','time':'constant','extrapolation':'forbid'}
    return spec


def check(problem,errors):
    meta,data=problem.manifest,problem.arrays
    def fail(path,expected,actual):
        errors.append(issue('E_INVENTORY',path,expected,str(actual),'Outside the public inventory DATA contract.'))
    p=meta.get('physics',{}).get('parameters',{})
    keys={'x_count_n','x_count_p','r_count_n','r_count_p'}
    if set(p)!=keys or any(set(v)!={'value','unit'} or type(v['value']) is not int or not 3<=v['value']<=32 or v['unit']!='1' for v in p.values()):
        fail('$.physics.parameters','four integer mesh counts3..32 with unit1',p);return
    if meta.get('task')!='graded-electrode-inventory-repair' or meta['spatial_dimension']!=1 or meta['meshes'] or meta['geometries'] or meta['conditions'] or meta['physics']['model']!='graded-electrode-inventory-v1':
        fail('$','independent 1D inventory states',meta.get('task'))
    if meta['time_axes']!={'instant':'times'} or not np.array_equal(data.get('times'),[0.]):fail('$.time_axes','instant at zero',meta['time_axes'])
    if meta['locations']!={'states':{'kind':'entities','ids':'state_ids'}} or not 1<=len(data.get('state_ids',[]))<=16:
        fail('$.locations','1..16 independent states',meta['locations'])
    for group,descriptions in zip(['fields','outputs'],declarations({k:v['value'] for k,v in p.items()})):
        if set(meta[group])!=set(descriptions):fail('$.'+group,'exact declared field set',list(meta[group]));return
        for name,description in descriptions.items():
            expected=field_spec(name,description,output=group=='outputs')
            if meta[group][name]!=expected:fail('$.'+group+'.'+name,str(expected),meta[group][name]);return
    for d in ['n','p']:
        epsilon=data['epsilon_'+d];c=data['concentration_'+d];cmax=data['cmax_'+d]
        if np.any(epsilon<.1) or np.any(epsilon>.9):fail('$.fields.epsilon_'+d,'0.1..0.9','out of range')
        if np.any(cmax<100) or np.any(cmax>1e6):fail('$.fields.cmax_'+d,'100..1e6 mol.m-3','out of range')
        if np.any(c<0) or np.any(c>cmax):fail('$.fields.concentration_'+d,'0..c_max','out of range')
        a=data['thickness_'+d]
        if np.any(a<1e-6) or np.any(a>1e-2):fail('$.fields.thickness_'+d,'1e-6..1e-2m','out of range')
    if np.any(data['area']<1e-4) or np.any(data['area']>10):fail('$.fields.area','1e-4..10m2','out of range')
