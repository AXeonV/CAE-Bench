"""Two frozen inviscid variable-acceleration cases with native exprField sources.

Stock rhoPimpleFoam supplies inviscid momentum and total-energy balance.
Stock SemiImplicitSource evaluates rho*a and rho*(U dot a) from input samples.
No compiled source code, new physical module, or custom PDE solver is used.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import time
from pathlib import Path
import h5py
import numpy as np
from native_closed_cavity import header,put,save,digest
from native_euler_transient import run as euler_run
from polytropic_reference import descriptor
from native_lowmach import sample
from titan_resources import reservation


def configure(job,s):
    assert set(s['sources'])=={'acceleration'}
    d=s['geometry']['dimension'];end=s['time_interval_s'][1]
    assert s['sources']['acceleration']['expression']==[0,'-10*P']+([0] if d==3 else [])
    times=np.array([0.,.1*end,.4*end,.6*end,end])
    values=np.array([sample(s['sources']['acceleration']['expression'],np.zeros((1,d)),float(t),s)[0] for t in times])
    problem=json.loads((job/'input/problem.json').read_text())
    with h5py.File(job/'input/input.h5','a') as f:
        count=len(f['cells']);f['source_history']=times;f['acceleration']=np.broadcast_to(values[:,None,:],(len(times),count,d))
    field=descriptor('acceleration',d,'m/s2','domain');field['time_axis']='source_history';field['sampling']['time']='linear';problem['fields']['acceleration']=field;problem['time_axes']['source_history']='source_history';problem['conditions'].append({'role':'source','variable':'acceleration','operator':'assign','location':'domain','data':{'value':{'field':'acceleration'}}});save(job/'input/problem.json',problem)
    # Piecewise-linear interpolation of the actual public input history.
    y=values[:,1];terms=[str(float(y[0]))]
    for i in range(len(times)-1):
        delta=float(y[i+1]-y[i])
        if delta:terms.append(f'({delta:.17g}*min(max((time()-{times[i]:.17g})/{times[i+1]-times[i]:.17g},0),1))')
    ay='('+'+'.join(terms)+')';a='vector(0,'+ay+',0)'
    n=job/'native'
    sources='force { type vectorSemiImplicitSource; selectionMode all; volumeMode specific; sources { U { explicit { type exprField; expression "rho*'+a+'"; } implicit none; } } }\n'
    sources+='forceWork { type scalarSemiImplicitSource; selectionMode all; volumeMode specific; sources { e { explicit { type exprField; expression "rho*(U & '+a+')"; } implicit none; } } }\n'
    put(n/'constant/fvOptions',header('dictionary','fvOptions')+sources)
    put(n/'system/fvSchemes',header('dictionary','fvSchemes')+'ddtSchemes { default Euler; } gradSchemes { default Gauss linear; } divSchemes { default none; div(phi,U) Gauss upwind; div(phi,h) Gauss upwind; div(phi,e) Gauss upwind; div(phi,K) Gauss upwind; div(phiv,p) Gauss linear; div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear; } laplacianSchemes { default Gauss linear corrected; } interpolationSchemes { default linear; } snGradSchemes { default corrected; } fluxRequired { default no; p; }\n')
    solvers='solvers { p { solver PCG; preconditioner DIC; tolerance 1e-10; relTol 0; } pFinal { $p; relTol 0; } rho { solver diagonal; } rhoFinal { solver diagonal; } "(U|e|h|K)" { solver PBiCGStab; preconditioner DILU; tolerance 1e-10; relTol 0; } "(U|e|h|K)Final" { solver PBiCGStab; preconditioner DILU; tolerance 1e-10; relTol 0; } } PIMPLE { nOuterCorrectors 3; nCorrectors 3; nNonOrthogonalCorrectors 0; transonic false; } relaxationFactors { equations { U 1; e 1; h 1; } }\n'
    put(n/'system/fvSolution',header('dictionary','fvSolution')+solvers)
    put(n/'system/controlDict',header('dictionary','controlDict')+f'application rhoPimpleFoam; startFrom startTime; startTime 0; stopAt endTime; endTime {end}; deltaT {end/1000}; adjustTimeStep no; writeControl timeStep; writeInterval 1; purgeWrite 0; writeFormat ascii; writePrecision 16; writeCompression off; timeFormat general; timePrecision 12; runTimeModifiable false;\n')
    save(job/'gravity-source-adapter.json',{'producer':'Native rhoPimpleFoam, mu=0 and heat conductivity=0; no missing viscous work since inviscid. Native exprField SemiImplicitSource supplies both rho*a and rho*(U dot a).','history_times':times.tolist(),'history_values':values.tolist(),'interpolation':'Exact piecewise-linear interpolation of supplied spatially uniform P0 acceleration. Native expression evaluates the current rho and U; no codedSource or compiled physical module.','adapter_sha256':digest(Path(__file__)),'numerical_validation':False})
    return 'rhoPimpleFoam'


def run(root,r,e,g):
    name='ch02euler-'+hashlib.sha256(e['design_id'].encode()).hexdigest()[:12]+'-'+str(time.time_ns())[-9:]
    with reservation(root,name):return euler_run(root,r,e,g,source_adapter=configure,native_name=name)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int,default=2);args=ap.parse_args();tasks=[]
    frozen=json.loads((args.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text())
    for p in args.snapshot.glob('qbank/02-fluid-mechanics/*/inviscid-compressible-transient-*/author/chapter02-ten-20261020/design.json'):
        assert digest(p)==frozen['designs'][p.relative_to(args.snapshot).as_posix()];r=json.loads(p.read_text());g=json.loads((p.parents[1]/'grading-template.json').read_text())
        for e in r['proposed_cases']:
            if e['detailed_spec']['sources']:tasks.append((r,e,g))
    assert len(tasks)==2
    with ProcessPoolExecutor(max_workers=min(2,args.workers)) as pool:states=list(pool.map(run,[args.root]*2,[r for r,e,g in tasks],[e for r,e,g in tasks],[g for r,e,g in tasks]))
    save(args.root/'maintenance/euler-gravity-summary.json',states)


if __name__=='__main__':main()
