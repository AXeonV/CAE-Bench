"""Unmodified OpenCFD Maxwell producer adapter (Oldroyd-B with solvent).

sigma in OpenFOAM is -tau_polymer/rho. No stress diffusion is added.
Outputs remain candidates, with no refinement or convergence certificate.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path
import numpy as np
import h5py
from native_closed_cavity import IMAGE,SOCKET,header,vector,put,save,digest,prepare_native,native_mesh,field as foam_field
from polytropic_reference import gmsh
from native_elmer_incompressible import evaluate


def prepare(job,e):
    s=e['detailed_spec'];L=s['geometry']['bounding_lengths'];assert len(L)==2 and s['geometry']['operation']=='box'
    assert not s['sources'];assert all(b['operator']=='velocity_wall' for b in s['boundaries'])
    holes=s['geometry']['holes']
    transient=s['analysis_kind']=='transient';end=1.;times=[0,.1,.4,.6,1.] if transient else [0.]
    # Reuse the existing block mesh writer, replacing every native boundary
    # value below from the actual frozen specification, including bottom/right.
    params={k:v['value'] for k,v in s['parameters'].items()};rho=params['density']
    p={'spatial_dimension':2,'length_m':[*L,.05],'target_cells_xyz':[*s['mesh_recipe']['base_divisions'],1],'obstacle_xy_fraction':bool(holes),'wall_speed_multiplier_linear_table':[[0,0],[.1,1],[1,1]],'wall_velocity_vectors_m_s':{},'dynamic_viscosity_Pa_s':params['solvent_viscosity'],'density_kg_m3':rho,'time_interval_s':[0,1],'native_dt_s':.001}
    native=job/'native';prepare_native(native,p)
    from foam_box_mesh import write
    names=list(write(native,s))
    ubc=[];pbc=[];sbc=[]
    for name in names:
        if name in ('front','back'):
            ubc.append(name+' { type empty; }');pbc.append(name+' { type empty; }');sbc.append(name+' { type empty; }');continue
        bc=s['boundaries'][int(name[2:])]
        expr=bc['data']['value']['expression'];vel=[[*evaluate(expr,np.array([[L[0]/2,L[1]/2]]),t,s)[0],0.] for t in times]
        if transient:ubc.append(name+' { type uniformFixedValue; uniformValue table ('+' '.join(f'({t} {vector(v)})' for t,v in zip(times,vel))+'); value uniform '+vector(vel[0])+'; }')
        else:ubc.append(name+' { type fixedValue; value uniform '+vector(vel[0])+'; }')
        pbc.append(name+' { type zeroGradient; }');sbc.append(name+' { type zeroGradient; }')
    put(native/'0/U',header('volVectorField','U')+'dimensions [0 1 -1 0 0 0 0];\ninternalField uniform (0 0 0);\nboundaryField {\n'+'\n'.join(ubc)+'\n}\n')
    put(native/'0/p',header('volScalarField','p')+'dimensions [0 2 -2 0 0 0 0];\ninternalField uniform 0;\nboundaryField {\n'+'\n'.join(pbc)+'\n}\n')
    A=np.eye(3)
    if transient:A[:2,:2]=s['initial']['conformation']['expression']
    sig=-params['polymer_viscosity']/(rho*params['relaxation_time'])*(A-np.eye(3));sv=[sig[0,0],sig[0,1],sig[0,2],sig[1,1],sig[1,2],sig[2,2]]
    put(native/'0/sigma',header('volSymmTensorField','sigma')+'dimensions [0 2 -2 0 0 0 0];\ninternalField uniform '+vector(sv)+';\nboundaryField {\n'+'\n'.join(sbc)+'\n}\n')
    put(native/'constant/turbulenceProperties',header('dictionary','turbulenceProperties')+f'simulationType laminar;\nlaminar {{ model Maxwell; MaxwellCoeffs {{ nuM [0 2 -1 0 0 0 0] {params["polymer_viscosity"]/rho}; lambda [0 0 1 0 0 0 0] {params["relaxation_time"]}; }} }}\n')
    app='pimpleFoam' if transient else 'simpleFoam';stop=1 if transient else 5000;dt=.001 if transient else 1
    put(native/'system/controlDict',header('dictionary','controlDict')+f'application {app}; startFrom startTime; startTime 0; stopAt endTime; endTime {stop}; deltaT {dt}; writeControl timeStep; writeInterval {1 if transient else 5000}; purgeWrite 0; writeFormat ascii; writePrecision 16; writeCompression off; timeFormat general; timePrecision 12; runTimeModifiable false;\nfunctions {{ gradU {{ type grad; libs (fieldFunctionObjects); field U; result gradU; executeControl writeTime; writeControl writeTime; }} }}\n')
    put(native/'system/fvSchemes',header('dictionary','fvSchemes')+'ddtSchemes { default '+('Euler' if transient else 'steadyState')+'; } gradSchemes { default Gauss linear; } divSchemes { default none; div(phi,U) Gauss linearUpwind grad(U); div(phi,sigma) Gauss upwind; div(sigma) Gauss linear; div((nuM*grad(U))) Gauss linear; div(((nu*dev2(T(grad(U)))))) Gauss linear; div((nu*dev2(T(grad(U))))) Gauss linear; } laplacianSchemes { default Gauss linear corrected; } interpolationSchemes { default linear; } snGradSchemes { default corrected; } fluxRequired { default no; p; }\n')
    solver='solvers { p { solver PCG; preconditioner DIC; tolerance 1e-9; relTol 0; } pFinal { $p; relTol 0; } U { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-9; relTol 0; } UFinal { $U; relTol 0; } sigma { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-9; relTol 0; } sigmaFinal { $sigma; relTol 0; } }\n'
    if transient:solver+='PIMPLE { nOuterCorrectors 2; nCorrectors 2; nNonOrthogonalCorrectors 0; pRefCell 0; pRefValue 0; turbulenceOnFinalIterOnly false; } relaxationFactors { equations { U 1; sigma 1; } }\n'
    else:solver+='SIMPLE { nNonOrthogonalCorrectors 0; pRefCell 0; pRefValue 0; residualControl { p 1e-8; U 1e-8; sigma 1e-8; } } relaxationFactors { fields { p 0.2; } equations { U 0.2; sigma 0.1; } }\n'
    put(native/'system/fvSolution',header('dictionary','fvSolution')+solver)
    return app


def run(root,e,g):
    job=root/'cases'/e['design_id'];status=job/'status.json'
    if status.exists():return json.loads(status.read_text())
    job.mkdir(parents=True);save(job/'design.json',e);state={'design_id':e['design_id'],'status':'preparing'};save(status,state)
    try:
        app=prepare(job,e);name='ch02maxwell-'+hashlib.sha256(e['design_id'].encode()).hexdigest()[:12]+'-'+str(time.time_ns())[-9:]
        cmd=['docker','--host',SOCKET,'run','--name',name,'--network','none','--cpus','1','--memory','768m','--user',f'{os.getuid()}:{os.getgid()}','-e','OMP_NUM_THREADS=1','-v',f'{job.resolve()}:/work','-w','/work/native',IMAGE,'bash','-c',f'source /usr/lib/openfoam/openfoam2512/etc/bashrc && cd /work/native && blockMesh > ../blockMesh.log 2>&1 && {app} > ../solver.log 2>&1']
        save(job/'execution.json',{'producer':f'unmodified OpenCFD {app} + native laminar Maxwell','image':IMAGE,'source':'image:/usr/lib/openfoam/openfoam2512/src/TurbulenceModels/turbulenceModels/laminar/Maxwell/Maxwell.C','source_url':'https://develop.openfoam.com/Development/openfoam/-/tree/OpenFOAM-v2512/src/TurbulenceModels/turbulenceModels/laminar/Maxwell','command':cmd,'script_sha256':digest(Path(__file__)),'start_unix':time.time(),'numerical_validation':False})
        state.update(status='running',container=name);save(status,state)
        with (job/'docker.log').open('w') as log:cp=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
        assert cp.returncode==0,f'native exit {cp.returncode}'
        # This state intentionally distinguishes raw solver completion from a
        # completed self-contained reference package.
        state['status']='native_complete_pending_conversion';save(job/'grading-template.json',g);save(status,state)
        if e['detailed_spec']['analysis_kind']=='steady' and 'SIMPLE solution converged' not in (job/'solver.log').read_text():
            state['status']='native_iteration_limit'
        else:state=convert(job)
    except Exception as ex:state.update(status='needs_attention',error=repr(ex))
    state['ended_unix']=time.time();save(status,state);return state


def convert(job):
    """Recover point outputs from the native FV field, with mapping disclosed."""
    state=json.loads((job/'status.json').read_text());assert state['status']=='native_complete_pending_conversion'
    e=json.loads((job/'design.json').read_text());s=e['detailed_spec'];native=job/'native';params={k:v['value'] for k,v in s['parameters'].items()};rho=params['density'];transient=s['analysis_kind']=='transient'
    xx,quads,patches,volume=native_mesh(native,2);x=xx[:,:2];q=np.array(quads,dtype=np.int64)-1;nc=len(q);n=len(x)
    c=np.concatenate((q[:,[0,1,2]],q[:,[0,2,3]]));faces=np.array([row for pp in patches.values() for row in pp],dtype=np.int64)-1;nb=len(faces);centres=x[q].mean(axis=1)
    incidence={tuple(sorted((row[j],row[(j+1)%4]))):i for i,row in enumerate(q) for j in range(4)};parent=np.array([incidence[tuple(sorted(row))] for row in faces]);mid=x[faces].mean(axis=1)
    tangent=x[faces[:,1]]-x[faces[:,0]];measure=np.linalg.norm(tangent,axis=1);normal=np.column_stack((tangent[:,1],-tangent[:,0]))/measure[:,None];normal[np.einsum('ij,ij->i',normal,mid-centres[parent])<0]*=-1
    boundary=np.zeros(n,bool);boundary[np.unique(faces)]=True
    for _ in range(2):boundary[np.unique(c[np.any(boundary[c],axis=1)])]=True
    keep=np.flatnonzero(~boundary);assert len(keep)
    ns=[[] for _ in x]
    for j,row in enumerate(faces):
        for node in row:ns[node].append(normal[j])
    singular=np.array([len(v)>0 and not np.allclose(v,v[0]) for v in ns]);traces=np.flatnonzero(~np.any(singular[faces],axis=1));assert len(traces)
    inp=job/'input';ref=job/'reference';inp.mkdir(exist_ok=True);ref.mkdir(exist_ok=True);gmsh(inp/'mesh.msh',x,c,faces,2)
    arrays={'nodes':np.arange(1,n+1,dtype=np.int64),'observed':(keep+1).astype(np.int64),'traces':(2*nc+traces+1).astype(np.int64),'cells':np.arange(1,2*nc+1,dtype=np.int64),'requested':np.array(s['output_times_s']),'initial':np.array([0.]),'history':np.array([0,.1,.4,.6,1.] if transient else [0.])}
    def loc(entity,key,dim=None):return {'kind':'mesh','mesh':'main','entity':entity,'ids':key,**({'dimension':dim} if dim is not None else {})}
    locations={'domain':loc('node','nodes'),'observed':loc('node','observed'),'traces':loc('element','traces',1)};fields={};conditions=[]
    def desc(q,where,unit,axis,kind='point',input=False):
        tensor=q in ('conformation','polymer_stress');vec=q in ('velocity','traction');z={'array':q,'quantity':q,'location':where,'time_axis':axis,'dtype':'float64','kind':'tensor' if tensor else 'vector' if vec else 'scalar','component_shape':[2,2] if tensor else [2] if vec else [1],'components':['xx','xy','yx','yy'] if tensor else ['x','y'] if vec else ['value'],'unit':unit,'value_kind':kind}
        if input:z['sampling']={'space':'piecewise_linear' if kind=='point' else 'piecewise_constant','time':'constant' if axis=='initial' or not transient else 'linear','extrapolation':'forbid'}
        return z
    if transient:
        for quantity,unit in [('velocity','m/s'),('conformation','1')]:
            key='initial_'+quantity;v=np.array(s['initial'][quantity]['expression']);arrays[key]=np.broadcast_to(v,(1,n,*v.shape)).copy();fields[key]=desc(quantity,'domain',unit,'initial',input=True);fields[key]['array']=key;conditions.append({'role':'initial','variable':quantity,'operator':'assign','location':'domain','data':{'value':{'field':key}}})
    from elmer_flow_mesh import select
    groups=np.full(nb,0,dtype=int)
    for i,b in enumerate(s['boundaries'][1:],1):groups[select(s,b['selection'],mid)]=i
    for i,b in enumerate(s['boundaries']):
        ids=np.flatnonzero(groups==i)
        if not len(ids):continue
        key=f'boundary{i}';arrays[key]=(2*nc+ids+1).astype(np.int64);locations[key]=loc('element',key,1);fk=key+'velocity';arrays[fk]=np.array([evaluate(b['data']['value']['expression'],mid[ids],t,s) for t in arrays['history']]);fields[fk]=desc('velocity',key,'m/s','history','average',input=True);fields[fk]['array']=fk;conditions.append({'role':'boundary','variable':'velocity','operator':'velocity_wall','location':key,'data':{'value':{'field':fk}}})
    outputs={}
    for r in s['observation_requests']:
        quantity=r['quantity'];outputs[quantity]=desc(quantity,'traces' if quantity=='traction' else 'observed',r['unit'],'requested',r['value_kind'])
    problem={'task':e['task'],'spatial_dimension':2,'data_file':'input.h5','physics':{'model':'fluid-reduced-viscoelastic-'+s['analysis_kind']+'-v1','parameters':s['parameters']},'geometries':{},'meshes':{'main':{'file':'mesh.msh'}},'locations':locations,'time_axes':{'initial':'initial','history':'history','requested':'requested'},'fields':fields,'conditions':conditions,'outputs':outputs}
    save(inp/'problem.json',problem)
    with h5py.File(inp/'input.h5','w') as f:
        for key,v in arrays.items():f[key]=v
    tdirs={round(float(p.name),12):p for p in native.iterdir() if p.is_dir() and re.fullmatch(r'[\d.eE+-]+',p.name)}
    denominator=np.zeros(n)
    for j in range(4):np.add.at(denominator,q[:,j],volume)
    def recover(v):
        out=np.zeros((n,*v.shape[1:]));weight=volume.reshape((-1,)+(1,)*(v.ndim-1))
        for j in range(4):np.add.at(out,q[:,j],v*weight)
        return out/denominator.reshape((-1,)+(1,)*(v.ndim-1))
    result={key:[] for key in outputs}
    for t in s['output_times_s']:
        folder=tdirs[round(t,12)] if transient else tdirs[max(tdirs)]
        assert folder.name!='0','no native steady output'
        u=foam_field(folder/'U',3,nc)[:,:2];p=foam_field(folder/'p',1,nc)[:,0]*rho;p=p-np.dot(volume,p)/sum(volume)+params['reference_pressure']
        sig=foam_field(folder/'sigma',6,nc);tau=-rho*np.stack((sig[:,0],sig[:,1],sig[:,1],sig[:,3]),axis=1).reshape(nc,2,2);A=np.eye(2)+params['relaxation_time']/params['polymer_viscosity']*tau
        grad=foam_field(folder/'gradU',9,nc).reshape(nc,3,3)[:,:2,:2]
        traction=np.einsum('bij,bj->bi',params['solvent_viscosity']*(grad[parent]+np.swapaxes(grad[parent],1,2))+tau[parent]-p[parent,None,None]*np.eye(2),normal)
        vals={'velocity':recover(u)[keep],'pressure':recover(p[:,None])[keep],'polymer_stress':recover(tau)[keep],'conformation':recover(A)[keep],'traction':traction[traces]}
        for key in outputs:assert np.isfinite(vals[key]).all();result[key].append(vals[key])
    with h5py.File(ref/'reference.h5','w') as f:
        for key in ('observed','traces','requested'):f[key]=arrays[key]
        for key,v in result.items():f[key]=np.array(v)
    save(ref/'grading.json',json.loads((job/'grading-template.json').read_text()))
    state.update(status='unvalidated_candidate',reference_sha256=digest(ref/'reference.h5'),nodes=n,cells=2*nc,frames=len(s['output_times_s']),mapping='Native FV stress sigma=-tau_p/rho; A=I+lambda*tau_p/mu_p. Quad mesh split into two triangles. Interior point fields are volume-weighted native cell-to-node recovery, not exact point samples; traction uses native gradU and parent-cell stress. Pressure volume mean is reference_pressure. No numerical verification.');save(job/'status.json',state)
    return state


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--only');ap.add_argument('--workers',type=int,default=18);args=ap.parse_args();assert args.workers<=18;tasks=[]
    freeze=json.loads((args.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text())
    for p in args.snapshot.glob('qbank/02-fluid-mechanics/*/viscoelastic-*/author/chapter02-ten-20261020/design.json'):
        r=json.loads(p.read_text());assert digest(p)==freeze['designs'][p.relative_to(args.snapshot).as_posix()]
        for e in r['proposed_cases']:
            if any(b['operator']!='velocity_wall' for b in e['detailed_spec']['boundaries']):continue
            if args.only and args.only not in e['design_id']:continue
            tasks.append(({**e,'task':r['task']},json.loads((p.parents[1]/'grading-template.json').read_text())))
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=args.workers) as pool:states=list(pool.map(run,[args.root]*len(tasks),[e for e,g in tasks],[g for e,g in tasks]))
    save(args.root/'maintenance/maxwell-summary.json',states);print(json.dumps(states))


if __name__=='__main__':main()
