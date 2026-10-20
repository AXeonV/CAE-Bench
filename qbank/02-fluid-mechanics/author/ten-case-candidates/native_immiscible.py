"""Configure stock interFoam for two viscous inertial phases, sigma=0.

Initial alpha is a union of actual mesh cells. No custom evolution equation.
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
from native_closed_cavity import IMAGE, SOCKET, header, put, save, digest, vector, field
from native_power_periodic import prepare as prepare_base, input_mesh
from native_lowmach import cell_source
from polytropic_reference import gmsh
from titan_resources import reservation


def mask(expression, points, lengths):
    x=points;L=np.array(lengths);X=x[:,0]/L[0];Y=x[:,1]/L[1]
    Z=x[:,2]/L[2] if len(L)==3 else np.zeros(len(x))
    result=np.zeros(len(x),dtype=bool)
    for term in expression.split(' or '):
        term=term.replace('^','**')
        env={'X':X,'Y':Y,'Z':Z,'x':x,'L':L,'pi':np.pi,'cos':np.cos,'sin':np.sin,'sum':lambda a:np.sum(a,axis=1)}
        result|=eval(term,{'__builtins__':{}},env)
    return result.astype(float)


def prepare(job,e):
    s=e['detailed_spec'];p={k:v['value'] for k,v in s['parameters'].items()};d=e['spatial_dimension'];view=copy.deepcopy(e);v=view['detailed_spec'];v['sources']={};v['materials']={'density':{'kind':'constant','parameters':{'density':{'value':p['density_a'],'unit':'kg/m3'}}},'viscosity':{'kind':'newtonian','parameters':{'dynamic_viscosity':{'value':p['viscosity_a'],'unit':'Pa.s'}}}}
    prepare_base(job,view);save(job/'native-adapter-view.json',view);n=job/'native';end=p['time_end'];dt=(end-p['time_start'])/1000;assert p['time_start']==0
    put(n/'constant/transportProperties',header('dictionary','transportProperties')+f'phases (a b); a {{ transportModel Newtonian; nu {p["viscosity_a"]/p["density_a"]}; rho {p["density_a"]}; }} b {{ transportModel Newtonian; nu {p["viscosity_b"]/p["density_b"]}; rho {p["density_b"]}; }} sigma 0;\n')
    put(n/'constant/g',header('uniformDimensionedVectorField','g')+'dimensions [0 1 -2 0 0 0 0]; value (0 0 0);\n')
    put(n/'system/fvSchemes',header('dictionary','fvSchemes')+'ddtSchemes { default Euler; } gradSchemes { default Gauss linear; } divSchemes { default none; div(rhoPhi,U) Gauss linearUpwind grad(U); div(phi,alpha) Gauss vanLeer; div(phirb,alpha) Gauss linear; div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear; } laplacianSchemes { default Gauss linear corrected; } interpolationSchemes { default linear; } snGradSchemes { default corrected; } fluxRequired { default no; p_rgh; pcorr; alpha.a; }\n')
    put(n/'system/fvSolution',header('dictionary','fvSolution')+'solvers { "alpha.a.*" { nAlphaCorr 2; nAlphaSubCycles 1; cAlpha 1; MULESCorr yes; nLimiterIter 5; solver smoothSolver; smoother symGaussSeidel; tolerance 1e-9; relTol 0; } "pcorr.*" { solver PCG; preconditioner DIC; tolerance 1e-9; relTol 0; } p_rgh { solver PCG; preconditioner DIC; tolerance 1e-9; relTol 0; } p_rghFinal { $p_rgh; } U { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-9; relTol 0; } UFinal { $U; } } PIMPLE { momentumPredictor yes; nOuterCorrectors 2; nCorrectors 2; nNonOrthogonalCorrectors 0; pRefCell 0; pRefValue 0; } relaxationFactors { equations { ".*" 1; } }\n')
    put(n/'system/controlDict',header('dictionary','controlDict')+f'application interFoam; startFrom startTime; startTime 0; stopAt endTime; endTime {end}; deltaT {dt}; adjustTimeStep false; maxCo 0.5; maxAlphaCo 0.5; maxDeltaT {dt}; writeControl timeStep; writeInterval 1; purgeWrite 0; writeFormat ascii; writePrecision 16; timeFormat general; timePrecision 12; runTimeModifiable false; functions {{ readSource {{ type readFields; libs (fieldFunctionObjects); fields (bodyAcceleration); readOnStart true; }} }}\n')
    return view


def initialize(job,e,view):
    m=input_mesh(job,view);s=e['detailed_spec'];d=e['spatial_dimension'];n=job/'native';parent=m['parent'];nv=m['native_volume'];nc=len(nv);x=m['x'];c=m['c'];centre=np.zeros((nc,d));np.add.at(centre,parent,x[c].mean(axis=1)*m['volume'][:,None]);centre/=nv[:,None]
    alpha=mask(s['initial']['alpha']['expression'],centre,s['geometry']['bounding_lengths']);assert 0<alpha.sum()<nc;m['alpha']=alpha[parent]
    a=cell_source(s['sources']['acceleration']['expression'],x,c,s['time_interval_s'][1],s);m['acceleration']=a;body=np.zeros((nc,d));np.add.at(body,parent,a*m['volume'][:,None]);body/=nv[:,None]
    patches=re.findall(r'(?m)^(\w+) \{ type (\w+);',(n/'system/blockMeshDict').read_text())
    def write(name,cls,dim,values,wall):
        vec=values.ndim==2;bc='\n'.join(key+' { type '+('empty' if typ=='empty' else wall)+';'+(' value uniform 0;' if typ!='empty' and wall=='fixedFluxPressure' else '')+' }' for key,typ in patches)
        vals='\n'.join(vector(v) if vec else str(v) for v in values)
        put(n/('0/'+name),header(cls,name)+f'dimensions {dim}; internalField nonuniform List<'+('vector' if vec else 'scalar')+f'>\n{nc}\n(\n'+vals+'\n); boundaryField {\n'+bc+'\n}\n')
    write('alpha.a','volScalarField','[0 0 0 0 0 0 0]',alpha,'zeroGradient');write('p_rgh','volScalarField','[1 -1 -2 0 0 0 0]',np.zeros(nc),'fixedFluxPressure');write('bodyAcceleration','volVectorField','[0 1 -2 0 0 0 0]',np.pad(body,((0,0),(0,3-d))),'zeroGradient')
    # interFoam's conservative momentum equation needs force density, rho*a.
    ramp=.1*s['time_interval_s'][1]
    put(n/'constant/fvOptions',header('dictionary','fvOptions')+f'acceleration {{ type vectorSemiImplicitSource; selectionMode all; volumeMode specific; sources {{ U {{ explicit {{ type exprField; expression "bodyAcceleration*(rho*min(max(time()/{ramp},0),1))"; }} implicit none; }} }} }}\n')
    np.savez(job/'adapter-data.npz',**m);return m


def package(job,e,m):
    s=e['detailed_spec'];d=e['spatial_dimension'];p={k:v['value'] for k,v in s['parameters'].items()};x=m['x'];c=m['c'];b=m['b'];nc=len(c);end=p['time_end'];times=np.array(s['output_times_s']);hist=np.array([0,.1*end,end]);arrays={'cells':np.arange(1,nc+1,dtype=np.int64),'walls':np.arange(nc+1,nc+len(b)+1,dtype=np.int64),'initial':np.array([0.]),'history':hist,'requested':times,'initial_alpha':m['alpha'][None,:,None],'initial_velocity':m['initial'][None],'acceleration':np.array([m['acceleration']*min(t/(.1*end),1) for t in hist])}
    locations={'domain':{'kind':'mesh','mesh':'main','entity':'element','dimension':d,'ids':'cells'},'walls':{'kind':'mesh','mesh':'main','entity':'element','dimension':d-1,'ids':'walls'}}
    def desc(key,q,axis,unit,components,input=False):
        z={'array':key,'quantity':q,'location':'domain','time_axis':axis,'dtype':'float64','kind':'scalar' if components==1 else 'vector','component_shape':[components],'components':['value'] if components==1 else list('xyz'[:d]),'unit':unit,'value_kind':'average'}
        if input:z['sampling']={'space':'piecewise_constant','time':'linear' if axis=='history' else 'constant','extrapolation':'forbid'}
        return z
    fields={'initial_alpha':desc('initial_alpha','alpha','initial','1',1,True),'initial_velocity':desc('initial_velocity','velocity','initial','m/s',d,True),'acceleration':desc('acceleration','acceleration','history','m/s2',d,True)}
    conditions=[{'role':'initial','variable':q,'operator':'assign','location':'domain','data':{'value':{'field':'initial_'+q}}} for q in ('alpha','velocity')]+[{'role':'source','variable':'acceleration','operator':'assign','location':'domain','data':{'value':{'field':'acceleration'}}},{'role':'boundary','variable':'flow','operator':'wall','location':'walls','data':{'mechanical':{'option':'no_slip'}}}]
    outputs={q:desc(q,q,'requested',unit,num) for q,unit,num in [('alpha','1',1),('pressure','Pa',1),('velocity','m/s',d)]};inp=job/'input';ref=job/'reference';inp.mkdir(exist_ok=True);ref.mkdir(exist_ok=True);gmsh(inp/'mesh.msh',x,c,b,d)
    save(inp/'problem.json',{'task':e['task'],'spatial_dimension':d,'physics':{'model':e['model'],'parameters':s['parameters']},'data_file':'input.h5','geometries':{},'meshes':{'main':{'file':'mesh.msh'}},'locations':locations,'time_axes':{'initial':'initial','history':'history','requested':'requested'},'fields':fields,'conditions':conditions,'outputs':outputs})
    with h5py.File(inp/'input.h5','w') as f:
        for k,v in arrays.items():f[k]=v
    folders={round(float(v.name),12):v for v in (job/'native').iterdir() if v.is_dir() and re.fullmatch(r'[\d.eE+-]+',v.name)};result={q:[] for q in outputs};nparent=len(m['native_volume'])
    for t in times:
        folder=folders[round(float(t),12)];assert folder.name!='0'
        for key,native,comp in [('alpha','alpha.a',1),('pressure','p_rgh',1),('velocity','U',3)]:
            value=field(folder/native,comp,nparent)[m['parent']];value=value[:,:d] if key=='velocity' else value
            if key=='pressure':value+=p['pressure_reference']-np.dot(m['volume'],value[:,0])/sum(m['volume'])
            assert np.isfinite(value).all();result[key].append(value)
    with h5py.File(ref/'reference.h5','w') as f:
        f['cells']=arrays['cells'];f['requested']=times
        for k,v in result.items():f[k]=np.array(v)
    return {'reference_sha256':digest(ref/'reference.h5'),'cells':nc,'frames':len(times),'mapping':'Native interFoam cell means assigned to child simplices; initial alpha is a pure-cell union selected by the frozen mask on native cell centres, not a supplied analytic subcell interface. g=0, sigma=0; actual acceleration through rho*a fvOptions. p_rgh is static pressure because g=0 and is shifted to specified volume mean. No accuracy or interface-reconstruction certification.'}


def run(root,e,grading):
    job=root/'cases'/e['design_id'];status=job/'status.json'
    if status.exists():return json.loads(status.read_text())
    job.mkdir(parents=True);save(job/'design.json',e);state={'design_id':e['design_id'],'status':'queued'};save(status,state);name='ch02vof-'+hashlib.sha256(e['design_id'].encode()).hexdigest()[:12]+'-'+str(time.time_ns())[-9:]
    try:
        with reservation(root,name):
            view=prepare(job,e);base=['docker','--host',SOCKET,'run','--network','none','--cpus','1','--memory','768m','--user',f'{os.getuid()}:{os.getgid()}','-e','OMP_NUM_THREADS=1','-v',f'{job.resolve()}:/work',IMAGE,'bash','-c'];prefix='source /usr/lib/openfoam/openfoam2512/etc/bashrc && cd /work/native && '
            subprocess.run(base[:-3]+['--rm']+base[-3:]+[prefix+'blockMesh > ../blockMesh.log 2>&1'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT);m=initialize(job,e,view)
            command=base[:-3]+['--name',name]+base[-3:]+[prefix+'interFoam > ../solver.log 2>&1'];save(job/'execution.json',{'producer':'unmodified OpenCFD interFoam v2512','image':IMAGE,'source':'image:applications/solvers/multiphase/interFoam','command':command,'script_sha256':digest(Path(__file__)),'start_unix':time.time(),'numerical_validation':False});state.update(status='running',container=name);save(status,state)
            with (job/'docker.log').open('w') as f:cp=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT)
            assert cp.returncode==0,f'native exit {cp.returncode}'
        state.update(package(job,e,m));save(job/'reference/grading.json',grading);state['status']='unvalidated_candidate'
    except Exception as ex:state.update(status='needs_attention',error=repr(ex),traceback=traceback.format_exc())
    state['ended_unix']=time.time();save(status,state);return state


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int,default=40);ap.add_argument('--only');args=ap.parse_args();tasks=[];freeze=json.loads((args.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text())
    for p in args.snapshot.glob('qbank/02-fluid-mechanics/*/*/author/chapter02-ten-20261020/design.json'):
        r=json.loads(p.read_text())
        if r['question'] not in ('2.5.3','2.5.4'):continue
        assert digest(p)==freeze['designs'][p.relative_to(args.snapshot).as_posix()]
        for e in r['proposed_cases']:
            if args.only and args.only not in e['design_id']:continue
            tasks.append(({**e,'task':r['task'],'model':r['model']},json.loads((p.parents[1]/'grading-template.json').read_text())))
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=min(args.workers,len(tasks))) as pool:states=list(pool.map(run,[args.root]*len(tasks),[e for e,g in tasks],[g for e,g in tasks]))
    save(args.root/'maintenance/immiscible-summary.json',states);print(json.dumps({'completed':sum(s['status']=='unvalidated_candidate' for s in states),'attention':[s for s in states if s['status']=='needs_attention']}))


if __name__=='__main__':main()
