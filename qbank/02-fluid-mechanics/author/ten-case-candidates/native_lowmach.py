"""Couple unmodified Elmer FlowSolver and HeatSolver for low-Mach cases.

Native Friction Heat retains viscous dissipation; the specified acceleration
is multiplied by 1-beta*(T-Tref), with no undeclared gravity. Native P1
discretization and constitutive interpolation errors are not assessed here.
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
import numpy as np
import h5py
from scipy.spatial import cKDTree
from elmer_flow_mesh import generate,partitions,write_native,select
from native_closed_cavity import SOCKET,save,put,digest
from native_gas_film import IMAGE,COMMIT
from native_elmer_incompressible import matc,evaluate,function
from polytropic_reference import gmsh
from titan_resources import reservation


def sample(expr,x,t,s):
    if isinstance(expr,list):return np.column_stack([sample(q,x,t,s) for q in expr])
    if isinstance(expr,str) and 'bump' in expr:
        return evaluate(expr.replace('bump(centre=.5*L,radius=.2*L)','B'),x,t,s)
    return evaluate(expr,x,t,s)


def boundary_groups(s,m):
    mid=m['x'][m['b']].mean(axis=1);L=np.array(s['geometry']['bounding_lengths']);thermal=np.full(len(mid),-1,dtype=int);fallback=None
    for i,b in enumerate(s['thermal_partition']):
        if 'inner obstacle' in b['selection']:take=~np.any(np.isclose(mid,0,atol=max(L)*1e-8)|np.isclose(mid,L,atol=max(L)*1e-8),axis=1)
        else:take=select(s,b['selection'],mid)
        if take is None:fallback=i;continue
        assert not np.any(thermal[take]>=0);thermal[take]=i
    if fallback is not None:thermal[thermal<0]=fallback
    assert np.all(thermal>=0)
    mech=partitions(s,m);pairs=list(dict.fromkeys(zip(mech.tolist(),thermal.tolist())));joint=np.array([pairs.index((a,b)) for a,b in zip(mech,thermal)])
    return mech,thermal,joint,pairs


def cell_source(expr,x,c,t,s):
    # A fixed barycentric quadrature constructs the supplied P0 input samples;
    # the resulting constants, not an implicit smooth function, drive Elmer.
    d=x.shape[1];bary=np.vstack((np.full(d+1,1/(d+1)),np.eye(d+1)*.5+np.full((d+1,d+1),.5/(d+1))))
    return np.mean([sample(expr,np.einsum('j,ijk->ik',w,x[c]),t,s) for w in bary],axis=0)


def prepare(job,e):
    s=e['detailed_spec'];d=e['spatial_dimension'];m=generate(s);mech,thermal,joint,pairs=boundary_groups(s,m);write_native(job/'native/mesh',m,joint,True)
    p={k:v['value'] for k,v in s['parameters'].items()};transient=s['analysis_kind']=='transient';end=(s['time_interval_s'] or [0,1])[1];hist=np.array([0,.1*end,.4*end,.6*end,end] if transient else [0.]);x=m['x'];c=m['c'];source=s['sources'].get('heat_source');sources=np.array([cell_source(source['expression'],x,c,t,s) for t in hist]) if source else np.zeros((len(hist),len(c)))
    txt=f'''Header
 CHECK KEYWORDS Warn
 Mesh DB "." "mesh"
 Results Directory "."
End
Simulation
 Coordinate System = Cartesian {d}D
 Simulation Type = {"Transient" if transient else "Steady"}
 Steady State Max Iterations = {20 if transient else 300}
 Set Dirichlet BCs by BC Numbering = Logical True
'''
    if transient:txt+=f'Timestepping Method = BDF\nBDF Order = 1\nTimestep Intervals(1) = 1000\nTimestep Sizes(1) = {end/1000}\nOutput Intervals(1) = 1\n'
    txt+='End\n'
    bodies=len(c) if source else 1
    if source:
        path=job/'native/mesh/mesh.elements';rows=path.read_text().splitlines();path.write_text('\n'.join(' '.join([str(i+1),str(i+1),*row.split()[2:]]) for i,row in enumerate(rows))+'\n')
    for i in range(bodies):txt+=f'Body {i+1}\nTarget Bodies(1) = {i+1}\nEquation = 1\nMaterial = 1\nBody Force = {i+1}\nInitial Condition = 1\nEnd\n'
    txt+='''Solver 1
 Equation = Navier-Stokes
 Procedure = "FlowSolve" "FlowSolver"
'''+f'Variable = "Flow Solution[Velocity:{d} Pressure:1]"\n'+''' Stabilization Method = Stabilized
 Laplace Discretization = Logical False
 Steady State Convergence Tolerance = 1e-8
 Nonlinear System Max Iterations = 30
 Nonlinear System Convergence Tolerance = 1e-8
 Nonlinear System Newton After Iterations = 1000000
 Nonlinear System Newton After Tolerance = 0
 Nonlinear System Relaxation Factor = 0.7
 Linear System Solver = Iterative
 Linear System Iterative Method = BiCGStabL
 Linear System Preconditioning = ILU1
 Linear System Max Iterations = 1000
 Linear System Convergence Tolerance = 1e-10
 Linear System Residual Output = 0
End
Solver 2
 Equation = Heat Equation
 Procedure = "HeatSolve" "HeatSolver"
 Variable = Temperature
 Variable DOFs = 1
 Stabilize = Logical True
 Steady State Convergence Tolerance = 1e-8
 Nonlinear System Max Iterations = 30
 Nonlinear System Convergence Tolerance = 1e-9
 Nonlinear System Relaxation Factor = 1
 Linear System Solver = Iterative
 Linear System Iterative Method = BiCGStabL
 Linear System Preconditioning = ILU1
 Linear System Max Iterations = 1000
 Linear System Convergence Tolerance = 1e-11
 Linear System Residual Output = 0
End
Solver 3
 Exec Solver = After Timestep
 Equation = ResultOutput
 Procedure = "ResultOutputSolve" "ResultOutputSolver"
 Output File Name = "solution"
 Vtu Format = Logical True
 Binary Output = Logical False
End
Equation 1
 Active Solvers(3) = 1 2 3
 Convection = Computed
End
Material 1
'''+f'Density = Real {p["density"]}\nHeat Capacity = Real {p["heat_capacity"]}\n'
    for key,ref,exponent in [('Viscosity','reference_viscosity','viscosity_exponent'),('Heat Conductivity','reference_conductivity','conductivity_exponent')]:txt+=f'{key} = Variable Temperature\nReal MATC "{p[ref]}*(tx/{p["reference_temperature"]})^{p[exponent]}"\n'
    txt+='End\nInitial Condition 1\nPressure = Real 0\n'+''.join(f'Velocity {j+1} = Real 0\n' for j in range(d))+f'Temperature = Real {p["reference_temperature"]}\nEnd\n'
    if transient:
        assert s['initial']['velocity']['expression']==[0.]*d and s['initial']['temperature']['expression']==p['reference_temperature']
    acc=s['sources'].get('acceleration',{'expression':[0.]*d})['expression']
    for i in range(bodies):
        txt+=f'Body Force {i+1}\nFriction Heat = Logical True\n'
        for j,a in enumerate(acc):
            # Acceleration is uniform in space for this frozen case family.
            assert isinstance(a,(float,int)) or not re.search(r'\b[XYZ]\b',a)
            ae=matc(a,s).replace(f'tx({d})','tx(1)')
            txt+=f'Flow Bodyforce {j+1} = Variable Temperature, Time\nReal MATC "({ae})*(1-{p["thermal_expansion"]}*(tx(0)-{p["reference_temperature"]}))"\n'
        if source:txt+='Volumetric Heat Source = Variable Time\nReal\n'+''.join(f'{t:.17g} {v:.17g}\n' for t,v in zip(hist,sources[:,i]))+'End\n'
        txt+='End\n'
    for i,(mi,ti) in enumerate(pairs):
        mb=s['boundaries'][mi];tb=s['thermal_partition'][ti];assert mb['operator']=='moving_wall'
        txt+=f'Boundary Condition {i+1}\nTarget Boundaries(1) = {i+1}\n'
        for j,a in enumerate(mb['data']['velocity']['expression']):txt+=function(f'Velocity {j+1}',a,s)
        expr=tb['value']['expression'];key='Temperature' if tb['operator']=='temperature' else 'Heat Flux'
        # Elmer's natural Heat Flux is INTO the fluid; DATA is outward positive.
        txt+=function(key,expr if key=='Temperature' else f'-({expr})',s)+'End\n'
    txt+=f'Boundary Condition {len(pairs)+1}\nTarget Boundaries(1) = {joint.max()+2}\nPressure = Real 0\nEnd\n';put(job/'native/case.sif',txt)
    if d==2:
        txt=txt.replace('Linear System Solver = Iterative','Linear System Solver = Direct\nLinear System Direct Method = UMFPACK')
        put(job/'native/case.sif',txt)
    np.savez(job/'adapter-data.npz',**m,mech=mech,thermal=thermal,joint=joint,hist=hist,sources=sources)
    return m,mech,thermal,hist,sources


def convert(job,e,data,native_frames=None):
    m,mech,thermal,hist,sources=data;s=e['detailed_spec'];x=m['x'];c=m['c'];b=m['b'];d=x.shape[1];nc=len(c);n=len(x);mid=x[b].mean(axis=1);transient=s['analysis_kind']=='transient';end=(s['time_interval_s'] or [0,1])[1]
    inp=job/'input';ref=job/'reference';inp.mkdir(exist_ok=True);ref.mkdir(exist_ok=True);gmsh(inp/'mesh.msh',x,c,b,d)
    arrays={'cells':np.arange(1,nc+1,dtype=np.int64),'history':hist,'requested':np.array(s['output_times_s']),'initial':np.array([0.])};locations={'domain':{'kind':'mesh','mesh':'main','entity':'element','dimension':d,'ids':'cells'}};fields={};conditions=[]
    def desc(q,where,axis,unit,dim=1,input=False):
        z={'array':q,'quantity':q,'location':where,'time_axis':axis,'dtype':'float64','kind':'scalar' if dim==1 else 'vector','component_shape':[dim],'components':['value'] if dim==1 else list('xyz'[:dim]),'unit':unit,'value_kind':'average'}
        if input:z['sampling']={'space':'piecewise_constant','time':'linear' if axis=='history' and transient else 'constant','extrapolation':'forbid'}
        return z
    def field(key,q,where,axis,unit,v,role,op,var):
        a=np.asarray(v,dtype=float);a=a[...,None] if a.ndim==2 else a;arrays[key]=a;fields[key]=desc(q,where,axis,unit,a.shape[-1],True);fields[key]['array']=key;conditions.append({'role':role,'variable':var,'operator':op,'location':where,'data':{'value':{'field':key}}})
    if transient:
        for q,unit in [('velocity','m/s'),('temperature','K')]:field('initial_'+q,q,'domain','initial',unit,[sample(s['initial'][q]['expression'],x[c].mean(axis=1),0,s)],'initial','assign',q)
    for q,v in s['sources'].items():
        val=sources if q=='heat_source' else np.array([sample(v['expression'],x[c].mean(axis=1),t,s) for t in hist]);field(q,q,'domain','history',v['unit'],val,'source','assign',q)
    for group,records,label in [(mech,s['boundaries'],'mechanical'),(thermal,s['thermal_partition'],'thermal')]:
        for i,record in enumerate(records):
            ids=np.flatnonzero(group==i)
            if not len(ids):continue
            key=f'{label}{i}';arrays[key]=(nc+ids+1).astype(np.int64);locations[key]={'kind':'mesh','mesh':'main','entity':'element','dimension':d-1,'ids':key}
            value=record['data']['velocity'] if label=='mechanical' else record['value'];q='velocity' if label=='mechanical' else 'temperature' if record['operator']=='temperature' else 'heat_flux';var='velocity' if label=='mechanical' else 'temperature';field(key+'value',q,key,'history',value['unit'],[sample(value['expression'],mid[ids],t,s) for t in hist],'boundary',record['operator'],var)
    outputs={q:desc(q,'domain','requested',unit,d if q=='velocity' else 1) for q,unit in [('velocity','m/s'),('pressure','Pa'),('temperature','K')]}
    problem={'task':e['task'],'spatial_dimension':d,'physics':{'model':e['model'],'parameters':s['parameters']},'data_file':'input.h5','geometries':{},'meshes':{'main':{'file':'mesh.msh'}},'locations':locations,'time_axes':{'history':'history','initial':'initial','requested':'requested'},'fields':fields,'conditions':conditions,'outputs':outputs};save(inp/'problem.json',problem)
    with h5py.File(inp/'input.h5','w') as f:
        for key,v in arrays.items():f[key]=v
    if native_frames is None:
        files=sorted((job/'native').rglob('solution*.vtu'));assert len(files)==1000 if transient else len(files)>0
    result={q:[] for q in outputs}
    for t in s['output_times_s']:
        if native_frames is None:
            file=files[round(t/end*1000)-1] if transient else files[-1];tree=ET.parse(file);pos=np.fromstring(tree.find('.//Points/DataArray').text,sep=' ').reshape(-1,3)[:,:d];dist,order=cKDTree(pos).query(x);assert len(np.unique(order))==n and dist.max()<max(s['geometry']['bounding_lengths'])*1e-7
            native={a.get('Name').lower():np.fromstring(a.text,sep=' ').reshape(n,-1)[order] for a in tree.findall('.//PointData/DataArray')}
        else:native=native_frames[round(float(t),12)]
        u=native['velocity'][:,:d][c].mean(axis=1);p=native['pressure'][c].mean(axis=1);p-=np.sum(p[:,0]*m['volume'])/sum(m['volume']);T=native['temperature'][c].mean(axis=1)
        for key,v in [('velocity',u),('pressure',p),('temperature',T)]:assert np.isfinite(v).all();result[key].append(v)
    with h5py.File(ref/'reference.h5','w') as f:
        f['cells']=arrays['cells'];f['requested']=arrays['requested']
        for key,v in result.items():f[key]=np.array(v)
    return {'reference_sha256':digest(ref/'reference.h5'),'nodes':n,'cells':nc,'frames':len(s['output_times_s']),'mapping':'Native stabilized P1 FlowSolver + HeatSolver, full symmetric stress, native Friction Heat, nodal constitutive coefficients; exact simplex means of native P1 outputs. Boussinesq retains base acceleration. Source P0 samples constructed once by fixed barycentric quadrature; no accuracy validation.'}


def run(root,e,g):
    job=root/'cases'/e['design_id'];status=job/'status.json'
    if status.exists():return json.loads(status.read_text())
    job.mkdir(parents=True);save(job/'design.json',e);state={'design_id':e['design_id'],'status':'queued'};save(status,state);name='ch02lowmach-'+hashlib.sha256(e['design_id'].encode()).hexdigest()[:12]+'-'+str(time.time_ns())[-9:]
    try:
        with reservation(root,name):
            state['status']='preparing';save(status,state);data=prepare(job,e)
            cmd=['docker','--host',SOCKET,'run','--name',name,'--network','none','--cpus','1','--memory','768m','--user',f'{os.getuid()}:{os.getgid()}','-e','OMP_NUM_THREADS=1','-e','OPENBLAS_NUM_THREADS=1','-e','MKL_NUM_THREADS=1','-v',f'{job.resolve()}:/work','-w','/work/native',IMAGE,'ElmerSolver','case.sif']
            save(job/'execution.json',{'producer':'unmodified Elmer FlowSolver + HeatSolver','image':IMAGE,'source_commit':COMMIT,'source_url':f'https://github.com/ElmerCSC/elmerfem/tree/{COMMIT}/fem/src/modules','command':cmd,'script_sha256':digest(Path(__file__)),'start_unix':time.time(),'numerical_validation':False})
            state.update(status='running',container=name);save(status,state)
            with (job/'solver.log').open('w') as log:cp=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
            assert cp.returncode==0,f'Elmer exit {cp.returncode}'
        state.update(convert(job,e,data));save(job/'reference/grading.json',g);state['status']='unvalidated_candidate'
    except Exception as ex:state.update(status='needs_attention',error=repr(ex))
    state['ended_unix']=time.time();save(status,state);return state


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--only');ap.add_argument('--workers',type=int,default=40);args=ap.parse_args();assert 1<=args.workers<=40;tasks=[]
    freeze=json.loads((args.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text())
    for p in args.snapshot.glob('qbank/02-fluid-mechanics/*/newtonian-lowmach-*/author/chapter02-ten-20261020/design.json'):
        r=json.loads(p.read_text());assert digest(p)==freeze['designs'][p.relative_to(args.snapshot).as_posix()]
        for e in r['proposed_cases']:
            if args.only and args.only not in e['design_id']:continue
            tasks.append(({**e,'task':r['task'],'model':r['model']},json.loads((p.parents[1]/'grading-template.json').read_text())))
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=args.workers) as pool:states=list(pool.map(run,[args.root]*len(tasks),[e for e,g in tasks],[g for e,g in tasks]))
    save(args.root/'maintenance/lowmach-summary.json',states);print(json.dumps({'complete':sum(s['status']=='unvalidated_candidate' for s in states),'attention':[s for s in states if s['status']=='needs_attention']}))


if __name__=='__main__':main()
