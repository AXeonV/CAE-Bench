"""Native Elmer ReynoldsSolver adapter. No custom PDE/physics routines.

Pinned upstream ReynoldsSolver at a19504ac: isothermal gas density factor p,
MM=-h, MS=-p*h^3/(12*mu), surface velocity=U0+U1, normal velocity=dh/dt.
All multiplicative 1/(R*Tref) factors cancel in the pressure equation.
Reference fields are unvalidated candidates; nodal flux uses recovered FE
gradients, with no error certificate. Input remains the actual P1 nodal data.
"""
import argparse
import hashlib
import json
import os
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path
import h5py
import numpy as np
from native_closed_cavity import SOCKET,save,digest,put
from polytropic_reference import gmsh

IMAGE='sha256:49e9458cc3b1ea3d7e7383c32056af59b0f718e74b0f30adbe3e1bccc0e7b059'
COMMIT='a19504ac53ec222e3355e182b08f2ff280c2203a'

def triangles(spec):
    import gmsh as g
    geo=spec['geometry'];L=geo['bounding_lengths'];g.initialize();g.option.setNumber('General.Terminal',0);g.option.setNumber('Mesh.MshFileVersion',4.1);g.option.setNumber('Mesh.Binary',0);g.option.setNumber('Mesh.Algorithm',6)
    def ring(vertices):
        p=[g.model.geo.addPoint(x,y,0,min(L)/12) for x,y in vertices];lines=[g.model.geo.addLine(p[i],p[(i+1)%len(p)]) for i in range(len(p))];return g.model.geo.addCurveLoop(lines)
    assert geo['operation']=='box';rings=[ring([[0,0],[L[0],0],L,[0,L[1]]])]
    for h in geo['holes']:
        (a,b),(c,d)=h['xy_corners'];rings.append(ring([[a,b],[c,b],[c,d],[a,d]]))
    g.model.geo.addPlaneSurface(rings);g.model.geo.synchronize();g.model.mesh.generate(2)
    tags,xyz,_=g.model.mesh.getNodes();xyz=np.array(xyz).reshape(-1,3)[:,:2];lut={int(t):i for i,t in enumerate(tags)}
    _,alltags,allconn=g.model.mesh.getElements(2);assert len(allconn)==1;c=np.array([[lut[int(t)] for t in row] for row in np.array(allconn[0]).reshape(-1,3)],dtype=np.int64)
    _,_,bc=g.model.mesh.getElements(1);b=np.array([[lut[int(t)] for t in row] for arr in bc for row in np.array(arr).reshape(-1,2)],dtype=np.int64);g.finalize()
    A=xyz[c][:,1:]-xyz[c][:,:1];det=np.linalg.det(A);neg=det<0;c[neg,1],c[neg,2]=c[neg,2].copy(),c[neg,1].copy();return xyz,c,b,np.abs(det)/2

def histories(spec):
    end=spec['time_interval_s'][1];return np.array([0,.1*end,.4*end,.6*end,end])

def evaluate(expr,x,t,end):
    X=x[:,0]/evaluate.L[0];Y=x[:,1]/evaluate.L[1];R=min(max(t/(.1*end),0),1);P=R-min(max((t-.4*end)/(.2*end),0),1)
    def bump(**kw):return np.maximum(1-((X-.5)/.2)**2-((Y-.5)/.2)**2,0)**4
    if isinstance(expr,list):return np.column_stack([evaluate(v,x,t,end) for v in expr])
    if isinstance(expr,(int,float)):return np.full(len(x),expr)
    expr=expr.replace('bump(centre=.5*L,radius=.2*L)','B').replace('^','**');B=bump();v=eval(expr,{'__builtins__':{}},{'X':X,'Y':Y,'R':R,'P':P,'B':B,'abs':np.abs});return np.broadcast_to(v,(len(x),)).copy()

def elmer_mesh(job,x,c,b):
    p=job/'native/mesh';p.mkdir(parents=True);n=len(x);nc=len(c);nb=len(b)
    put(p/'mesh.header',f'{n} {nc} {nb}\n2\n303 {nc}\n202 {nb}\n')
    put(p/'mesh.nodes','\n'.join(f'{i+1} -1 {a} {bb} 0' for i,(a,bb) in enumerate(x))+'\n')
    put(p/'mesh.elements','\n'.join(f'{i+1} 1 303 '+' '.join(map(str,v+1)) for i,v in enumerate(c))+'\n')
    parent={tuple(sorted(np.delete(v,j))):i+1 for i,v in enumerate(c) for j in range(3)}
    put(p/'mesh.boundary','\n'.join(f'{i+1} {i+1} {parent[tuple(sorted(v))]} 0 202 '+' '.join(map(str,v+1)) for i,v in enumerate(b))+'\n')

def prepare(job,e):
    s=e['detailed_spec'];x,c,b,area=triangles(s);L=s['geometry']['bounding_lengths'];evaluate.L=L;times=histories(s);end=times[-1]
    h=np.array([evaluate(s['domain_conditions']['gap']['expression'],x,t,end) for t in times]);u0=np.array([evaluate(s['domain_conditions']['lower_velocity']['expression'],x,t,end) for t in times]);u1=np.array([evaluate(s['domain_conditions']['upper_velocity']['expression'],x,t,end) for t in times])
    # GetReal evaluates MATC at the actual nodes and then the native solver
    # interpolates with its element shape functions: same P1 input reconstruction.
    Tr=.1*end;Td=.2*end
    ramp=f'(.5*(tx(2)/{Tr}+1-abs(tx(2)/{Tr}-1)))'
    down=f'(.5*((tx(2)-{.4*end})/{Td}+abs((tx(2)-{.4*end})/{Td}))-.5*((tx(2)-{.6*end})/{Td}+abs((tx(2)-{.6*end})/{Td})))'
    pulse=f'({ramp}-{down})'
    def matc(expr):
        if isinstance(expr,(float,int)):return str(expr)
        v=f'(1-((tx(0)/{L[0]}-.5)/.2)^2-((tx(1)/{L[1]}-.5)/.2)^2)'
        expr=expr.replace('bump(centre=.5*L,radius=.2*L)',f'(.5*({v}+abs({v})))^4')
        return expr.replace('X',f'(tx(0)/{L[0]})').replace('Y',f'(tx(1)/{L[1]})').replace('R',ramp).replace('P',pulse)
    def function(key,expr):return f'{key} = Variable Coordinate 1, Coordinate 2, Time\n Real MATC "{matc(expr)}"\n'
    i=int(e['design_id'].split('-')[-2])-1;gexpr=s['domain_conditions']['gap']['expression'];hbase=matc(gexpr)
    if i in (0,1):hdot=f'{-1e-6 if i==0 else 1e-6}/{Tr}*(tx(2)<{Tr})'
    elif i==4:hdot=f'(-.05*1e-5*(2-.5*tx(0)/{L[0]}-.5*tx(1)/{L[1]})/{Tr})*(tx(2)<{Tr})'
    elif i==9:hdot=f'(-.05*1e-5)*((tx(2)<{Tr})/{Tr}-(tx(2)>={.4*end})*(tx(2)<{.6*end})/{Td})'
    else:hdot='0'
    elmer_mesh(job,x,c,b)
    text='''Header
 CHECK KEYWORDS Warn
 Mesh DB "." "mesh"
 Results Directory "."
End
Simulation
 Coordinate System = Cartesian 2D
 Simulation Type = Transient
 Timestepping Method = BDF
 BDF Order = 1
 Timestep Intervals(1) = 1000
'''+f' Timestep Sizes(1) = {end/1000}\n Output Intervals(1) = 1\n Steady State Max Iterations = 1\nEnd\n'
    text+='''Body 1
 Equation = 1
 Material = 1
 Initial Condition = 1
End
Initial Condition 1
 FilmPressure = Real 100000
End
Solver 1
 Equation = "Reynolds"
 Procedure = "ReynoldsSolver" "ReynoldsSolver"
 Variable = "FilmPressure"
 Variable DOFs = 1
 Linear System Solver = Direct
 Linear System Direct Method = UMFPACK
 Nonlinear System Max Iterations = 30
 Nonlinear System Convergence Tolerance = 1e-10
 Nonlinear System Relaxation Factor = 1
End
Solver 2
 Exec Solver = After Timestep
 Equation = "ResultOutput"
 Procedure = "ResultOutputSolve" "ResultOutputSolver"
 Output File Name = "solution"
 Vtu Format = Logical True
 Binary Output = Logical False
End
Equation 1
 Active Solvers(2) = 1 2
End
Material 1
 Compressibility Model = String "isothermal ideal gas"
 Viscosity Model = String "newtonian"
 Reference Pressure = Real 0
'''+f' Viscosity = Real {s["parameters"]["viscosity"]["value"]}\n'
    text+=function('Gap Height',gexpr)
    for axis in range(2):
        a=s['domain_conditions']['lower_velocity']['expression'][axis];bb=s['domain_conditions']['upper_velocity']['expression'][axis]
        text+=function(f'Surface Velocity {axis+1}',f'({a})+({bb})')
    text+=f'Normal Velocity = Variable Coordinate 1, Coordinate 2, Time\n Real MATC "{hdot}"\nEnd\n'
    for j,edge in enumerate(b):
        mid=x[edge].mean(axis=0);inner=not(np.any(np.isclose(mid,0,atol=1e-14)) or np.any(np.isclose(mid,L,atol=1e-14)))
        pexpr=s['boundaries'][1 if inner else 0]['data']['value']['expression']
        vals=[evaluate(pexpr,mid[None],t,end)[0] for t in times]
        text+=f'Boundary Condition {j+1}\n Target Boundaries(1) = {j+1}\n FilmPressure = Variable Time\n Real\n'+''.join(f'{t:.17g} {v:.17g}\n' for t,v in zip(times,vals))+' End\nEnd\n'
    put(job/'native/case.sif',text)
    np.savez(job/'adapter-data.npz',x=x,c=c,b=b,area=area,times=times,h=h,u0=u0,u1=u1)
    return x,c,b,area,times,h,u0,u1

def convert(job,e,data):
    x,c,b,area,ts,h,u0,u1=data;s=e['detailed_spec'];end=ts[-1];evaluate.L=s['geometry']['bounding_lengths'];outtimes=s['output_times_s'];n=len(x);nc=len(c)
    inp=job/'input';ref=job/'reference';inp.mkdir(exist_ok=True);ref.mkdir(exist_ok=True);gmsh(inp/'mesh.msh',x,c,b,2)
    interior=np.ones(n,dtype=bool);interior[np.unique(b)]=False
    for _ in range(1):interior[np.unique(c[np.any(~interior[c],axis=1)])]=False
    keep=np.flatnonzero(interior);assert len(keep)>0
    def loc(entity,dimension,ids):return {'kind':'mesh','mesh':'main','entity':entity,'ids':ids,**({'dimension':dimension} if entity=='element' else {})}
    locations={'domain':loc('node',0,'nodes'),'observed':loc('node',0,'observed'),'area':loc('element',2,'cells'),'load':{'kind':'aggregate','source':'area','ids':'load_id','operation':'sum'}}
    def desc(q,location,axis,unit,dim=1,input=False,point=True):
        z={'array':q,'quantity':q,'location':location,'time_axis':axis,'dtype':'float64','kind':'scalar' if dim==1 else 'vector','component_shape':[dim],'components':['value'] if dim==1 else ['x','y'],'unit':unit,'value_kind':'point' if point else 'average'}
        if input:z['sampling']={'space':'piecewise_linear' if point else 'piecewise_constant','time':'constant' if axis=='initial' else 'linear','extrapolation':'forbid'}
        return z
    fields={q:desc(q,'domain','history',u,2 if 'velocity' in q else 1,True) for q,u in [('gap','m'),('lower_velocity','m/s'),('upper_velocity','m/s')]};fields['initial_pressure']=desc('pressure','domain','initial','Pa',input=True);fields['initial_pressure']['array']='initial_pressure'
    conditions=[{'role':'material','variable':q,'operator':'geometry','location':'domain','data':{'value':{'field':q}}} for q in ('gap','lower_velocity','upper_velocity')]+[{'role':'initial','variable':'pressure','operator':'assign','location':'domain','data':{'value':{'field':'initial_pressure'}}}]
    with h5py.File(inp/'input.h5','w') as f:
        f['nodes']=np.arange(1,n+1,dtype=np.int64);f['observed']=(keep+1).astype(np.int64);f['cells']=np.arange(1,nc+1,dtype=np.int64);f['load_id']=np.array([1],dtype=np.int64);f['history']=ts;f['initial']=np.array([0.]);f['requested']=np.array(outtimes);f['gap']=h[...,None];f['lower_velocity']=u0;f['upper_velocity']=u1;f['initial_pressure']=np.full((1,n,1),100000.)
        for j,edge in enumerate(b):
            name=f'edge{j+1}';f[name]=np.array([nc+j+1],dtype=np.int64);locations[name]=loc('element',1,name);mid=x[edge].mean(axis=0);inner=not(np.any(np.isclose(mid,0,atol=1e-14)) or np.any(np.isclose(mid,evaluate.L,atol=1e-14)));expr=s['boundaries'][1 if inner else 0]['data']['value']['expression'];q=f'pressure{j+1}';f[q]=np.array([evaluate(expr,mid[None],t,end)[0] for t in ts])[:,None,None];fields[q]=desc('pressure',name,'history','Pa',input=True,point=False);fields[q]['array']=q;conditions.append({'role':'boundary','variable':'pressure','operator':'film_pressure','location':name,'data':{'value':{'field':q}}})
    outputs={q:desc(q,'load' if q=='load' else 'observed','requested',u,2 if q=='film_flux' else 1) for q,u in [('pressure','Pa'),('density','kg/m3'),('film_flux','m2/s'),('load','N')]};outputs['load']['value_kind']='integral'
    problem={'task':'gas-film','spatial_dimension':2,'physics':{'model':'fluid-reduced-gas-film-v1','parameters':s['parameters']},'data_file':'input.h5','geometries':{},'meshes':{'main':{'file':'mesh.msh'}},'locations':locations,'time_axes':{'initial':'initial','history':'history','requested':'requested'},'fields':fields,'conditions':conditions,'outputs':outputs};save(inp/'problem.json',problem)
    pressures=[];fluxes=[];loads=[];A=x[c][:,1:]-x[c][:,:1]
    files=sorted((job/'native').rglob('solution*.vtu'))
    assert len(files)==1000,f'Expected 1000 native frames, got {len(files)}'
    for t in outtimes:
        path=files[round(t/end*1000)-1];tree=ET.parse(path);pos=np.fromstring(tree.find('.//Points/DataArray').text,sep=' ').reshape(-1,3)[:,:2];arr=next(a for a in tree.findall('.//PointData/DataArray') if a.get('Name','').lower()=='filmpressure');p=np.fromstring(arr.text,sep=' ')
        # Default native ASCII VTU coordinates have eight significant digits.
        # Node order is retained; tolerate only that serialization roundoff.
        assert np.allclose(pos,x,atol=max(evaluate.L)*1e-8,rtol=0),'native node ordering differs beyond ASCII serialization roundoff'
        grad=np.linalg.solve(A,(p[c][:,1:]-p[c][:,:1])[...,None])[...,0];ng=np.zeros((n,2));weight=np.zeros(n)
        for j in range(3):np.add.at(ng,c[:,j],grad*area[:,None]);np.add.at(weight,c[:,j],area)
        ng/=weight[:,None];ht=evaluate(s['domain_conditions']['gap']['expression'],x,t,end);v=evaluate(s['domain_conditions']['lower_velocity']['expression'],x,t,end)+evaluate(s['domain_conditions']['upper_velocity']['expression'],x,t,end);q=-ht[:,None]**3*ng/(12*s['parameters']['viscosity']['value'])+ht[:,None]*v/2
        pressures.append(p[keep,None]);fluxes.append(q[keep]);loads.append([[np.dot(area,p[c].mean(axis=1)-s['parameters']['reference_pressure']['value'])]])
    with h5py.File(ref/'reference.h5','w') as f:
        f['observed']=(keep+1).astype(np.int64);f['load_id']=np.array([1],dtype=np.int64);f['requested']=np.array(outtimes);f['pressure']=np.array(pressures);f['density']=np.array(pressures)/(s['parameters']['specific_gas_constant']['value']*s['parameters']['reference_temperature']['value']);f['film_flux']=np.array(fluxes);f['load']=np.array(loads)
    return {'reference_sha256':digest(ref/'reference.h5'),'nodes':n,'cells':nc,'frames':len(outtimes),'field_mapping':'Elmer GetReal at native P1 nodes; boundary piecewise constants use element groups and shared-node FE enforcement. Flux uses area-weighted recovered pressure gradients; no accuracy certificate.'}

def run(root,e,grading):
    job=root/'cases'/e['design_id'];status=job/'status.json'
    if status.exists():return json.loads(status.read_text())
    job.mkdir(parents=True);save(job/'design.json',e);state={'design_id':e['design_id'],'status':'preparing'};save(status,state)
    try:
        data=prepare(job,e);name='ch02gas-'+hashlib.sha256(e['design_id'].encode()).hexdigest()[:12]
        cmd=['docker','--host',SOCKET,'run','--name',name,'--network','none','--cpus','1','--memory','2g','--user',f'{os.getuid()}:{os.getgid()}','-v',f'{job.resolve()}:/work','-w','/work/native',IMAGE,'ElmerSolver','case.sif']
        save(job/'execution.json',{'command':cmd,'start_unix':time.time(),'source_commit':COMMIT,'source_url':f'https://github.com/ElmerCSC/elmerfem/blob/{COMMIT}/fem/src/modules/ReynoldsSolver.F90','image':IMAGE,'script_sha256':digest(Path(__file__)),'numerical_validation':False});state.update(status='running',container=name);save(status,state)
        cp=subprocess.run(cmd,capture_output=True,text=True,timeout=3600);put(job/'solver.log',cp.stdout+cp.stderr);assert cp.returncode==0,f'Elmer exit {cp.returncode}'
        state.update(convert(job,e,data));save(job/'reference/grading.json',grading);state['status']='unvalidated_candidate'
    except Exception as ex:state.update(status='needs_attention',error=repr(ex))
    save(status,state);return state

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--limit',type=int,default=10);args=ap.parse_args();p=next(args.snapshot.glob('qbank/02-fluid-mechanics/*/gas-film/author/chapter02-ten-20261020/design.json'));r=json.loads(p.read_text());g=json.loads((p.parents[1]/'grading-template.json').read_text());states=[]
    frozen=json.loads((args.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text());assert frozen['design_complete'];assert hashlib.sha256(p.read_text().encode()).hexdigest()==frozen['designs'][p.relative_to(args.snapshot).as_posix()]
    from concurrent.futures import ProcessPoolExecutor
    # Separate processes: Gmsh has global state and must not be used in threads.
    with ProcessPoolExecutor(max_workers=10) as pool:
        futures=[pool.submit(run,args.root,e,g) for e in r['proposed_cases'][:args.limit]]
        states=[f.result() for f in futures]
    save(args.root/'maintenance/gas-film-summary.json',states);print(json.dumps({'completed':sum(s['status']=='unvalidated_candidate' for s in states),'needs_attention':sum(s['status']=='needs_attention' for s in states)}))

if __name__=='__main__':main()
