"""Check public state declarations; never compute the repair outputs."""
import numpy as np
from caeoj.validation import issue


def check(problem, errors):
    meta, data = problem.manifest, problem.arrays

    def fail(path, expected, actual):
        errors.append(issue('E_ECM',path,expected,str(actual),'Outside the public ECM DATA contract.'))

    p=meta.get('physics',{}).get('parameters',{})
    if set(p)!={'grid_count','rc_count'}:
        fail('$.physics.parameters','grid_count and rc_count',p)
        return
    k,r=p['grid_count']['value'],p['rc_count']['value']
    if type(k) is not int or not 4<=k<=64 or type(r) is not int or not 0<=r<=3:
        fail('$.physics.parameters','K integer4..64 and R integer0..3',p)
        return
    if any(x['unit']!='1' for x in p.values()):
        fail('$.physics.parameters','unit1',p)
    if meta.get('task')!='diffusion-element-heat-repair' or meta['spatial_dimension']!=1 or meta['meshes'] or meta['geometries'] or meta['conditions']:
        fail('$','1D independent ECM state declaration',meta.get('task'))
    if meta['time_axes']!={'instant':'times'} or not np.array_equal(data.get('times'),[0.]):
        fail('$.time_axes','instant at zero',meta['time_axes'])
    if meta['locations']!={'states':{'kind':'entities','ids':'state_ids'}} or not 1<=len(data.get('state_ids',[]))<=32:
        fail('$.locations','1..32 states',meta['locations'])
    fields={'current':('current','A',['value'],'float64'),
            'average_soc':('state_of_charge','1',['value'],'float64'),
            'diffusion_enabled':('enabled','1',['value'],'bool'),
            'soc_profile':('state_of_charge','1',[f'cell_{i}' for i in range(k)],'float64'),
            'ocv_coefficients':('voltage_coefficients','V',['c0','c1','c2','c3'],'float64'),
            'element_heat':('irreversible_heat_power','W',['value'] if r==0 else [f'element_{i}' for i in range(r+1)],'float64'),
            'reversible_heat':('reversible_heat_power','W',['value'],'float64')}
    outputs={'surface_soc':('state_of_charge','1',['value'],'float64'),
             'diffusion_overpotential':('voltage','V',['value'],'float64'),
             'irreversible_heat':('irreversible_heat_power','W',['value'],'float64'),
             'total_heat':('heat_power','W',['value'],'float64')}
    for group,descriptions in [('fields',fields),('outputs',outputs)]:
        if set(meta[group])!=set(descriptions):
            fail('$.'+group,'exact declared fields',list(meta[group]))
            return
        for name,(quantity,unit,components,dtype) in descriptions.items():
            spec=meta[group][name]
            expected={'array':name,'quantity':quantity,'unit':unit,'location':'states','time_axis':'instant',
                      'dtype':dtype,'component_shape':[len(components)],'components':components,
                      'kind':'scalar' if len(components)==1 else 'components','value_kind':'point'}
            if group=='fields':expected['sampling']={'space':'uniform','time':'constant','extrapolation':'forbid'}
            if spec!=expected:
                fail('$.'+group+'.'+name,str(expected),spec)
                return
    profile=data['soc_profile'][0]
    average=data['average_soc'][0,:,0]
    slopes=(profile[:,-1]-profile[:,0])*k/(k-1)
    expected=average[:,None]+slopes[:,None]*((np.arange(k)+.5)/k-.5)
    if np.max(np.abs(profile-expected))>1e-12:
        fail('$.fields.soc_profile','linear distribution with given average','incompatible profile')
    endpoints=np.column_stack([average-slopes/2,average+slopes/2])
    if np.any(endpoints<.05) or np.any(endpoints>.95):
        fail('$.fields.soc_profile','endpoints .05..95',endpoints)
    enabled=data['diffusion_enabled'][0,:,0]
    if np.any(np.abs(slopes[~enabled])>1e-12):
        fail('$.fields.diffusion_enabled','zero slope when disabled',slopes[~enabled])
    if np.any(np.abs(data['current'])>100) or np.any(np.abs(data['reversible_heat'])>50):
        fail('$.fields','current<=100A and reversible heat<=50W','out of range')
    if np.any(data['element_heat']<0) or np.any(data['element_heat']>100):
        fail('$.fields.element_heat','0..100W','out of range')
    coefficients=data['ocv_coefficients'][0]
    for c in coefficients:
        if not (2<=c[0]<=5 and .1<=c[1]<=2 and np.all(np.abs(c[2:])<=.2)):
            fail('$.fields.ocv_coefficients','published coefficient ranges',c)
        candidates=[0.,1.]
        if c[3]!=0 and 0<-c[2]/(3*c[3])<1:candidates.append(-c[2]/(3*c[3]))
        if min(c[1]+2*c[2]*s+3*c[3]*s*s for s in candidates)<.05:
            fail('$.fields.ocv_coefficients','U derivative>=.05 on [0,1]',c)
