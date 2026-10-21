"""Configure unmodified Elmer FlowSolver and translate its P1 fields.

This module contains geometry, configuration and storage adapters, no PDE
implementation. Frozen experiment definitions are never altered. All resulting
fields are unvalidated candidates, including fields from iteration-limited runs.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path
import h5py
import numpy as np
from native_closed_cavity import SOCKET,save,digest,put
from native_gas_film import IMAGE,COMMIT
from polytropic_reference import gmsh
from elmer_flow_mesh import generate,partitions,write_native


def vector_expr(v,d):
    if isinstance(v,list):return v
    assert v in ('(.1*sin(2*pi*Y),0[,0])','(0.1*sin(2*pi*Y),0[,0])'),v
    return ['.1*sin(2*pi*Y)']+[0]*(d-1)


def evaluate(expr,x,t,s):
    d=x.shape[1];L=s['geometry']['bounding_lengths'];end=(s['time_interval_s'] or [0,1])[1]
    R=1 if s['analysis_kind']=='steady' else np.clip(t/(.1*end),0,1)
    down=0 if s['analysis_kind']=='steady' else np.clip((t-.4*end)/(.2*end),0,1)
    ns={a:x[:,j]/L[j] for j,a in enumerate('XYZ'[:d])}
    ns['B']=np.maximum(1-np.sum(((x/np.array(L)-.5)/.2)**2,axis=1),0)**4
    ns.update(R=R,P=R-down,V=R-2*down,pi=np.pi,sin=np.sin,cos=np.cos,abs=np.abs,min=np.minimum,max=np.maximum,sqrt=np.sqrt)
    if isinstance(expr,list):return np.column_stack([evaluate(v,x,t,s) for v in expr])
    if isinstance(expr,(float,int)):return np.full(len(x),expr,dtype=float)
    return np.broadcast_to(eval(expr.replace('^','**'),{'__builtins__':{}},ns),(len(x),)).copy()


def matc(expr,s):
    d=s['geometry']['dimension'];L=s['geometry']['bounding_lengths'];end=(s['time_interval_s'] or [0,1])[1]
    t=f'tx({d})';r=f'(.5*({t}/{.1*end}+1-abs({t}/{.1*end}-1)))'
    down=f'(.5*(({t}-{.4*end})/{.2*end}+abs(({t}-{.4*end})/{.2*end}))-.5*(({t}-{.6*end})/{.2*end}+abs(({t}-{.6*end})/{.2*end})))'
    names={'R':r,'P':f'({r}-{down})','V':f'({r}-2*{down})'} if s['analysis_kind']!='steady' else {'R':'1','P':'1','V':'1'}
    names.update({a:f'(tx({j})/{L[j]})' for j,a in enumerate('XYZ'[:d])});names['pi']=str(np.pi)
    return re.sub(r'\b(?:X|Y|Z|R|P|V|pi)\b',lambda m:names[m[0]],str(expr).replace('**','^'))


def function(key,expr,s):
    axes=', '.join([f'Coordinate {j+1}' for j in range(s['geometry']['dimension'])]+['Time'])
    return f'{key} = Variable {axes}\n Real MATC "{matc(expr,s)}"\n'


def material(s):
    v=s['materials']['viscosity'];p={k:q['value'] for k,q in v['parameters'].items()};kind=v['kind']
    txt='Density = Real 1\n'
    if kind=='newtonian':return txt+f'Viscosity = Real {p["dynamic_viscosity"]}\n'
    assert kind in ('cross','carreau','carreau_yasuda'),kind
    txt+=f'Viscosity Model = String "{"cross" if kind=="cross" else "carreau"}"\nViscosity = Real {p["infinite_shear_viscosity"]}\nViscosity Difference = Real {p["zero_shear_viscosity"]-p["infinite_shear_viscosity"]}\n'
    exponent=p['cross_exponent'] if kind=='cross' else p['power_index']
    transition=p['relaxation_time']**exponent if kind=='cross' else p['relaxation_time']
    txt+=f'Viscosity Exponent = Real {exponent}\nViscosity Transition = Real {transition}\n'
    if kind=='carreau_yasuda':txt+=f'Yasuda Exponent = Real {p["transition_index"]}\n'
    return txt


def rate_values(data,t,s):
    if 'rate_m_dimension_per_s' in data:return data['rate_m_dimension_per_s']
    r=data['rate'];value=float(r['expression']);history=r['time_history'];assert isinstance(history,dict)
    samples=np.array(history['samples']);return value*np.interp(t,samples[:,0],samples[:,1])


def rate_expr(data,s):
    if 'rate_m_dimension_per_s' in data:return str(data['rate_m_dimension_per_s'])
    r=data['rate'];end=s['time_interval_s'][1]
    assert np.allclose(r['time_history']['samples'],[[0,1],[.1*end,1.5],[end,1.5]])
    return f'{r["expression"]}*(1+.5*R)'


def prepare(job,e,linear_method=None):
    s=e['detailed_spec'];d=e['spatial_dimension'];m=generate(s);groups=partitions(s,m)
    pin=not any(b['operator'] in ('pressure_outlet','traction') for b in s['boundaries'])
    nativegroups=groups.copy();nexttag=len(s['boundaries'])
    for i,bc in enumerate(s['boundaries']):
        if bc['operator']=='flow_rate':
            for j in np.flatnonzero(groups==i):nativegroups[j]=nexttag;nexttag+=1
    write_native(job/'native/mesh',m,nativegroups,pin)
    transient=s['analysis_kind']=='transient';end=(s['time_interval_s'] or [0,1])[1]
    txt=f'''Header
 CHECK KEYWORDS Warn
 Mesh DB "." "mesh"
 Results Directory "."
End
Simulation
 Coordinate System = Cartesian {d}D
 Simulation Type = {"Transient" if transient else "Steady"}
 Steady State Max Iterations = 1
 Set Dirichlet BCs by BC Numbering = Logical True
'''
    if transient:txt+=f'Timestepping Method = BDF\nBDF Order = 1\nTimestep Intervals(1) = 1000\nTimestep Sizes(1) = {end/1000}\nOutput Intervals(1) = 1\n'
    txt+='''End
Body 1
 Target Bodies(1) = 1
 Equation = 1
 Material = 1
 Body Force = 1
 Initial Condition = 1
End
Solver 1
 Equation = Navier-Stokes
 Procedure = "FlowSolve" "FlowSolver"
'''+f' Variable = "Flow Solution[Velocity:{d} Pressure:1]"\n'+''' Stabilization Method = Stabilized
 Laplace Discretization = Logical False
 Nonlinear System Max Iterations = 100
 Nonlinear System Convergence Tolerance = 1e-8
 Nonlinear System Newton After Iterations = 1000000
 Nonlinear System Newton After Tolerance = 0
 Nonlinear System Relaxation Factor = 0.8
 Linear System Solver = Iterative
 Linear System Iterative Method = BiCGStabL
 Linear System Preconditioning = ILU1
 Linear System Max Iterations = 1000
 Linear System Convergence Tolerance = 1e-10
 Linear System Residual Output = 0
End
Solver 2
 Exec Solver = After Timestep
 Equation = ResultOutput
 Procedure = "ResultOutputSolve" "ResultOutputSolver"
 Output File Name = "solution"
 Vtu Format = Logical True
 Binary Output = Logical False
End
Equation 1
 Active Solvers(2) = 1 2
End
Material 1
'''+material(s)+'End\nInitial Condition 1\nPressure = Real 0\n'
    init=s['initial'].get('velocity',{'expression':[0]*d})['expression']
    assert isinstance(init,list) and all(isinstance(v,(float,int)) for v in init)
    txt+=''.join(f'Velocity {j+1} = Real {v}\n' for j,v in enumerate(init))+'End\nBody Force 1\n'
    for key,field in s['sources'].items():
        assert key=='acceleration'
        txt+=''.join(function(f'Flow Bodyforce {j+1}',v,s) for j,v in enumerate(vector_expr(field['expression'],d)))
    txt+='End\n'
    for i,bc in enumerate(s['boundaries']):
        if not np.any(groups==i):continue
        if bc['operator']=='flow_rate':
            ids=np.flatnonzero(groups==i);data=bc['data'];Y=m['x'][m['b'][ids]].mean(axis=1)[:,1]/s['geometry']['bounding_lengths'][1]
            assert np.allclose(m['normal'][ids],[-1]+[0]*(d-1))
            shape=data['shape']['expression'];assert shape in ('1+0.5*Y','1+.5*R*Y')
            area=m['measure'][ids].sum();moment=np.dot(m['measure'][ids],Y);factor='1' if shape=='1+0.5*Y' else 'R'
            for j,y in zip(ids,Y):
                txt+=f'Boundary Condition {nativegroups[j]+1}\nTarget Boundaries(1) = {nativegroups[j]+1}\n'
                value=f'({rate_expr(data,s)})*(1+.5*({factor})*{y})/({area}+.5*({factor})*{moment})'
                txt+=function('Velocity 1',value,s)+''.join(f'Velocity {axis+1} = Real 0\n' for axis in range(1,d))+'End\n'
            continue
        txt+=f'Boundary Condition {i+1}\nTarget Boundaries(1) = {i+1}\n'
        op=bc['operator'];data=bc['data']
        if op in ('no_slip','velocity','moving_wall'):
            expr=[0]*d if op=='no_slip' else data['velocity']['expression']
            txt+=''.join(function(f'Velocity {j+1}',v,s) for j,v in enumerate(expr))
        elif op in ('slip','symmetry'):
            # Native normal/tangential coordinates also support a partition
            # containing several differently oriented planes in 3D.
            txt+='Normal-Tangential Velocity = Logical True\nVelocity 1 = Real 0\n'
        elif op=='pressure_outlet':txt+=f'External Pressure = Real {data["pressure_Pa"]}\n'
        elif op=='traction':
            expr=data['traction']['expression']
            if expr=='-R*0.1*n':txt+=function('External Pressure','R*0.1',s)
            else:
                assert expr==[0.]*d
                txt+=''.join(f'Pressure {j+1} = Real 0\n' for j in range(d))
        else:raise ValueError(op)
        txt+='End\n'
    if pin:txt+=f'Boundary Condition {len(s["boundaries"])+1}\nTarget Boundaries(1) = {groups.max()+2}\nPressure = Real 0\nEnd\n'
    if d==2 or linear_method=='UMFPACK':txt=txt.replace('Linear System Solver = Iterative','Linear System Solver = Direct\nLinear System Direct Method = UMFPACK')
    put(job/'native/case.sif',txt);np.savez(job/'adapter-data.npz',**m,groups=groups)
    return m,groups


def mu_of(g,s):
    v=s['materials']['viscosity'];p={k:q['value'] for k,q in v['parameters'].items()}
    if v['kind']=='newtonian':return np.full(len(g),p['dynamic_viscosity'])
    a=p.get('transition_index',2);lam=p['relaxation_time'];lo=p['infinite_shear_viscosity'];delta=p['zero_shear_viscosity']-lo
    if v['kind']=='cross':return lo+delta/(1+(lam*g)**p['cross_exponent'])
    return lo+delta*(1+(lam*g)**a)**((p['power_index']-1)/a)


def package(job,e,m,groups,native_cell_frames=None):
    s=e['detailed_spec'];x=m['x'];c=m['c'];b=m['b'];d=x.shape[1];n=len(x);nc=len(c);nb=len(b);L=np.array(s['geometry']['bounding_lengths'])
    inp=job/'input';ref=job/'reference';inp.mkdir(exist_ok=True);ref.mkdir(exist_ok=True);gmsh(inp/'mesh.msh',x,c,b,d)
    transient=s['analysis_kind']=='transient';end=(s['time_interval_s'] or [0,1])[1];ts=np.array([0,.1*end,.4*end,.6*end,end] if transient else [0.]);ot=s['output_times_s']
    def loc(entity,ids,dim=None):return {'kind':'mesh','mesh':'main','entity':entity,'ids':ids,**({'dimension':dim} if dim is not None else {})}
    locations={'domain':loc('element','cells',d),'nodes':loc('node','nodes')};fields={};conditions=[];arrays={'cells':np.arange(1,nc+1,dtype=np.int64),'nodes':np.arange(1,n+1,dtype=np.int64),'history':ts,'initial':np.array([0.]),'requested':np.array(ot)}
    def desc(q,location,unit,components=1,axis='requested',kind='average',input=False):
        z={'array':q,'quantity':q,'location':location,'time_axis':axis,'dtype':'float64','kind':'scalar' if components==1 else 'vector','component_shape':[components],'components':['value'] if components==1 else list('xyz'[:components]),'unit':unit,'value_kind':kind}
        if input:z['sampling']={'space':'piecewise_linear' if kind=='point' else 'piecewise_constant','time':'constant' if axis=='initial' or not transient else 'linear','extrapolation':'forbid'}
        return z
    def field(name,q,expr,nodes,location,unit,role,operator,condition_location,axis='history'):
        arr=np.array([evaluate(expr,x[nodes],t,s) for t in (ts if axis=='history' else [0.])]);arr=arr[...,None] if arr.ndim==2 else arr
        arrays[name]=arr;fields[name]=desc(q,location,unit,arr.shape[-1],axis,'point',True);fields[name]['array']=name
        conditions.append({'role':role,'variable':'flow' if role=='boundary' else 'velocity','operator':operator,'location':condition_location,'data':{'velocity' if role=='boundary' else 'value':{'field':name}}})
    if transient:field('initial_velocity','velocity',s['initial']['velocity']['expression'],np.arange(n),'nodes','m/s','initial','assign','domain','initial')
    for key,v in s['sources'].items():field(key,key,vector_expr(v['expression'],d),np.arange(n),'nodes','m/s2','source','acceleration','domain')
    for i,bc in enumerate(s['boundaries']):
        ids=np.flatnonzero(groups==i)
        if not len(ids):continue
        name=f'boundary{i+1}';arrays[name]=(nc+ids+1).astype(np.int64);locations[name]=loc('element',name,d-1)
        op=bc['operator'];data=bc['data']
        if op in ('moving_wall','velocity'):
            idsnode=np.unique(b[ids]);nl=name+'nodes';arrays[nl]=(idsnode+1).astype(np.int64);locations[nl]=loc('node',nl)
            field(name+'velocity','velocity',data['velocity']['expression'],idsnode,nl,'m/s','boundary',op,name)
        elif op=='flow_rate':
            rk=name+'rate';unit='m2/s' if d==2 else 'm3/s';arrays[rk]=np.array([np.full((len(ids),1),rate_values(data,t,s)) for t in ts]);fields[rk]=desc('rate',name,unit,1,'history','average',True);fields[rk]['array']=rk;fields[rk]['sampling']['space']='uniform'
            sh=name+'shape';original=data['shape'];expr=original['expression']
            if original['space_reconstruction']=='piecewise_linear':
                nodes=np.unique(b[ids]);nl=name+'nodes';arrays[nl]=(nodes+1).astype(np.int64);locations[nl]=loc('node',nl);where=nl;pos=x[nodes];vk='point'
            else:where=name;pos=x[b[ids]].mean(axis=1);vk='average'
            arrays[sh]=np.array([evaluate(expr,pos,t,s) for t in ts])[...,None];fields[sh]=desc('shape',where,'1',1,'history',vk,True);fields[sh]['array']=sh
            conditions.append({'role':'boundary','variable':'flow','operator':op,'location':name,'data':{'rate':{'field':rk},'shape':{'field':sh}}})
        elif op=='traction':
            expr=data['traction']['expression'];q=name+'traction';v=np.array([-0.1*evaluate('R',x[b[ids]].mean(axis=1),t,s)[:,None]*m['normal'][ids] if expr=='-R*0.1*n' else np.zeros((len(ids),d)) for t in ts]);arrays[q]=v;fields[q]=desc('traction',name,'Pa',d,'history','average',True);fields[q]['array']=q
            conditions.append({'role':'boundary','variable':'flow','operator':op,'location':name,'data':{'traction':{'field':q}}})
        elif op=='pressure_outlet':conditions.append({'role':'boundary','variable':'flow','operator':op,'location':name,'data':{'pressure':{'value':data['pressure_Pa'],'unit':'Pa'},'backflow':{'option':'forbid'}}})
        else:conditions.append({'role':'boundary','variable':'flow','operator':op,'location':name,'data':{}})
    # Omit derivative traces adjoining a geometric corner or BC intersection.
    normals_by_node=[[] for _ in x];groups_by_node=[set() for _ in x]
    for j,row in enumerate(b):
        for node in row:normals_by_node[node].append(m['normal'][j]);groups_by_node[node].add(groups[j])
    singular=np.array([len(g)>1 or (len(v)>0 and not np.allclose(v,v[0])) for g,v in zip(groups_by_node,normals_by_node)])
    traces=np.flatnonzero(~np.any(singular[b],axis=1));assert len(traces)
    arrays['traces']=(nc+traces+1).astype(np.int64);locations['traces']=loc('element','traces',d-1)
    outlet=next((i for i,q in enumerate(s['boundaries']) if q['selection']=='x=Lx'),None)
    integral=np.flatnonzero(groups==outlet) if outlet is not None else np.flatnonzero(np.isclose(x[b].mean(axis=1)[:,1],L[1]) & (x[b].mean(axis=1)[:,0]>.25*L[0]) & (x[b].mean(axis=1)[:,0]<.75*L[0]))
    arrays['integral_faces']=(nc+integral+1).astype(np.int64);arrays['aggregate']=np.array([1],dtype=np.int64);locations['integral_faces']=loc('element','integral_faces',d-1);locations['aggregate']={'kind':'aggregate','source':'integral_faces','ids':'aggregate','operation':'sum'}
    outputs={}
    for request in s['observation_requests']:
        q=request['quantity'];where='traces' if q=='traction' else 'aggregate' if q in ('force','volume_flow','mass_flow') else 'domain'
        outputs[q]=desc(q,where,request['unit'],d if q in ('velocity','traction','force') else 1,kind=request['value_kind'])
    a=s['analysis'];analysis={'type':s['analysis_kind'],'compressibility':'incompressible','flow_regime':'laminar','temperature':{'value':a['temperature_K'],'unit':'K'},'pressure':{'representation':a['pressure_representation'],'reference_pressure':{'value':a['reference_pressure_Pa'],'unit':'Pa'}}}
    if transient:analysis['time_interval']={'start':s['time_interval_s'][0],'end':end}
    gauge=a.get('pressure_gauge')
    if gauge:
        where='domain'
        if gauge['kind']=='point':
            where='gauge_point';arrays['gauge_id']=np.array([1],dtype=np.int64);arrays['gauge_coordinates']=np.array([gauge['point_m']],dtype=np.float64);locations[where]={'kind':'points','ids':'gauge_id','coordinates':'gauge_coordinates'}
        analysis['pressure_gauge']={'kind':gauge['kind'],'location':where,'value':{'value':gauge['value_Pa'],'unit':'Pa'}}
    problem={'task':e['task'],'contract_version':2,'profile':'cfd-2.1','spatial_dimension':d,'materials':{'fluid':{'region':'domain',**s['materials']}},'analysis':analysis,'data_file':'input.h5','geometries':{},'meshes':{'main':{'file':'mesh.msh'}},'locations':locations,'time_axes':{'history':'history','initial':'initial','requested':'requested'},'fields':fields,'conditions':conditions,'outputs':outputs}
    save(inp/'problem.json',problem)
    with h5py.File(inp/'input.h5','w') as f:
        for k,v in arrays.items():f[k]=v
    if native_cell_frames is not None:
        assert set(outputs)<=set(native_cell_frames) and set(outputs)<= {'velocity','pressure'}
        with h5py.File(ref/'reference.h5','w') as f:
            for k in {locations[o['location']]['ids'] for o in outputs.values()}|{'requested'}:f[k]=arrays[k]
            for q in outputs:
                values=np.asarray(native_cell_frames[q]);assert values.shape==(len(ot),nc,d if q=='velocity' else 1) and np.isfinite(values).all()
                f[q]=values
        return {'reference_sha256':digest(ref/'reference.h5'),'nodes':n,'cells':nc,'frames':len(ot),'mapping':'Native high-order field cell averages supplied by source-specific I/O adapter; original frozen input sampling preserved. No accuracy validation.'}
    files=sorted((job/'native').rglob('solution*.vtu'));assert len(files)==(1000 if transient else 1),len(files)
    frames={q:[] for q in outputs};A=x[c][:,1:]-x[c][:,:1]
    for t in ot:
        path=files[round(t/end*1000)-1] if transient else files[-1];tree=ET.parse(path);pos=np.fromstring(tree.find('.//Points/DataArray').text,sep=' ').reshape(-1,3)[:,:d]
        from scipy.spatial import cKDTree
        distance,order=cKDTree(pos).query(x);assert len(np.unique(order))==n and distance.max()<max(L)*1e-7,'native node identity differs'
        fields_native={a.get('Name').lower():np.fromstring(a.text,sep=' ').reshape(n,-1) for a in tree.findall('.//PointData/DataArray')}
        u=fields_native['velocity'][order,:d];p=fields_native['pressure'][order,0];assert np.all(np.isfinite(u)) and np.all(np.isfinite(p))
        gauge=s['analysis'].get('pressure_gauge')
        if gauge:
            if gauge['kind']=='mean':offset=np.dot(m['volume'],p[c].mean(axis=1))/sum(m['volume'])
            else:
                pt=np.array(gauge['point_m']);w=np.linalg.solve(np.swapaxes(A,1,2),(pt-x[c[:,0]])[...,None])[...,0];good=np.flatnonzero((w>=-1e-10).all(axis=1)&(w.sum(axis=1)<=1+1e-10));assert len(good)
                j=good[0];offset=(1-w[j].sum())*p[c[j,0]]+w[j]@p[c[j,1:]]
            p=p-offset+gauge['value_Pa']
        # grad[entity, component, derivative], exact P1 element derivative.
        grad=np.swapaxes(np.linalg.solve(A,u[c][:,1:]-u[c][:,:1]),1,2);twod=grad+np.swapaxes(grad,1,2);g=np.sqrt(.5*np.sum(twod**2,axis=(1,2)));mu=mu_of(g,s)
        sigma=mu[:,None,None]*twod-p[c].mean(axis=1)[:,None,None]*np.eye(d)
        parent=m['parent'];traction=mu[parent,None]*np.einsum('bij,bj->bi',twod[parent],m['normal'])-p[b].mean(axis=1)[:,None]*m['normal']
        vals={'velocity':u[c].mean(axis=1),'pressure':p[c].mean(axis=1)[:,None],'density':np.ones((nc,1)),'dynamic_viscosity':mu[:,None],'shear_rate':g[:,None],'traction':traction[traces],
              'force':-np.sum(traction[integral]*m['measure'][integral,None],axis=0)[None], 'volume_flow':np.array([[np.sum(np.einsum('ij,ij->i',u[b[integral]].mean(axis=1),m['normal'][integral])*m['measure'][integral])]])}
        vals['mass_flow']=vals['volume_flow'].copy()
        for q in outputs:assert np.all(np.isfinite(vals[q]));frames[q].append(vals[q])
    with h5py.File(ref/'reference.h5','w') as f:
        for k in {locations[o['location']]['ids'] for o in outputs.values()}|{'requested'}:f[k]=arrays[k]
        for q,v in frames.items():f[q]=np.array(v)
    mapping='Native stabilized P1 velocity/pressure; cell averages and exact P1 derivatives; traction from parent-element gradient and face-mean pressure. No convergence or accuracy certification.'
    if any(b['operator']=='flow_rate' for b in s['boundaries']):mapping+=' Flow-rate normalization uses actual face-average shapes and measures. Native continuous FE Dirichlet nodes approximate the resulting facewise constant boundary data; interface-node ambiguity is an unquantified discretization limitation.'
    return {'reference_sha256':digest(ref/'reference.h5'),'nodes':n,'cells':nc,'frames':len(ot),'mapping':mapping}


def run(root,e,grading,linear_method=None):
    job=root/'cases'/e['design_id'];status=job/'status.json'
    if status.exists():return json.loads(status.read_text())
    job.mkdir(parents=True);save(job/'design.json',e);state={'design_id':e['design_id'],'status':'preparing'};save(status,state)
    lease=None
    try:
        name='ch02elmer-'+hashlib.sha256(e['design_id'].encode()).hexdigest()[:12]+'-'+str(time.time_ns())[-9:]
        from titan_resources import reservation
        lease=reservation(root,name);lease.__enter__()
        m,groups=prepare(job,e,linear_method)
        cmd=['docker','--host',SOCKET,'run','--name',name,'--network','none','--cpus','1','--memory','768m','--user',f'{os.getuid()}:{os.getgid()}','-e','OMP_NUM_THREADS=1','-e','OPENBLAS_NUM_THREADS=1','-e','MKL_NUM_THREADS=1','-v',f'{job.resolve()}:/work','-w','/work/native',IMAGE,'ElmerSolver','case.sif']
        save(job/'execution.json',{'command':cmd,'start_unix':time.time(),'source_commit':COMMIT,'source_url':f'https://github.com/ElmerCSC/elmerfem/blob/{COMMIT}/fem/src/modules/FlowSolve.F90','image':IMAGE,'script_sha256':digest(Path(__file__)),'mesh_adapter_sha256':digest(Path(__file__).with_name('elmer_flow_mesh.py')),'linear_method_override':linear_method,'numerical_validation':False,'iterations_are_not_an_accuracy_certificate':True})
        state.update(status='running',container=name);save(status,state)
        with (job/'solver.log').open('w') as log:cp=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
        assert cp.returncode==0,f'Elmer exit {cp.returncode}'
        state.update(package(job,e,m,groups));save(job/'reference/grading.json',grading);state['status']='unvalidated_candidate'
    except Exception as ex:state.update(status='needs_attention',error=repr(ex))
    finally:
        if lease is not None:lease.__exit__(None,None,None)
    state['ended_unix']=time.time();save(status,state);return state


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int,default=40);ap.add_argument('--only');ap.add_argument('--linear-method',choices=['UMFPACK']);args=ap.parse_args();assert 1<=args.workers<=40
    frozen=json.loads((args.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text());tasks=[]
    for p in args.snapshot.glob('qbank/02-fluid-mechanics/*/*/author/chapter02-ten-20261020/design.json'):
        r=json.loads(p.read_text());assert digest(p)==frozen['designs'][p.relative_to(args.snapshot).as_posix()]
        if r['family'] not in ('closed_flow','generalized_flow'):continue
        for e in r['proposed_cases']:
            i=int(e['design_id'].split('-')[-2])-1
            if i not in ([1,2,4,6,7] if r['family']=='closed_flow' else [2,3,4,6,7,8]):continue
            e={**e,'model':r['model'],'task':r['task']}
            if args.only and args.only not in e['design_id']:continue
            tasks.append((e,json.loads((p.parents[1]/'grading-template.json').read_text())))
    # CPU allocation includes all submitted jobs. One native worker per core;
    # one process per Gmsh state. Limit is also bounded by actual memory headroom.
    mem=int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024
    out=json.loads(subprocess.check_output(['docker','inspect','caeoj-solver-library-daemon']))[0]
    pid=out['State']['Pid'];cg=next(l.split(':',2)[2] for l in Path(f'/proc/{pid}/cgroup').read_text().splitlines() if l.startswith('0::')).strip();parent=Path('/sys/fs/cgroup')/cg.lstrip('/')
    limits=[]
    for level in [parent,*parent.parents]:
        cap=level/'memory.max'
        if cap.exists() and cap.read_text().strip()!='max':
            stat=dict(line.split() for line in (level/'memory.stat').read_text().splitlines())
            # Same reclaimable-cache accounting as Docker's working set. Preserve
            # an additional 8 GiB after every worker's full memory reservation.
            used=int((level/'memory.current').read_text())-int(stat.get('inactive_file',0))
            limits.append(int(cap.read_text())-used)
    assert limits,'outer memory constraint not found'
    avail=min(limits);workers=min(args.workers,len(tasks),max(0,int((min(mem,avail)-8*1024**3)/(768*1024**2))))
    assert workers>0,'insufficient real memory headroom'
    save(args.root/'maintenance/elmer-flow-plan.json',{'jobs':[e['design_id'] for e,g in tasks],'workers':workers,'cpu_quota':40,'host_available_bytes':mem,'parent_available_bytes':avail,'time':time.time(),'numerical_validation':False})
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=workers) as pool:states=list(pool.map(run,[args.root]*len(tasks),[e for e,g in tasks],[g for e,g in tasks],[args.linear_method]*len(tasks)))
    save(args.root/'maintenance/elmer-flow-summary.json',states)
    print(json.dumps({'completed':sum(s['status']=='unvalidated_candidate' for s in states),'attention':[s for s in states if s['status']=='needs_attention']}))


if __name__=='__main__':main()
