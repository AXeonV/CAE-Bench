"""Validate the public thermal state contract; do not compute repair outputs."""
import numpy as np
from caeoj.validation import issue
PHASE_FIELDS={'current':('volumetric_current_density','A.m-3'),'eta':('voltage','V'),
              'ocp':('voltage','V'),'equilibrium':('voltage','V'),
              'entropy':('voltage_temperature_derivative','V.K-1')}


def declarations(parameters):
    fields={}
    for d in ['n','p']:
        components=['value'] if parameters['phases_'+d]==1 else ['primary','secondary']
        for name,(quantity,unit) in PHASE_FIELDS.items():fields[name+'_'+d]=(quantity,unit,components)
    fields.update({k:('length','m',['value']) for k in ['length_n','length_p','length_s','length_cn','length_cp']})
    fields.update({'temperature':('temperature','K',['value']),'area':('area','m2',['value']),'volume':('volume','m3',['value'])})
    outputs={'heat_negative':('volumetric_heat_power','W.m-3',['value']),
             'heat_positive':('volumetric_heat_power','W.m-3',['value']),
             'area_heat':('area_heat_power','W.m-2',['value']),'cell_heat':('heat_power','W',['value']),
             'volume_heat':('volumetric_heat_power','W.m-3',['value'])}
    return fields,outputs


def field_spec(name,description,output=False):
    quantity,unit,components=description
    result={'array':name,'quantity':quantity,'unit':unit,'location':'states','time_axis':'instant','dtype':'float64',
            'kind':'scalar' if len(components)==1 else 'components','component_shape':[len(components)],
            'components':components,'value_kind':'point'}
    if not output:result['sampling']={'space':'uniform','time':'constant','extrapolation':'forbid'}
    return result


def check(problem,errors):
    meta,data=problem.manifest,problem.arrays
    def fail(path,expected,actual):errors.append(issue('E_HYSTERESIS',path,expected,str(actual),'Outside public thermal DATA contract.'))
    p=meta.get('physics',{}).get('parameters',{})
    if set(p)!={'phases_n','phases_p','mask_n','mask_p','pairs'} or any(set(v)!={'value','unit'} or type(v['value']) is not int or v['unit']!='1' for v in p.values()):
        fail('$.physics.parameters','five integer parameters with unit1',p);return
    p={k:v['value'] for k,v in p.items()}
    if any(p['phases_'+d] not in [1,2] or not 0<=p['mask_'+d]<2**p['phases_'+d] for d in ['n','p']) or not 1<=p['pairs']<=32:
        fail('$.physics.parameters','P1..2,mask0..2^P-1,pairs1..32',p);return
    if meta.get('task')!='hysteresis-heat-repair' or meta['spatial_dimension']!=1 or meta['meshes'] or meta['geometries'] or meta['conditions'] or meta['physics']['model']!='ocp-hysteresis-heat-v1':fail('$','uniform local thermal states',meta.get('task'))
    if meta['time_axes']!={'instant':'times'} or not np.array_equal(data.get('times'),[0.]):fail('$.time_axes','instant at zero',meta['time_axes'])
    if meta['locations']!={'states':{'kind':'entities','ids':'state_ids'}} or not 1<=len(data.get('state_ids',[]))<=16:fail('$.locations','1..16 independent states',meta['locations'])
    for group,description in zip(['fields','outputs'],declarations(p)):
        if set(meta[group])!=set(description):fail('$.'+group,'exact declared fields',list(meta[group]));return
        for name,details in description.items():
            expected=field_spec(name,details,group=='outputs')
            if meta[group][name]!=expected:fail('$.'+group+'.'+name,str(expected),meta[group][name]);return
    for d in ['n','p']:
        for name,limit in [('current',1e7),('eta',1),('entropy',.003)]:
            if np.any(np.abs(data[name+'_'+d])>limit):fail('$.fields.'+name+'_'+d,'absolute value<='+str(limit),'out of range')
        for name in ['ocp','equilibrium']:
            if np.any(data[name+'_'+d]<-2) or np.any(data[name+'_'+d]>6):fail('$.fields.'+name+'_'+d,'-2..6V','out of range')
        for k in range(p['phases_'+d]):
            if not (p['mask_'+d]>>k)&1 and np.any(np.abs(data['ocp_'+d][:,:,k]-data['equilibrium_'+d][:,:,k])>1e-12):fail('$.fields.equilibrium_'+d,'U_eq=U for single phase','incompatible input')
    for name,low,high in [('temperature',250,400),('area',1e-4,10),('volume',1e-10,1)]+[(x,1e-6,1e-2) for x in ['length_n','length_p','length_s','length_cn','length_cp']]:
        if np.any(data[name]<low) or np.any(data[name]>high):fail('$.fields.'+name,f'{low}..{high}','out of range')
