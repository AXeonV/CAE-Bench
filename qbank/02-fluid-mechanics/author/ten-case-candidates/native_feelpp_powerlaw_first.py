"""Finite first-case adapter for the unmodified, pinned Feel++ CFD toolbox.

Only mesh, native configuration and input trace translation live here. Raw native
outputs are retained; completion does not claim a packaged/validated reference.
"""
import argparse
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

import numpy as np
from elmer_flow_mesh import generate, partitions
from native_closed_cavity import SOCKET, save
from titan_resources import reservation

CASE = 'ch02-2-1-5-01-power_law_channel'
IMAGE = 'sha256:c5a7643109973d30c9b2a1adb9a2d18579129bbfba28bb659254a0fa9489de95'


def prepare(root, snapshot):
    freeze=json.loads((snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text())
    matches=[]
    for p in snapshot.glob('qbank/02-fluid-mechanics/*/generalized-newtonian-incompressible-steady-2d/author/chapter02-ten-20261020/design.json'):
        assert hashlib.sha256(p.read_bytes()).hexdigest()==freeze['designs'][p.relative_to(snapshot).as_posix()]
        record=json.loads(p.read_text())
        matches.extend((record,e) for e in record['proposed_cases'] if e['design_id']==CASE)
    assert len(matches)==1
    record,e=matches[0];s=e['detailed_spec'];assert s['analysis_kind']=='steady' and not s['sources']
    job=root/'cases'/CASE
    assert not job.exists(), 'Never overwrite or retry an existing case'
    job.mkdir();native=job/'native';native.mkdir();save(job/'design.json',e)
    mesh=generate(s);groups=partitions(s,mesh);np.savez(job/'adapter-data.npz',**mesh,groups=groups)
    x=mesh['x'];c=mesh['c'];b=mesh['b'];velocity={};stress={};names={10000:(2,'Omega')};tags=[]
    for k,(nodes,group) in enumerate(zip(b,groups)):
        bc=s['boundaries'][int(group)]
        if bc['operator']=='no_slip':tag=1;name='wall';velocity[name]={'expr':'{0,0}'}
        elif bc['operator']=='pressure_outlet':
            assert bc['data']['pressure_Pa']==0
            tag=2;name='outlet';stress[name]={'expr':'{0,0}'}
        elif bc['operator']=='velocity':
            assert bc['data']['velocity']['expression']==['0.1*R*4*Y*(1-Y)',0]
            tag=100+k;name=f'inlet_facet_{k}';yy=x[nodes,1];L=s['geometry']['bounding_lengths'][1]
            values=.4*(yy/L)*(1-yy/L);slope=(values[1]-values[0])/(yy[1]-yy[0]);intercept=values[0]-slope*yy[0]
            velocity[name]={'expr':'{('+format(intercept,'.17g')+')+('+format(slope,'.17g')+')*y,0}:y'}
        else:raise ValueError(bc['operator'])
        names[tag]=(1,name);tags.append(tag)
    # Linear mesh and original node/cell ordering; P2 trace on each inlet facet
    # equals the frozen nodal P1 input, including every shared endpoint.
    lines=['$MeshFormat','2.2 0 8','$EndMeshFormat','$PhysicalNames',str(len(names))]
    lines += [f'{dim} {tag} "{name}"' for tag,(dim,name) in sorted(names.items())]
    lines += ['$EndPhysicalNames','$Nodes',str(len(x))]
    lines += [f'{i+1} {a[0]:.17g} {a[1]:.17g} 0' for i,a in enumerate(x)]
    lines += ['$EndNodes','$Elements',str(len(c)+len(b))]
    lines += [f'{i+1} 2 2 10000 10000 '+' '.join(str(int(j)+1) for j in row) for i,row in enumerate(c)]
    lines += [f'{len(c)+i+1} 1 2 {tag} {tag} '+' '.join(str(int(j)+1) for j in row) for i,(row,tag) in enumerate(zip(b,tags))]
    lines += ['$EndElements'];(native/'mesh.msh').write_text('\n'.join(lines)+'\n')
    q={k:v['value'] for k,v in s['materials']['viscosity']['parameters'].items()};mu=q['reference_viscosity'];g=q['reference_shear_rate'];n=q['power_index']
    ends=[mu*(v/g)**(n-1) for v in [q['minimum_shear_rate'],q['maximum_shear_rate']]]
    model={'Name':CASE,'ShortName':'power_law_channel','Models':{'fluid':{'setup':{'equations':'Navier-Stokes','viscosity_law':'power_law'}}},'Meshes':{'fluid':{'Import':{'filename':'/work/native/mesh.msh'}}},'Materials':{'Omega':{'rho':s['materials']['density']['parameters']['density']['value'],'mu':mu,'mu_k':mu*g**(1-n),'mu_power_law_n':n,'mu_min':min(ends),'mu_max':max(ends)}},'BoundaryConditions':{'fluid':{'velocity':velocity,'normal_stress':stress}},'PostProcess':{'fluid':{'Exports':{'fields':['velocity','pressure','pid','materials.dynamic-viscosity']}}}}
    save(native/'cfd.json',model)
    (native/'cfd.cfg').write_text('directory=/work/native/output\ncase.dimension=2\ncase.discretization=P2P1G1\nts.steady=true\n[fluid]\nfilename=/work/native/cfd.json\nsolver=Newton\nsnes-maxit=40\nsnes-rtol=1e-8\nsnes-atol=1e-10\nsnes-monitor=true\nksp-type=preonly\npc-type=lu\npc-factor-mat-solver-package-type=mumps\n')
    save(job/'parallel-numerical-plan.json',{'actual_native_ranks':8,'cpu_per_case':8,'workload':'parallel_long','solver_budget_seconds':14300,'target_seconds':7200,'maximum_seconds':14400,'stationary_nonlinear_max_iterations':40,'physics_modified':False,'input_mapping':'Frozen inlet nodal values reconstructed separately as exact P1 trace on each supplied facet; native P2 velocity retains that trace. Complete zero sigma*n outlet, no pressure gauge or extra outlet velocity constraint.','scope':'First native raw solve; native high-order output and cell-average conversion remain to inspect. No candidate claimed before packaging.'})
    return job, {'nodes':len(x),'cells':len(c),'boundary_faces':len(b),'inlet_trace_facets':len(velocity)-1}


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--snapshot',type=Path,required=True);p.add_argument('--workers',type=int,default=8);a=p.parse_args()
    if (a.root/'cases'/CASE).exists():raise RuntimeError('Existing case preserved; no automatic retry')
    job,meshinfo=prepare(a.root,a.snapshot);name='ch02feelpp-'+hashlib.sha256(CASE.encode()).hexdigest()[:12]
    command=['docker','--host',SOCKET,'run','--name',name,'--network','none','--cpus','8','--memory','8g','--label','ch02.workload=parallel_long','--user','0:0','-e','HOME=/tmp','-e','OMP_NUM_THREADS=1','-e','OPENBLAS_NUM_THREADS=1','-v',f'{job.resolve()}:/work','-w','/work/native','--entrypoint','/bin/bash',IMAGE,'-c','mpirun --allow-run-as-root --oversubscribe -np 8 /usr/bin/feelpp_toolbox_fluid --config-file /work/native/cfd.cfg']
    state={'design_id':CASE,'status':'running','container':name,'producer':'unmodified Feel++ CFD toolbox v0.111.0','numerical_validation':False,**meshinfo}
    try:
        with reservation(a.root,name,cpu=8,memory_limit_bytes=8*1024**3,workload='parallel_long'):
            save(job/'execution.json',{'command':command,'image':IMAGE,'start_unix':time.time(),'native_ranks':8,'solver_budget_seconds':14300,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()});save(job/'status.json',state)
            with (job/'native-solver.log').open('w') as out:
                result=subprocess.run(command,stdout=out,stderr=subprocess.STDOUT,timeout=14460)
            state.update(status='native_raw_complete_pending_package' if result.returncode==0 else 'needs_attention',native_exit_code=result.returncode,reference_produced=False)
    except Exception as ex:
        # Runtime guard owns identity-verified stopping. Never blind-restart.
        state.update(status='needs_attention',error=repr(ex),reference_produced=False)
    old=json.loads((job/'status.json').read_text()) if (job/'status.json').exists() else {}
    if old.get('status')=='stopped_runtime_limit':return
    state['finished_unix']=time.time();save(job/'status.json',state)


if __name__=='__main__':main()
