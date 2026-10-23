"""Public data validation only; no numerical repair or reference calculation."""
import numpy as np
import hashlib
from caeoj.validation import issue
TASK='reconstructed-energy-repair'
MODEL='reconstructed-total-energy-v1'
FIXTURE_COORDINATES = {'node_coordinates': '7149ac0db1718f99c32201a02c769b48955aacaa85790d5425cc39da4c289ffd', 'wall_coordinates': '842f50bba24c1bdef65f4e214c862cd546b299fed17e79b091748560a3a0cc80'}
def definitions(d,operation):
    xyz=list('xyz')[:d]
    if operation==1:
        return {},{'flow_density':('flow_density','kg/m^3',1,'nodes',['value']),
                   'flow_momentum':('flow_momentum_density','kg/(m^2*s)',2,'nodes',xyz),
                   'flow_energy':('flow_total_energy_density','J/m^3',1,'nodes',['value']),
                   'wall_cf':('skin_friction_coefficient','1',1,'wall',['value']),
                   'residuals':('log10_residual','1',6,'diagnostic',['density','momentum_x','momentum_y','energy','tke','omega'])}
    fields={'temperature':('temperature','K',1,'ends',['value']),
            'velocity':('velocity','m/s',d,'ends',xyz),
            'pressure':('pressure','Pa',1,'ends',['value']),
            'density':('density','kg/m^3',1,'ends',['value']),
            'enthalpy':('specific_total_enthalpy','J/kg',1,'ends',['value']),
            'gradient_temperature':('temperature_gradient','K/m',d,'ends',xyz),
            'gradient_velocity':('velocity_gradient','1/s',d*d,'ends',[a+b for a in xyz for b in xyz]),
            'gradient_pressure':('pressure_gradient','Pa/m',d,'ends',xyz),
            'limiters':('primitive_limiter','1',d+2,'ends',['T']+xyz+['p']),
            'displacement':('displacement','m',d,'edges',xyz)}
    out={k:fields[k] for k in ['temperature','velocity','pressure','density','enthalpy']}
    out['momentum']=('momentum_density','kg/(m^2*s)',d,'ends',xyz)
    out['energy']=('total_energy_density','J/m^3',1,'ends',['value'])
    return fields,out
def specs(defs,inputs=False):
    out={}
    for k,(quantity,unit,c,loc,components) in defs.items():
        z={'array':k,'quantity':quantity,'unit':unit,'location':loc,'time_axis':'instant','dtype':'float64','kind':'scalar' if c==1 else 'components','component_shape':[c],'components':components,'value_kind':'point'}
        if inputs:z['sampling']={'space':'uniform','time':'constant','extrapolation':'forbid'}
        out[k]=z
    return out
def check(problem,errors):
    m,a=problem.manifest,problem.arrays
    def fail(path,expected,actual):errors.append(issue('E_RECONSTRUCTION',path,expected,str(actual),'Outside DATA contract.'))
    p=m['physics']['parameters'];values={k:v['value'] for k,v in p.items()}
    if set(values)!={'operation','gamma','gas_constant','kappa','relax','muscl','limiter','cfl','iterations'}:fail('$.physics.parameters','exact documented parameter set',values);return
    op=values['operation'];d=m['spatial_dimension']
    if op not in [0,1] or d not in [2,3] or (op==1 and d!=2):fail('$.physics','operation/dimension',values);return
    if m['task']!=TASK or m['physics']['model']!=MODEL or m['geometries'] or m['meshes'] or m['conditions']:fail('$','fixed task and empty optional blocks',m['task'])
    units={k:'1' for k in values};units['gas_constant']='J/(kg*K)'
    for k,v in p.items():
        if v!={'value':values[k],'unit':units[k]}:fail('$.physics.parameters.'+k,'value/unit object',v)
    for k,lo,hi in [('gamma',1.1,1.67),('gas_constant',200,500),('kappa',-1,1),('relax',0,1),('cfl',100,400),('iterations',2000,3000)]:
        if not lo<=values[k]<=hi:fail('$.physics.parameters.'+k,f'{lo}..{hi}',values[k])
    if type(values['iterations']) is not int:fail('$.physics.parameters.iterations','JSON integer',values['iterations'])
    if values['muscl'] not in [0,1] or values['limiter'] not in [0,1,2]:fail('$.physics.parameters','muscl 0/1 and limiter 0/1/2',values)
    if m['time_axes']!={'instant':'times'} or not np.array_equal(a.get('times'),[0.]):fail('$.time_axes','instant [0]',m['time_axes'])
    fields,out=definitions(d,op)
    if m['fields']!=specs(fields,True):fail('$.fields','exact DATA field descriptors',m['fields'])
    if m['outputs']!=specs(out):fail('$.outputs','exact DATA output descriptors',m['outputs'])
    counts={'nodes':13900,'wall':100,'diagnostic':1} if op else {'edges':len(a.get('edge_ids',[])),'ends':len(a.get('end_ids',[]))}
    ids={'nodes':'node_ids','wall':'wall_ids','diagnostic':'diagnostic_ids'} if op else {'edges':'edge_ids','ends':'end_ids'}
    expected={k:{'kind':'entities','ids':ids[k]} for k in counts}
    if op:
        for k in ['nodes','wall']:expected[k]={'kind':'points','ids':ids[k],'coordinates':k[:-1]+'_coordinates' if k=='nodes' else 'wall_coordinates'}
    if m['locations']!=expected:fail('$.locations','documented entities',m['locations'])
    for k,n in counts.items():
        if not np.array_equal(a.get(ids[k]),np.arange(n,dtype='int64')):fail('$.locations.'+k,'ordered consecutive ids',a.get(ids[k]))
    if op:
        for name,expected_sha in FIXTURE_COORDINATES.items():
            if name not in a:fail('$.locations.'+name,'fixed mesh coordinates','missing');continue
            coords=np.array(a[name],dtype='<f8',copy=True);coords[coords==0]=0.
            if hashlib.sha256(coords.tobytes()).hexdigest()!=expected_sha:fail('$.locations.'+name,'coordinates of public/flatplate.su2','different coordinates')
    if not op:
        n=counts['edges']
        if not 1<=n<=32 or counts['ends']!=2*n:fail('$.locations','1..32 edges, 2 ends per edge',counts)
        for k,lo,hi in [('temperature',100,2000),('pressure',1000,1e7),('density',1e-4,100),('enthalpy',1e4,1e7),('velocity',-2000,2000),('limiters',0,1),('displacement',-.2,.2)]:
            if np.any(a[k]<lo) or np.any(a[k]>hi):fail('$.fields.'+k,f'{lo}..{hi}',a[k])
        for k in ['gradient_temperature','gradient_velocity','gradient_pressure']:
            if np.any(abs(a[k])>1e8):fail('$.fields.'+k,'abs <=1e8',a[k])
        if values['gas_constant']>0 and np.all(a['temperature']>0):
            rho_eos=a['pressure']/(values['gas_constant']*a['temperature'])
            if np.any(abs(a['density']-rho_eos)>1e-12+1e-12*abs(rho_eos)):fail('$.fields.density','abs(rho-p/(R*T)) <= 1e-12 kg/m^3 + 1e-12*abs(p/(R*T))','inconsistent input density')
