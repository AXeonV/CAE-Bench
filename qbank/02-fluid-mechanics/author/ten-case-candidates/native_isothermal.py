"""Stock rhoSimple/rhoPimple with native all-cell fixedTemperatureConstraint.

Closed geometries, zero bulk viscosity. PerfectGas or affine PerfectFluid
EOS. The auxiliary energy equation is constrained to the specified T and
is not used as an adiabatic approximation to the isothermal problem.
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
import numpy as np
from native_closed_cavity import IMAGE, SOCKET, header, put, save, digest, vector, field
from native_power_periodic import prepare as prepare_base, input_mesh, convert
from native_elmer_incompressible import evaluate
from titan_resources import reservation


def acceleration(s,d):
    a=s['sources'].get('acceleration',{'expression':[0.]*d})['expression']
    if isinstance(a,str):
        assert a=='(.05*R,-.1*R[,0])';a=['.05*R','-.1*R']+[0.]*(d-2)
    return a


def prepare(job,e):
    s=e['detailed_spec'];d=e['spatial_dimension'];a=s['analysis'];T=a['temperature_K'];steady=s['analysis_kind']=='steady';end=(s['time_interval_s'] or [0,1])[1];density=s['materials']['density'];dp={k:v['value'] for k,v in density['parameters'].items()};vp={k:v['value'] for k,v in s['materials']['viscosity']['parameters'].items()};assert vp['bulk_viscosity']==0 and a['pressure_representation']=='absolute';assert all(b['operator'] in ('moving_wall','no_slip','slip','symmetry') for b in s['boundaries']);view=copy.deepcopy(e);v=view['detailed_spec'];v['sources']={};v['materials']={'density':{'kind':'constant','parameters':{'density':{'value':1.,'unit':'kg/m3'}}},'viscosity':{'kind':'newtonian','parameters':{'dynamic_viscosity':{'value':vp['dynamic_viscosity'],'unit':'Pa.s'}}}};prepare_base(job,view);n=job/'native';save(job/'native-adapter-view.json',view)
    if density['kind']=='isothermal_ideal_gas':R=dp['specific_gas_constant'];offset=0.;eos='perfectGas';thermo='hePsiThermo';equation=''
    else:
        assert density['kind']=='linear_barotropic';R=dp['sound_speed']**2/T;offset=dp['reference_density']-dp['reference_pressure']/dp['sound_speed']**2;eos='perfectFluid';thermo='heRhoThermo';equation=f'equationOfState {{ R {R:.17g}; rho0 {offset:.17g}; }}'
    target=a['mean_density_kg_m3'] if steady else s['initial']['density']['expression'];assert isinstance(target,(int,float)) and target>0
    # Stock rhoSimple closedVolume enforces integral(psi*p)=initialMass.
    # For an affine EOS rho=offset+psi*p, choose its numerical initialMass
    # as targetMass-offset*V. There is no prescribed steady initial state.
    proxy=target-offset if steady else target;pinit=(proxy-offset)*R*T;assert proxy>0 and pinit>0
    save(job/'native-EOS-mapping.json',{'EOS':eos,'psi_per_Pa':1/(R*T),'density_offset_kg_m3':offset,'target_mean_density_kg_m3':target if steady else None,'numerical_initial_density_kg_m3':proxy,'initial_absolute_pressure_Pa':pinit,'native_closed_volume_mass_proxy':'initialMass=(targetMean-offset)*V; native correction imposes mean(psi*p)=targetMean-offset' if steady else 'physical initial density retained; native transient continuity equation','auxiliary_thermo':'Cp=1004.5 and Pr=1 do not define additional physical inputs: all cell temperatures are constrained to the supplied fixed T.'})
    put(n/'constant/thermophysicalProperties',header('dictionary','thermophysicalProperties')+f'thermoType {{ type {thermo}; mixture pureMixture; transport const; thermo hConst; equationOfState {eos}; specie specie; energy sensibleEnthalpy; }} mixture {{ specie {{ molWeight {8314.46261815324/R:.17g}; }} {equation} thermodynamics {{ Cp 1004.5; Hf 0; }} transport {{ mu {vp["dynamic_viscosity"]}; Pr 1; }} }}\n');(n/'constant/transportProperties').unlink()
    patches=re.findall(r'(?m)^(\w+) \{ type (\w+);',(n/'system/blockMeshDict').read_text());pbc=[];tbc=[];abc=[]
    for name,typ in patches:
        empty=typ=='empty';pbc.append(name+' { type '+('empty' if empty else 'zeroGradient')+'; }');tbc.append(name+' { type empty; }' if empty else name+f' {{ type fixedValue; value uniform {T}; }}');abc.append(name+' { type '+('empty' if empty else 'zeroGradient')+'; }')
    put(n/'0/p',header('volScalarField','p')+f'dimensions [1 -1 -2 0 0 0 0]; internalField uniform {pinit:.17g}; boundaryField {{ '+'\n'.join(pbc)+' }\n');put(n/'0/T',header('volScalarField','T')+f'dimensions [0 0 0 1 0 0 0]; internalField uniform {T}; boundaryField {{ '+'\n'.join(tbc)+' }\n')
    app='rhoSimpleFoam' if steady else 'rhoPimpleFoam';functions='gradU { type grad; libs (fieldFunctionObjects); field U; result gradU; executeControl writeTime; writeControl writeTime; }';options=f'fixedT {{ type fixedTemperatureConstraint; selectionMode all; mode uniform; temperature constant {T}; }}\n'
    if s['sources']:
        value=evaluate(acceleration(s,d),np.zeros((1,d)),end,s)[0];value=np.pad(value,(0,3-d));put(n/'0/bodyAcceleration',header('volVectorField','bodyAcceleration')+'dimensions [0 1 -2 0 0 0 0]; internalField uniform '+vector(value)+'; boundaryField { '+'\n'.join(abc)+' }\n');scale='1' if steady else f'min(max(time()/{.1*end},0),1)';options+=f'acceleration {{ type vectorSemiImplicitSource; selectionMode all; volumeMode specific; sources {{ U {{ explicit {{ type exprField; expression "bodyAcceleration*(rho*({scale}))"; }} implicit none; }} }} }}\n';functions+=' readSource { type readFields; libs (fieldFunctionObjects); fields (bodyAcceleration); readOnStart true; }'
    put(n/'constant/fvOptions',header('dictionary','fvOptions')+options);put(n/'system/controlDict',header('dictionary','controlDict')+f'application {app}; startFrom startTime; startTime 0; stopAt endTime; endTime {10000 if steady else end}; deltaT {1 if steady else end/1000}; writeControl timeStep; writeInterval {10000 if steady else 1}; purgeWrite 0; writeFormat ascii; writePrecision 16; writeCompression off; timeFormat general; timePrecision 12; runTimeModifiable false; functions {{ {functions} }}\n')
    put(n/'system/fvSchemes',header('dictionary','fvSchemes')+'ddtSchemes { default '+('steadyState' if steady else 'Euler')+'; } gradSchemes { default Gauss linear; } divSchemes { default none; div(phi,U) Gauss upwind; div(phi,h) Gauss upwind; div(phi,e) Gauss upwind; div(phi,K) Gauss upwind; div(phiv,p) Gauss linear; div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear; } laplacianSchemes { default Gauss linear corrected; } interpolationSchemes { default linear; } snGradSchemes { default corrected; } fluxRequired { default no; p; }\n')
    solvers='solvers { p { solver PCG; preconditioner DIC; tolerance 1e-10; relTol 0; } pFinal { $p; } U { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-10; relTol 0; } UFinal { $U; } h { $U; } hFinal { $h; } rho { solver diagonal; } rhoFinal { $rho; } }\n'
    solvers+=f'SIMPLE {{ nNonOrthogonalCorrectors 0; pRefCell 0; pRefValue {pinit:.17g}; residualControl {{ U 1e-9; }} }} relaxationFactors {{ fields {{ p 0.2; rho 0.5; }} equations {{ U 0.3; h 1; }} }}\n' if steady else 'PIMPLE { nOuterCorrectors 3; nCorrectors 3; nNonOrthogonalCorrectors 0; transonic false; } relaxationFactors { equations { U 1; h 1; } }\n';put(n/'system/fvSolution',header('dictionary','fvSolution')+solvers);return app,view


def run(root,e,g):
    job=root/'cases'/e['design_id'];status=job/'status.json'
    if status.exists():return json.loads(status.read_text())
    job.mkdir(parents=True);save(job/'design.json',e);state={'design_id':e['design_id'],'status':'queued'};save(status,state);name='ch02iso-'+hashlib.sha256(e['design_id'].encode()).hexdigest()[:12]+'-'+str(time.time_ns())[-9:]
    try:
        with reservation(root,name):
            app,view=prepare(job,e);base=['docker','--host',SOCKET,'run','--network','none','--cpus','1','--memory','768m','--user',f'{os.getuid()}:{os.getgid()}','-e','OMP_NUM_THREADS=1','-v',f'{job.resolve()}:/work',IMAGE,'bash','-c'];prefix='source /usr/lib/openfoam/openfoam2512/etc/bashrc && cd /work/native && '
            subprocess.run(base[:-3]+['--rm']+base[-3:]+[prefix+'blockMesh > ../blockMesh.log 2>&1'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT);m=input_mesh(job,view);cmd=base[:-3]+['--name',name]+base[-3:]+[prefix+app+' > ../solver.log 2>&1'];save(job/'execution.json',{'producer':f'unmodified OpenCFD {app} with native fixedTemperatureConstraint','image':IMAGE,'source':'image:fvOptions/constraints/derived/fixedTemperatureConstraint and specie/equationOfState/{perfectGas,perfectFluid}','command':cmd,'script_sha256':digest(Path(__file__)),'conversion_script_sha256':digest(Path(__file__).with_name('native_power_periodic.py')),'start_unix':time.time(),'steady_stop':'Native momentum residual only; closedVolume shifts absolute pressure after the pressure solve, making its normalized initial residual unsuitable for this global stopping criterion. Per-solve pressure tolerance remains 1e-10.','numerical_validation':False});state.update(status='running',container=name);save(status,state)
            with (job/'docker.log').open('w') as f:cp=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
            assert cp.returncode==0,f'native exit {cp.returncode}'
            if e['detailed_spec']['analysis_kind']=='steady' and 'SIMPLE solution converged' not in (job/'solver.log').read_text():state['status']='native_iteration_limit'
            else:
                folders={float(p.name):p for p in (job/'native').iterdir() if p.is_dir() and re.fullmatch(r'[\d.eE+-]+',p.name)};T=field(folders[max(folders)]/'T',1,len(m['native_volume']));deviation=float(np.max(np.abs(T-e['detailed_spec']['analysis']['temperature_K'])));assert deviation<1e-8,'native constraint did not preserve fixed temperature';pe=copy.deepcopy(e)
                if pe['detailed_spec']['sources']:pe['detailed_spec']['sources']['acceleration']['expression']=acceleration(pe['detailed_spec'],e['spatial_dimension'])
                save(job/'assembly-design.json',pe);state.update(convert(job,pe,m),fixed_temperature_max_deviation_K=deviation);save(job/'reference/grading.json',g);state['status']='unvalidated_candidate'
    except Exception as ex:state.update(status='needs_attention',error=repr(ex),traceback=traceback.format_exc())
    state['ended_unix']=time.time();save(status,state);return state


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int,default=40);ap.add_argument('--only');args=ap.parse_args();tasks=[];freeze=json.loads((args.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text())
    for p in args.snapshot.glob('qbank/02-fluid-mechanics/*/*/author/chapter02-ten-20261020/design.json'):
        r=json.loads(p.read_text())
        if r['family']!='isothermal_compressible':continue
        assert digest(p)==freeze['designs'][p.relative_to(args.snapshot).as_posix()]
        for i,e in enumerate(r['proposed_cases']):
            if i not in (0,1,2,5,6) or (args.only and args.only not in e['design_id']):continue
            tasks.append(({**e,'task':r['task']},json.loads((p.parents[1]/'grading-template.json').read_text())))
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=min(args.workers,len(tasks))) as pool:states=list(pool.map(run,[args.root]*len(tasks),[e for e,g in tasks],[g for e,g in tasks]))
    save(args.root/'maintenance/isothermal-summary.json',states);print(json.dumps({'completed':sum(s['status']=='unvalidated_candidate' for s in states),'attention':[s for s in states if s['status']=='needs_attention']}))


if __name__=='__main__':main()
