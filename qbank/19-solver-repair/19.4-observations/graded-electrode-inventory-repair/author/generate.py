"""Generate FV states; independent sums are checks, not published references."""
import argparse
import importlib.util
from pathlib import Path
import numpy as np
from caeoj.storage import write_hdf5
from caeoj.validation import write_json
TASK=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('inventory_declarations',TASK/'extension/caeoj_task_ext/inventory.py')
contract=importlib.util.module_from_spec(spec);spec.loader.exec_module(contract)


def make_case(root,name,counts,mode,seed):
    rng=np.random.default_rng(seed);n=6
    arrays={'state_ids':np.array([3,17,47,81,251,901],dtype='int64'),'times':np.array([0.],dtype='float64')}
    checks={}
    for d in ['n','p']:
        x=counts['x_count_'+d];r=counts['r_count_'+d]
        xx=(np.arange(x)+.5)/x;rr=(np.arange(r)+.5)/r
        cmax=rng.uniform(15000,60000,(n,1));eps=rng.uniform(.45,.65,(n,1))+rng.uniform(.05,.25,(n,1))*(xx-.5)
        profile=.45+.2*(xx[None,:,None]-.5)+.12*(rr[None,None,:]-.5)
        profile=np.broadcast_to(profile,(n,x,r)).copy()+rng.uniform(-.1,.1,(n,1,1))
        if mode=='anti' or (mode=='opposite' and d=='p'):profile=1-profile
        if mode=='random':profile=rng.uniform(.1,.9,(n,x,r));eps=rng.uniform(.1,.9,(n,x))
        if mode=='constant-epsilon':eps=np.repeat(eps[:,:1],x,axis=1)
        if mode=='constant-concentration':profile[:]=rng.uniform(.1,.9,(n,1,1))
        if mode=='radial-only':profile[:]=.4+.2*rr[None,None,:]
        if mode=='zero':profile[:]=0
        if mode=='full':profile[:]=1
        concentration=profile*cmax[:,:,None]
        arrays['epsilon_'+d]=eps[None]
        arrays['concentration_'+d]=concentration.reshape(n,x*r)[None]
        arrays['cmax_'+d]=cmax[None]
        arrays['thickness_'+d]=rng.uniform(4e-5,2e-4,(1,n,1))
        if mode=='scales':arrays['thickness_'+d]=np.geomspace(1e-6,1e-2,n)[None,:,None]
        shell=np.diff(np.linspace(0,1,r+1)**3)
        radial=np.sum(concentration*shell[None,None,:],axis=2)
        weighted=np.sum(radial*eps,axis=1)/x
        volume=weighted/np.mean(eps,axis=1)
        checks['radial_'+d]=radial[None].tolist()
        checks['volume_'+d]=volume[None,:,None].tolist()
        checks['stoichiometry_'+d]=(volume/cmax[:,0])[None,:,None].tolist()
        checks['inventory_'+d]=weighted[None,:,None]*arrays['thickness_'+d]
    arrays['area']=rng.uniform(.02,.3,(1,n,1))
    if mode=='scales':arrays['area']=np.geomspace(1e-4,10,n)[None,:,None]
    for d in ['n','p']:checks['inventory_'+d]=(checks['inventory_'+d]*arrays['area']).tolist()
    checks['total_inventory']=(np.asarray(checks['inventory_n'])+np.asarray(checks['inventory_p'])).tolist()
    fields,outputs=contract.declarations(counts)
    manifest={'task':TASK.name,'spatial_dimension':1,'data_file':'input.h5','geometries':{},'meshes':{},'conditions':[],
              'physics':{'model':'graded-electrode-inventory-v1','parameters':{k:{'value':v,'unit':'1'} for k,v in counts.items()}},
              'locations':{'states':{'kind':'entities','ids':'state_ids'}},'time_axes':{'instant':'times'},
              'fields':{k:contract.field_spec(k,v) for k,v in fields.items()},'outputs':{k:contract.field_spec(k,v,True) for k,v in outputs.items()}}
    target=root/'cases'/name;target.mkdir(parents=True,exist_ok=True)
    write_json(target/'problem.json',manifest);write_hdf5(target/'input.h5',arrays)
    (root/'independent-checks').mkdir(exist_ok=True);write_json(root/'independent-checks'/(name+'.json'),checks)
    return {'case':name,'mode':mode,'counts':counts,'seed':seed,'states':n,'origin':'author FV state adaptation of PyBaMM#5810; not an issue time trajectory'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    cases=[('01-correlated-public',5,7,6,4,'correlated'),('02-constant-public',4,6,4,5,'constant-epsilon'),
           ('03-anticorrelated',7,5,8,6,'anti'),('04-opposite-electrodes',8,9,7,6,'opposite'),
           ('05-uniform-concentration',6,8,5,7,'constant-concentration'),('06-radial-only',5,7,11,9,'radial-only'),
           ('07-zero',3,4,3,5,'zero'),('08-saturated',8,9,5,4,'full'),
           ('09-random',11,7,9,13,'random'),('10-coarse',3,3,3,3,'correlated'),
           ('11-fine',32,32,32,32,'random'),('12-mixed-resolution',3,32,32,3,'anti'),
           ('13-scales',9,11,7,5,'scales'),('14-random-geometry',17,19,11,13,'random')]
    catalog=[make_case(args.output,name,dict(zip(['x_count_n','x_count_p','r_count_n','r_count_p'],[xn,xp,rn,rp])),mode,190401+i) for i,(name,xn,xp,rn,rp,mode) in enumerate(cases)]
    write_json(args.output/'catalog.json',catalog)
