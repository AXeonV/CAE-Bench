"""Adapted, analytically cross-checkable real Cantera regression families."""
from pathlib import Path
import json,importlib.util
import numpy as np
from caeoj.storage import write_hdf5
from caeoj.validation import write_json
Q=Path(__file__).resolve().parents[1]
MULTI=True
ISSUE=1996
MODULE='multisite_flow'
s=importlib.util.spec_from_file_location('contract',Q/f'extension/caeoj_task_ext/{MODULE}.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
W=Path(f'work/repair-22/cantera-{ISSUE}/generated')
def make(name,kind,seed):
 rng=np.random.default_rng(seed);n=12
 T=rng.uniform(650,1100,n);P=rng.uniform(6e4,2e5,n);u=rng.uniform(.05,.3,n);area=rng.uniform(300,1800,n);n0=rng.uniform(1e-8,7e-8,n)
 ka=rng.uniform(3e13,3e14,n) if MULTI else rng.uniform(3e5,3e6,n);kd=rng.uniform(5e3,3e4,n);kc=rng.uniform(5e3,3e4,n)
 xa=rng.uniform(.3,.8,n);xb=rng.uniform(0,.1,n);x=np.column_stack([xa,xb,1-xa-xb]);order=np.arange(n)%6
 if kind=='inert-last':order=np.tile([0,2],6)
 if kind=='zero-adsorption':ka[:]=0
 if kind=='zero-conversion':kc[:]=0
 if kind=='product-rich':x=np.column_stack([np.full(n,.1),np.full(n,.75),np.full(n,.15)])
 if kind=='trace-substrate':x=np.column_stack([np.full(n,.001),np.full(n,.249),np.full(n,.75)])
 if kind=='site-density':n0=np.geomspace(1e-9,1e-6,n)
 if kind=='pressure-scale':P=np.geomspace(1e4,1e6,n)
 if kind=='kinetic-regimes':ka*=np.geomspace(.01,2,n)
 C0=P/(8314.46261815324*T)*x[:,0]
 char=u*(ka*C0+kd+kc)/(area*np.maximum(kc,1)*n0*np.maximum(ka,1))
 if MULTI:char=u*C0/(area*np.maximum(kc,1)*n0*.25)
 z=np.minimum(char*np.geomspace(.02,2,n),1.5)
 if kind in ['zero-adsorption','zero-conversion']:z[:]=.01
 arrays={'state_ids':np.arange(n,dtype='int64')*17+7,'times':np.array([0.]),'species_order':order[None,:,None].astype('int64'),'temperature':T[None,:,None],'pressure':P[None,:,None],'inlet_speed':u[None,:,None],'surface_area_to_volume':area[None,:,None],'site_density':n0[None,:,None],'adsorption_rate':ka[None,:,None],'desorption_rate':kd[None,:,None],'conversion_rate':kc[None,:,None],'distance':z[None,:,None],'inlet_mole_fractions':x[None]}
 if MULTI:
  theta=np.column_stack([rng.uniform(.05,.9,n),np.zeros(n)]);theta[:,1]=1-theta[:,0];raw=(np.arange(n)%2).astype('int64');theta[raw==1]*=rng.uniform(.6,1.4,(sum(raw==1),1))
  arrays.update(initial_coverages=theta[None],coverage_mode=raw[None,:,None])
 meta={'task':c.TASK,'spatial_dimension':1,'data_file':'input.h5','geometries':{},'meshes':{},'conditions':[],'physics':{'model':c.MODEL,'parameters':{}},'locations':{'states':{'kind':'entities','ids':'state_ids'}},'time_axes':{'instant':'times'},'fields':{k:c.spec(k,v) for k,v in c.FIELDS.items()},'outputs':{k:c.spec(k,v,True) for k,v in c.OUTPUTS.items()}}
 case=Q/'cases'/name;case.mkdir(parents=True,exist_ok=True);write_hdf5(case/'input.h5',arrays);write_json(case/'problem.json',meta)
 return {'case':name,'family':kind,'seed':seed,'states':n,'origin':f'author-created catalytic conversion regression motivated by Cantera issue{ISSUE}; not an upstream experiment'}
if __name__=='__main__':
 families=[('01-reacting-last-public','mixed'),('02-inert-last-public','inert-last'),('03-zero-adsorption','zero-adsorption'),('04-zero-conversion','zero-conversion'),('05-product-rich','product-rich'),('06-trace-substrate','trace-substrate'),('07-site-density','site-density'),('08-pressure-scale','pressure-scale'),('09-kinetic-regimes','kinetic-regimes')]
 write_json(Q/'author/data-evidence/cases.json',[make(n,k,ISSUE*100+i) for i,(n,k) in enumerate(families)])
