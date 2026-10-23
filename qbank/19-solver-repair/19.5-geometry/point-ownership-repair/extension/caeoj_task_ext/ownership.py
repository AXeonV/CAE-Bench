"""Declaration validation only; does not classify or assign any query point."""
import itertools
import numpy as np

def descriptions():
    return {name:{'array':name,'quantity':quantity,'unit':unit,'location':'probes','time_axis':'instant',
      'dtype':'float64','kind':'scalar','component_shape':[1],'components':['value'],'value_kind':'point'}
      for name,quantity,unit in [('owned','point_owned','1'),('cell_id','owning_cell_id','1'),('distance','cell_distance','m')]}

def check(problem,errors):
    from caeoj.validation import issue,read_mesh,resolve_file
    m=problem.manifest;a=problem.arrays;d=m['spatial_dimension']
    def fail(path,expected,actual):errors.append(issue('E_OWNERSHIP',path,expected,actual,'Outside the public ownership DATA contract.'))
    physics=m.get('physics',{});parameters=physics.get('parameters',{});mode=parameters.get('mode',{});padding=parameters.get('padding',{})
    if m.get('task')!='point-ownership-repair' or d not in (2,3) or physics.get('model')!='simplex-ownership-v1' or set(parameters)!={'mode','padding'}:
        fail('$.physics','simplex-ownership-v1, mode and padding only',physics);return
    if set(mode)!={'value','unit'} or type(mode.get('value')) is not int or mode['value'] not in (0,1,2) or mode.get('unit')!='1':
        fail('$.physics.parameters.mode','JSON integer0/1/2, unit1',mode)
    if set(padding)!={'value','unit'} or type(padding.get('value')) not in (int,float) or not np.isfinite(padding['value']) or not 0<=padding['value']<=5 or padding.get('unit')!='m':
        fail('$.physics.parameters.padding','finite0..5m',padding)
    expected_locations={'nodes':{'kind':'mesh','mesh':'source','entity':'node','ids':'node_ids'},
      'probes':{'kind':'points','ids':'probe_ids','coordinates':'probe_coordinates'}}
    if m['geometries'] or m['conditions'] or m['meshes']!={'source':{'file':'source.msh'}} or m['locations']!=expected_locations:
        fail('$.locations','all source nodes and query points; no conditions/geometries',m['locations']);return
    if m['fields'] or m['outputs']!=descriptions():fail('$.outputs','three declared scalar outputs; no input fields',m['outputs'])
    if m['time_axes']!={'instant':'times'} or not np.array_equal(a.get('times'),[0.]):fail('$.time_axes','one zero instant',m['time_axes'])
    ids=a.get('node_ids',[]);probes=a.get('probe_ids',[])
    if not d+1<=len(ids)<=48 or not 1<=len(probes)<=24 or np.any(np.asarray(probes)<=0) or np.any(np.diff(ids)<=0) or np.any(np.diff(probes)<=0):
        fail('$.locations','ascending identities,3/4..48 nodes,1..24 probes','invalid');return
    mesh=read_mesh(resolve_file(problem.path.parent,'source.msh','.msh'),geometry=True)
    if set(map(int,ids))!=mesh['nodes']:fail('$.locations.nodes','all source node tags',ids)
    xyz=np.asarray([mesh['node_coordinates'][int(i)] for i in ids]);queries=a['probe_coordinates']
    if np.any(np.abs(xyz)>100) or np.any(np.abs(queries)>200) or d==2 and np.any(xyz[:,2]!=0):
        fail('$.meshes.source','coordinates in DATA;2D z=0','outside range')
    if min(np.linalg.norm(x-y) for x,y in itertools.combinations(xyz,2))<1e-3:
        fail('$.meshes.source','distinct nodes separated by1e-3m','near duplicate')
    if len(queries)>1 and min(np.linalg.norm(x-y) for x,y in itertools.combinations(queries,2))<1e-4:
        fail('$.locations.probes','distinct queries separated by1e-4m','near duplicate')
    cells=[];keys=set();used=set()
    for tag,(kind,nodes) in mesh['connectivity'].items():
        if kind==15:continue
        if kind!=(2 if d==2 else 4):fail('$.meshes.source','linear top-dimensional simplices and optional point elements',kind);continue
        if not 1<=tag<=1000000:fail('$.meshes.source','cell IDs1..1000000',tag)
        key=tuple(sorted(nodes))
        if key in keys:fail('$.meshes.source','no duplicate simplex',tag)
        keys.add(key);used.update(nodes);cells.append(tag)
        points=np.asarray([mesh['node_coordinates'][int(i)] for i in nodes]);s=np.linalg.svd((points[1:]-points[0]).T,compute_uv=False)
        if s[-1]/s[0]<.05:fail('$.meshes.source','simplex singular value ratio>=.05',tag)
    if not 1<=len(cells)<=16 or used!=mesh['nodes']:fail('$.meshes.source','1..16 cells using all nodes',cells)
