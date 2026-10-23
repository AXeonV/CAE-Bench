"""Create attributed synthetic instantaneous contact regression families."""
import importlib.util,json
from pathlib import Path
import numpy as np
from caeoj.storage import write_hdf5
from caeoj.validation import write_json
Q=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('contract',Q/'extension/caeoj_task_ext/granular_contact.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
def make(index,kind,mode,newton):
    rng=np.random.default_rng(421900+index)
    x=np.array([[0,0,0],[.85,.1,.15],[-.55,.6,.1],[0,-.7,.45]],float)
    if kind=='single':x=x[:2]
    if kind=='noncontact':x=np.array([[-1.1,0,0],[1.1,0,0],[0,1.2,.3]])
    if kind=='cluster':x=np.vstack([np.zeros(3),np.array([[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]])*.83])
    if kind in ['rotation','permutation','cluster']:
        rot,_=np.linalg.qr(rng.normal(size=(3,3)));x=x@rot.T
    n=len(x);diameter=np.ones(n);density=rng.uniform(500,2200,n)
    if kind=='polydisperse':diameter=np.array([1.1,1.05,.95,1.2])
    velocity=rng.uniform(-.01,.01,(n,3));omega=rng.uniform(-.03,.03,(n,3));gn=1.;gt=.7
    if kind in ['elastic','single','noncontact']:gn=gt=0.;velocity[:]=0;omega[:]=0
    if kind=='normal':gt=0.
    ids=np.arange(n,dtype='int64')*17+7
    if kind=='permutation':
        perm=rng.permutation(n);x=x[perm];diameter=diameter[perm];density=density[perm];velocity=velocity[perm];omega=omega[perm]
    params={'box_length':8.,'normal_stiffness':12000.+index*1300,'tangential_stiffness':3000.,'normal_damping':gn,'tangential_damping':gt,'friction':.6,'tally_mode':mode}
    arrays={'particle_ids':ids,'system_ids':np.array([0],dtype='int64'),'times':np.array([0.]),'position':x[None],'diameter':diameter[None,:,None],'material_density':density[None,:,None],'velocity':velocity[None],'angular_velocity':omega[None]}
    meta={'task':c.TASK,'spatial_dimension':3,'data_file':'input.h5','geometries':{},'meshes':{},'conditions':[],'physics':{'model':c.MODEL,'parameters':{k:{'value':({'on':1,'off':0}[v] if k=='newton_pair' else {'global':0,'particle':1,'both':2}[v] if k=='tally_mode' else v),'unit':c.UNITS[k]} for k,v in params.items()}},'locations':{'particles':{'kind':'entities','ids':'particle_ids'},'system':{'kind':'entities','ids':'system_ids'}},'time_axes':{'instant':'times'},'fields':{k:c.spec(k,v) for k,v in c.FIELDS.items()},'outputs':c.output_specs(mode)}
    name=f'{index:02d}-{kind}-{mode}-{newton}';dest=Q/'cases'/name;dest.mkdir(parents=True,exist_ok=True);write_hdf5(dest/'input.h5',arrays);write_json(dest/'problem.json',meta)
    return {'case':name,'family':kind,'tally_mode':mode,'seed':421900+index,'origin':'Author-created contact regression motivated by LAMMPS issue4219/PR4346, not an upstream numerical dataset.'}
if __name__=='__main__':
    cases=[('elastic','both','off'),('single','both','off'),('rotation','global','off'),('rotation','particle','off'),('rotation','both','off'),('polydisperse','both','off'),('permutation','both','off'),('cluster','both','off'),('normal','global','off'),('cluster','particle','off'),('noncontact','both','off'),('rotation','both','off')]
    write_json(Q/'author/data-evidence/cases.json',[make(i,*v) for i,v in enumerate(cases,1)])
