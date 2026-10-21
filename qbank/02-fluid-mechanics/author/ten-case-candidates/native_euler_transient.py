"""Adapter for unmodified OpenCFD rhoCentralFoam, inviscid perfect gas.

Uses native forwardStep tutorial thermodynamics and flux scheme. mu=0,
Pr=1 switches off both viscous stress and heat conduction. Only closed
slip/adiabatic cases without external sources are admitted by this adapter.
No accuracy or shock admissibility validation is claimed.
"""
import argparse
import hashlib
import json
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import h5py
import numpy as np
from native_closed_cavity import IMAGE,SOCKET,prepare_native,native_mesh,gmsh,field,header,put,save,digest
from polytropic_reference import descriptor

def initial_values(spec,i,xyz,conn):
    d=xyz.shape[1];d=spec['geometry']['dimension'];L=np.array(spec['geometry']['bounding_lengths']);a=xyz[np.array(conn)-1,:d];lo=a.min(axis=1);hi=a.max(axis=1)
    z,w=np.polynomial.legendre.leggauss(8);z=(z+1)/2;w=w/2;rhoavg=np.zeros(len(conn));Tavg=rhoavg.copy()
    import itertools
    for ids in itertools.product(range(8),repeat=d):
        v=lo+(hi-lo)*z[list(ids)];X=v[:,0]/L[0];Y=v[:,1]/L[1]
        def bump(centre,radius):return np.maximum(1-np.sum(((v/L-centre)/radius)**2,axis=1),0)**4
        if i==0:rho=1+.001*np.cos(np.pi*X)
        elif i==1:rho=1+.1*bump(.4,.15)
        elif i==2:rho=1-.1*bump(.5,.15)
        elif i==3:rho=np.where(X<.5,1.,.125)
        elif i==4:rho=np.where(X<.5,1.,.5)
        elif i==5:rho=1+.001*np.cos(np.pi*X)*np.cos(np.pi*Y)
        elif i==9:rho=1+.01*bump(.25,.1)
        else:rho=np.ones(len(conn))
        if i==3:p=np.where(X<.5,86100.,8610.)
        elif i==4:p=np.full(len(conn),86100.)
        elif i==6:p=86100*(1+.3*bump(.5,.15))
        elif i==7:p=86100*(1+.3*bump(.3,.1))
        else:p=86100*rho**1.4
        weight=np.prod(w[list(ids)]);rhoavg+=weight*rho;Tavg+=weight*p/(287*rho)
    return rhoavg,Tavg

def command(job,name,script):return ['docker','--host',SOCKET,'run','--name',name,'--network','none','--cpus','1','--memory','768m','--user',f'{os.getuid()}:{os.getgid()}','-e','HOME=/tmp','-v',f'{job.resolve()}:/work',IMAGE,'bash','-c','source /usr/lib/openfoam/openfoam2512/etc/bashrc && cd /work/native && '+script]

def run(root,r,e,grading,source_adapter=None,native_name=None):
    job=root/'cases'/e['design_id'];status=job/'status.json'
    if status.exists():return json.loads(status.read_text())
    s=e['detailed_spec'];assert not s['sources'] or source_adapter is not None;d=e['spatial_dimension'];i=int(e['design_id'].split('-')[-2])-1
    assert s['geometry']['operation']=='box';job.mkdir(parents=True);save(job/'design.json',e);state={'design_id':e['design_id'],'status':'preparing'};save(status,state)
    try:
        L=s['geometry']['bounding_lengths']+([.02] if d==2 else []);cells=s['mesh_recipe']['base_divisions']+([1] if d==2 else [])
        p={'spatial_dimension':d,'length_m':L,'target_cells_xyz':cells,'obstacle_xy_fraction':[.4,.6,.3,.5] if s['geometry']['holes'] else None,'wall_speed_multiplier_linear_table':[[0,0],[.001,0]],'wall_velocity_vectors_m_s':{},'dynamic_viscosity_Pa_s':0.,'density_kg_m3':1.,'time_interval_s':[0,.001],'native_dt_s':1e-6}
        native=job/'native';prepare_native(native,p);base=native_name or 'ch02euler-'+hashlib.sha256(e['design_id'].encode()).hexdigest()[:12]
        cmd=command(job,base+'-mesh','blockMesh');save(job/'mesh-execution.json',{'command':cmd,'image':IMAGE});cp=subprocess.run(cmd,capture_output=True,text=True,timeout=120);put(job/'blockMesh.log',cp.stdout+cp.stderr);assert cp.returncode==0
        xyz,conn,patches,vol=native_mesh(native,d);rho,T=initial_values(s,i,xyz,conn);n=len(conn)
        def scalar_file(name,vals,dimensions):
            body='\n'.join(f'{x:.16g}' for x in vals);bcs=[]
            for key in patches:bcs.append(f'{key} {{ type zeroGradient; }}')
            if d==2:bcs += ['front { type empty; }','back { type empty; }']
            put(native/'0'/name,header('volScalarField',name)+f'dimensions {dimensions};\ninternalField nonuniform List<scalar>\n{n}\n(\n{body}\n);\nboundaryField {{ '+' '.join(bcs)+' }\n')
        scalar_file('T',T,'[0 0 0 1 0 0 0]');scalar_file('p',rho*287*T,'[1 -1 -2 0 0 0 0]')
        bcs=[f'{key} {{ type slip; }}' for key in patches]
        if d==2:bcs+=['front { type empty; }','back { type empty; }']
        put(native/'0/U',header('volVectorField','U')+'dimensions [0 1 -1 0 0 0 0]; internalField uniform (0 0 0); boundaryField { '+' '.join(bcs)+' }\n')
        put(native/'constant/thermophysicalProperties',header('dictionary','thermophysicalProperties')+f'thermoType {{ type hePsiThermo; mixture pureMixture; transport const; thermo hConst; equationOfState perfectGas; specie specie; energy sensibleInternalEnergy; }} mixture {{ specie {{ molWeight {8314.46261815324/287:.17g}; }} thermodynamics {{ Cp 1004.5; Hf 0; }} transport {{ mu 0; Pr 1; }} }}\n')
        put(native/'constant/turbulenceProperties',header('dictionary','turbulenceProperties')+'simulationType laminar;\n')
        put(native/'system/fvSchemes',header('dictionary','fvSchemes')+'fluxScheme Kurganov; ddtSchemes { default Euler; } gradSchemes { default Gauss linear; } divSchemes { default none; div(tauMC) Gauss linear; } laplacianSchemes { default Gauss linear corrected; } interpolationSchemes { default linear; reconstruct(rho) vanLeer; reconstruct(U) vanLeerV; reconstruct(T) vanLeer; } snGradSchemes { default corrected; }\n')
        put(native/'system/fvSolution',header('dictionary','fvSolution')+'solvers { "(rho|rhoU|rhoE)" { solver diagonal; } U { solver smoothSolver; smoother GaussSeidel; tolerance 1e-9; relTol 0; } h { $U; tolerance 1e-10; } e { $U; tolerance 1e-10; } }\n')
        put(native/'system/controlDict',header('dictionary','controlDict')+'application rhoCentralFoam; startFrom startTime; startTime 0; stopAt endTime; endTime .001; deltaT .000001; adjustTimeStep no; writeControl timeStep; writeInterval 1; purgeWrite 0; writeFormat ascii; writePrecision 16; writeCompression off; timeFormat general; timePrecision 12; runTimeModifiable false;\n')
        inp=job/'input';ref=job/'reference';inp.mkdir();ref.mkdir();ids=gmsh(inp/'mesh.msh',xyz,conn,patches,d)
        def loc(key,dim):return {'kind':'mesh','mesh':'main','entity':'element','dimension':dim,'ids':key}
        locations={'domain':loc('cells',d)}
        conditions=[];fields={}
        with h5py.File(inp/'input.h5','w') as f:
            f['cells']=np.arange(1,n+1,dtype=np.int64);f['initial']=np.array([0.]);f['requested']=np.array(s['output_times_s'])
            for q,a,u,cc in [('density',rho,'kg/m3',1),('temperature',T,'K',1),('velocity',np.zeros((n,d)),'m/s',d)]:
                f[q]=a[None,:,None] if cc==1 else a[None];fields[q]=descriptor(q,cc,u,'domain');fields[q]['time_axis']='initial';conditions.append({'role':'initial','variable':q,'operator':'assign','location':'domain','data':{'value':{'field':q}}})
            for key,v in ids.items():
                f[key]=v;locations[key]=loc(key,d-1);conditions.append({'role':'boundary','variable':'velocity','operator':'slip_wall','location':key,'data':{'impermeable':{'option':'yes'}}})
        outputs={q:descriptor(q,cc,u,'domain',True) for q,u,cc in [('velocity','m/s',d),('pressure','Pa',1),('temperature','K',1),('density','kg/m3',1)]}
        for o in outputs.values():o['time_axis']='requested'
        problem={'task':r['task'],'spatial_dimension':d,'physics':{'model':r['model'],'parameters':s['parameters']},'data_file':'input.h5','geometries':{},'meshes':{'main':{'file':'mesh.msh'}},'locations':locations,'time_axes':{'initial':'initial','requested':'requested'},'fields':fields,'conditions':conditions,'outputs':outputs};save(inp/'problem.json',problem)
        app='rhoCentralFoam' if source_adapter is None else source_adapter(job,s)
        cmd=command(job,base,app);save(job/'execution.json',{'command':cmd,'image':IMAGE,'producer':'unmodified OpenCFD '+app,'source':'OpenCFD v2512 applications/solvers/compressible/rhoCentralFoam; native forwardStep tutorial inviscid configuration','script_sha256':digest(Path(__file__)),'start_unix':time.time(),'numerical_validation':False});state.update(status='running',container=base);save(status,state);cp=subprocess.run(cmd,capture_output=True,text=True,timeout=1800);put(job/'rhoCentralFoam.log',cp.stdout+cp.stderr);assert cp.returncode==0,f'Native exit {cp.returncode}'
        native_times={round(float(p.name),12):p for p in native.iterdir() if p.is_dir() and p.name[0].isdigit()};result={q:[] for q in outputs}
        for t in s['output_times_s']:
            td=native_times[t]
            for q,nativeq,cc in [('velocity','U',3),('pressure','p',1),('temperature','T',1),('density','rho',1)]:result[q].append(field(td/nativeq,cc,n)[:,:d] if q=='velocity' else field(td/nativeq,cc,n))
        assert all(np.isfinite(a).all() for a in result.values())
        with h5py.File(ref/'reference.h5','w') as f:
            f['cells']=np.arange(1,n+1,dtype=np.int64);f['requested']=np.array(s['output_times_s'])
            for q,a in result.items():f[q]=np.array(a)
        save(ref/'grading.json',grading);state.update(status='unvalidated_candidate',cells=n,reference_sha256=digest(ref/'reference.h5'),output_frames=len(s['output_times_s']),input_sha256={p.name:digest(p) for p in inp.iterdir()},limitations=['No numerical or entropy/shock verification.','Native FV cell values represent approximate cell averages.','Initial density and temperature sampled by 8-point tensor Gauss integration; pressure then follows the actual input equation of state.'])
    except Exception as ex:state.update(status='needs_attention',error=repr(ex))
    save(status,state);return state

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--limit',type=int,default=18);args=ap.parse_args();ready=[]
    frozen=json.loads((args.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text());assert frozen['design_complete'] and len(frozen['designs'])==63
    for p in args.snapshot.glob('qbank/02-fluid-mechanics/*/inviscid-compressible-transient-*/author/chapter02-ten-20261020/design.json'):
        assert hashlib.sha256(p.read_text().encode()).hexdigest()==frozen['designs'][p.relative_to(args.snapshot).as_posix()]
        r=json.loads(p.read_text());g=json.loads((p.parents[1]/'grading-template.json').read_text())
        for e in r['proposed_cases']:
            if not e['detailed_spec']['sources']:ready.append((r,e,g))
    assert len(ready)==18
    # At most 18 independent one-core jobs; caller checks shared host/cgroup headroom.
    with ThreadPoolExecutor(max_workers=18) as pool:states=list(pool.map(lambda v:run(args.root,*v),ready[:args.limit]))
    save(args.root/'maintenance/euler-transient-summary.json',states);print(json.dumps({'completed':sum(s['status']=='unvalidated_candidate' for s in states),'needs_attention':sum(s['status']=='needs_attention' for s in states)}))

if __name__=='__main__':main()
