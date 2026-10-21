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
from itertools import combinations
from pathlib import Path

import numpy as np
from elmer_flow_mesh import generate, partitions
from native_closed_cavity import SOCKET, save
from titan_resources import reservation
from native_elmer_incompressible import evaluate

CASE = 'ch02-2-1-5-01-power_law_channel'
RANKS = 8
IMAGE = 'sha256:c5a7643109973d30c9b2a1adb9a2d18579129bbfba28bb659254a0fa9489de95'


def prepare(root, snapshot):
    freeze=json.loads((snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text())
    matches=[]
    for p in snapshot.glob('qbank/02-fluid-mechanics/*/generalized-newtonian-incompressible-*-*d/author/chapter02-ten-20261020/design.json'):
        assert hashlib.sha256(p.read_bytes()).hexdigest()==freeze['designs'][p.relative_to(snapshot).as_posix()]
        record=json.loads(p.read_text())
        matches.extend((record,e) for e in record['proposed_cases'] if e['design_id']==CASE)
    assert len(matches)==1
    record,e=matches[0];s=e['detailed_spec'];assert not s['sources'];transient=s['analysis_kind']=='transient'
    end=s['time_interval_s'][1] if transient else 1.;ramp=f'(0.5*(t/{.1*end:.17g}+1-abs(t/{.1*end:.17g}-1)))'
    job=root/'cases'/CASE
    assert not job.exists(), 'Never overwrite or retry an existing case'
    job.mkdir();native=job/'native';native.mkdir();save(job/'design.json',e)
    mesh=generate(s);groups=partitions(s,mesh);np.savez(job/'adapter-data.npz',**mesh,groups=groups)
    x=mesh['x'];c=mesh['c'];b=mesh['b'];d=x.shape[1];zero='{'+','.join(['0']*d)+'}';velocity={};stress={};stress_vectors={};names={10000:(d,'Omega')};tags=[]
    for k,(nodes,group) in enumerate(zip(b,groups)):
        bc=s['boundaries'][int(group)]
        if bc['operator']=='no_slip':tag=1;name='wall';velocity[name]={'expr':zero}
        elif bc['operator']=='pressure_outlet':
            assert bc['data']['pressure_Pa']==0
            tag=2;name='outlet';stress[name]={'expr':zero}
        elif bc['operator']=='velocity':
            tag=100+k;name=f'inlet_facet_{k}';positions=x[nodes]
            values=evaluate(bc['data']['velocity']['expression'],positions,end if transient else 0.,s)
            coordinates=np.column_stack([np.ones(len(nodes)),positions]);coeff=np.linalg.lstsq(coordinates,values,rcond=None)[0]
            assert np.max(np.abs(coordinates@coeff-values))<1e-12
            expressions=['('+format(coeff[0,k],'.17g')+')'+''.join('+('+format(coeff[j+1,k],'.17g')+')*'+axis for j,axis in enumerate('xyz'[:d])) for k in range(d)]
            if transient:expressions=[f'({v})*{ramp}' for v in expressions]
            velocity[name]={'expr':'{'+','.join(expressions)+'}:'+':'.join(list('xyz'[:d])+(['t'] if transient else []))}
        elif bc['operator']=='traction':
            expr=bc['data']['traction']['expression'];tag=20+int(group);name=f'traction_{group}'
            if expr in ('-0.1*R*n','-R*0.1*n'):
                vector=-.1*mesh['normal'][k]
            else:
                assert expr==[0.]*d,expr
                vector=np.zeros(d)
            components=[format(float(v),'.17g') for v in vector]
            if transient and isinstance(expr,str):components=[f'({v})*{ramp}' for v in components]
            value={'expr':'{'+','.join(components)+'}'+(':t' if transient and isinstance(expr,str) else '')}
            if name in stress:
                previous=stress_vectors[name]
                assert np.allclose(previous,vector,rtol=0,atol=1e-12), 'Normal must be constant on this traction partition'
            else:stress[name]=value;stress_vectors[name]=vector.copy()
        else:raise ValueError(bc['operator'])
        names[tag]=(d-1,name);tags.append(tag)
    # Linear mesh and original node/cell ordering; P2 trace on each inlet facet
    # equals the frozen nodal P1 input, including every shared endpoint.
    lines=['$MeshFormat','2.2 0 8','$EndMeshFormat','$PhysicalNames',str(len(names))]
    lines += [f'{dim} {tag} "{name}"' for tag,(dim,name) in sorted(names.items())]
    lines += ['$EndPhysicalNames','$Nodes',str(len(x))]
    lines += [f'{i+1} '+' '.join(format(float(v),'.17g') for v in list(a)+([0.] if d==2 else [])) for i,a in enumerate(x)]
    lines += ['$EndNodes','$Elements',str(len(c)+len(b))]
    lines += [f'{i+1} {2 if d==2 else 4} 2 10000 10000 '+' '.join(str(int(j)+1) for j in row) for i,row in enumerate(c)]
    lines += [f'{len(c)+i+1} {1 if d==2 else 2} 2 {tag} {tag} '+' '.join(str(int(j)+1) for j in row) for i,(row,tag) in enumerate(zip(b,tags))]
    lines += ['$EndElements'];(native/'mesh.msh').write_text('\n'.join(lines)+'\n')
    q={k:v['value'] for k,v in s['materials']['viscosity']['parameters'].items()};mu=q['reference_viscosity'];g=q['reference_shear_rate'];n=q['power_index']
    ends=[mu*(v/g)**(n-1) for v in [q['minimum_shear_rate'],q['maximum_shear_rate']]]
    model={'Name':CASE,'ShortName':'power_law_channel','Models':{'fluid':{'setup':{'equations':'Navier-Stokes','viscosity_law':'power_law'}}},'Meshes':{'fluid':{'Import':{'filename':'/work/native/mesh.msh','partition':True,'number-of-partition':RANKS}}},'Materials':{'Omega':{'rho':s['materials']['density']['parameters']['density']['value'],'mu':mu,'mu_k':mu*g**(1-n),'mu_power_law_n':n,'mu_min':min(ends),'mu_max':max(ends)}},'BoundaryConditions':{'fluid':{'velocity':velocity,'normal_stress':stress}},'PostProcess':{'fluid':{'Exports':{'fields':['velocity','pressure','pid','materials.dynamic-viscosity']}}}}
    edges=np.unique(np.sort(np.concatenate([c[:,pair] for pair in combinations(range(d+1),2)]),axis=1),axis=0)
    midpoints=x[edges].mean(axis=1)
    def point_expr(pt):return '{'+','.join(format(float(v),'.17g') for v in list(pt)+([0.] if d==2 else []))+'}'
    point_measures={f'midpoint_{i:05d}':{'coord':point_expr(pt),'fields':['velocity','pressure'],'include_coordinates':1} for i,pt in enumerate(midpoints)}
    derived=any(q['quantity'] in ('density','dynamic_viscosity','shear_rate') for q in s['observation_requests'])
    if derived or d==3:
        point_measures.update({f'vertex_{i:05d}':{'coord':point_expr(pt),'fields':['velocity'],'include_coordinates':1} for i,pt in enumerate(x)})
    model['PostProcess']['fluid'].update(Save={'Fields':{'names':['velocity','pressure']}},Measures={'Points':point_measures})
    if transient:
        assert d==2, '3D transient runtime/step plan requires a separate review'
        initial=s['initial']['velocity']['expression'];assert initial==[0.]*d
        assert s['time_interval_s'][0]==0. and end==1.
        assert all(abs(t/.001-round(t/.001))<1e-9 for t in s['output_times_s'])
        model['InitialConditions']={'fluid':{'velocity':{'Expression':{'expr':zero}}}}
    mapping='Triangle P2 mean: average3edge midpoints. Tetrahedron P2 mean: -sum4vertex values/20+sum6edge midpoint values/5. P1 pressure mean: average edge midpoints. These are exact polynomial integrals on the original straight simplex. Nonlinear derived fields use declared order12 tensor Gauss-Duffy quadrature (12^dimension points), without exactness/accuracy certification. Native point measures evaluate the high-order FE field.'
    save(job/'native-point-map.json',{'dimension':d,'edges':edges.tolist(),'coordinates':midpoints.tolist(),'include_vertex_velocity':derived or d==3,'derived_quadrature_duffy_order':12,'integration':mapping})
    save(native/'cfd.json',model)
    global_time=f'ts.steady={str(not transient).lower()}\n'+(f'ts.time-initial=0\nts.time-final={end:.17g}\nts.time-step=0.001\n' if transient else '')
    native_time=f'ts.steady={str(not transient).lower()}\n'+(f'ts.time-initial=0\nts.time-final={end:.17g}\nts.time-step=0.001\nbdf.order=1\ntime-stepping=BDF\n' if transient else '')
    (native/'cfd.cfg').write_text(f'directory=/work/native/output\ncase.dimension={d}\ncase.discretization=P2P1G1\n'+global_time+'[fluid]\nfilename=/work/native/cfd.json\n'+native_time+'solver=Newton\nsnes-maxit=40\nsnes-rtol=1e-8\nsnes-atol=1e-10\nsnes-monitor=true\nksp-type=preonly\npc-type=lu\npc-factor-mat-solver-package-type=mumps\n')
    save(job/'parallel-numerical-plan.json',{'actual_native_ranks':RANKS,'cpu_per_case':RANKS,'memory_limit_gib':16 if d==3 else 8,'workload':'parallel_long','solver_budget_seconds':14300,'target_seconds':7200,'maximum_seconds':14400,'stationary_nonlinear_max_iterations':40,'physics_modified':False,'input_mapping':'Frozen inlet nodal values reconstructed separately as exact P1 trace on each supplied facet; native P2 velocity retains that trace. Full supplied sigma*n traction, no extra outlet velocity or pressure gauge constraint.','scope':'Candidate only after native termination, original global mesh topology and complete requested field mapping; no accuracy validation.'})
    if transient:
        plan=json.loads((job/'parallel-numerical-plan.json').read_text());plan.update(native_time_scheme='BDF1',dt_seconds=.001,expected_time_steps=1000,output_times=s['output_times_s'],ramp_history='Original nodal spatial input times piecewise-linear R(t), once only. Uniform zero initial field. Every requested time is an actual native step.');save(job/'parallel-numerical-plan.json',plan)
    return job, {'nodes':len(x),'cells':len(c),'boundary_faces':len(b),'inlet_trace_facets':len(velocity)-1,'spatial_dimension':d}


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--snapshot',type=Path,required=True);p.add_argument('--workers',type=int,default=8);a=p.parse_args()
    assert 8<=RANKS<=16
    if (a.root/'cases'/CASE).exists():raise RuntimeError('Existing case preserved; no automatic retry')
    job,meshinfo=prepare(a.root,a.snapshot);name='ch02feelpp-dist-'+hashlib.sha256(CASE.encode()).hexdigest()[:12]
    memory_gib=16 if meshinfo['spatial_dimension']==3 else 8
    command=['docker','--host',SOCKET,'run','--name',name,'--network','none','--cpus',str(RANKS),'--memory',f'{memory_gib}g','--label','ch02.workload=parallel_long','--user','0:0','-e','HOME=/tmp','-e','OMP_NUM_THREADS=1','-e','OPENBLAS_NUM_THREADS=1','-v',f'{job.resolve()}:/work','-w','/work/native','--entrypoint','/bin/bash',IMAGE,'-c',f'mpirun --allow-run-as-root --oversubscribe -np {RANKS} /usr/bin/feelpp_toolbox_fluid --config-file /work/native/cfd.cfg']
    state={'design_id':CASE,'status':'running','container':name,'producer':'unmodified Feel++ CFD toolbox v0.111.0','numerical_validation':False,**meshinfo}
    try:
        with reservation(a.root,name,cpu=RANKS,memory_limit_bytes=memory_gib*1024**3,workload='parallel_long'):
            save(job/'execution.json',{'command':command,'image':IMAGE,'start_unix':time.time(),'native_ranks':RANKS,'solver_budget_seconds':14300,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()});save(job/'status.json',state)
            with (job/'native-solver.log').open('w') as out:
                result=subprocess.run(command,stdout=out,stderr=subprocess.STDOUT,timeout=14460)
            state.update(status='native_raw_complete_pending_package' if result.returncode==0 else 'needs_attention',native_exit_code=result.returncode,reference_produced=False)
    except Exception as ex:
        # Runtime guard owns identity-verified stopping. Never blind-restart.
        state.update(status='needs_attention',error=repr(ex),reference_produced=False)
    old=json.loads((job/'status.json').read_text()) if (job/'status.json').exists() else {}
    if old.get('status')=='stopped_runtime_limit':return
    state['finished_unix']=time.time();save(job/'status.json',state)
    if state['status']=='native_raw_complete_pending_package':
        from finish_feelpp_powerlaw import finish
        finish(a.root,a.snapshot,case_id=CASE)


if __name__=='__main__':main()
