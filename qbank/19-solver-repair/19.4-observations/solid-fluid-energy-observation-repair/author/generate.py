"""Generate twelve genuinely distinct solid/fluid observation experiments."""
import sys
from pathlib import Path
import numpy as np
from caeoj.storage import write_hdf5
from caeoj.validation import write_json
TASK=Path(__file__).resolve().parents[1];sys.path.insert(0,str(TASK/'extension'))
from caeoj_task_ext.energy_observation import inputs,outputs,parameter_units

def parameters(**changes):
 p=dict(length_x=1.,length_y=1.,length_z=1.,nx=4,ny=2,nz=2,density_solid=2.,density_fluid=5.,specific_heat_solid=3.,specific_heat_fluid=7.,conductivity_solid=1.,conductivity_fluid=1.,viscosity=1.,heat_transfer_coefficient=1.,temperature_reference=300.,inlet_speed=0.,source_constant=0.,source_radial=1.,source_axial=1.,source_time_slope=0.,dt=0.,step_count=0,velocity_order=2);p.update(changes);return p
T=[300,2,3,4,1,-.5,.75,-1,.5,.25];U=[.2,.1,.05,-.1,-.3,.05,.2,.1,.4,-.1,.05,-.05]
CASES=[]
for i,(coord,mode,names) in enumerate([(c,a,n) for c in ['cartesian','rz'] for a in ['normal','ad'] for n in ['standard','renamed']]):
 p=parameters();t=T.copy();u=U.copy()
 if coord=='rz':
  p.update(length_z=0.,nz=0,ny=4)
  for j in [3,6,8,9]:t[j]=0
  for j in [3,7,8,9,10,11]:u[j]=0
 if i==1:p.update(length_x=.4,length_y=.7,length_z=.2,density_solid=780.,density_fluid=997.,specific_heat_solid=460.,specific_heat_fluid=4180.);t=[310,-3,2,1,-.5,.25,-.1,.2,.3,-.2];u=[-.2,.1,.2,.1,.3,-.1,.1,0,-.4,.2,0,.1]
 if i==2:t=[295]+[0]*9 # exact zero thermal gradient control; retain moving flow.
 if i==3:u=[0]*12;p.update(source_constant=-2.,source_radial=4.,source_axial=-1.)
 if i==5:p.update(length_x=.2,length_y=.8,density_solid=31.,density_fluid=950.,specific_heat_solid=12.,specific_heat_fluid=4000.);u=[-v for v in u]
 if i==6:p.update(nx=8,ny=6);t[0]=275;t[1]=-6;t[2]=8
 if i==7:p.update(length_x=.6,length_y=.3,nx=6,ny=4);t[1]=0;t[2]=-4
 CASES.append((f'{i+1:02d}-{coord}-{mode}-{names}'+('-public' if i==0 else ''),f'explicit-{coord}-{mode}-{names}-v1',p,t,u))
for i,(transient,order) in enumerate([(False,1),(False,2),(True,1),(True,2)]):
 p=parameters(length_z=0.,nz=0,ny=4,specific_heat_solid=2.,specific_heat_fluid=4.,density_solid=3.,velocity_order=order,inlet_speed=1.)
 if transient:p.update(dt=.1 if order==1 else .15,step_count=3 if order==1 else 4,source_time_slope=0. if order==1 else .5)
 if order==2:p.update(length_x=.8,length_y=.6,temperature_reference=285.,conductivity_solid=1.5,conductivity_fluid=.75,inlet_speed=.4,heat_transfer_coefficient=2.)
 CASES.append((f'{i+9:02d}-rz-'+('transient' if transient else 'steady')+'-q'+str(order)+'q1'+('-public' if i==0 else ''),'coupled-rz-'+('transient' if transient else 'steady')+'-v1',p,[0]*10,[0]*12))

def main():
 records=[]
 for name,model,p,t,u in CASES:
  d=TASK/'cases'/name;d.mkdir(parents=True,exist_ok=True);times=np.arange(p['step_count']+1,dtype=float)*p['dt'] if 'transient' in model else np.array([0.])
  arrays={'experiment_ids':np.array([1],dtype='int64'),'initial_time':np.array([0.]),'times':times,'temperature_coefficients':np.array(t,dtype=float).reshape(1,1,10),'velocity_coefficients':np.array(u,dtype=float).reshape(1,1,12)}
  manifest={'task':'solid-fluid-energy-observation-repair','spatial_dimension':2 if '-rz-' in model else 3,'data_file':'input.h5','geometries':{},'meshes':{},'locations':{'experiments':{'kind':'entities','ids':'experiment_ids'}},'time_axes':{'initial':'initial_time','frames':'times'},'fields':inputs(),'outputs':outputs(),'physics':{'model':model,'parameters':{k:{'value':v,'unit':parameter_units()[k]} for k,v in p.items()}},'conditions':[]}
  write_json(d/'problem.json',manifest);write_hdf5(d/'input.h5',arrays);records.append({'case':name,'model':model,'frames':len(times),'public':name.endswith('public'),'source':'Author experiments using true issue22074/PR22075 observer and retained NS/HC formulations, not unmodified upstream inputs.'})
 write_json(TASK/'author/data-evidence/cases.json',records)
if __name__=='__main__':main()
