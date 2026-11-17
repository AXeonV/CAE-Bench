"""Evaluate published parallel-plate and hydrostatic solutions, with exact BCs.

MIT 2.25 Couette & Poiseuille Flows, p.1; MIT Unified Fluids Lecture 2,
hydrostatic equation. No numerically solved or manufactured PDE reference here.
Polynomial restrictions at natural boundaries preserve full symmetric traction.
"""
from pathlib import Path
import argparse, json, math, time
import gmsh, h5py
import numpy as np
from convert_supplement import field
from prepare_supplement import inside

COUETTE='https://ocw.mit.edu/courses/2-25-advanced-fluid-mechanics-fall-2013/1a114d602956fa0dd328155f9b45f93d_MIT2_25F13_Couet_and_Pois.pdf'
HYDRO='https://web.mit.edu/16.unified/www/archives2006-2007/FALL/fluids/Fluids_Lectures/f02.pdf'


def specifications():
    rows=[
      dict(name='couette-periodic',A=0.,C=.1,periodic=True,purpose='single moving plate; constant shear and periodic seam'),
      dict(name='counter-couette',A=-.1,C=.1,periodic=True,purpose='opposed plates; zero net transport despite finite shear'),
      dict(name='aiding-couette-poiseuille',C=.05,B=.015,periodic=True,purpose='wall and body-force transport reinforce'),
      dict(name='adverse-couette-poiseuille',C=.05,B=-.05,periodic=True,purpose='adverse forcing creates internal counterflow and shear zero'),
      dict(name='traction-poiseuille',B=.02,ends='traction',pressure_drive=True,purpose='normal and tangential total traction; pressure-driven transport'),
      dict(name='half-channel-symmetry',C=.08,B=-.02,ends='traction',pressure_drive=True,top='symmetry',purpose='half Poiseuille channel; mirror plane has nonzero speed and zero shear'),
      dict(name='half-channel-slip',C=.08,B=-.02,periodic=True,top='slip',purpose='shear-free ceiling; body-force balances curvature'),
      dict(name='couette-inlet-traction',C=.075,ends='mixed',angle=.37,purpose='linear inflow and exact total traction; oblique normals'),
      dict(name='plug-pressure-outlet',A=.04,ends='plug',top='slip',bottom='slip',p0=12.,purpose='uniform velocity inflow; reservoir pressure and zero tangential traction'),
      dict(name='plug-flow-rate',A=.1,ends='rate',top='symmetry',bottom='symmetry',rho=997.,mu=.89,purpose='total volume flow normalization and mass-flow conversion'),
      dict(name='vertical-poiseuille',B=.015,periodic=True,angle=math.pi/2,absolute=True,purpose='vertical transport, global components, absolute mean pressure'),
      dict(name='hydrostatic-concave',static=True,boxes=[[0,0,4,1],[0,1,2,3]],g=[.3,-9.81],gauge='mean',rho=2.,purpose='area-weighted mean pressure in a concave domain'),
      dict(name='hydrostatic-island',static=True,boxes=[[0,0,4,3]],holes=[[1,1,2,2]],g=[.2,-.4],split_source=True,gauge='point',rho=10.,purpose='hole normals, point gauge and superposed accelerations'),
      dict(name='hydrostatic-reservoir',static=True,ends='hydro-outlet',g=[0.,-9.81],angle=.23,absolute=True,p0=101500.,purpose='spatial reservoir-pressure field, hydrostatic stress and oblique gravity'),
      dict(name='co-moving-plates',A=.12,periodic=True,absolute=True,purpose='rigid translation: finite convection, zero shear, absolute pressure forces'),
      dict(name='split-flow-rate',A=.08,ends='split-rate',top='moving_wall',bottom='moving_wall',g=[0.,-.2],rho=5.,p0=20.,purpose='two separately normalized inflow regions, moving walls and transverse hydrostatics'),
    ]
    for i,s in enumerate(rows):
        s['name']='x80-exact-'+s['name'];s.setdefault('A',0.);s.setdefault('B',0.);s.setdefault('C',0.)
        s.setdefault('rho',1.7);s.setdefault('mu',.12);s.setdefault('angle',0.);s.setdefault('g',[0.,0.])
        s.setdefault('p0',7.);s.setdefault('boxes',[[0,0,4,2]]);s.setdefault('holes',[])
        s['mesh_kind']=['triangles','quadrilaterals','mixed'][i%3]
        if s.get('ends') in ('traction','mixed','hydro-outlet'):s['mesh_kind']='triangles'
        s['difficulty']='easy' if i in (0,1,8,9,14) else 'medium'
        s['entity_sampling']=i in (6,9,12,15)
        s['source']=HYDRO if s.get('static') else COUETTE
    return rows


def rotation(s):
    t=s['angle'];return np.array([[math.cos(t),-math.sin(t)],[math.sin(t),math.cos(t)]])


def exact(s,xy):
    xy=np.asarray(xy);R=rotation(s);q=xy@R;x=q[:,0];y=q[:,1]
    A,B,C=s['A'],s['B'],s['C'];H=max(v[3] for v in s['boxes'])
    # u=A+C*y+B*y*(H-y); quadratic coefficient is -B.
    if s.get('top') in ('slip','symmetry') and B<0:
        # Half-channel specification explicitly gives u=C*y+B*y^2.
        speed=A+C*y+B*y*y;derivative=C+2*B*y;curvature=2*B
    else:
        speed=A+C*y+B*y*(H-y);derivative=C+B*(H-2*y);curvature=-2*B
    u=np.column_stack((speed,np.zeros(len(x))))@R.T
    G=np.zeros((len(x),2,2));G[:,0,1]=derivative;G=np.einsum('ij,njk,lk->nil',R,G,R)
    gp=np.array(s['g'])*s['rho']
    if s.get('pressure_drive'):gp[0]=s['mu']*curvature
    p=s['p0']+q@gp-s.get('pressure_shift',0.)
    D=(G+G.transpose(0,2,1))/2
    return dict(velocity=u,pressure=p[:,None],density=np.full((len(x),1),s['rho']),
                dynamic_viscosity=np.full((len(x),1),s['mu']),shear_rate=np.sqrt(2*np.einsum('nij,nij->n',D,D))[:,None],
                stress=-p[:,None,None]*np.eye(2)[None]+2*s['mu']*D,gradient=G)


def mesh(s,d,n=3):
    xmax=max(v[2] for v in s['boxes']);ymax=max(v[3] for v in s['boxes'])
    squares=[(i,j) for i in range(xmax*n) for j in range(ymax*n) if inside((i+.5)/n,(j+.5)/n,s)]
    vertices=sorted(set((i+dx,j+dy) for i,j in squares for dx,dy in ((0,0),(1,0),(1,1),(0,1))))
    # Non-contiguous identities exercise tag binding; contract IDs stay increasing.
    tags={v:101+7*k for k,v in enumerate(vertices)};R=rotation(s)
    local=np.array(vertices,dtype=float)/n;xy=local@R.T
    nodes={tags[v]:xy[k] for k,v in enumerate(vertices)};elements={};types={};edges={};offset=5001
    for z,(i,j) in enumerate(squares):
        q=[tags[(i+dx,j+dy)] for dx,dy in ((0,0),(1,0),(1,1),(0,1))]
        for a,b in zip(q,q[1:]+q[:1]):
            key=tuple(sorted((a,b)))
            if key in edges:del edges[key]
            else:edges[key]=(a,b)
        split=s['mesh_kind']=='triangles' or (s['mesh_kind']=='mixed' and z%2==0)
        for cell in ([q[:3],[q[0],q[2],q[3]]] if split else [q]):
            elements[offset]=cell;types[offset]=2 if len(cell)==3 else 3;offset+=3
    patches={}
    for a,b in edges.values():
        aa=np.array(nodes[a])@R;bb=np.array(nodes[b])@R;mid=(aa+bb)/2
        if abs(mid[0])<1e-10:name='left_lower' if s.get('ends')=='split-rate' and mid[1]<ymax/2 else 'left'
        elif abs(mid[0]-xmax)<1e-10:name='right'
        elif abs(mid[1])<1e-10:name='bottom'
        elif abs(mid[1]-ymax)<1e-10:name='top'
        else:name='internal_'+str(round(mid[0],6))+'_'+str(round(mid[1],6))
        patches.setdefault(name,[]).append((offset,[a,b]));offset+=3
    gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.model.add(s['name'])
    gmsh.model.addDiscreteEntity(2,100);gmsh.model.mesh.addNodes(2,100,list(nodes),np.column_stack((xy,np.zeros(len(xy)))).ravel())
    for typ in (2,3):
        ids=[k for k in elements if types[k]==typ]
        if ids:gmsh.model.mesh.addElementsByType(100,typ,ids,np.array([elements[k] for k in ids]).ravel())
    gmsh.model.addPhysicalGroup(2,[100],100)
    for k,(name,rows) in enumerate(patches.items(),1):
        gmsh.model.addDiscreteEntity(1,k);gmsh.model.mesh.addElementsByType(k,1,[v[0] for v in rows],np.array([v[1] for v in rows]).ravel());gmsh.model.addPhysicalGroup(1,[k],k)
    gmsh.option.setNumber('Mesh.MshFileVersion',4.1);gmsh.write(str(d/'mesh.msh'));gmsh.finalize()
    return nodes,elements,patches


def quadrature(points,order=8):
    z,w=np.polynomial.legendre.leggauss(order);z=(z+1)/2;w=w/2;p=np.array(points)
    if len(p)==2:return (1-z[:,None])*p[0]+z[:,None]*p[1],w*np.linalg.norm(p[1]-p[0])
    if len(p)==4:
        q=[];weights=[]
        for a,wa in zip(z,w):
            for b,wb in zip(z,w):q.append((1-a)*(1-b)*p[0]+a*(1-b)*p[1]+a*b*p[2]+(1-a)*b*p[3]);weights.append(wa*wb*abs(np.linalg.det(np.array([p[1]-p[0],p[3]-p[0]]))))
        return np.array(q),np.array(weights)
    q=[];weights=[];jac=abs(np.linalg.det(np.array([p[1]-p[0],p[2]-p[0]])))
    for a,wa in zip(z,w):
        for b,wb in zip(z,w):q.append(p[0]+a*(p[1]-p[0])+(1-a)*b*(p[2]-p[0]));weights.append(wa*wb*(1-a)*jac)
    return np.array(q),np.array(weights)


def make_case(s,source,policy):
    started=time.monotonic()
    name=s['name'];d=source/'cases'/name;refdir=source/'reference'/name;d.mkdir(parents=True,exist_ok=True);refdir.mkdir(parents=True,exist_ok=True)
    nodes,cells,patches=mesh(s,d);R=rotation(s)
    arrays={'clock':np.array([0.]),'domain_ids':np.array(sorted(cells),dtype=np.int64),'node_ids':np.array(sorted(nodes),dtype=np.int64)}
    locations={'domain':dict(kind='mesh',mesh='fluid',entity='element',dimension=2,ids='domain_ids',physical_group=dict(dimension=2,tag=100)),
               'nodes':dict(kind='mesh',mesh='fluid',entity='node',ids='node_ids')}
    qs=[];ws=[]
    for conn in cells.values():
        q,w=quadrature([nodes[k] for k in conn]);qs.extend(q);ws.extend(w)
    qs=np.array(qs);ws=np.array(ws)
    if s.get('gauge')=='mean' or s.get('periodic'):
        s['pressure_shift']=float((exact(s,qs)['pressure'][:,0]@ws)/ws.sum()-s['p0'])
    candidates=np.array([[.37,.29],[1.19,.63],[.61,1.37],[2.71,.81],[3.39,1.61]])
    candidates=np.array([p for p in candidates if inside(*p,s)])@R.T
    arrays.update(probe_ids=np.array([901+13*i for i in range(len(candidates))],dtype=np.int64),probe_xy=candidates,pin_ids=np.array([30001],dtype=np.int64),pin_xy=candidates[:1])
    locations.update(probes=dict(kind='points',ids='probe_ids',coordinates='probe_xy'),pin=dict(kind='points',ids='pin_ids',coordinates='pin_xy'))
    outputs={};fields={};conditions=[];result={'clock':arrays['clock']};result['probe_ids']=arrays['probe_ids']
    base=[('velocity','vector','m/s'),('pressure','scalar','Pa'),('density','scalar','kg/m3'),('dynamic_viscosity','scalar','Pa.s'),('shear_rate','scalar','1/s')]
    ev=exact(s,candidates)
    for q,k,u in base:outputs[q]=field(q,'probes',k,u);result[q]=ev[q][None]
    # Full nodal results and entity/region averages use genuine geometric quadrature.
    node_xy=np.array([nodes[int(k)] for k in arrays['node_ids']]);nv=exact(s,node_xy)
    result['node_ids']=arrays['node_ids'];result['domain_ids']=arrays['domain_ids']
    arrays['mean_ids']=np.array([40001],dtype=np.int64);result['mean_ids']=arrays['mean_ids']
    locations['mean_domain']=dict(kind='aggregate',source='domain',ids='mean_ids',operation='mean')
    for q,k,u in base:
        outputs['nodal_'+q]=field(q,'nodes',k,u,array='nodal_'+q);result['nodal_'+q]=nv[q][None]
        rows=[]
        for cid in arrays['domain_ids']:
            zz,ww=quadrature([nodes[v] for v in cells[int(cid)]]);rows.append(np.einsum('n,nc->c',ww,exact(s,zz)[q])/ww.sum())
        outputs['cell_'+q]=field(q,'domain',k,u,'average','cell_'+q);result['cell_'+q]=np.array(rows)[None]
        outputs['mean_'+q]=field(q,'mean_domain',k,u,'average','mean_'+q)
        result['mean_'+q]=(np.einsum('n,nc->c',ws,exact(s,qs)[q])/ws.sum())[None,None]

    def add_field(key,quantity,loc,values,unit,kind='vector',space='uniform',value_kind='point'):
        if np.max(np.abs(np.asarray(values)-np.asarray(values)[0]))<1e-12:space='uniform'
        elif space=='piecewise_linear':assert s['mesh_kind']=='triangles'
        if space=='uniform':
            loc='domain' if loc=='nodes' else loc.removesuffix('_nodes')
            values=np.tile(np.asarray(values)[0],(len(arrays[locations[loc]['ids']]),1));value_kind='average'
            if s['entity_sampling']:space='piecewise_constant'
        arrays[key]=np.array(values,dtype=float)[None];f=field(quantity,loc,kind,unit,value_kind,key);f['sampling']=dict(space=space,time='constant',extrapolation='hold' if space=='uniform' else 'forbid');fields[key]=f
        return {'field':key}

    patch_normals={};qtotal={}
    for k,(pname,rows) in enumerate(patches.items(),1):
        # location names contain identifiers only, independent of geometry labels.
        key='b'+str(k);ids=np.array(sorted(v[0] for v in rows),dtype=np.int64);arrays[key+'_ids']=ids
        locations[key]=dict(kind='mesh',mesh='fluid',entity='element',dimension=1,ids=key+'_ids',physical_group=dict(dimension=1,tag=k))
        conns={v[0]:v[1] for v in rows};bn=sorted(set(v for _,conn in rows for v in conn))
        arrays[key+'_nodes_ids']=np.array(bn,dtype=np.int64);locations[key+'_nodes']=dict(kind='mesh',mesh='fluid',entity='node',ids=key+'_nodes_ids')
        bx=np.array([nodes[v] for v in bn]);values=exact(s,bx)
        a,b=[nodes[v] for v in rows[0][1]];normal=np.array([b[1]-a[1],a[0]-b[0]]);normal/=np.linalg.norm(normal);patch_normals[pname]=normal
        op='no_slip';data={};ends=s.get('ends')
        if s.get('periodic') and pname in ('left','right'):
            op='periodic';partner='right' if pname=='left' else 'left';pk=list(patches).index(partner)+1
            shift=R@np.array([4. if pname=='left' else -4.,0.])
            data=dict(partner={'location':'b'+str(pk)},translation_x={'value':float(shift[0]),'unit':'m'},translation_y={'value':float(shift[1]),'unit':'m'})
        elif pname in ('top','bottom') and s.get(pname) in ('slip','symmetry'):op=s[pname]
        elif pname=='right' and ends in ('plug','rate','split-rate','hydro-outlet'):
            op='pressure_outlet';data=dict(pressure=add_field(key+'_pressure','reservoir',key+'_nodes',values['pressure'],'Pa','scalar','piecewise_linear'),backflow={'option':'forbid'})
        elif pname.startswith('left') and ends in ('rate','split-rate'):
            op='flow_rate';length=sum(np.linalg.norm(nodes[c[1]]-nodes[c[0]]) for _,c in rows)
            rate=float(-np.dot(values['velocity'][0],normal)*length);assert rate>0
            # Distinct positive shape magnitudes must cancel in each region's normalization.
            sh=7. if pname=='left' else 3.
            data=dict(rate={'value':rate,'unit':'m2/s'},shape=add_field(key+'_shape','profile_shape',key+'_nodes',np.full((len(bn),1),sh),'1','scalar','uniform'))
        elif (ends=='traction' and pname in ('left','right')) or (ends=='mixed' and pname=='right'):
            op='traction';data={'traction':add_field(key+'_traction','total_traction',key+'_nodes',values['stress']@normal,'Pa','vector','piecewise_linear')}
        elif pname.startswith('left') and ends in ('plug','mixed'):
            op='velocity';data={'velocity':add_field(key+'_inflow','inlet_data',key+'_nodes',values['velocity'],'m/s','vector','piecewise_linear')}
        elif np.max(np.abs(values['velocity']))>1e-14:
            op='moving_wall';assert np.max(np.abs(values['velocity']@normal))<1e-12
            data={'velocity':add_field(key+'_wall','wall_data',key+'_nodes',values['velocity'],'m/s','vector','piecewise_linear')}
        conditions.append(dict(role='boundary',variable='flow',operator=op,location=key,data=data))
        # Boundary averages and oriented line integrals, using the same pressure representation.
        tr=[];force=np.zeros(2);flux=0.
        for tag in ids:
            zz,ww=quadrature([nodes[v] for v in conns[int(tag)]]);ev=exact(s,zz);t=ev['stress']@normal
            tr.append(np.einsum('n,nc->c',ww,t)/ww.sum());force-=np.einsum('n,nc->c',ww,t);flux+=float(ww@(ev['velocity']@normal))
        qtotal[pname]=flux
        outputs[key+'_traction']=field('traction',key,'vector','Pa','average',key+'_traction_out');result[key+'_traction_out']=np.array(tr)[None];result[key+'_ids']=ids
        aid=key+'_sum_ids';arrays[aid]=np.array([80001+k],dtype=np.int64);result[aid]=arrays[aid]
        locations[key+'_sum']=dict(kind='aggregate',source=key,ids=aid,operation='sum')
        for quantity,value,kind,unit in [('force',force,'vector','N/m'),('volume_flow',[flux],'scalar','m2/s'),('mass_flow',[s['rho']*flux],'scalar','kg/(m.s)')]:
            out=key+'_'+quantity;outputs[out]=field(quantity,key+'_sum',kind,unit,'integral',out);result[out]=np.array(value,dtype=float)[None,None]
    # Curvature requires acceleration only when not driven by pressure.
    H=max(v[3] for v in s['boxes']);curvature=(2*s['B'] if s.get('top') in ('slip','symmetry') and s['B']<0 else -2*s['B'])
    accel=np.array(s['g'],dtype=float)
    if not s.get('pressure_drive'):accel[0]-=s['mu']/s['rho']*curvature
    if np.any(accel):
        chunks=[accel] if not s.get('split_source') else [np.array([accel[0],0.]),np.array([0.,accel[1]])]
        for i,chunk in enumerate(chunks):
            val=np.tile(R@chunk,(len(nodes),1));key='acceleration_'+str(i)
            conditions.append(dict(role='source',variable='velocity',operator='acceleration',location='domain',data={'value':add_field(key,'body_acceleration','nodes',val,'m/s2','vector','uniform')}))
    pressure={'representation':'absolute'} if s.get('absolute') else dict(representation='gauge',reference_pressure={'value':101325.,'unit':'Pa'})
    analysis=dict(type='steady',compressibility='incompressible',flow_regime='laminar',temperature={'value':293.,'unit':'K'},pressure=pressure)
    if not any(c['operator'] in ('traction','pressure_outlet') for c in conditions):
        if s.get('gauge')=='mean' or s.get('periodic'):analysis['pressure_gauge']=dict(kind='mean',location='domain',value={'value':s['p0'],'unit':'Pa'})
        else:analysis['pressure_gauge']=dict(kind='point',location='pin',value={'value':float(exact(s,candidates[:1])['pressure'][0,0]),'unit':'Pa'})
    j=dict(task='newtonian-incompressible-steady-2d',spatial_dimension=2,contract_version=2,profile='cfd-2.1',data_file='input.h5',geometries={},meshes={'fluid':{'file':'mesh.msh'}},locations=locations,time_axes={'steady':'clock'},fields=fields,outputs=outputs,conditions=conditions,analysis=analysis,
      materials={'liquid':dict(region='domain',density=dict(kind='constant',parameters={'density':{'value':s['rho'],'unit':'kg/m3'}}),viscosity=dict(kind='newtonian',parameters={'dynamic_viscosity':{'value':s['mu'],'unit':'Pa.s'}}))})
    (d/'problem.json').write_text(json.dumps(j,indent=2)+'\n')
    with h5py.File(d/'input.h5','w') as h:
        for key,value in arrays.items():h[key]=value
    with h5py.File(refdir/'reference.h5','w') as h:
        for key,value in result.items():h[key]=value
    (refdir/'grading.json').write_text(json.dumps(dict(version=1,checks=[dict(id='all_outputs',evaluator='direct_outputs',reference='reference.h5',policy=policy)]),indent=2)+'\n')
    # Direct differential balance, not a second source for the reference values.
    gp=np.array(s['g'])*s['rho']
    if s.get('pressure_drive'):gp[0]=s['mu']*curvature
    residual=-gp+np.array([s['mu']*curvature,0.])+s['rho']*accel
    assert np.max(np.abs(residual))<1e-12
    assert abs(sum(qtotal.values()))<1e-12
    return dict(definition=s,area=float(ws.sum()),boundary_fluxes=qtotal,momentum_residual=float(np.max(np.abs(residual))),
                seconds=time.monotonic()-started,
                analytic_source=s['source'],formula='u=A+C*y+B*y*(H-y); half-channel u=A+C*y+B*y^2; p=p0+grad(p).x; stress=-pI+mu*(grad(u)+grad(u).T)',
                reference_kind='published exact parallel-plate / hydrostatic formula evaluation',numerical_solver_used=False)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('policy',type=Path);p.add_argument('report',type=Path);a=p.parse_args()
    policy=json.loads(a.policy.read_text());records=[make_case(s,a.source,policy) for s in specifications()]
    a.report.write_text(json.dumps(records,indent=2)+'\n');print('Created',len(records),'published-exact cases')
