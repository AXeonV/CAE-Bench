"""Stock rhoSimpleFoam + full-R LRR + native temperature constraint.

2.3.5 parameter schema stays public. A private 2.1 view reuses native mesh/EOS
configuration; it is never shipped as the public problem. Zero bulk only.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
import traceback
import h5py
import numpy as np
import native_isothermal as iso
import native_turbulence as turb
from native_closed_cavity import IMAGE, SOCKET, header, put, save, digest, field
from titan_resources import reservation


def prepare(job, e, pressure_retry=False):
    view = copy.deepcopy(e); s = view['detailed_spec']; p = {k:v['value'] for k,v in s['parameters'].items()}
    assert p['bulk_viscosity'] == 0 and s['analysis_kind'] == 'steady'
    s['analysis'] = {'temperature_K':p['reference_temperature'], 'pressure_representation':'absolute', 'mean_density_kg_m3':p['mean_density']}
    s['materials'] = {'density':{'kind':'isothermal_ideal_gas','parameters':{'specific_gas_constant':{'value':p['specific_gas_constant'],'unit':'J/(kg.K)'}}}, 'viscosity':{'kind':'newtonian','parameters':{'dynamic_viscosity':{'value':p['reference_viscosity'],'unit':'Pa.s'},'bulk_viscosity':{'value':0.,'unit':'Pa.s'}}}}
    s['sources'] = {}  # Actual source is mapped from public P0 inputs after mesh creation.
    app, mesh_view = iso.prepare(job, view); n = job/'native'
    put(n/'constant/turbulenceProperties', header('dictionary','turbulenceProperties')+'simulationType RAS; RAS { RASModel LRR; turbulence on; printCoeffs on; }\n')
    schemes=(n/'system/fvSchemes').read_text().replace('default none;', 'default Gauss linear;').replace('div(phi,U) Gauss upwind;', 'div(phi,U) Gauss upwind; div(phi,R) Gauss upwind; div(phi,epsilon) Gauss upwind; div(devRhoReff) Gauss linear;')+'\nwallDist { method meshWave; }\n'
    put(n/'system/fvSchemes',schemes)
    solution=(n/'system/fvSolution').read_text().replace('solvers {','solvers { R { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-9; relTol 0; } epsilon { $R; }',1).replace('residualControl { U 1e-9; }','residualControl { U 1e-8; R 1e-8; epsilon 1e-8; }').replace('U 0.3; h 1;', 'U 0.3; R 0.3; epsilon 0.3; h 1;')
    if pressure_retry:
        solution=solution.replace('solver PCG; preconditioner DIC; tolerance 1e-10; relTol 0;', 'solver GAMG; smoother DICGaussSeidel; tolerance 1e-10; relTol 0; maxIter 1000; nCellsInCoarsestLevel 10; agglomerator faceAreaPair; mergeLevels 1;')
        solution=solution.replace('p 0.2; rho 0.5;', 'p 0.05; rho 0.1;').replace('U 0.3; R 0.3; epsilon 0.3;', 'U 0.1; R 0.1; epsilon 0.1;')
        control=(n/'system/controlDict').read_text().replace('functions {', 'functions { diagnosticRanges { type fieldMinMax; libs (fieldFunctionObjects); fields (p rho U R epsilon T); mode component; log true; writeControl timeStep; writeInterval 1; }', 1)
        put(n/'system/controlDict',control)
        save(job/'retry-configuration.json', {'variant':'one bounded conservative-relaxation and GAMG attempt', 'original_failure':'Continuity and epsilon diverge before pressure PCG FPE at native iteration 15', 'physical_changes':False, 'convergence_threshold_changes':False, 'iteration_limit_changes':False, 'pressure_tolerance':1e-10, 'relaxation':{'p':.05,'rho':.1,'U':.1,'R':.1,'epsilon':.1}, 'pressure_solver':'native GAMG/DICGaussSeidel', 'script_sha256':digest(Path(__file__)), 'numerical_validation':False})
    put(n/'system/fvSolution',solution)
    return app, mesh_view


def initialize(job,e,view):
    m = turb.initialize(job,e,view,'LRR'); n=job/'native'
    # initialize() supplies exact native cell acceleration averages but its
    # incompressible source lacks rho. Replace that configuration explicitly.
    options=f'fixedT {{ type fixedTemperatureConstraint; selectionMode all; mode uniform; temperature constant {e["detailed_spec"]["parameters"]["reference_temperature"]["value"]}; }}\n'
    if e['detailed_spec']['sources']:
        options+='acceleration { type vectorSemiImplicitSource; selectionMode all; volumeMode specific; sources { U { explicit { type exprField; expression "bodyAcceleration*rho"; } implicit none; } } }\n'
        control=(n/'system/controlDict').read_text().replace('functions {','functions { readSource { type readFields; libs (fieldFunctionObjects); fields (bodyAcceleration); readOnStart true; }',1);put(n/'system/controlDict',control)
    put(n/'constant/fvOptions',header('dictionary','fvOptions')+options)
    turb.scalar_file(n,'alphat','[1 -1 -1 0 0 0 0]',np.zeros(len(m['native_volume'])),'zeroGradient')
    return m


def convert(job,e,m):
    assembly=copy.deepcopy(e); assembly['detailed_spec']['parameters']['density']={'value':1.,'unit':'kg/m3'}
    result=turb.convert(job,assembly,m,'LRR')
    folders={float(p.name):p for p in (job/'native').iterdir() if p.is_dir() and re.fullmatch(r'[\d.eE+-]+',p.name)};folder=folders[max(folders)];nc=len(m['native_volume']);p=field(folder/'p',1,nc);T=field(folder/'T',1,nc);params=e['detailed_spec']['parameters'];Tref=params['reference_temperature']['value'];R=params['specific_gas_constant']['value'];assert np.max(np.abs(T-Tref))<1e-8 and np.min(p)>0
    pressure=p[m['parent']];density=pressure/(R*Tref)
    with h5py.File(job/'reference/reference.h5','r+') as f:f['pressure'][...]=pressure[None];f['density']=density[None]
    path=job/'input/problem.json';problem=json.loads(path.read_text());problem['physics']['parameters']=e['detailed_spec']['parameters'];save(path,problem)
    result.update(reference_sha256=digest(job/'reference/reference.h5'),mapping='Native rhoSimpleFoam with full-R LRR (no isotropic-pressure subtraction), perfect-gas EOS, closed-volume mass and native fixedTemperatureConstraint. Absolute static p and rho=p/(R*Tref) retained. Supplied acceleration P0 values averaged to native cells, force=rho*a. No numerical validation.')
    return result


def run(root,e,g,pressure_retry=False):
    job=root/'cases'/e['design_id'];status=job/'status.json'
    if status.exists():return json.loads(status.read_text())
    job.mkdir(parents=True);save(job/'design.json',e);state={'design_id':e['design_id'],'status':'queued'};save(status,state);name='ch02isorans-'+hashlib.sha256(e['design_id'].encode()).hexdigest()[:12]+'-'+str(time.time_ns())[-9:]
    try:
        with reservation(root,name):
            app,view=prepare(job,e,pressure_retry);common=['docker','--host',SOCKET,'run','--network','none','--cpus','1','--memory','768m','--user',f'{os.getuid()}:{os.getgid()}','-e','OMP_NUM_THREADS=1','-v',f'{job.resolve()}:/work',IMAGE,'bash','-c'];prefix='source /usr/lib/openfoam/openfoam2512/etc/bashrc && cd /work/native && '
            subprocess.run(common[:-3]+['--rm']+common[-3:]+[prefix+'blockMesh > ../blockMesh.log 2>&1'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT);m=initialize(job,e,view);command=common[:-3]+['--name',name]+common[-3:]+[prefix+app+' > ../solver.log 2>&1']
            save(job/'execution.json',{'producer':'unmodified OpenCFD rhoSimpleFoam + full-R LRR + fixedTemperatureConstraint','image':IMAGE,'source':'image:src/TurbulenceModels/turbulenceModels/{RAS/LRR,ReynoldsStress}; native perfectGas and fixedTemperatureConstraint','script_sha256':digest(Path(__file__)),'numerical_configuration_variant':'conservative-pressure-retry' if pressure_retry else 'initial', 'dependency_sha256':{p.name:digest(p) for p in [Path(iso.__file__),Path(turb.__file__)]},'command':command,'start_unix':time.time(),'numerical_validation':False});state.update(status='running',container=name);save(status,state)
            with (job/'docker.log').open('w') as log:cp=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
            assert cp.returncode==0,f'native exit {cp.returncode}'
            if 'SIMPLE solution converged' not in (job/'solver.log').read_text():state['status']='native_iteration_limit'
            else:state.update(convert(job,e,m));save(job/'reference/grading.json',g);state['status']='unvalidated_candidate'
    except Exception as ex:state.update(status='needs_attention',error=repr(ex),traceback=traceback.format_exc())
    state['ended_unix']=time.time();save(status,state);return state


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int,default=40);ap.add_argument('--only');args=ap.parse_args();freeze=json.loads((args.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text());tasks=[]
    for p in args.snapshot.glob('qbank/02-fluid-mechanics/*/isothermal-rans-3d/author/chapter02-ten-20261020/design.json'):
        assert digest(p)==freeze['designs'][p.relative_to(args.snapshot).as_posix()];r=json.loads(p.read_text())
        for e in r['proposed_cases']:
            if args.only and args.only not in e['design_id']:continue
            if e['detailed_spec']['parameters']['bulk_viscosity']['value']!=0:continue
            tasks.append(({**e,'task':r['task'],'model':r['model']},json.loads((p.parents[1]/'grading-template.json').read_text())))
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=min(args.workers,len(tasks))) as pool:states=list(pool.map(run,[args.root]*len(tasks),[e for e,g in tasks],[g for e,g in tasks]))
    save(args.root/'maintenance/isothermal-rans-summary.json',states)


if __name__=='__main__':main()
