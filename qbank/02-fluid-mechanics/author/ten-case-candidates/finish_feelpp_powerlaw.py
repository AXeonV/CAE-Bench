"""Map native Feel++ point measures to exact P2/P1 triangle cell averages."""
import csv
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

import numpy as np
from native_closed_cavity import SOCKET,save
from native_elmer_incompressible import package

CASE='ch02-2-1-5-01-power_law_channel'


def finish(root,snapshot):
    job=root/'cases'/CASE;status=json.loads((job/'status.json').read_text())
    assert status['status']=='native_raw_complete_pending_package'
    container=json.loads(subprocess.check_output(['docker','--host',SOCKET,'inspect',status['container']]))[0]
    assert not container['State']['Running'] and container['State']['Pid']==0 and container['State']['ExitCode']==0
    assert container['Image']==json.loads((job/'execution.json').read_text())['image']
    assert any(q['Source']==str(job.resolve()) and q['Destination']=='/work' for q in container['Mounts'])
    m=dict(np.load(job/'adapter-data.npz'));journal=json.loads((job/'native/output/np_8/journal.json').read_text());mesh=journal['Mesh']['fluid']
    assert mesh['n_elements']==len(m['c']), 'Native mesh still replicated; do not count a candidate'
    assert mesh['n_points']==len(m['x']) and len(mesh['partitioning']['n_elements'])==8
    assert all(0<v<len(m['c']) for v in mesh['partitioning']['n_elements'])
    residuals=[float(v) for v in re.findall(r'SNES Residual norm ([0-9.eE+-]+)',(job/'native-solver.log').read_text())]
    assert residuals and residuals[-1]<=max(1e-10,1e-8*residuals[0])
    pointmap=json.loads((job/'native-point-map.json').read_text());edges=np.asarray(pointmap['edges'],dtype=int);positions=np.asarray(pointmap['coordinates'])
    path=job/'native/output/np_8/fluid.measures/values.csv'
    with path.open() as f:rows=list(csv.DictReader(f))
    assert len(rows)==1
    row=rows[0];u=[];p=[]
    for i,pt in enumerate(positions):
        prefix=f'Points_midpoint_{i:05d}_';actual=[float(row[prefix+'coordinates_'+str(k)]) for k in range(2)]
        assert np.max(np.abs(np.asarray(actual)-pt))<1e-12
        u.append([float(row[prefix+'field_velocity_'+str(k)]) for k in range(2)]);p.append(float(row[prefix+'field_pressure']))
    lookup={tuple(v):i for i,v in enumerate(edges)};indices=np.array([[lookup[tuple(sorted((a,b)))] for a,b in [(c[0],c[1]),(c[1],c[2]),(c[2],c[0])]] for c in m['c']])
    fields={'velocity':np.asarray(u)[indices].mean(axis=1)[None],'pressure':np.asarray(p)[indices].mean(axis=1)[None,:,None]}
    records=list(snapshot.glob('qbank/02-fluid-mechanics/*/generalized-newtonian-incompressible-steady-2d/author/chapter02-ten-20261020/design.json'));assert len(records)==1
    record=json.loads(records[0].read_text());entry=next(e for e in record['proposed_cases'] if e['design_id']==CASE);entry={**entry,'task':record['task']}
    result=package(job,entry,m,m['groups'],native_cell_frames=fields)
    grading=json.loads((records[0].parents[1]/'grading-template.json').read_text());save(job/'reference/grading.json',grading)
    save(job/'native-to-contract.json',{'native_point_map_sha256':hashlib.sha256((job/'native-point-map.json').read_bytes()).hexdigest(),'native_measures_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'mapping':pointmap['integration'],'partitioning':mesh['partitioning'],'native_nonlinear_final_residual':residuals[-1],'numerical_validation':False})
    status.update(result,status='unvalidated_candidate',reference_produced=True,finished_unix=time.time());save(job/'status.json',status)
    return status
