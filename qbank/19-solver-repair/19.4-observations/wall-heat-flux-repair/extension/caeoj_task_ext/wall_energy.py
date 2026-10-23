"""Strict public shape, topology and supported-domain checker; no solution."""
import numpy as np
from caeoj.validation import issue
TASK='wall-heat-flux-repair';MODEL='wall-energy-transport-v1'
UNITS={'density':'kg/m^3','heat_capacity':'J/(kg*K)','viscosity':'Pa*s','conductivity':'W/(m*K)','velocity':'m/s','bottom_temperature':'K','top_temperature':'K','bottom_heat_flux':'W/m^2','boundary_mode':'1','cfl':'1','iterations':'1'}
def descriptor(k,quantity,unit,loc,c=1,components=None,integral=False):
    return {'array':k,'quantity':quantity,'unit':unit,'location':loc,'time_axis':'steady','dtype':'float64','kind':'scalar' if c==1 else 'components','component_shape':[c],'components':components or ['value'],'value_kind':'integral' if integral else 'point'}
def fields():
    x=descriptor('inlet_temperature','temperature','K','inlet');x['sampling']={'space':'piecewise_linear','time':'constant','extrapolation':'forbid'};return {'inlet_temperature':x}
def outputs():
    return {'temperature':descriptor('temperature','temperature','K','nodes'),
            'velocity':descriptor('velocity','velocity','m/s','nodes',2,['x','y']),
            'pressure':descriptor('pressure','pressure','Pa','nodes'),
            'wall_heat_flux':descriptor('wall_heat_flux','heat_flux','W/m^2','wall'),
            'bottom_heat_rate':descriptor('bottom_heat_rate','heat_rate','W','bottom_integral',integral=True),
            'top_heat_rate':descriptor('top_heat_rate','heat_rate','W','top_integral',integral=True),
            'temperature_residual':descriptor('temperature_residual','log10_residual','1','diagnostic')}
def locations():
    x={'nodes':{'kind':'mesh','mesh':'channel','entity':'node','ids':'node_ids'},
       'wall':{'kind':'mesh','mesh':'channel','entity':'node','ids':'wall_ids'},
       'inlet':{'kind':'mesh','mesh':'channel','entity':'node','ids':'inlet_ids','physical_group':{'dimension':1,'tag':3}},
       'diagnostic':{'kind':'entities','ids':'diagnostic_ids'}}
    for tag,name in [(1,'bottom'),(2,'top')]:
        x[name+'_edges']={'kind':'mesh','mesh':'channel','entity':'element','dimension':1,'ids':name+'_edge_ids','physical_group':{'dimension':1,'tag':tag}}
        x[name+'_integral']={'kind':'aggregate','source':name+'_edges','ids':name+'_observation_id','operation':'sum'}
    return x
def check(problem,errors):
    m,a=problem.manifest,problem.arrays
    def fail(path,expected,actual):errors.append(issue('E_WALL_ENERGY',path,expected,str(actual),'Outside public DATA contract.'))
    if m['task']!=TASK or m['physics']['model']!=MODEL or m['spatial_dimension']!=2 or m['geometries'] or m['conditions'] or m['meshes']!={'channel':{'file':'mesh.msh'}}:fail('$','fixed task/2D channel blocks',m['task'])
    if m['locations']!=locations() or m['fields']!=fields() or m['outputs']!=outputs():fail('$','exact DATA locations/fields/outputs','descriptor mismatch')
    if m['time_axes']!={'steady':'times'} or not np.array_equal(a.get('times'),[0.]):fail('$.time_axes','steady=[0]',m['time_axes'])
    p=m['physics']['parameters']
    if set(p)!=set(UNITS):fail('$.physics.parameters','exact documented parameters',p);return
    v={k:x['value'] for k,x in p.items()}
    for k,unit in UNITS.items():
        if p[k]!={'value':v[k],'unit':unit}:fail('$.physics.parameters.'+k,unit,p[k])
    bounds={'density':(.5,3),'heat_capacity':(500,2000),'viscosity':(.001,.1),'conductivity':(1,20),'velocity':(0,.2),'bottom_temperature':(250,450),'top_temperature':(250,450),'bottom_heat_flux':(-2000,2000),'cfl':(.5,20),'iterations':(100,30000)}
    for k,(lo,hi) in bounds.items():
        if not lo<=v[k]<=hi:fail('$.physics.parameters.'+k,f'{lo}..{hi}',v[k])
    if v['boundary_mode'] not in [0,1] or (v['velocity']>0 and v['boundary_mode']!=0):fail('$.physics.parameters','T/T flow or static flux/T',v)
    if type(v['iterations']) is not int:fail('$.physics.parameters.iterations','JSON integer',v['iterations'])
    if np.any(a['inlet_temperature']<250) or np.any(a['inlet_temperature']>450):fail('$.fields.inlet_temperature','250..450 K',a['inlet_temperature'])
    mesh=problem.meshes['channel'];nodes=mesh['nodes'];n=len(nodes)
    if mesh['elements'][0] or mesh['elements'][3] or not mesh['elements'][2] or any(mesh['connectivity'][tag][0]!=3 for tag in mesh['elements'][2]) or any(mesh['connectivity'][tag][0]!=1 for tag in mesh['elements'][1]):fail('$.meshes.channel','first-order quadrilateral cells and boundary lines','unsupported element type')
    if not 100<=n<=3000 or not np.array_equal(a['node_ids'],sorted(nodes)):fail('$.locations.nodes','100..3000 full ordered nodes',n)
    if not np.array_equal(a['diagnostic_ids'],[0]) or not np.array_equal(a['bottom_observation_id'],[0]) or not np.array_equal(a['top_observation_id'],[0]):fail('$.locations','one diagnostic and observation per wall',a['diagnostic_ids'])
    groups=problem.meshes['channel']['groups'];wall=sorted(groups[(1,1)]['nodes']|groups[(1,2)]['nodes'])
    if not np.array_equal(a['wall_ids'],wall):fail('$.locations.wall','bottom+top node union in tag order',a['wall_ids'])
    if v['velocity']>0:
        inlet_nodes=sorted(groups[(1,3)]['nodes']);ys=np.array([mesh['node_coordinates'][tag][1] for tag in inlet_nodes])
        endpoint_ids=[inlet_nodes[int(np.argmin(ys))],inlet_nodes[int(np.argmax(ys))]]
        lookup={int(tag):float(T) for tag,T in zip(a['inlet_ids'],a['inlet_temperature'][0,:,0])}
        for tag,target in zip(endpoint_ids,[v['bottom_temperature'],v['top_temperature']]):
            if tag not in lookup or not np.isclose(lookup[tag],target,rtol=0,atol=1e-10):fail('$.fields.inlet_temperature','continuous inlet/wall endpoint temperatures',lookup.get(tag,'missing endpoint'))
