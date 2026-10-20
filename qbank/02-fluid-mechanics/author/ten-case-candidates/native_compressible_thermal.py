"""Stock rhoCentralFoam full-energy thermal cases without external sources.

Zero bulk viscosity only. Native sigmaDotU retains viscous stress work.
Power transport uses an exact native log-polynomial representation; only
the combination of stock thermo templates requires runtime registration.
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
from native_closed_cavity import IMAGE, SOCKET, header, put, save, digest, field, native_mesh
from native_power_periodic import prepare as prepare_base, input_mesh
from native_lowmach import sample
from elmer_flow_mesh import select
from polytropic_reference import gmsh
from titan_resources import reservation


def prepare(job,e):
    s=e['detailed_spec'];p={k:v['value'] for k,v in s['parameters'].items()};assert s['analysis_kind']=='transient' and not s['sources'] and p['bulk_viscosity']==0;view=copy.deepcopy(e);v=view['detailed_spec'];v['materials']={'density':{'kind':'constant','parameters':{'density':{'value':1.,'unit':'kg/m3'}}},'viscosity':{'kind':'newtonian','parameters':{'dynamic_viscosity':{'value':p['reference_viscosity'],'unit':'Pa.s'}}}};prepare_base(job,view);save(job/'native-adapter-view.json',view);n=job/'native';end=p['time_end'];assert p['time_start']==0;cp=p['heat_capacity_ratio']*p['specific_gas_constant']/(p['heat_capacity_ratio']-1)
    if p['viscosity_exponent']==0 and p['conductivity_exponent']==0:
        transport='const';coeff=f'mu {p["reference_viscosity"]}; Pr {cp*p["reference_viscosity"]/p["reference_conductivity"]};'
    else:
        transport='logPolynomial';coeff='';record={}
        for key,ref,expo in [('mu','reference_viscosity','viscosity_exponent'),('kappa','reference_conductivity','conductivity_exponent')]:
            values=[float(np.log(p[ref])-p[expo]*np.log(p['reference_temperature'])),p[expo],0,0,0,0,0,0];coeff+=key+'LogCoeffs<8> ('+' '.join(map(str,values))+');'+chr(10);record[key]=values
        save(job/'transport-mapping.json',{'native_model':'logPolynomial','coefficients':record,'identity':'ln(property)=ln(reference)-exponent*ln(Tref)+exponent*ln(T); no tabulation or fitted law','registration_only':True})
    put(n/'constant/thermophysicalProperties',header('dictionary','thermophysicalProperties')+f'thermoType {{ type hePsiThermo; mixture pureMixture; transport {transport}; thermo hConst; equationOfState perfectGas; specie specie; energy sensibleInternalEnergy; }} mixture {{ specie {{ molWeight {8314.46261815324/p["specific_gas_constant"]:.17g}; }} thermodynamics {{ Cp {cp:.17g}; Hf 0; }} transport {{ {coeff} }} }}\n');(n/'constant/transportProperties').unlink()
    put(n/'system/fvSchemes',header('dictionary','fvSchemes')+'fluxScheme Kurganov; ddtSchemes { default Euler; } gradSchemes { default Gauss linear; } divSchemes { default none; div(tauMC) Gauss linear; } laplacianSchemes { default Gauss linear corrected; } interpolationSchemes { default linear; reconstruct(rho) vanLeer; reconstruct(U) vanLeerV; reconstruct(T) vanLeer; } snGradSchemes { default corrected; }\n')
    put(n/'system/fvSolution',header('dictionary','fvSolution')+'solvers { "(rho|rhoU|rhoE)" { solver diagonal; } U { solver smoothSolver; smoother GaussSeidel; tolerance 1e-10; relTol 0; } h { $U; } e { $U; } }\n')
    put(n/'system/controlDict',header('dictionary','controlDict')+('libs ("/producer/libcaeojNativeThermo.so");\n' if transport=='logPolynomial' else '')+f'application rhoCentralFoam; startFrom startTime; startTime 0; stopAt endTime; endTime {end}; deltaT {end/100000}; adjustTimeStep yes; maxCo 0.3; maxDeltaT {end/1000}; writeControl adjustableRunTime; writeInterval {end/1000}; purgeWrite 0; writeFormat ascii; writePrecision 16; writeCompression off; timeFormat general; timePrecision 12; runTimeModifiable false;\n');return view


def initialize(job,e,view):
    s=e['detailed_spec'];d=e['spatial_dimension'];p={k:v['value'] for k,v in s['parameters'].items()};n=job/'native';m=input_mesh(job,view);xx,conn,patches,volume=native_mesh(n,d);x=xx[:,:d];end=p['time_end'];hist=np.array([0,.1*end,.4*end,.6*end,end]);T0=s['initial']['temperature']['expression'];rho0=s['initial']['density']['expression'];assert T0==p['reference_temperature'] and rho0==1. and s['initial']['velocity']['expression']==[0.]*d
    tbc=[];pbc=[]
    for name,faces in patches.items():
        centres=x[np.array(faces)-1].mean(axis=1);group=np.full(len(centres),-1,dtype=int);fallback=None
        for i,bc in enumerate(s['thermal_partition']):
            take=select(s,bc['selection'],centres)
            if take is None:fallback=i
            else:group[take]=i
        if fallback is not None:group[group<0]=fallback
        assert np.all(group>=0) and len(np.unique(group))==1,'native patch crosses thermal partition';bc=s['thermal_partition'][group[0]];a=np.array([sample(bc['value']['expression'],centres,t,s) for t in hist]);assert np.allclose(a,a[:,:1]),'spatially varying thermal patch needs mapped native input'
        values=a[:,0]
        if bc['operator']=='temperature':body='type uniformFixedValue; uniformValue table ('+' '.join(f'({t:.17g} {v:.17g})' for t,v in zip(hist,values))+f'); value uniform {T0};'
        else:
            assert bc['operator']=='outward_heat_flux'
            if np.all(values==0):body='type zeroGradient;'
            else:
                assert p['conductivity_exponent']==0,'nonlinear conductivity heat-flux BC needs native coupled flux implementation';gradient=-values/p['reference_conductivity'];body='type uniformFixedGradient; uniformGradient table ('+' '.join(f'({t:.17g} {v:.17g})' for t,v in zip(hist,gradient))+f'); value uniform {T0};'
        tbc.append(name+' { '+body+' }');pbc.append(name+' { type zeroGradient; }')
    if d==2:tbc+=['front { type empty; }','back { type empty; }'];pbc+=['front { type empty; }','back { type empty; }']
    put(n/'0/T',header('volScalarField','T')+f'dimensions [0 0 0 1 0 0 0]; internalField uniform {T0}; boundaryField {{ '+'\n'.join(tbc)+' }\n');put(n/'0/p',header('volScalarField','p')+f'dimensions [1 -1 -2 0 0 0 0]; internalField uniform {rho0*p["specific_gas_constant"]*T0}; boundaryField {{ '+'\n'.join(pbc)+' }\n');return m


def package(job,e,m):
    s=e['detailed_spec'];d=e['spatial_dimension'];x=m['x'];c=m['c'];b=m['b'];nc=len(c);mid=x[b].mean(axis=1);end=s['time_interval_s'][1];hist=np.array([0,.1*end,.4*end,.6*end,end]);arrays={'cells':np.arange(1,nc+1,dtype=np.int64),'initial':np.array([0.]),'history':hist,'requested':np.array(s['output_times_s'])};locations={'domain':{'kind':'mesh','mesh':'main','entity':'element','dimension':d,'ids':'cells'}};fields={};conditions=[]
    def descriptor(key,q,where,axis,unit,num,input=False):
        z={'array':key,'quantity':q,'location':where,'time_axis':axis,'dtype':'float64','kind':'scalar' if num==1 else 'vector','component_shape':[num],'components':['value'] if num==1 else list('xyz'[:d]),'unit':unit,'value_kind':'average'}
        if input:z['sampling']={'space':'piecewise_constant','time':'linear' if axis=='history' else 'constant','extrapolation':'forbid'}
        return z
    def add(key,q,where,axis,unit,v,role,op,var):
        v=np.asarray(v,dtype=float);v=v[...,None] if v.ndim==2 else v;arrays[key]=v;fields[key]=descriptor(key,q,where,axis,unit,v.shape[-1],True);conditions.append({'role':role,'variable':var,'operator':op,'location':where,'data':{'value':{'field':key}}})
    for q,unit in [('velocity','m/s'),('density','kg/m3'),('temperature','K')]:add('initial_'+q,q,'domain','initial',unit,[sample(s['initial'][q]['expression'],x[c].mean(axis=1),0,s)],'initial','assign',q)
    for label,records in [('mechanical',s['boundaries']),('thermal',s['thermal_partition'])]:
        group=np.zeros(len(mid),dtype=int)
        for i,bc in enumerate(records):
            take=select(s,bc['selection'],mid)
            if take is not None:group[take]=i
        for i,bc in enumerate(records):
            ids=np.flatnonzero(group==i)
            if not len(ids):continue
            key=label+str(i);arrays[key]=(nc+ids+1).astype(np.int64);locations[key]={'kind':'mesh','mesh':'main','entity':'element','dimension':d-1,'ids':key};v=bc['data']['velocity'] if label=='mechanical' else bc['value'];q='velocity' if label=='mechanical' else 'temperature' if bc['operator']=='temperature' else 'heat_flux';add(key+'value',q,key,'history',v['unit'],[sample(v['expression'],mid[ids],t,s) for t in hist],'boundary',bc['operator'],'velocity' if label=='mechanical' else 'temperature')
    outputs={q:descriptor(q,q,'domain','requested',unit,num) for q,unit,num in [('density','kg/m3',1),('velocity','m/s',d),('temperature','K',1),('pressure','Pa',1)]};inp=job/'input';ref=job/'reference';inp.mkdir(exist_ok=True);ref.mkdir(exist_ok=True);gmsh(inp/'mesh.msh',x,c,b,d);save(inp/'problem.json',{'task':e['task'],'spatial_dimension':d,'physics':{'model':e['model'],'parameters':s['parameters']},'data_file':'input.h5','geometries':{},'meshes':{'main':{'file':'mesh.msh'}},'locations':locations,'time_axes':{'initial':'initial','history':'history','requested':'requested'},'fields':fields,'conditions':conditions,'outputs':outputs})
    with h5py.File(inp/'input.h5','w') as f:
        for k,v in arrays.items():f[k]=v
    folders={round(float(p.name),12):p for p in (job/'native').iterdir() if p.is_dir() and re.fullmatch(r'[\d.eE+-]+',p.name)};result={q:[] for q in outputs};nparent=len(m['native_volume'])
    for t in s['output_times_s']:
        folder=folders[round(t,12)];assert folder.name!='0'
        for q,name,num in [('density','rho',1),('velocity','U',3),('temperature','T',1),('pressure','p',1)]:
            value=field(folder/name,num,nparent)[m['parent']];value=value[:,:d] if q=='velocity' else value;assert np.isfinite(value).all();result[q].append(value)
    with h5py.File(ref/'reference.h5','w') as f:
        f['cells']=arrays['cells'];f['requested']=arrays['requested']
        for k,v in result.items():f[k]=v
    return {'reference_sha256':digest(ref/'reference.h5'),'cells':nc,'frames':len(arrays['requested']),'mapping':'Native rhoCentralFoam perfect-gas full total energy, sigmaDotU stress work and conductive diffusion; zero bulk viscosity and no external sources. Adaptive acoustic time step with uniform physical write schedule. Native FV cell means assigned to conforming child simplices; absolute pressure retained. Power laws, if present, use stock logPolynomialTransport with coefficients exactly representing the given powers; only native type registration is added. No numerical validation.'}


def run(root,e,g):
    job=root/'cases'/e['design_id'];status=job/'status.json'
    if status.exists():return json.loads(status.read_text())
    job.mkdir(parents=True);save(job/'design.json',e);state={'design_id':e['design_id'],'status':'queued'};save(status,state);name='ch02thermal-'+hashlib.sha256(e['design_id'].encode()).hexdigest()[:12]+'-'+str(time.time_ns())[-9:]
    try:
        p=e['detailed_spec']['parameters'];needs_library=p['viscosity_exponent']['value']!=0 or p['conductivity_exponent']['value']!=0;library=None;library_sha=None
        if needs_library:
            from titan_resources import identity
            deadline=time.monotonic()+24*3600;build=root/'maintenance/native-thermo-registration'
            while time.monotonic()<deadline:
                bs=json.loads((build/'status.json').read_text())
                if bs['stage']=='built':library=Path(bs['library']);library_sha=bs['library_sha256'];assert digest(library)==library_sha;break
                owner=json.loads((root/'maintenance/native-thermo-build-controller.json').read_text());assert identity(owner['pid'])==str(owner['starttime']),'native registration build failed';time.sleep(30)
            else:raise RuntimeError('24h bounded native registration wait expired')
        with reservation(root,name):
            view=prepare(job,e);base=['docker','--host',SOCKET,'run','--network','none','--cpus','1','--memory','768m','--user',f'{os.getuid()}:{os.getgid()}','-e','OMP_NUM_THREADS=1','-v',f'{job.resolve()}:/work']+(['-v',f'{library.parent.resolve()}:/producer:ro'] if library else [])+[IMAGE,'bash','-c'];prefix='source /usr/lib/openfoam/openfoam2512/etc/bashrc && cd /work/native && '
            subprocess.run(base[:-3]+['--rm']+base[-3:]+[prefix+'blockMesh > ../blockMesh.log 2>&1'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT);m=initialize(job,e,view);cmd=base[:-3]+['--name',name]+base[-3:]+[prefix+'rhoCentralFoam > ../solver.log 2>&1'];save(job/'execution.json',{'producer':'unmodified OpenCFD rhoCentralFoam v2512 full-energy viscous branch','image':IMAGE,'source':'image:applications/solvers/compressible/rhoCentralFoam/rhoCentralFoam.C','command':cmd,'script_sha256':digest(Path(__file__)),'start_unix':time.time(),'native_type_registration_sha256':library_sha,'native_registration_only':bool(library),'numerical_validation':False});state.update(status='running',container=name);save(status,state)
            with (job/'docker.log').open('w') as f:cp=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
            assert cp.returncode==0,f'native exit {cp.returncode}'
            state.update(package(job,e,m));save(job/'reference/grading.json',g);state['status']='unvalidated_candidate'
    except Exception as ex:state.update(status='needs_attention',error=repr(ex),traceback=traceback.format_exc())
    state['ended_unix']=time.time();save(status,state);return state


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int,default=40);ap.add_argument('--only');args=ap.parse_args();tasks=[];freeze=json.loads((args.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text())
    for p in args.snapshot.glob('qbank/02-fluid-mechanics/*/*/author/chapter02-ten-20261020/design.json'):
        r=json.loads(p.read_text())
        if r['question'] not in ('2.2.10','2.2.12'):continue
        assert digest(p)==freeze['designs'][p.relative_to(args.snapshot).as_posix()]
        for e in r['proposed_cases']:
            s=e['detailed_spec']
            if s['sources'] or s['parameters']['bulk_viscosity']['value']!=0:continue
            if args.only and args.only not in e['design_id']:continue
            tasks.append(({**e,'task':r['task'],'model':r['model']},json.loads((p.parents[1]/'grading-template.json').read_text())))
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=min(args.workers,len(tasks))) as pool:states=list(pool.map(run,[args.root]*len(tasks),[e for e,g in tasks],[g for e,g in tasks]))
    save(args.root/'maintenance/compressible-thermal-summary.json',states);print(json.dumps({'completed':sum(s['status']=='unvalidated_candidate' for s in states),'attention':[s for s in states if s['status']=='needs_attention']}))


if __name__=='__main__':main()
