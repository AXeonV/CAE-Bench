"""Represent constant reservoir vectors as DATA-required boundary fields.

Only serialization changes; numerical states and native reference files untouched.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import h5py
import numpy as np


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def normalize(job):
    path=job/'input/problem.json';problem=json.loads(path.read_text());changes=[]
    for c in problem['conditions']:
        if c['operator']!='water_reservoir':continue
        name=c['location'];value=c['data']['velocity']
        if 'value' in value:changes.append((c,name,value))
    bad=[key for key,f in problem['fields'].items() if f['location'] in {c['location'] for c in problem['conditions'] if c['operator']=='water_reservoir'} and f['value_kind']!='average']
    if not changes and not bad:return False
    archive=job/'input-before-reservoir-field-serialization';archive.mkdir(exist_ok=False)
    for name in ['problem.json','input.h5']:shutil.copy2(job/'input'/name,archive/name)
    ref=job/'reference/reference.h5';refhash=digest(ref) if ref.exists() else None
    with h5py.File(job/'input/input.h5','a') as f:
        for c,name,value in changes:
            key=name+'_external_velocity';count=len(f[problem['locations'][name]['ids']]);v=np.array(value['value'],dtype=float)
            assert v.shape==(2,) and value['unit']=='m/s'
            f[key]=np.broadcast_to(v,(1,count,2))
            problem['fields'][key]={'array':key,'quantity':'velocity','location':name,'time_axis':'constant','dtype':'float64','kind':'vector','component_shape':[2],'components':['x','y'],'unit':'m/s','value_kind':'average','sampling':{'space':'piecewise_constant','time':'constant','extrapolation':'forbid'}}
            c['data']['velocity']={'field':key}
        for key in bad:problem['fields'][key]['value_kind']='average'
    path.write_text(json.dumps(problem,indent=2)+'\n')
    assert not ref.exists() or digest(ref)==refhash
    (job/'reservoir-field-serialization.json').write_text(json.dumps({'scope':'DATA representation only: constant vector becomes same-location P0 average field; boundary depth value_kind average. Same values, entities and time histories; no numerical rerun.','old_problem_sha256':digest(archive/'problem.json'),'new_problem_sha256':digest(path),'new_input_sha256':digest(job/'input/input.h5'),'reference_sha256_unchanged':refhash,'numerical_validation':False},indent=2)+'\n')
    return True


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);args=ap.parse_args()
    ids=['ch02-2-9-2-07-cross_waves']
    ids+=json.loads((args.root/'maintenance/pyclaw-steady-handoff.json').read_text())['case_ids']
    print(json.dumps({case:normalize(args.root/'cases'/case) for case in ids}))
