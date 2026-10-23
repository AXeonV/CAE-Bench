"""Generate local phase states and independent heat/geometry checks."""
import argparse
import importlib.util
from pathlib import Path
import numpy as np
from caeoj.storage import write_hdf5
from caeoj.validation import write_json
TASK=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('hys_contract',TASK/'extension/caeoj_task_ext/hysteresis.py');contract=importlib.util.module_from_spec(spec);spec.loader.exec_module(contract)


def make_case(root,name,parameters,mode,seed):
    rng=np.random.default_rng(seed);n=6
    arrays={'state_ids':np.array([7,31,88,201,449,801],dtype='int64'),'times':np.array([0.],dtype='float64')}
    for name0 in ['length_n','length_p','length_s','length_cn','length_cp']:arrays[name0]=rng.uniform(1e-5,2e-4,(1,n,1))
    arrays['area']=rng.uniform(.01,.2,(1,n,1));arrays['volume']=rng.uniform(1e-5,1e-4,(1,n,1));arrays['temperature']=rng.uniform(260,380,(1,n,1))
    heat={}
    for d in ['n','p']:
        phases=parameters['phases_'+d]
        current=rng.uniform(-1e5,1e5,(n,phases))
        eta=np.sign(current)*rng.uniform(.01,.15,(n,phases));entropy=rng.uniform(-1e-4,1e-4,(n,phases))
        equilibrium=rng.uniform(.05,.3,(n,phases)) if d=='n' else rng.uniform(3,4.5,(n,phases))
        gap=np.sign(current)*rng.uniform(.01,.12,(n,phases))
        if mode=='negative-instant':gap*=-1
        if mode=='zero-current':current[:]=0
        if mode=='no-gap':gap[:]=0
        if mode=='no-reaction':eta[:]=0;entropy[:]=0
        if mode=='cycle':
            current=np.full((n,phases),20000.);current[1::2]*=-1
            gap=np.full((n,phases),.08);gap[1::2]*=-1
            eta[:]=0;entropy[:]=0;equilibrium[:]=.2 if d=='n' else 4.
            for key in ['area','volume','temperature','length_n','length_p','length_s','length_cn','length_cp']:arrays[key][:]=arrays[key][0,0,0]
            if d=='p':
                current*=-float(arrays['length_n'][0,0,0]/arrays['length_p'][0,0,0])
                gap=np.sign(current)*.08
        for k in range(phases):
            if not (parameters['mask_'+d]>>k)&1:gap[:,k]=0
        ocp=equilibrium+gap
        for key,value in [('current',current),('eta',eta),('entropy',entropy),('equilibrium',equilibrium),('ocp',ocp)]:arrays[key+'_'+d]=value[None]
        heat[d]=np.sum(current*(eta+arrays['temperature'][0]*entropy+gap),axis=1)[None,:,None]
    if mode=='scales':
        arrays['area']=np.geomspace(1e-4,10,n)[None,:,None];arrays['volume']=np.geomspace(1e-10,1,n)[None,:,None]
        arrays['length_n']=np.geomspace(1e-6,1e-2,n)[None,:,None];arrays['length_p']=arrays['length_n'][:,:,::-1].copy()
    area_heat=arrays['length_n']*heat['n']+arrays['length_p']*heat['p'];power=parameters['pairs']*arrays['area']*area_heat
    independent={'heat_negative':heat['n'].tolist(),'heat_positive':heat['p'].tolist(),'area_heat':area_heat.tolist(),'cell_heat':power.tolist(),'volume_heat':(power/arrays['volume']).tolist()}
    fields,outputs=contract.declarations(parameters)
    manifest={'task':TASK.name,'spatial_dimension':1,'data_file':'input.h5','geometries':{},'meshes':{},'conditions':[],
              'physics':{'model':'ocp-hysteresis-heat-v1','parameters':{k:{'value':v,'unit':'1'} for k,v in parameters.items()}},
              'locations':{'states':{'kind':'entities','ids':'state_ids'}},'time_axes':{'instant':'times'},
              'fields':{k:contract.field_spec(k,v) for k,v in fields.items()},'outputs':{k:contract.field_spec(k,v,True) for k,v in outputs.items()}}
    target=root/'cases'/name;target.mkdir(parents=True,exist_ok=True);write_json(target/'problem.json',manifest);write_hdf5(target/'input.h5',arrays)
    (root/'independent-checks').mkdir(exist_ok=True);write_json(root/'independent-checks'/(name+'.json'),independent)
    return {'case':name,'parameters':parameters,'mode':mode,'seed':seed,'states':n,'origin':'author local-state adaptation of PyBaMM#3867; not an integrated battery experiment'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    cases=[('01-both-hysteretic-public',1,1,1,1,1,'mixed'),('02-no-hysteresis-public',1,1,0,0,1,'mixed'),
           ('03-negative-only',1,1,1,0,2,'mixed'),('04-positive-only',1,1,0,1,3,'mixed'),
           ('05-two-negative-phases',2,1,3,1,2,'mixed'),('06-two-positive-phases',1,2,1,3,4,'mixed'),
           ('07-mixed-phase-switches',2,2,1,2,3,'mixed'),('08-all-phases',2,2,3,3,2,'mixed'),
           ('09-zero-current',2,2,3,3,1,'zero-current'),('10-zero-gap',2,1,3,1,2,'no-gap'),
           ('11-isolated-hysteresis',1,2,1,3,1,'no-reaction'),('12-negative-instant',2,2,3,1,2,'negative-instant'),
           ('13-loop-states',1,1,1,1,2,'cycle'),('14-geometry-scales',2,2,3,3,32,'scales')]
    catalog=[make_case(args.output,name,dict(zip(['phases_n','phases_p','mask_n','mask_p','pairs'],[pn,pp,mn,mp,pairs])),mode,190403+i) for i,(name,pn,pp,mn,mp,pairs,mode) in enumerate(cases)]
    write_json(args.output/'catalog.json',catalog)
