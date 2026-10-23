"""Declare physical cases and fixed Eulerian probes; actual ASPECT produces references."""
from pathlib import Path
import json, math
import numpy as np
from caeoj.storage import write_hdf5

Q=Path(__file__).resolve().parents[1]
W=Q.parents[3]/'work/repair-22/aspect-6818/formal'
COMMON={'density':(1.,'kg/m^3'),'viscosity':(1.,'Pa*s'),'temperature':(300.,'K'),'time_step':(.25,'s'),'end_time':(1.,'s'),'refinement':(1,'1')}

def field(d,k):
 return {'array':k,'quantity':k,'unit':'m/s' if k=='velocity' else 'Pa','location':'probes','time_axis':'frames','dtype':'float64','kind':'vector' if k=='velocity' else 'scalar','component_shape':[d if k=='velocity' else 1],'components':['x','y','z'][:d] if k=='velocity' else ['value'],'value_kind':'point'}

def make(name,d,values,description):
 p={k:{'value':v,'unit':u} for k,(v,u) in COMMON.items()}
 units={'family':'1','width':'m','height':'m','depth':'m','rate_x':'1/s','rate_y':'1/s','velocity_x':'m/s','velocity_y':'m/s','peak_velocity':'m/s','inner_radius':'m','outer_radius':'m','angular_speed':'1/s','refinement':'1','end_time':'s'}
 for k,v in values.items():p[k]={'value':v,'unit':units[k]}
 v={k:a['value'] for k,a in p.items()};family=v['family'];points=[]
 if family==2:
  p['end_time']['value']=0.;v['end_time']=0.
  for r in [v['inner_radius']+f*(v['outer_radius']-v['inner_radius']) for f in [.2,.5,.8]]:
   for j in range(12):points.append([r*math.cos(j*math.pi/6),r*math.sin(j*math.pi/6)])
 else:
  for xf in [.1,.3,.5,.7,.9]:
   x=xf*v['width']
   for yf in ([.2,.5,.8] if d==3 else [0.]):
    y=yf*v.get('depth',0.)
    if family==0:
     shift=v['end_time']*(v['rate_x']*x+v.get('rate_y',0)*y)
     low=max(0,shift);high=v['height']+min(0,shift)
    else:low=0;high=v['height']+min(0,v['end_time']*v['rate_x']*(x-v['width']/2))
    for f in [.15,.5,.85]:
     z=low+f*(high-low)
     points.append([x,y,z] if d==3 else [x,z])
 times=np.array([0.]) if family==2 else np.arange(round(v['end_time']/v['time_step'])+1,dtype='float64')*v['time_step']
 arrays={'probe_ids':np.arange(len(points),dtype='int64')*7+3,'probe_coordinates':np.asarray(points,dtype='float64'),'times':times}
 p.pop('family')
 model=['deformed-tangential-parallel-v1', 'deformed-tangential-wedge-v1', 'deformed-tangential-annulus-v1'][family]
 p.pop('family')
 model=['deformed-tangential-parallel-v1', 'deformed-tangential-wedge-v1', 'deformed-tangential-annulus-v1'][family]
 m={'task':'deformed-tangential-boundary-repair','spatial_dimension':d,'data_file':'input.h5','physics':{'model':model,'parameters':p},'geometries':{},'meshes':{},'conditions':[],
 'locations':{'probes':{'kind':'points','ids':'probe_ids','coordinates':'probe_coordinates'}},'time_axes':{'frames':'times'},'fields':{},'outputs':{k:field(d,k) for k in ['velocity','pressure']}}
 path=W/'cases'/name;path.mkdir(parents=True,exist_ok=True);(path/'problem.json').write_text(json.dumps(m,indent=2));write_hdf5(path/'input.h5',arrays)
 return {'case':name,'family':family,'dimension':d,'description':description,'points':len(points),'frames':len(times),'origin':'author adaptation of actual ASPECT issue6818/PR6829; mathematical plug and rigid-rotation families independently derived; nonuniform family retains upstream boundary mechanism'}

if __name__=='__main__':
 defs=[
 ('01-parallel-public',2,dict(family=0,width=2.,height=1.,rate_x=.3,velocity_x=1.),'changing parallel planes with nonzero positive material flow'),
 ('02-annulus-public',2,dict(family=2,inner_radius=1.,outer_radius=2.,angular_speed=1.,refinement=3),'static curved manifold, inner driven rigid rotation'),
 ('03-parallel-negative',2,dict(family=0,width=1.5,height=1.2,rate_x=-.3,velocity_x=-.7),'negative tilt and reversed flow'),
 ('04-parallel-pivot',2,dict(family=0,width=.2,height=1.,rate_x=2.,velocity_x=.1,refinement=2),'current normal largest component changes during time evolution'),
 ('05-parallel-static',2,dict(family=0,width=1.5,height=.8,rate_x=0.,velocity_x=.8),'zero deformation regression in the active mesh pathway'),
 ('06-three-dimensional',3,dict(family=0,width=2.,depth=1.,height=1.,rate_x=.3,rate_y=.2,velocity_x=1.,velocity_y=-.4),'two horizontal material components and two boundary slopes'),
 ('07-three-dimensional-negative',3,dict(family=0,width=1.4,depth=1.,height=1.,rate_x=-.2,rate_y=.25,velocity_x=-.6,velocity_y=.7),'mixed slope signs and mixed flow directions'),
 ('08-three-dimensional-pivot',3,dict(family=0,width=.4,depth=.2,height=1.,rate_x=0.,rate_y=1.6,velocity_x=.2,velocity_y=.1),'normal component pivot in the second horizontal direction'),
 ('09-wedge-negative',2,dict(family=1,width=2.,height=.5,rate_x=-.1,peak_velocity=1.,refinement=6),'upstream-type nonuniform bottom drive with tilted top'),
 ('10-wedge-positive',2,dict(family=1,width=2.,height=.6,rate_x=.15,peak_velocity=-.8,refinement=6),'opposite top tilt and reversed nonuniform drive'),
 ('11-wedge-static',2,dict(family=1,width=2.,height=.5,rate_x=0.,peak_velocity=1.,refinement=6),'nonuniform flow regression without changing plane'),
 ('12-annulus-reverse',2,dict(family=2,inner_radius=.7,outer_radius=1.7,angular_speed=-.6,refinement=3),'changed curvature ratio and reversed rigid rotation')]
 catalog=[make(*x) for x in defs];(Q/'author/data-evidence').mkdir(parents=True,exist_ok=True)
 (Q/'author/data-evidence/cases.json').write_text(json.dumps(catalog,indent=2))
