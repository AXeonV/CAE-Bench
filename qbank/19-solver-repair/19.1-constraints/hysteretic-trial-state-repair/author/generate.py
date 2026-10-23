"""Generate physically distinct direct-material root-cause adaptations and regressions."""
import json,sys
from pathlib import Path
import numpy as np
from caeoj.storage import write_hdf5
from caeoj.validation import write_json
TASK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(TASK/'extension'))
from caeoj_task_ext.material_state import INPUTS,OUTPUTS,spec

def program(kind,np_,nn,sign,seed,zero=False,delta=0.,elastic=False):
 rng=np.random.default_rng(seed);scale=rng.uniform(.2,3.);length=rng.uniform(.8,1.2)
 def side(n,force,stretch):
  x=np.linspace(.001,.025,n)*length*stretch;slope=np.geomspace(1e9,4e7,n)*scale*force/stretch
  f=np.cumsum(slope*np.diff(np.r_[0.,x]));return np.c_[f,x]
 pos=side(np_,1.,1.);neg=-side(nn,1.3,1.1)
 history=[] if zero else ([sign*.0002] if elastic else [sign*.0003,sign*.0041])
 continuation=[sign*.0003,sign*.0005] if elastic else [sign*.0082,sign*.0171]
 probes=[-sign*.006,sign*.009,-sign*.002] if seed%2 else [sign*.012,-sign*.01,sign*.001,-sign*.003]
 return {'kind':kind,'positive':pos.tolist(),'negative':neg.tolist(),'pinch':rng.uniform(.1,1.,2).tolist(),'beta':float(rng.uniform(0,1)),
  'history':history,'probes':probes,'delta':delta*sign,'continuation':continuation,'rollback_probe':-sign*.007}

def main():
 cases=[]
 for j,(case,mode) in enumerate([('01-hysteretic-public','hys2'),('02-sm-public','sm7'),('03-asymmetric-three-point','hys3'),('04-sm-intermediate-points','smvar'),('05-independent-side-counts','unequal'),('06-zero-committed','zero'),('07-machine-threshold','threshold'),('08-multiple-trial-excursions','probes'),('09-elastic-nontrigger','elastic'),('10-monotonic-nontrigger','control')]):
  items=[]
  for i in range(4):
   kind=0 if mode in ('hys2','hys3') else 1 if mode in ('sm7','smvar','unequal') else i%2
   np_=2 if mode=='hys2' else 3 if kind==0 else 7 if mode=='sm7' else 2+i if mode=='smvar' else 2+i if mode=='unequal' else 3+i
   nn=7-i if mode=='unequal' else np_
   delta=[0.,np.finfo(float).eps*.25,np.finfo(float).eps*.75,2*np.finfo(float).eps][i] if mode=='threshold' else 1e-8 if mode in ('control','elastic') else 0.
   items.append(program(kind,np_,nn,1 if i<2 else -1,100*j+i+1,zero=mode=='zero',delta=delta,elastic=mode=='elastic'))
  arrays={'program_ids':np.array([13,29,47,83],dtype='int64'),'times':np.array([0.])}
  for key,(_,_,components) in INPUTS.items():arrays[key]=np.zeros((1,4,len(components)),dtype='float64')
  for i,p in enumerate(items):
   def set_(name,value):arrays[name][0,i,:len(value)]=value
   for k,v in [('material_kind',p['kind']),('positive_count',len(p['positive'])),('negative_count',len(p['negative'])),('beta',p['beta']),('history_count',len(p['history'])),('trial_count',len(p['probes'])),('return_delta',p['delta']),('continuation_count',len(p['continuation'])),('rollback_probe',p['rollback_probe'])]:set_(k,[v])
   for side in ('positive','negative'):
    set_(side+'_stress',[x[0] for x in p[side]]);set_(side+'_strain',[x[1] for x in p[side]])
   for k,v in [('pinching',p['pinch']),('history',p['history']),('trials',p['probes']),('continuation',p['continuation'])]:set_(k,v)
  manifest={'task':'hysteretic-trial-state-repair','spatial_dimension':1,'data_file':'input.h5','geometries':{},'meshes':{},'conditions':[],
   'physics':{'model':'hysteretic-trial-state-v1','parameters':{}},'locations':{'programs':{'kind':'entities','ids':'program_ids'}},'time_axes':{'instant':'times'},
   'fields':{k:spec(k,v) for k,v in INPUTS.items()},'outputs':{k:spec(k,v,True) for k,v in OUTPUTS.items()}}
  d=TASK/'cases'/case;d.mkdir(parents=True,exist_ok=True);write_hdf5(d/'input.h5',arrays);write_json(d/'problem.json',manifest)
  cases.append({'case':case,'mode':mode,'programs':items,'origin':'author direct-material adaptation of OpenSees issue 1817; no full original bridge trajectory claimed'})
 write_json(TASK/'author/data-evidence/cases.json',cases)
if __name__=='__main__':main()
