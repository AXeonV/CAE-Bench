"""Actual local OpenFOAM1912 cross checks of the revised continuous cavities.

Existing solver pimpleFoam; fixedFluxPressure derives pressure flux from the
prescribed velocity rather than imposing an independent physical Neumann datum.
The output uses cubic reconstruction of ASCII finite-volume cell fields at
the exact same public observations; no VTK float32 conversion is used.
"""
import argparse,json,os,subprocess,time
from pathlib import Path
import numpy as np
from catalog import WORK

def foam(object,body,cls='dictionary'):
    return f'FoamFile\n{{version 2.0; format ascii; class {cls}; object {object};}}\n'+body+'\n'

def setup(case,index,N,dt):
    for name in ('0','constant','system'):(case/name).mkdir(parents=True,exist_ok=True)
    nu,T=(.01,10.) if index==12 else (.1,.5)
    steps=int(np.ceil(T/dt));dt=T/steps
    grade='((0.2 0.35 8)(0.6 0.3 1)(0.2 0.35 0.125))'
    block=f'''convertToMeters 1;
vertices ((0 0 -0.05)(1 0 -0.05)(1 1 -0.05)(0 1 -0.05)(0 0 0.05)(1 0 0.05)(1 1 0.05)(0 1 0.05));
blocks (hex (0 1 2 3 4 5 6 7) ({N} {N} 1) simpleGrading ({grade} {grade} 1));
edges ();
boundary (lid {{type wall; faces ((3 7 6 2));}} walls {{type wall; faces ((0 4 7 3)(1 2 6 5)(0 1 5 4));}} frontBack {{type empty; faces ((0 3 2 1)(4 5 6 7));}});
mergePatchPairs ();
'''
    (case/'system/blockMeshDict').write_text(foam('blockMeshDict',block))
    (case/'0/U').write_text(foam('U','''dimensions [0 1 -1 0 0 0 0]; internalField uniform (0 0 0);
boundaryField {lid {type fixedValue; value uniform (1 0 0);} walls {type fixedValue; value uniform (0 0 0);} frontBack {type empty;}}
''','volVectorField'))
    (case/'0/p').write_text(foam('p','''dimensions [0 2 -2 0 0 0 0]; internalField uniform 0;
boundaryField {lid {type fixedFluxPressure; value uniform 0;} walls {type fixedFluxPressure; value uniform 0;} frontBack {type empty;}}
''','volScalarField'))
    (case/'constant/transportProperties').write_text(foam('transportProperties',f'transportModel Newtonian; nu [0 2 -1 0 0 0 0] {nu};'))
    (case/'constant/turbulenceProperties').write_text(foam('turbulenceProperties','simulationType laminar;'))
    (case/'system/fvSchemes').write_text(foam('fvSchemes','''ddtSchemes {default backward;}
gradSchemes {default Gauss linear;} divSchemes {default none; div(phi,U) Gauss linear; div((nuEff*dev2(T(grad(U))))) Gauss linear;}
laplacianSchemes {default Gauss linear corrected;} interpolationSchemes {default linear;}
snGradSchemes {default corrected;} fluxRequired {default no; p;}
'''))
    (case/'system/fvSolution').write_text(foam('fvSolution','''solvers {
p {solver PCG; preconditioner DIC; tolerance 1e-10; relTol 0;}
pFinal {$p; relTol 0;}
U {solver smoothSolver; smoother symGaussSeidel; tolerance 1e-10; relTol 0;}
UFinal {$U; relTol 0;}
}
PIMPLE {momentumPredictor yes; nOuterCorrectors 2; nCorrectors 2; nNonOrthogonalCorrectors 0; pRefCell 0; pRefValue 0;}
'''))
    x=(np.arange(41)+.5)/41;xx,yy=np.meshgrid(x,x)
    probes='\n'.join(f'({a:.17g} {b:.17g} 0)' for a,b in zip(xx.ravel(),yy.ravel()))
    control=f'''application pimpleFoam; startFrom startTime; startTime 0; stopAt endTime; endTime {T}; deltaT {dt:.17g};
writeControl timeStep; writeInterval {steps}; purgeWrite 0; writeFormat ascii; writePrecision 17;
writeCompression off; timeFormat general; timePrecision 12; runTimeModifiable false; adjustTimeStep no;
functions {{ observations {{ type probes; libs ("libsampling.so"); fields (U p); interpolationScheme cellPoint;
executeControl timeStep; executeInterval {steps}; writeControl timeStep; writeInterval {steps}; probeLocations ({probes}); }} }}
'''
    (case/'system/controlDict').write_text(foam('controlDict',control))
    return dt,T

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--only',nargs='*',type=int);args=parser.parse_args()
    env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'}
    extra=subprocess.check_output(['bash','-lc','source /usr/share/openfoam/etc/bashrc >/dev/null 2>&1; env -0'])
    env.update(dict(entry.decode().split('=',1) for entry in extra.split(b'\0') if b'=' in entry))
    for index in (18,12):
        if args.only and index not in args.only:continue
        for N in (64,128):
            job=WORK/'independent-cavity-openfoam'/f'C{index:02}'/f'N{N}'
            record=job/'process.json'
            if record.exists() and json.loads(record.read_text()).get('returncode')==0:
                data=json.loads(record.read_text())
                if not (job/'native.npz').exists():convert(job,N,data['dt'],data['time'])
                continue
            if record.exists():
                stamp=str(int(time.time()))
                for name in ('process.json','solver.log','blockMesh.log'):
                    old=job/name
                    if old.exists():old.rename(job/(name+'.failed-'+stamp))
            dt,T=setup(job,index,N,(.0002 if index==18 else .002)*64/N)
            started=time.time()
            with (job/'blockMesh.log').open('w') as log:
                subprocess.run(['blockMesh','-case',str(job)],stdout=log,stderr=subprocess.STDOUT,env=env,check=True)
            with (job/'solver.log').open('w') as log:
                # Ubuntu's1912 binary has a sha1 stream bug when functionObjects
                # are enabled. Use unchanged solver without online functions,
                # then export actual final fields by the official VTK utility.
                p=subprocess.Popen(['pimpleFoam','-noFunctionObjects','-case',str(job)],stdout=log,stderr=subprocess.STDOUT,env=env)
                data=dict(status='running',pid=p.pid,started_unix=started,index=index,N=N,dt=dt,time=T)
                record.write_text(json.dumps(data,indent=2));rc=p.wait()
            data.update(status='finished',returncode=rc,wall_seconds=time.time()-started)
            record.write_text(json.dumps(data,indent=2));print(json.dumps(data),flush=True)
            if rc:break
            convert(job,N,dt,T)


def convert(job,N,dt,T):
    # Read original double-precision ASCII fields, avoiding foamToVTK's legacy
    # float32 point coordinates and accidental duplicate coordinate identities.
    from cylinder_openfoam import geometry,read_vector_field
    from scipy.interpolate import RectBivariateSpline
    import re
    _,_,_,centers=geometry(job/'constant/polyMesh')
    uv=read_vector_field(job/f'{T:g}/U')
    text=(job/f'{T:g}/p').read_text()
    match=re.search(r'internalField\s+nonuniform\s+List<scalar>\s+(\d+)\s*\(',text)
    if match is None:raise ValueError('Expected nonuniform pressure')
    pp=np.fromstring(text[match.end():text.index(')',match.end())],sep=' ')
    if len(pp)!=int(match[1]):raise ValueError('Wrong pressure count')
    # Polygon centroid arithmetic differs only at roundoff between rows.
    xy=np.round(centers[:,:2],12)
    sort=np.lexsort((xy[:,0],xy[:,1]));x=np.unique(xy[:,0]);y=np.unique(xy[:,1])
    if len(x)!=N or len(y)!=N or len(centers)!=N*N:raise ValueError('Unexpected rectangular cell identities')
    query=(np.arange(41)+.5)/41
    values={}
    for name,raw in [('u',uv[:,0]),('v',uv[:,1]),('p',pp)]:
        values[name]=RectBivariateSpline(y,x,raw[sort].reshape(N,N))(query,query).ravel()
    np.savez(job/'native.npz',**values,time=T,dt=dt,coordinate_rounding_bound=5e-13)

if __name__=='__main__':main()
