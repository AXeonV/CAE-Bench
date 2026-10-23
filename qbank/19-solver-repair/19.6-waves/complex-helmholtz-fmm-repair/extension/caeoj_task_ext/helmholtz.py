"""Public declarations only; no Green function, operator or answer computation."""
import numpy as np

TASK='complex-helmholtz-fmm-repair';MODEL='complex-helmholtz-operators-v1'


def locations(operation):
    targets={'kind':'points','ids':'target_ids','coordinates':'target_coordinates'}
    if operation==0:return {'sources':{'kind':'points','ids':'source_ids','coordinates':'source_coordinates'},'targets':targets}
    return {'surface_nodes':{'kind':'mesh','mesh':'surface','entity':'node','ids':'node_ids'},'targets':targets}


def spec(name,quantity,location,unit,components):
    return {'array':name,'quantity':quantity,'unit':unit,'location':location,'time_axis':'instant','dtype':'float64','kind':'components','component_shape':[len(components)],'components':components,'value_kind':'point'}


def descriptions(operation):
    complex_parts=['real','imag']
    if operation==0:
        fields={'strength':spec('strength','complex_source_strength','sources','1',complex_parts)}
        outputs={}
        for method in ['fmm','local']:
            outputs[method+'_potential']=spec(method+'_potential',method+'_helmholtz_potential','targets','1/m',complex_parts)
            outputs[method+'_gradient']=spec(method+'_gradient',method+'_helmholtz_target_gradient','targets','1/m2',[c+'_'+p for c in ['x','y','z'] for p in complex_parts])
        return fields,outputs
    fields={'density':spec('density','complex_surface_density','surface_nodes','1',complex_parts)}
    outputs={}
    for name,unit in [('single_layer','m'),('double_layer','1'),('hypersingular','1/m')]:
        outputs['boundary_'+name]=spec('boundary_'+name,'projected_'+name,'surface_nodes',unit,complex_parts)
    for name,unit in [('single_layer','m'),('double_layer','1')]:
        outputs['potential_'+name]=spec('potential_'+name,'exterior_'+name,'targets',unit,complex_parts)
    return fields,outputs


def triangle_distances(points,vertices,triangles):
    """Validation geometry, not Helmholtz evaluation."""
    v=vertices[triangles];a=v[:,0];u=v[:,1]-a;w=v[:,2]-a
    normal=np.cross(u,w);norm=np.linalg.norm(normal,axis=1);normal/=norm[:,None]
    delta=points[:,None,:]-a[None,:,:];signed=np.einsum('ptc,tc->pt',delta,normal)
    projected=delta-signed[:,:,None]*normal[None,:,:]
    uu=np.einsum('tc,tc->t',u,u);uw=np.einsum('tc,tc->t',u,w);ww=np.einsum('tc,tc->t',w,w);det=uu*ww-uw*uw
    pu=np.einsum('ptc,tc->pt',projected,u);pw=np.einsum('ptc,tc->pt',projected,w)
    bu=(pu*ww-pw*uw)/det;bw=(pw*uu-pu*uw)/det
    distances=np.where((bu>=0)&(bw>=0)&(bu+bw<=1),np.abs(signed),np.inf)
    for i,j in [(0,1),(1,2),(2,0)]:
        start=v[:,i];edge=v[:,j]-start;delta=points[:,None,:]-start[None,:,:]
        t=np.clip(np.einsum('ptc,tc->pt',delta,edge)/np.einsum('tc,tc->t',edge,edge),0,1)
        distances=np.minimum(distances,np.linalg.norm(delta-t[:,:,None]*edge[None,:,:],axis=2))
    return distances,signed


def check(problem,errors):
    from caeoj.validation import issue,read_mesh,resolve_file
    m=problem.manifest;a=problem.arrays
    def fail(path,want,got):errors.append(issue('E_HELMHOLTZ',path,want,got,'Outside the public complex Helmholtz DATA contract.'))
    physics=m.get('physics',{});par=physics.get('parameters',{})
    if m.get('task')!=TASK or m['spatial_dimension']!=3 or physics.get('model')!=MODEL or set(par)!={'operation','wavenumber_real','wavenumber_imag'}:
        fail('$.physics','exact model and three parameters',physics);return
    for n,item in par.items():
        wantunit='1' if n=='operation' else '1/m'
        if set(item)!={'value','unit'} or item['unit']!=wantunit or type(item['value']) not in (int,float) or not np.isfinite(item['value']):
            fail('$.physics.parameters.'+n,'finite scalar with exact unit',item);return
    op=par['operation']['value']
    if type(op) is not int or op not in (0,1):fail('$.physics.parameters.operation','JSON integer 0 or 1',op);return
    for n,lo,hi in [('wavenumber_real',.5,3),('wavenumber_imag',0,1.2)]:
        if not lo<=par[n]['value']<=hi:fail('$.physics.parameters.'+n,f'{lo}..{hi}',par[n]['value'])
    if m['geometries'] or m['conditions'] or m['meshes']!=({} if op==0 else {'surface':{'file':'surface.msh'}}):
        fail('$.meshes','exact mesh declaration and no conditions/geometries',m['meshes']);return
    if m['locations']!=locations(op) or m['time_axes']!={'instant':'times'} or not np.array_equal(a.get('times'),[0.]):
        fail('$.locations','exact locations and static label',m['locations']);return
    fields,outputs=descriptions(op)
    if m['fields']!=fields or m['outputs']!=outputs:fail('$.fields/outputs','exact operation field descriptions',m['outputs']);return
    names={'times','target_ids','target_coordinates'}|({'source_ids','source_coordinates','strength'} if op==0 else {'node_ids','density'})
    if set(a)!=names:fail('$.data_file','only operation arrays',list(a));return
    points=a['target_coordinates'];limit=24 if op==0 else 12
    if not 1<=len(points)<=limit or np.max(np.abs(points))>10:fail('$.locations.targets','target count/range in DATA',points.shape);return
    if len(points)>1 and np.min(np.linalg.norm(points[:,None,:]-points[None,:,:]+np.eye(len(points))[:,:,None]*1e6,axis=2))<.001:
        fail('$.locations.targets','distinct target spacing >=.001m','too close');return
    value=a['strength' if op==0 else 'density']
    if np.max(np.abs(value))>2:fail('$.fields','each real and imaginary part <=2',float(np.max(np.abs(value))))
    if op==0:
        sources=a['source_coordinates'];n=len(sources)
        if not 32<=n<=512 or np.max(np.abs(sources))>10 or np.linalg.norm(np.ptp(sources,axis=0))>4:
            fail('$.locations.sources','source count/coordinate range/diameter in DATA',sources.shape);return
        sep=np.linalg.norm(sources[:,None,:]-sources[None,:,:],axis=2);np.fill_diagonal(sep,np.inf)
        if np.min(sep)<.001 or np.min(np.linalg.norm(points[:,None,:]-sources[None,:,:],axis=2))<.2:
            fail('$.locations','source spacing >=.001m and source-target distance >=.2m','too close')
        return
    mesh=read_mesh(resolve_file(problem.path.parent,'surface.msh','.msh'),geometry=True)
    ids=a['node_ids'].tolist();index={int(n):i for i,n in enumerate(ids)}
    if not 18<=len(ids)<=100 or min(ids)<1 or max(ids)>1000000 or mesh['nodes']!=set(ids):fail('$.locations.surface_nodes','all 18..100 positive bounded nodes',ids);return
    vertices=np.asarray([mesh['node_coordinates'][int(n)] for n in ids]);rows=mesh['connectivity']
    if not 32<=len(rows)<=196 or any(tag<=0 or row[0]!=2 for tag,row in rows.items()):fail('$.meshes.surface','32..196 first-order triangles with positive tags',len(rows));return
    triangles=np.asarray([[index[n] for n in row[1]] for _,row in sorted(rows.items())])
    if set(triangles.ravel())!=set(range(len(ids))) or np.max(np.abs(vertices))>10 or np.linalg.norm(np.ptp(vertices,axis=0))>4:
        fail('$.meshes.surface','all nodes used, bounded coordinates and diameter','invalid nodes');return
    v=vertices[triangles];cross=np.cross(v[:,1]-v[:,0],v[:,2]-v[:,0]);area2=np.linalg.norm(cross,axis=1)
    lengths=np.linalg.norm(v[:,[1,2,0]]-v,axis=2)
    if np.min(area2)<.002 or np.min(lengths)<.05:fail('$.meshes.surface','triangle area >=.001m^2 and edges >=.05m','small element');return
    edges={};neighbors={i:set() for i in range(len(ids))}
    for tri in triangles:
        for i,j in zip(tri,np.roll(tri,-1)):
            key=tuple(sorted((int(i),int(j))));edges.setdefault(key,[]).append((int(i),int(j)));neighbors[int(i)].add(int(j));neighbors[int(j)].add(int(i))
    if len({tuple(sorted(t)) for t in triangles})!=len(triangles) or any(len(e)!=2 or e[0]!=e[1][::-1] for e in edges.values()):fail('$.meshes.surface','unique oriented closed triangular manifold','invalid topology');return
    reached={0};todo=[0]
    while todo:
        node=todo.pop()
        for new in neighbors[node]-reached:reached.add(new);todo.append(new)
    if len(reached)!=len(ids) or len(ids)-len(edges)+len(triangles)!=2:fail('$.meshes.surface','single connected convex closed surface','disconnected/topology');return
    normals=cross/area2[:,None]
    plane=np.einsum('tnc,tc->tn',vertices[None,:,:]-v[:,0,None,:],normals)
    if np.max(plane)>1e-10:fail('$.meshes.surface','outward convex face support planes','nonconvex/inward');return
    origin=vertices.mean(axis=0);q=v-origin
    volume=np.sum(np.einsum('tc,tc->t',q[:,0],np.cross(q[:,1],q[:,2])))/6
    if not .1<=volume<=50:fail('$.meshes.surface','volume .1..50m^3',float(volume))
    distance,signed=triangle_distances(points,vertices,triangles)
    if np.any(np.max(signed,axis=1)<=1e-10) or np.min(distance)<.3:
        fail('$.locations.targets','exterior points at least .3m from triangles','inside/near boundary')
