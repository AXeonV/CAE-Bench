"""Map native Feel++ point measures to exact P2/P1 triangle cell averages."""
import csv
import hashlib
import json
import re
import subprocess
import time
from itertools import combinations
from pathlib import Path

import numpy as np
from native_closed_cavity import SOCKET,save
from native_elmer_incompressible import package

CASE='ch02-2-1-5-01-power_law_channel'


def primary_cell_means(d,c,vertex_velocity,midpoint_velocity,midpoint_pressure,indices):
    velocity=midpoint_velocity[indices].mean(axis=1) if d==2 else -.05*vertex_velocity[c].sum(axis=1)+.2*midpoint_velocity[indices].sum(axis=1)
    return {'velocity':velocity[None],'pressure':midpoint_pressure[indices].mean(axis=1)[None,:,None]}


def derived_cell_means(m,vertex_velocity,midpoint_velocity,indices,parameters,order):
    """Postprocess the native P2 polynomial; this integrates no PDE."""
    c=m['c'];x=m['x'];d=x.shape[1];inverse=np.linalg.inv(x[c][:,1:]-x[c][:,:1])
    grad_lambda=np.stack([-inverse.sum(axis=2)]+[inverse[:,:,k] for k in range(d)],axis=1)
    dofs=np.concatenate([vertex_velocity[c],midpoint_velocity[indices]],axis=1)
    ab,weights=np.polynomial.legendre.leggauss(order);ab=(ab+1)/2;weights=weights/2
    shear=np.zeros(len(c));viscosity=np.zeros(len(c))
    from itertools import product
    import math
    pairs=[(0,1),(1,2),(2,0)] if d==2 else list(combinations(range(d+1),2))
    for quadrature_indices in product(range(order),repeat=d):
        remaining=1.;coords=[];weight=float(math.factorial(d))
        for axis,index in enumerate(quadrature_indices):
            coords.append(remaining*ab[index]);weight*=weights[index]*(1-ab[index])**(d-axis-1);remaining*=1-ab[index]
        lam=np.array([remaining,*coords])
        shape_grad=np.concatenate([(4*lam-1)[None,:,None]*grad_lambda,np.stack([4*(lam[q]*grad_lambda[:,p]+lam[p]*grad_lambda[:,q]) for p,q in pairs],axis=1)],axis=1)
        grad=np.einsum('nki,nkj->nij',dofs,shape_grad);twod=grad+grad.swapaxes(1,2);rate=np.sqrt(.5*np.sum(twod**2,axis=(1,2)))
        clipped=np.clip(rate,parameters['minimum_shear_rate'],parameters['maximum_shear_rate'])
        mu=parameters['reference_viscosity']*(clipped/parameters['reference_shear_rate'])**(parameters['power_index']-1)
        shear+=weight*rate;viscosity+=weight*mu
    return shear,viscosity


def finish(root,snapshot,case_id=CASE):
    job=root/'cases'/case_id;status=json.loads((job/'status.json').read_text())
    assert status['status']=='native_raw_complete_pending_package'
    container=json.loads(subprocess.check_output(['docker','--host',SOCKET,'inspect',status['container']]))[0]
    assert not container['State']['Running'] and container['State']['Pid']==0 and container['State']['ExitCode']==0
    execution=json.loads((job/'execution.json').read_text());ranks=execution['native_ranks'];assert 8<=ranks<=16
    assert container['Image']==execution['image']
    assert any(q['Source']==str(job.resolve()) and q['Destination']=='/work' for q in container['Mounts'])
    m=dict(np.load(job/'adapter-data.npz'));output=job/f'native/output/np_{ranks}';journal=json.loads((output/'journal.json').read_text());mesh=journal['Mesh']['fluid']
    assert mesh['n_elements']==len(m['c']), 'Native mesh still replicated; do not count a candidate'
    assert mesh['n_points']==len(m['x']) and len(mesh['partitioning']['n_elements'])==ranks
    assert all(0<v<len(m['c']) for v in mesh['partitioning']['n_elements'])
    residuals=[float(v) for v in re.findall(r'SNES Residual norm ([0-9.eE+-]+)',(job/'native-solver.log').read_text())]
    assert residuals and residuals[-1]<=max(1e-10,1e-8*residuals[0])
    pointmap=json.loads((job/'native-point-map.json').read_text());edges=np.asarray(pointmap['edges'],dtype=int);positions=np.asarray(pointmap['coordinates'])
    path=output/'fluid.measures/values.csv'
    with path.open() as f:rows=list(csv.DictReader(f))
    assert len(rows)==1
    row=rows[0];u=[];p=[];d=m['x'].shape[1]
    for i,pt in enumerate(positions):
        prefix=f'Points_midpoint_{i:05d}_';actual=[float(row[prefix+'coordinates_'+str(k)]) for k in range(d)]
        assert np.max(np.abs(np.asarray(actual)-pt))<1e-12
        u.append([float(row[prefix+'field_velocity_'+str(k)]) for k in range(d)]);p.append(float(row[prefix+'field_pressure']))
    pairs=[(0,1),(1,2),(2,0)] if d==2 else list(combinations(range(d+1),2))
    lookup={tuple(v):i for i,v in enumerate(edges)};indices=np.array([[lookup[tuple(sorted((cell[a],cell[b])))] for a,b in pairs] for cell in m['c']])
    records=list(snapshot.glob(f'qbank/02-fluid-mechanics/*/generalized-newtonian-incompressible-steady-{d}d/author/chapter02-ten-20261020/design.json'));assert len(records)==1
    record=json.loads(records[0].read_text());entry=next(e for e in record['proposed_cases'] if e['design_id']==case_id);entry={**entry,'task':record['task']}
    vertex_velocity=[]
    if pointmap.get('include_vertex_velocity'):
        for i,pt in enumerate(m['x']):
            prefix=f'Points_vertex_{i:05d}_';actual=[float(row[prefix+'coordinates_'+str(k)]) for k in range(d)]
            assert np.max(np.abs(np.asarray(actual)-pt))<1e-12
            vertex_velocity.append([float(row[prefix+'field_velocity_'+str(k)]) for k in range(d)])
    fields=primary_cell_means(d,m['c'],np.asarray(vertex_velocity),np.asarray(u),np.asarray(p),indices)
    if any(q['quantity'] in ('density','dynamic_viscosity','shear_rate') for q in entry['detailed_spec']['observation_requests']):
        spec=entry['detailed_spec'];parameters={k:v['value'] for k,v in spec['materials']['viscosity']['parameters'].items()}
        shear,mu=derived_cell_means(m,np.asarray(vertex_velocity),np.asarray(u),indices,parameters,pointmap['derived_quadrature_duffy_order'])
        fields.update(shear_rate=shear[None,:,None],dynamic_viscosity=mu[None,:,None],density=np.full((1,len(m['c']),1),spec['materials']['density']['parameters']['density']['value']))
    result=package(job,entry,m,m['groups'],native_cell_frames=fields)
    grading=json.loads((records[0].parents[1]/'grading-template.json').read_text());save(job/'reference/grading.json',grading)
    save(job/'native-to-contract.json',{'native_point_map_sha256':hashlib.sha256((job/'native-point-map.json').read_bytes()).hexdigest(),'native_measures_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'mapping':pointmap['integration'],'partitioning':mesh['partitioning'],'native_nonlinear_final_residual':residuals[-1],'numerical_validation':False})
    status.update(result,status='unvalidated_candidate',reference_produced=True,finished_unix=time.time());save(job/'status.json',status)
    return status
