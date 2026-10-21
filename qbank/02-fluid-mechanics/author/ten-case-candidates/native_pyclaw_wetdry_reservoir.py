"""One frozen reservoir-flood case, using native wet/dry evolution."""
import argparse
import copy
import json
from pathlib import Path
import h5py
import numpy as np
from native_pyclaw_wetdry import run,prepare as wetdry_prepare
from native_lowmach import sample
from native_closed_cavity import save,digest
from shallow_reservoir_fields import normalize

CASE='ch02-2-9-3-07-reservoir_flood'


def prepare(job,e,allow_bed=True):
    assert e['design_id']==CASE
    spec=e['detailed_spec'];bc=spec['boundaries'][1]
    assert len(spec['boundaries'])==2 and bc['selection']=='x=0' and bc['operator']=='water_reservoir'
    assert bc['data']['depth']['expression']=='.1+.4*R' and bc['data']['velocity']['expression']==[0.,0.]
    private=copy.deepcopy(e);private['detailed_spec']['boundaries']=spec['boundaries'][:1]
    m,ids=wetdry_prepare(job,private,True)
    x,c,b=m['x'],m['c'],m['b'];inlet=np.all(np.isclose(x[b,0],0.),axis=1)
    assert inlet.any() and (~inlet).any()
    start,end=spec['time_interval_s'];assert start==0.
    times=np.array([start,.1*end,end]);vals=np.array([sample('.1+.4*R',np.zeros((1,2)),float(t),spec)[0] for t in times]);assert np.allclose(vals,[.1,.5,.5])
    problem=json.loads((job/'input/problem.json').read_text());problem['locations']['reservoir']={'kind':'mesh','mesh':'main','entity':'element','dimension':1,'ids':'reservoir'};problem['time_axes']['reservoir_history']='reservoir_history'
    problem['fields']['reservoir_depth']={'array':'reservoir_depth','quantity':'depth','location':'reservoir','time_axis':'reservoir_history','dtype':'float64','kind':'scalar','component_shape':[1],'components':['value'],'unit':'m','value_kind':'average','sampling':{'space':'piecewise_constant','time':'linear','extrapolation':'forbid'}}
    problem['conditions'].append({'role':'boundary','variable':'water','operator':'water_reservoir','location':'reservoir','data':{'depth':{'field':'reservoir_depth'},'velocity':{'value':[0.,0.],'unit':'m/s'}}})
    save(job/'input/problem.json',problem)
    with h5py.File(job/'input/input.h5','a') as f:
        del f['wall'];f['wall']=np.flatnonzero(~inlet).astype(np.int64)+len(c)+1;f['reservoir']=np.flatnonzero(inlet).astype(np.int64)+len(c)+1;f['reservoir_history']=times;f['reservoir_depth']=np.broadcast_to(vals[:,None,None],(len(times),int(inlet.sum()),1))
    normalize(job)
    raw=dict(np.load(job/'native-input.npz'));raw.update(reservoir_times=times,reservoir_depth=vals);np.savez(job/'native-input.npz',**raw)
    save(job/'reservoir-adapter.json',{'scope':'Same frozen initial depth with true zero-depth cells, zero drag and external h=.1+.4R,u=0 at x=0. External ghost states only; native sw_aug_2D supplies signed waves at boundary. Other faces walls.','native_input_sha256':digest(job/'native-input.npz'),'numerical_validation':False})
    return m,ids


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int,default=1);args=ap.parse_args()
    p=next(args.snapshot.glob('qbank/02-fluid-mechanics/*/wetting-drying/author/chapter02-ten-20261020/design.json'));freeze=json.loads((args.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text());assert digest(p)==freeze['designs'][p.relative_to(args.snapshot).as_posix()];d=json.loads(p.read_text());e=next(e for e in d['proposed_cases'] if e['design_id']==CASE);g=json.loads((p.parents[1]/'grading-template.json').read_text())
    state=run(args.root,{**e,'task':d['task'],'model':d['model']},g,prepare_fn=prepare,runtime_name='pyclaw_wetdry_reservoir_runtime.py');save(args.root/'maintenance/pyclaw-wetdry-reservoir-summary.json',state)


if __name__=='__main__':main()
