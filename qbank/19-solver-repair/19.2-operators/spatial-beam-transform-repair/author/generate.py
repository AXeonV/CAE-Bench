"""Build data declarations, with genuine library replay performed separately."""
import json
from pathlib import Path
import numpy as np
from caeoj.storage import write_hdf5
from caeoj.validation import write_json
ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT/'extension'))
from caeoj_task_ext.beam_repair import INPUTS,OUTPUTS,spec

def main():
    coverage=[('01-aligned-public','aligned'),('02-oblique-public','oblique'),('03-spatial-mixed','spatial'),
              ('04-axial','axial'),('05-torsion','torsion'),('06-shear-bending','shear'),('07-uniform-body-force','body'),
              ('08-symmetric-section','symmetric'),('09-negative-direction','negative'),('10-section-roll','roll')]
    cases=[]
    for seed,(case,mode) in enumerate(coverage,1):
        rng=np.random.default_rng(seed);n=4
        directions=np.array([[1.,0,0],[1,2,0],[2,-1,3],[-1,3,2]])
        if mode=='aligned':directions[:]=[1,0,0]
        elif mode=='negative':directions*=-1
        elif mode in ['spatial','body','roll']:directions=np.array([[2.,3,4],[-3,4,2],[5,-2,-4],[-4,-3,-1]])
        starts=rng.uniform(-2,2,(n,3));lengths=np.array([.5,1.2,3,8.])
        ends=starts+directions/np.linalg.norm(directions,axis=1)[:,None]*lengths[:,None]
        axis=np.tile([0.,1,0],(n,1))
        if mode=='roll':axis=np.array([[1.,-2,4],[-2,1,3],[3,1,1],[1,2,-3]])
        E=rng.uniform(50e9,210e9,n);nu=rng.uniform(.18,.35,n);A=rng.uniform(.003,.015,n)
        Iy=rng.uniform(1e-6,2e-5,n);Iz=Iy*np.array([1.,2.,.6,3.]);J=(Iy+Iz)*.6
        if mode=='symmetric':Iz=Iy.copy()
        Ay=A*.8;Az=A*.7
        if mode=='shear':Ay=A*.002;Az=A*.004
        rho=rng.uniform(1000,8000,n);acc=np.zeros((n,3));tip=rng.uniform(-100,100,(n,6))
        if mode=='axial':
            tip[:]=0;tip[:,:3]=directions/np.linalg.norm(directions,axis=1)[:,None]*rng.uniform(-100,100,n)[:,None]
        if mode=='torsion':
            tip[:]=0;tip[:,3:]=directions/np.linalg.norm(directions,axis=1)[:,None]*rng.uniform(-10,10,n)[:,None]
        if mode=='body':acc=rng.uniform(-9.81,9.81,(n,3));tip[:]=0
        arrays={'beam_ids':np.array([11,27,43,89],dtype='int64'),'times':np.array([0.]),'endpoints':np.c_[starts,ends][None],
                'section_axis':axis[None],'body_acceleration':acc[None],'tip_load':tip[None]}
        for name,val in zip(['young_modulus','poisson_ratio','area','inertia_y','inertia_z','torsion_constant','shear_area_y','shear_area_z','density'],[E,nu,A,Iy,Iz,J,Ay,Az,rho]):arrays[name]=val[None,:,None]
        manifest={'task':'spatial-beam-transform-repair','spatial_dimension':3,'data_file':'input.h5','geometries':{},'meshes':{},'conditions':[],
                  'physics':{'model':'linear-timoshenko-spatial-beam-v1','parameters':{}},'locations':{'beams':{'kind':'entities','ids':'beam_ids'}},
                  'time_axes':{'instant':'times'},'fields':{k:spec(k,v) for k,v in INPUTS.items()},'outputs':{k:spec(k,v,True) for k,v in OUTPUTS.items()}}
        d=ROOT/'cases'/case;d.mkdir(parents=True,exist_ok=True);write_hdf5(d/'input.h5',arrays);write_json(d/'problem.json',manifest)
        cases.append({'case':case,'mode':mode,'beams':n,'seed':seed,'origin':'author adaptation of genuine source issue; no upstream original trajectory claimed'})
    write_json(ROOT/'author/data-evidence/cases.json',cases)
if __name__=='__main__':main()

