"""Public declaration checks; never choose a projection or correct an answer."""
import itertools
import numpy as np


def spec(name,quantity,unit,components,location,kind='components',output=False):
    v={'array':name,'quantity':quantity,'unit':unit,'location':location,'time_axis':'instant','dtype':'float64',
       'kind':kind,'component_shape':[len(components)],'components':components,'value_kind':'point'}
    if not output:v['sampling']={'space':'piecewise_linear','time':'constant','extrapolation':'forbid'}
    return v


def descriptions(d,ids):
    return {'nodal_values':spec('nodal_values','nodal_value','1',['a','b','c'],'nodes')},{
        'projection':spec('projection','projection_position','m',list('xyz')[:d],'probes','vector',True),
        'distance':spec('distance','projection_distance','m',['value'],'probes','scalar',True),
        'weights':spec('weights','barycentric_weights','1',[f'node_{int(i)}' for i in ids],'probes',output=True),
        'mapped_values':spec('mapped_values','mapped_value','1',['a','b','c'],'probes',output=True)}


def check(problem,errors):
    from caeoj.validation import issue,read_mesh,resolve_file
    m=problem.manifest;a=problem.arrays;d=m['spatial_dimension']
    def fail(path,expected,actual):errors.append(issue('E_PROJECTION',path,expected,actual,'Outside the public nearest projection DATA contract.'))
    phys=m.get('physics',{});parameters=phys.get('parameters',{});mode=parameters.get('mode',{})
    if m.get('task')!='nearest-projection-repair' or d not in (2,3) or phys.get('model')!='nearest-simplex-state-v1' or set(parameters)!= {'mode'} or set(mode)!= {'value','unit'} or type(mode.get('value')) is not int or mode['value'] not in (0,1) or mode.get('unit')!='1':
        fail('$.physics','exact model and mode integer0/1',phys);return
    if m['geometries'] or m['conditions'] or m['meshes']!={'source':{'file':'source.msh'}}:
        fail('$.meshes','source.msh only, no geometry or conditions',m['meshes']);return
    expected_locations={'nodes':{'kind':'mesh','mesh':'source','entity':'node','ids':'node_ids'},'probes':{'kind':'points','ids':'probe_ids','coordinates':'probe_coordinates'}}
    if m['locations']!=expected_locations or not 2<=len(a.get('node_ids',[]))<=16 or not 1<=len(a.get('probe_ids',[]))<=32:
        fail('$.locations','all source nodes and1..32 probes',m['locations']);return
    if m['time_axes']!={'instant':'times'} or not np.array_equal(a.get('times'),[0.]):fail('$.time_axes','one zero instant',m['time_axes'])
    inputs,outputs=descriptions(d,a['node_ids'])
    for group,expected in [('fields',inputs),('outputs',outputs)]:
        if m[group]!=expected:fail('$.'+group,expected,m[group]);return
    mesh=read_mesh(resolve_file(problem.path.parent,'source.msh','.msh'),geometry=True)
    if set(map(int,a['node_ids']))!=mesh['nodes']:fail('$.locations.nodes','all source node tags',a['node_ids'])
    xyz=np.array([mesh['node_coordinates'][int(tag)] for tag in a['node_ids']])
    if np.any(np.abs(xyz)>100) or np.any(np.abs(a['probe_coordinates'])>200):fail('$.locations','coordinate ranges in DATA','outside range')
    if np.any(np.abs(a['nodal_values'])>1000):fail('$.fields.nodal_values','values in[-1000,1000]','outside range')
    if d==2 and np.any(xyz[:,2]!=0):fail('$.meshes.source','D2 z exactly zero',xyz)
    distances=[np.linalg.norm(u-v) for u,v in itertools.combinations(xyz,2)]
    if min(distances)<1e-3 or max(distances)>100:fail('$.meshes.source','all pair distances 1e-3..100m',distances)
    groups={1:set(),2:set(),4:set()};limits={1:32,2:24,4:8}
    for tag,(kind,nodes) in mesh['connectivity'].items():
        if kind==15:continue
        if kind not in groups or d==2 and kind==4:fail('$.meshes.source','allowed low-order simplex types',kind);continue
        key=tuple(sorted(nodes))
        if key in groups[kind]:fail('$.meshes.source','no duplicate simplex',tag)
        groups[kind].add(key)
        pts=np.array([mesh['node_coordinates'][int(n)] for n in nodes]);s=np.linalg.svd((pts[1:]-pts[0]).T,compute_uv=False)
        if s[-1]/s[0]<.01:fail('$.meshes.source','simplex singular value ratio>=.01',tag)
    for kind,primitives in groups.items():
        if len(primitives)>limits[kind]:fail('$.meshes.source','primitive count limit',len(primitives))
    for tri in groups[2]:
        if any(tuple(edge) not in groups[1] for edge in itertools.combinations(tri,2)):fail('$.meshes.source','explicit triangle edges',tri)
    for tetra in groups[4]:
        if any(tuple(face) not in groups[2] for face in itertools.combinations(tetra,3)):fail('$.meshes.source','explicit tetra faces',tetra)
