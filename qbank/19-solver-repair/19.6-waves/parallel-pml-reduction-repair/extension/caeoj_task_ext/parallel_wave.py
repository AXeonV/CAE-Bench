"""Public declaration and mesh checks; never solve or correct a wave field."""
import numpy as np
TASK='parallel-pml-reduction-repair';MODELS={'parallel-scalar-sh-v1':0,'parallel-scalar-acoustic-potential-v1':1}
UNITS={'processes':'1','density':'kg/m^3','p_speed':'m/s','s_speed':'m/s','frequency':'Hz','time_step':'s'}

def locations():
    return {'cells':{'kind':'mesh','mesh':'domain','entity':'element','dimension':2,'ids':'cell_ids'},
            'sources':{'kind':'points','ids':'source_ids','coordinates':'source_coordinates'},
            'probes':{'kind':'points','ids':'probe_ids','coordinates':'probe_coordinates'}}

def descriptions(branch):
    def spec(array,quantity,unit,location,time_axis,dtype='float64'):
        return {'array':array,'quantity':quantity,'unit':unit,'location':location,'time_axis':time_axis,
                'dtype':dtype,'kind':'scalar','component_shape':[1],'components':['value'],'value_kind':'point'}
    inputs={'source_amplitude':spec('source_amplitude','line_force_amplitude' if branch==0 else 'acoustic_potential_source_amplitude','N/m' if branch==0 else 'N','sources','static'),
            'pml_region':spec('pml_region','spectral_element_pml_region','1','cells','static','int64')}
    inputs['pml_region']['value_kind']='average'
    outputs={'response':spec('wave_response','sh_displacement' if branch==0 else 'acoustic_displacement_potential','m' if branch==0 else 'kg/m','probes','physical')}
    return inputs,outputs

def check(problem,errors):
    from caeoj.validation import issue,read_mesh,resolve_file
    m=problem.manifest;a=problem.arrays
    def fail(path,expected,actual):errors.append(issue('E_PARALLEL_WAVE',path,expected,actual,'Outside the public parallel scalar wave DATA contract.'))
    physics=m.get('physics',{});params=physics.get('parameters',{})
    if m.get('task')!=TASK or m['spatial_dimension']!=2 or physics.get('model') not in MODELS or set(params)!=set(UNITS):
        fail('$.physics','exact parallel scalar wave model and parameter set',physics);return
    v={}
    v['wave_branch']=MODELS[physics['model']]
    for k,item in params.items():
        if set(item)!={'value','unit'} or item.get('unit')!=UNITS[k] or type(item.get('value')) not in (int,float) or not np.isfinite(item['value']):
            fail('$.physics.parameters.'+k,'finite scalar and declared SI unit',item);return
        v[k]=item['value']
    for k,allowed in [('processes',(1,3,4))]:
        if type(v[k]) is not int or v[k] not in allowed:fail('$.physics.parameters.'+k,str(allowed)+' as JSON integer',v[k])
    if errors:return
    branch=v['wave_branch'];dt=v['time_step'];freq=v['frequency']
    for k,lo,hi in [('density',1000,3000),('p_speed',1000,4000),('frequency',10,20),('time_step',.000125,.00025)]:
        if not lo<=v[k]<=hi:fail('$.physics.parameters.'+k,f'{lo}..{hi}',v[k])
    if branch==0 and not 1000<=v['s_speed']<=2000 or branch==1 and v['s_speed']!=0:
        fail('$.physics.parameters.s_speed','SH 1000..2000; acoustic exactly zero',v['s_speed'])
    if branch==0 and v['p_speed']<=np.sqrt(4/3)*v['s_speed']:fail('$.physics.parameters.p_speed','positive bulk modulus',v['p_speed'])
    if errors:return
    if m['geometries'] or m['conditions'] or m['meshes']!={'domain':{'file':'mesh.msh'}}:fail('$.meshes','only domain mesh.msh, empty conditions/geometries',m['meshes']);return
    if m['locations']!=locations() or m['time_axes']!={'static':'static_time','physical':'times'}:fail('$.locations','exact cells, sources, probes and time axes',m['locations']);return
    ins,outs=descriptions(branch)
    if m['fields']!=ins or m['outputs']!=outs:fail('$.fields/outputs','exact public field and response declarations',m['outputs']);return
    if set(a)!={'cell_ids','source_ids','source_coordinates','probe_ids','probe_coordinates','static_time','times','source_amplitude','pml_region'}:fail('$.data_file','exact declared support and field arrays',list(a));return
    times=a['times'];t0=-1.2/freq
    if not np.array_equal(a['static_time'],[0.]) or not 1000<=len(times)<=6400 or not .6<=(len(times)*dt)<=.8+1e-12 or not np.allclose(times,t0+np.arange(len(times))*dt,rtol=0,atol=1e-12):
        fail('$.time_axes','static label 0 and uniform physical samples from -1.2/f, duration 0.6..0.8s',times.shape)
    if not 1<=len(a['source_ids'])<=2 or not 2<=len(a['probe_ids'])<=8:fail('$.locations','1..2 sources, 2..8 probes',(len(a['source_ids']),len(a['probe_ids'])))
    if np.any(np.abs(a['source_amplitude'])<1e7) or np.any(np.abs(a['source_amplitude'])>1e8):fail('$.fields.source_amplitude','absolute amplitude 1e7..1e8',a['source_amplitude'].tolist())
    if not set(np.unique(a['pml_region']))<={0,2} or branch==0 and np.any(a['pml_region']):fail('$.fields.pml_region','0 or 2; only zero for SH',np.unique(a['pml_region']).tolist())
    if errors:return
    mesh=read_mesh(resolve_file(problem.path.parent,'mesh.msh','.msh'),geometry=True)
    if len({tuple(x) for x in mesh['node_coordinates'].values()})!=len(mesh['nodes']):fail('$.meshes.domain','unique coordinate for every node tag',len(mesh['nodes']));return
    if not 768<=len(a['cell_ids'])<=6000 or set(mesh['connectivity'])!=set(a['cell_ids']):fail('$.meshes.domain','768..6000 quads, cell_ids cover all elements',len(mesh['connectivity']));return
    cells=[];node_cells={};spacing=[]
    for i,tag in enumerate(a['cell_ids']):
        kind,row=mesh['connectivity'][int(tag)]
        if kind!=3:fail('$.meshes.domain','only Gmsh type3 linear quadrilateral elements',kind);return
        q=np.array([mesh['node_coordinates'][n][:2] for n in row]);w=q[1,0]-q[0,0];h=q[3,1]-q[0,1]
        if not 20<=w<=25 or w!=h or not np.array_equal(q,q[0]+np.array([[0,0],[w,0],[w,h],[0,h]])):
            fail('$.meshes.domain','axis aligned CCW squares, uniform side 20..25m',q.tolist());return
        spacing.append(w);cells.append(q)
        for n in row:node_cells.setdefault(n,[]).append(i)
    if len(set(spacing))!=1:fail('$.meshes.domain','one uniform element side length',set(spacing));return
    if v['p_speed']*dt/(min(spacing)*.1726731646460114)>.3:fail('$.physics.parameters.time_step','GLL minimum spacing CFL <= .3',dt)
    # Check connected components are full rectangular coupons with no holes.
    todo=set(range(len(cells)));components=[]
    cell_nodes=[mesh['connectivity'][int(tag)][1] for tag in a['cell_ids']]
    while todo:
        stack=[todo.pop()];component=[]
        while stack:
            i=stack.pop();component.append(i)
            for n in cell_nodes[i]:
                for j in node_cells[n]:
                    if j in todo:todo.remove(j);stack.append(j)
        components.append(component)
    if len(components) not in (1,2):fail('$.meshes.domain','one or two disconnected rectangles',len(components));return
    rectangles=[]
    for comp in components:
        q=np.concatenate([cells[i] for i in comp]);lo=q.min(axis=0);hi=q.max(axis=0)
        if len({tuple(cells[i][0]) for i in comp})!=len(comp) or len(comp)*spacing[0]**2!=np.prod(hi-lo) or not 600<=hi[0]-lo[0]<=2400 or lo[1]!=0 or hi[1]!=800:
            fail('$.meshes.domain','complete width600..2400m by height800m rectangle',[(hi-lo).tolist(),len(comp)]);return
        rectangles.append((lo,hi))
        want=np.array([2 if cells[i][0,1]<lo[1]+3*spacing[0] or cells[i][0,1]>=hi[1]-3*spacing[0] else 0 for i in comp])
        if np.any(a['pml_region']) and not np.array_equal(a['pml_region'][0,comp,0],want):fail('$.fields.pml_region','exact three rows at top/bottom in every component',comp[:5])
    if len(rectangles)==2:
        left,right=sorted(rectangles,key=lambda r:r[0][0])
        if right[0][0]-left[1][0]<4*spacing[0]:fail('$.meshes.domain','disjoint components with horizontal gap at least4h',rectangles)
    for name in ['source_coordinates','probe_coordinates']:
        for xy in a[name]:
            owners=[(lo,hi) for lo,hi in rectangles if np.all(xy>lo+4*spacing[0]) and np.all(xy<hi-4*spacing[0])]
            if len(owners)!=1:fail('$.locations.'+name,'strictly inside one rectangle, >4h from its walls',xy.tolist())
    if np.any(np.linalg.norm(a['probe_coordinates'][:,None,:]-a['source_coordinates'][None,:,:],axis=2)<4*spacing[0]):fail('$.locations.probes','at least4h away from every source',a['probe_coordinates'].tolist())
