"""One finite stock shallowWaterFoam obstacle-wave production, no validation.

Only zero drag, zero bed, initially resting fully wet closed water are admitted.
No reservoir approximation, friction source or PDE extension is introduced.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import traceback
import numpy as np
from native_closed_cavity import IMAGE,SOCKET,header,put,save,digest,native_mesh,field
from native_lowmach import sample
from foam_box_mesh import write
from polytropic_reference import gmsh
from titan_resources import reservation
CASE='ch02-2-9-2-06-obstacle_wave'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int,default=1);a=ap.parse_args();r=a.root
    p=next(a.snapshot.glob('qbank/02-fluid-mechanics/*/fully-wet-transient/author/chapter02-ten-20261020/design.json'));freeze=json.loads((a.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text());assert digest(p)==freeze['designs'][p.relative_to(a.snapshot).as_posix()]
    d=json.loads(p.read_text());e=next(e for e in d['proposed_cases'] if e['design_id']==CASE);e={**e,'task':d['task'],'model':d['model']};s=e['detailed_spec']
    assert s['parameters']['drag_rate']['value']==0 and all(b['operator']=='water_wall' for b in s['boundaries']) and not s['sources']
    j=r/'cases'/CASE;assert not j.exists(),'Existing attempt requires explicit inspection';j.mkdir();save(j/'design.json',e);state={'design_id':CASE,'status':'queued'};save(j/'status.json',state)
    name='ch02sw-obstacle-'+str(time.time_ns())[-9:];n=j/'native'
    try:
        with reservation(r,name):
            patches=write(n,s);end=s['time_interval_s'][1];dt=.0005;assert abs(end/dt-round(end/dt))<1e-9
            assert all(abs(t/dt-round(t/dt))<1e-9 for t in s['output_times_s'])
            put(n/'system/controlDict',header('dictionary','controlDict')+f'application shallowWaterFoam; startFrom startTime; startTime 0; stopAt endTime; endTime {end}; deltaT {dt}; writeControl timeStep; writeInterval 1; purgeWrite 0; writeFormat ascii; writePrecision 16; writeCompression off; timeFormat general; timePrecision 12; runTimeModifiable false;\n')
            put(n/'system/fvSchemes',header('dictionary','fvSchemes')+'ddtSchemes { default Euler; } gradSchemes { default Gauss linear; } divSchemes { default none; div(phiv,hU) Gauss upwind; } laplacianSchemes { default Gauss linear corrected; } interpolationSchemes { default linear; } snGradSchemes { default corrected; } fluxRequired { default no; h; }\n')
            put(n/'system/fvSolution',header('dictionary','fvSolution')+'solvers { h { solver PCG; preconditioner DIC; tolerance 1e-10; relTol 0; } hFinal { $h; } hU { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-10; relTol 0; } hUFinal { $hU; } } PIMPLE { nOuterCorrectors 3; nCorrectors 1; nNonOrthogonalCorrectors 0; momentumPredictor yes; }\n')
            put(n/'constant/gravitationalProperties',header('dictionary','gravitationalProperties')+f'g [0 1 -2 0 0 0 0] (0 0 -{s["parameters"]["gravity"]["value"]}); rotating false;\n')
            base=['docker','--host',SOCKET,'run','--network','none','--cpus','1','--memory','768m','--user',f'{os.getuid()}:{os.getgid()}','-e','OMP_NUM_THREADS=1','-v',f'{j}:/work','-w','/work/native']
            env='source /usr/lib/openfoam/openfoam2512/etc/bashrc && '
            with (j/'blockMesh.log').open('w') as log:cp=subprocess.run(base+['--name',name+'-mesh',IMAGE,'bash','-c',env+'blockMesh'],stdout=log,stderr=subprocess.STDOUT)
            assert cp.returncode==0,'native blockMesh failure'
            xyz,quads,patch,area=native_mesh(n,2);x=xyz[:,:2];q=np.array(quads)-1;c=np.concatenate((q[:,[0,1,2]],q[:,[0,2,3]]));b=np.array([v for pp in patch.values() for v in pp])-1
            h=sample(s['initial']['depth']['expression'],x,0,s);u=sample(s['initial']['velocity']['expression'],x,0,s);bed=sample(s['domain_conditions']['bed']['expression'],x,0,s)
            assert np.min(h)>0 and np.all(u==0) and np.all(bed==0)
            # Exact P1 triangle integrals, summed in the native quad order.
            ha=(h[q[:,0]]*2+h[q[:,1]]+h[q[:,2]]*2+h[q[:,3]])/6
            np.savez(j/'mesh-input-identity.npz',x=x,c=c,b=b,quads=q,area=area,initial_depth=h,initial_velocity=u,bed=bed)
            inp=j/'input';inp.mkdir();gmsh(inp/'mesh.msh',x,c,b,2)
            wall='\n'.join(k+' { type '+('empty;' if k in ('front','back') else 'zeroGradient;')+' }' for k in patches)
            put(n/'0/h',header('volScalarField','h')+'dimensions [0 1 0 0 0 0 0]; internalField nonuniform List<scalar> '+str(len(ha))+' (\n'+'\n'.join(format(v,'.17g') for v in ha)+'\n); boundaryField { '+wall+' }\n')
            wall='\n'.join(k+' { type '+('empty;' if k in ('front','back') else 'slip;')+' }' for k in patches)
            put(n/'0/hU',header('volVectorField','hU')+'dimensions [0 2 -1 0 0 0 0]; internalField uniform (0 0 0); boundaryField { '+wall+' }\n')
            cmd=base+['--name',name,IMAGE,'bash','-c',env+'shallowWaterFoam']
            save(j/'execution.json',{'command':cmd,'image':IMAGE,'script_sha256':digest(Path(__file__)),'mesh_script_sha256':digest(Path(__file__).with_name('foam_box_mesh.py')),'source':'image:/usr/lib/openfoam/openfoam2512/applications/solvers/incompressible/shallowWaterFoam/shallowWaterFoam.C','scope':'Stock no-rotation inviscid shallow water. Zero frozen drag/bed. Exact rectangular cutout; slip momentum walls. P1 initial depth exact native quad means.','numerical_validation':False,'dt':dt,'steps':round(end/dt)})
            save(j/'grading-template.json',json.loads((p.parents[1]/'grading-template.json').read_text()));state.update(status='running',container=name);save(j/'status.json',state)
            with (j/'solver.log').open('w') as log:cp=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
            assert cp.returncode==0,f'native exit {cp.returncode}'
            for t in s['output_times_s']:
                depth=field(n/format(t,'.12g')/'h',1,len(q));assert np.isfinite(depth).all() and np.min(depth)>0
            state.update(status='native_complete_pending_conversion',remaining='Assemble self-contained problem/input and native-to-real-node reference recovery; not a completed candidate yet.')
    except Exception as ex:state.update(status='needs_attention',error=repr(ex),traceback=traceback.format_exc())
    state['ended_unix']=time.time();save(j/'status.json',state)
if __name__=='__main__':main()
