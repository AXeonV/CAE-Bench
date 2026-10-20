"""Native OpenCFD SST RANS, LRR URANS and WALE statistics adapter.

Closures are producer choices explicitly permitted by these task statements.
No model equation is implemented here. Initial R and epsilon are mapped from
the supplied k/l, preserving isotropic R instead of inventing fluctuations.
"""
import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import time
import traceback
from pathlib import Path
import h5py
import numpy as np
from native_closed_cavity import IMAGE,SOCKET,header,put,save,digest,vector,field
from native_power_periodic import prepare as prepare_base,input_mesh
from native_lowmach import cell_source
from elmer_flow_mesh import select
from titan_resources import reservation


def spatial_expr(v,d):
    if isinstance(v,list):return v
    assert v in ('(.1*1*sin(2*pi*Y),0[,0])','(.1*R*sin(2*pi*Y),0[,0])'),v
    return ['.1*'+('R' if '*R*' in v else '1')+'*sin(2*pi*Y)']+[0]*(d-1)


def scalar_file(native,name,dimensions,values,wall_type):
    n=len(values);boundaries=re.findall(r'(?m)^(\w+) \{ type (\w+);', (native/'system/blockMeshDict').read_text());entries=[]
    for key,typ in boundaries:
        if typ=='empty':entries.append(key+' { type empty; }')
        else:entries.append(key+' { type '+wall_type+'; value uniform '+str(values[0])+'; }')
    put(native/'0'/name,header('volScalarField',name)+'dimensions '+dimensions+';\ninternalField nonuniform List<scalar>\n'+str(n)+'\n(\n'+'\n'.join(map(str,values))+'\n);\nboundaryField {\n'+'\n'.join(entries)+'\n}\n')


def prepare(job,e,steady_closure="kOmegaSST"):
    s=e['detailed_spec'];p={k:v['value'] for k,v in s['parameters'].items()};view=copy.deepcopy(e);v=view['detailed_spec'];v['analysis_kind']='steady' if s['analysis_kind']=='steady' else 'transient';v['sources']={};v['materials']={'density':{'kind':'constant','parameters':{'density':{'value':p['density'],'unit':'kg/m3'}}},'viscosity':{'kind':'newtonian','parameters':{'dynamic_viscosity':{'value':p['reference_viscosity'],'unit':'Pa.s'}}}};app=prepare_base(job,view);save(job/'native-adapter-view.json',view);native=job/'native';mode='WALE' if s['analysis_kind']=='discrete_statistics' else steady_closure if s['analysis_kind']=='steady' else 'LRR'
    if mode=='LRR':turb='simulationType RAS; RAS { RASModel LRR; turbulence on; printCoeffs on; LRRCoeffs { Cmu 0.09; C1 1.8; C2 0.6; Ceps1 1.44; Ceps2 1.92; Cs 0.25; Ceps 0.15; wallReflection true; kappa 0.41; Cref1 0.5; Cref2 0.3; } }\n'
    elif mode=='kEpsilon':turb='simulationType RAS; RAS { RASModel kEpsilon; turbulence on; printCoeffs on; }\n'
    elif mode=='kOmegaSST':turb='simulationType RAS; RAS { RASModel kOmegaSST; turbulence on; printCoeffs on; }\n'
    else:turb='simulationType LES; LES { LESModel WALE; turbulence on; printCoeffs on; delta cubeRootVol; WALECoeffs { Ck 0.094; Cw 0.325; } cubeRootVolCoeffs { deltaCoeff 1; } }\n'
    put(native/'constant/turbulenceProperties',header('dictionary','turbulenceProperties')+turb)
    schemes=(native/'system/fvSchemes').read_text().replace('div(phi,U) Gauss linearUpwind grad(U);','div(phi,U) Gauss linearUpwind grad(U); div(phi,R) Gauss upwind; div(phi,epsilon) Gauss upwind; div(R) Gauss linear; div(devRhoReff) Gauss linear; div((nu*dev2(T(grad(U))))) Gauss linear;')+'\nwallDist { method meshWave; }\n';put(native/'system/fvSchemes',schemes)
    sol=(native/'system/fvSolution').read_text().replace('solvers {','solvers { R { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-9; relTol 0; } RFinal { $R; relTol 0; } epsilon { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-9; relTol 0; } epsilonFinal { $epsilon; relTol 0; }')
    sol=sol.replace('equations { U 0.5; }','equations { U 0.5; R 0.4; epsilon 0.4; }').replace('equations { U 1; }','equations { U 1; R 1; epsilon 1; }').replace('residualControl { p 1e-9; U 1e-9; }','residualControl { p 1e-6; U 1e-6; R 1e-6; epsilon 1e-6; }')
    put(native/'system/fvSolution',sol)
    if mode=='kOmegaSST':
        schemes=schemes.replace('div(phi,U) Gauss linearUpwind grad(U);','div(phi,U) Gauss upwind;').replace('div(phi,R) Gauss upwind;','div(phi,k) Gauss upwind; div(phi,omega) Gauss upwind;');put(native/'system/fvSchemes',schemes)
        sol=sol.replace('solvers {','solvers { k { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-9; relTol 0; } omega { $k; }').replace('R 1e-6; epsilon 1e-6;','k 1e-6; omega 1e-6;').replace('R 0.4; epsilon 0.4;','k 0.1; omega 0.1;').replace('p 0.3;','p 0.1;').replace('U 0.5;','U 0.1;');put(native/'system/fvSolution',sol)
    if mode=='kEpsilon':
        schemes=schemes.replace('div(phi,U) Gauss linearUpwind grad(U);','div(phi,U) Gauss upwind;').replace('div(phi,R) Gauss upwind;','div(phi,k) Gauss upwind;');put(native/'system/fvSchemes',schemes)
        sol=sol.replace('solvers {','solvers { k { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-9; relTol 0; }').replace('R 1e-6; epsilon 1e-6;','k 1e-6; epsilon 1e-6;').replace('R 0.4; epsilon 0.4;','k 0.05; epsilon 0.05;').replace('p 0.3;','p 0.05;').replace('U 0.5;','U 0.05;');put(native/'system/fvSolution',sol)
    control=(native/'system/controlDict').read_text();control=control.rsplit('}',1)[0]+' closureFields { type turbulenceFields; libs (fieldFunctionObjects); fields (k); executeControl writeTime; writeControl writeTime; } }\n'
    if s['sources']:control=control.rsplit('}',1)[0]+' readSource { type readFields; libs (fieldFunctionObjects); fields (bodyAcceleration); readOnStart true; } }\n'
    put(native/'system/controlDict',control);return app,view,mode


def initialize(job,e,view,mode):
    m=input_mesh(job,view);s=e['detailed_spec'];d=e['spatial_dimension'];native=job/'native';nc=len(m['c']);nparent=len(m['native_volume']);parent=m['parent'];volume=m['volume'];end=(s['time_interval_s'] or [0,1])[1]
    def average(v):
        out=np.zeros((nparent,*v.shape[1:]));weight=volume.reshape((-1,)+(1,)*(v.ndim-1));np.add.at(out,parent,v*weight);return out/m['native_volume'].reshape((-1,)+(1,)*(v.ndim-1))
    if s['sources']:
        assert set(s['sources'])=={'acceleration'}
        expr=spatial_expr(s['sources']['acceleration']['expression'],d);raw=cell_source(expr,m['x'],m['c'],end,s);m['acceleration']=raw;body=average(raw);body3=np.pad(body,((0,0),(0,3-d)));names=re.findall(r'(?m)^(\w+) \{ type (\w+);',(native/'system/blockMeshDict').read_text());bc='\n'.join(name+' { type '+('empty' if typ=='empty' else 'zeroGradient')+'; }' for name,typ in names)
        put(native/'0/bodyAcceleration',header('volVectorField','bodyAcceleration')+'dimensions [0 1 -2 0 0 0 0];\ninternalField nonuniform List<vector>\n'+str(nparent)+'\n(\n'+'\n'.join(vector(v) for v in body3)+'\n);\nboundaryField {\n'+bc+'\n}\n')
        scale='1' if s['analysis_kind']=='steady' else f'min(max(time()/{.1*end},0),1)'
        put(native/'constant/fvOptions',header('dictionary','fvOptions')+'acceleration { type vectorSemiImplicitSource; selectionMode all; volumeMode specific; sources { U { explicit { type exprField; expression "bodyAcceleration*('+scale+')"; } implicit none; } } }\n')
    if mode=='LRR':
        kexpr=s['initial'].get('turbulent_kinetic_energy',{'expression':.001})['expression'];lexpr=s['initial'].get('turbulence_length_scale',{'expression':.05})['expression'];k=cell_source(kexpr,m['x'],m['c'],0,s);length=cell_source(lexpr,m['x'],m['c'],0,s);m['initial_k']=k;m['initial_l']=length;kn=average(k);epsilon=average(.09**.75*k**1.5/length);R=np.zeros((nparent,6));R[:,[0,3,5]]=2*kn[:,None]/3
        names=re.findall(r'(?m)^(\w+) \{ type (\w+);',(native/'system/blockMeshDict').read_text());bc='\n'.join(name+' { type '+('empty' if typ=='empty' else 'kqRWallFunction')+';'+('' if typ=='empty' else ' value uniform (0 0 0 0 0 0);')+' }' for name,typ in names)
        put(native/'0/R',header('volSymmTensorField','R')+'dimensions [0 2 -2 0 0 0 0];\ninternalField nonuniform List<symmTensor>\n'+str(nparent)+'\n(\n'+'\n'.join(vector(v) for v in R)+'\n);\nboundaryField {\n'+bc+'\n}\n');scalar_file(native,'epsilon','[0 2 -3 0 0 0 0]',epsilon,'epsilonWallFunction')
    elif mode=='kEpsilon':
        scalar_file(native,'k','[0 2 -2 0 0 0 0]',np.full(nparent,.001),'kqRWallFunction');scalar_file(native,'epsilon','[0 2 -3 0 0 0 0]',np.full(nparent,.09**.75*.001**1.5/.05),'epsilonWallFunction')
    elif mode=='kOmegaSST':
        scalar_file(native,'k','[0 2 -2 0 0 0 0]',np.full(nparent,.001),'kqRWallFunction');scalar_file(native,'omega','[0 0 -1 0 0 0 0]',np.full(nparent,np.sqrt(.001)/(.09**.25*.05)),'omegaWallFunction')
    scalar_file(native,'nut','[0 2 -1 0 0 0 0]',np.zeros(nparent),'nutLowReWallFunction' if mode=='WALE' else 'nutkWallFunction');np.savez(job/'adapter-data.npz',**m)
    return m


def convert(job,e,m,mode):
    s=e['detailed_spec'];d=e['spatial_dimension'];params={k:v['value'] for k,v in s['parameters'].items()};nc=len(m['c']);parent=m['parent'];nparent=len(m['native_volume']);end=(s['time_interval_s'] or [0,1])[1];hist=np.array([0,.1*end,.4*end,.6*end,end] if s['analysis_kind']!='steady' else [0.]);x=m['x'];c=m['c'];b=m['b'];mid=x[b].mean(axis=1);groups=np.zeros(len(b),dtype=int)
    for i,bc in enumerate(s['boundaries'][1:],1):groups[select(s,bc['selection'],mid)]=i
    arrays={'cells':np.arange(1,nc+1,dtype=np.int64),'history':hist,'initial':np.array([0.]),'requested':np.array(s['output_times_s'])};locations={'domain':{'kind':'mesh','mesh':'main','entity':'element','dimension':d,'ids':'cells'}};fields={};conditions=[]
    def desc(q,where,axis,unit,components=1,input=False):
        tensor=q=='velocity_covariance';z={'array':q,'quantity':q,'location':where,'time_axis':axis,'dtype':'float64','kind':'tensor' if tensor else 'scalar' if components==1 else 'vector','component_shape':[d,d] if tensor else [components],'components':[a+b for a in 'xyz'[:d] for b in 'xyz'[:d]] if tensor else ['value'] if components==1 else list('xyz'[:d]),'unit':unit,'value_kind':'average'}
        if input:z['sampling']={'space':'piecewise_constant','time':'linear' if axis=='history' and s['analysis_kind']!='steady' else 'constant','extrapolation':'forbid'}
        return z
    def field_entry(key,q,where,axis,unit,v,role,operator,var):
        v=np.asarray(v,dtype=float);v=v[...,None] if v.ndim==2 else v;arrays[key]=v;fields[key]=desc(q,where,axis,unit,v.shape[-1],True);fields[key]['array']=key;conditions.append({'role':role,'variable':var,'operator':operator,'location':where,'data':{'value':{'field':key}}})
    if s['analysis_kind']!='steady':
        field_entry('initial_velocity','velocity','domain','initial','m/s',m['initial'][None],'initial','assign','velocity')
        if mode=='LRR':
            for key,unit,name in [('turbulent_kinetic_energy','m2/s2','initial_k'),('turbulence_length_scale','m','initial_l')]:field_entry(key,key,'domain','initial',unit,m[name][None],'initial','assign',key)
    if s['sources']:field_entry('acceleration','acceleration','domain','history','m/s2',np.array([m['acceleration']*(1 if s['analysis_kind']=='steady' else np.clip(t/(.1*end),0,1)) for t in hist]),'source','assign','acceleration')
    from native_elmer_incompressible import evaluate
    for i,bc in enumerate(s['boundaries']):
        ids=np.flatnonzero(groups==i)
        if not len(ids):continue
        name=f'boundary{i}';arrays[name]=(nc+ids+1).astype(np.int64);locations[name]={'kind':'mesh','mesh':'main','entity':'element','dimension':d-1,'ids':name};field_entry(name+'velocity','velocity',name,'history','m/s',np.array([evaluate(bc['data']['velocity']['expression'],mid[ids],t,s) for t in hist]),'boundary','moving_wall','velocity')
    outputs={r['quantity']:desc(r['quantity'],'domain','requested',r['unit'],d if r['quantity']=='velocity' else 1) for r in s['observation_requests']};inp=job/'input';ref=job/'reference';inp.mkdir(exist_ok=True);ref.mkdir(exist_ok=True)
    from polytropic_reference import gmsh
    gmsh(inp/'mesh.msh',x,c,b,d);save(inp/'problem.json',{'task':e['task'],'spatial_dimension':d,'physics':{'model':e['model'],'parameters':s['parameters']},'data_file':'input.h5','geometries':{},'meshes':{'main':{'file':'mesh.msh'}},'locations':locations,'time_axes':{'history':'history','initial':'initial','requested':'requested'},'fields':fields,'conditions':conditions,'outputs':outputs})
    with h5py.File(inp/'input.h5','w') as f:
        for k,v in arrays.items():f[k]=v
    tdirs={round(float(p.name),12):p for p in (job/'native').iterdir() if p.is_dir() and re.fullmatch(r'[\d.eE+-]+',p.name)}
    if mode=='WALE':
        a=params['statistics_start'];delta=params['statistics_step'];count=round((params['statistics_end']-a)/delta)+1;times=a+np.arange(count)*delta
    else:times=s['output_times_s']
    us=[];ps=[]
    for t in times:
        folder=tdirs[round(float(t),12)] if s['analysis_kind']!='steady' else tdirs[max(tdirs)];assert folder.name!='0';u=field(folder/'U',3,nparent)[:,:d][parent];p=field(folder/'p',1,nparent)[parent]*params['density']
        if mode!='LRR':
            # Native eddy-viscosity momentum absorbs isotropic SGS k in p;
            # LRR explicitly transports full R, so its p is already static.
            k=field(folder/'turbulenceProperties:k',1,nparent)[parent];p-=2/3*params['density']*k
        p-=np.dot(m['volume'],p[:,0])/sum(m['volume']);assert np.isfinite(u).all() and np.isfinite(p).all();us.append(u);ps.append(p)
    if mode=='WALE':
        u=np.array(us);mean=u.mean(axis=0);delta=u-mean;result={'velocity':mean[None],'pressure':np.array(ps).mean(axis=0)[None],'velocity_covariance':np.einsum('sni,snj->nij',delta,delta)[None]/len(times)}
    else:result={'velocity':np.array(us),'pressure':np.array(ps)}
    with h5py.File(ref/'reference.h5','w') as f:
        f['cells']=arrays['cells'];f['requested']=arrays['requested']
        for k,v in result.items():f[k]=v
    return {'reference_sha256':digest(ref/'reference.h5'),'cells':nc,'native_cells':nparent,'frames':len(arrays['requested']),'closure':mode,'mapping':'Native FV cell means assigned to conforming child simplices. LRR uses full Reynolds-stress divergence and static pressure; kOmegaSST/WALE isotropic k is subtracted from native modified pressure, then mean gauge enforced. Statistics use actual equally weighted samples after spatial averages, population covariance. Body P0 input is volume-averaged into native source cells; URANS initial R=2k/3 I and epsilon=Cmu^.75 k^1.5/l. No resolution, closure-error or convergence certification.'}


def run(root,e,g,steady_closure="kOmegaSST"):
    job=root/'cases'/e['design_id'];status=job/'status.json'
    if status.exists():return json.loads(status.read_text())
    job.mkdir(parents=True);save(job/'design.json',e);state={'design_id':e['design_id'],'status':'queued'};save(status,state);name='ch02turb-'+hashlib.sha256(e['design_id'].encode()).hexdigest()[:12]+'-'+str(time.time_ns())[-9:]
    try:
        with reservation(root,name):
            app,view,mode=prepare(job,e,steady_closure);common=['docker','--host',SOCKET,'run','--network','none','--cpus','1','--memory','768m','--user',f'{os.getuid()}:{os.getgid()}','-e','OMP_NUM_THREADS=1','-v',f'{job.resolve()}:/work','-w','/work/native'];cmd=common+['--rm',IMAGE,'bash','-c','source /usr/lib/openfoam/openfoam2512/etc/bashrc && cd /work/native && blockMesh > ../blockMesh.log 2>&1'];subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT);data=initialize(job,e,view,mode);cmd=common+['--name',name,IMAGE,'bash','-c',f'source /usr/lib/openfoam/openfoam2512/etc/bashrc && cd /work/native && {app} > ../solver.log 2>&1'];save(job/'execution.json',{'producer':f'unmodified OpenCFD {app}, {mode}','image':IMAGE,'source':'image:/usr/lib/openfoam/openfoam2512/src/TurbulenceModels/turbulenceModels/'+('RAS/'+mode if mode in ('LRR','kOmegaSST','kEpsilon') else 'LES/WALE'),'command':cmd,'script_sha256':digest(Path(__file__)),'start_unix':time.time(),'numerical_validation':False});state.update(status='running',container=name);save(status,state)
            with (job/'docker.log').open('w') as log:cp=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
            assert cp.returncode==0,f'native exit {cp.returncode}'
        if e['detailed_spec']['analysis_kind']=='steady' and 'SIMPLE solution converged' not in (job/'solver.log').read_text():state['status']='native_iteration_limit'
        else:state.update(convert(job,e,data,mode));save(job/'reference/grading.json',g);state['status']='unvalidated_candidate'
    except Exception as ex:state.update(status='needs_attention',error=repr(ex),traceback=traceback.format_exc())
    state['ended_unix']=time.time();save(status,state);return state


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int,default=40);ap.add_argument('--only');ap.add_argument('--steady-closure',choices=['kOmegaSST','kEpsilon'],default='kOmegaSST');args=ap.parse_args();tasks=[];freeze=json.loads((args.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text())
    for p in args.snapshot.glob('qbank/02-fluid-mechanics/*/*/author/chapter02-ten-20261020/design.json'):
        r=json.loads(p.read_text())
        if r['question'] not in ('2.3.1','2.3.2','2.3.3','2.3.4'):continue
        assert digest(p)==freeze['designs'][p.relative_to(args.snapshot).as_posix()]
        for e in r['proposed_cases']:
            if args.only and args.only not in e['design_id']:continue
            tasks.append(({**e,'task':r['task'],'model':r['model']},json.loads((p.parents[1]/'grading-template.json').read_text())))
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=min(args.workers,len(tasks))) as pool:states=list(pool.map(run,[args.root]*len(tasks),[e for e,g in tasks],[g for e,g in tasks],[args.steady_closure]*len(tasks)))
    save(args.root/'maintenance/turbulence-summary.json',states);print(json.dumps({'completed':sum(s['status']=='unvalidated_candidate' for s in states),'attention':[s for s in states if s['status']=='needs_attention']}))


if __name__=='__main__':main()
