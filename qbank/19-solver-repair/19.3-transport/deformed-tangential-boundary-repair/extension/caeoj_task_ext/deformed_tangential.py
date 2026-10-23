"""Validate fixed Eulerian input declarations; never compute or modify results."""
import math
import numpy as np
from caeoj.validation import issue

def check(problem,errors):
 m,a=problem.manifest,problem.arrays
 def fail(path,expected,actual):errors.append(issue('E_DEFORMED_TANGENTIAL',path,expected,str(actual),'Outside public DATA contract.'))
 if m.get('task')!='deformed-tangential-boundary-repair' or m['meshes'] or m['geometries'] or m['conditions'] or m['fields']:
  fail('$','declared task with native geometry and no input fields',m.get('task'))
 if m['locations']!={'probes':{'kind':'points','ids':'probe_ids','coordinates':'probe_coordinates'}} or not 1<=len(a.get('probe_ids',[]))<=128:
  fail('$.locations','1..128 fixed Cartesian points',m['locations']);return
 if m['time_axes']!={'frames':'times'}:fail('$.time_axes','frames=times',m['time_axes']);return
 d=m['spatial_dimension']; raw=m['physics']['parameters']
 common={'density':'kg/m^3','viscosity':'Pa*s','temperature':'K','refinement':'1','time_step':'s','end_time':'s'}
 try:p={k:v['value'] for k,v in raw.items()};family={'deformed-tangential-parallel-v1': 0, 'deformed-tangential-wedge-v1': 1, 'deformed-tangential-annulus-v1': 2}[m['physics']['model']]
 except (KeyError,TypeError):fail('$.physics.parameters','documented scalar parameters',raw);return
 units=dict(common)
 if family==0:
  units.update(width='m',height='m',rate_x='1/s',velocity_x='m/s')
  if d==3:units.update(depth='m',rate_y='1/s',velocity_y='m/s')
 elif family==1:units.update(width='m',height='m',rate_x='1/s',peak_velocity='m/s')
 else:units.update(inner_radius='m',outer_radius='m',angular_speed='1/s')
 if d not in (2,3) or (family!=0 and d!=2) or set(raw)!=set(units):fail('$.physics.parameters','exact per-family parameters/dimension',list(raw));return
 for k,u in units.items():
  if raw[k].get('unit')!=u:fail('$.physics.parameters.'+k,'unit '+u,raw[k])
 def bound(k,lo,hi):
  if not lo<=p[k]<=hi:fail('$.physics.parameters.'+k,f'{lo}..{hi}',p[k])
 for k,lo,hi in [('density',.1,10),('viscosity',.1,10),('temperature',200,1000),('time_step',.05,1)]:bound(k,lo,hi)
 limit=4 if family==2 else (2 if d==3 else 6)
 if type(p['refinement']) is not int or not 1<=p['refinement']<=limit:fail('$.physics.parameters.refinement',f'integer1..{limit}',p['refinement'])
 if family==2:
  if p['end_time']!=0:fail('$.physics.parameters.end_time','0 for static annulus',p['end_time'])
  for k in ['inner_radius','outer_radius']:bound(k,.5,2.5)
  if not .5<=p['outer_radius']-p['inner_radius']<=1.5:fail('$.physics.parameters','radius difference .5..1.5',p)
  bound('angular_speed',-1,1);expected=np.array([0.])
 else:
  bound('end_time',.1,2)
  steps=p['end_time']/p['time_step']
  if not 1<=round(steps)<=8 or abs(steps-round(steps))>1e-12:fail('$.physics.parameters','1..8 equal time steps',steps);return
  expected=np.arange(round(steps)+1,dtype='float64')*p['time_step']
  bound('width',.2 if family==0 else .5,2);bound('height',.5 if family==0 else .4,1.2 if family==0 else 1)
  bound('rate_x',-2 if family==0 else -.2,2 if family==0 else .2)
  if family==0:
   bound('velocity_x',-1,1)
   if d==3:bound('depth',.2,1);bound('rate_y',-2,2);bound('velocity_y',-1,1)
   if p['end_time']*(abs(p['rate_x'])*p['width']+abs(p.get('rate_y',0))*p.get('depth',0))>.8*p['height']+1e-12:fail('$.physics.parameters','bounded parallel deformation',p)
  else:
   bound('peak_velocity',-1,1)
   if p['end_time']*abs(p['rate_x'])*p['width']/2>.3*p['height']+1e-12:fail('$.physics.parameters','bounded top deformation',p)
 if np.shape(a.get('times'))!=expected.shape or not np.allclose(a.get('times'),expected,rtol=0,atol=1e-12):fail('$.time_axes.frames','declared equal physical times',a.get('times'))
 if set(m['outputs'])!={'velocity','pressure'}:fail('$.outputs','velocity and pressure',m['outputs']);return
 for k in ['velocity','pressure']:
  spec={'array':k,'quantity':k,'unit':'m/s' if k=='velocity' else 'Pa','location':'probes','time_axis':'frames','dtype':'float64','kind':'vector' if k=='velocity' else 'scalar','component_shape':[d if k=='velocity' else 1],'components':['x','y','z'][:d] if k=='velocity' else ['value'],'value_kind':'point'}
  if m['outputs'][k]!=spec:fail('$.outputs.'+k,str(spec),m['outputs'][k])
 points=a['probe_coordinates']
 if family==2:
  radius=np.linalg.norm(points,axis=1);margin=1e-4*min(p['inner_radius'],p['outer_radius']-p['inner_radius'])
  inside=(radius-p['inner_radius']>=margin)&(p['outer_radius']-radius>=margin)
 else:
  dims=[p['width'],p['height']]+([p['depth']] if d==3 else []);margin=1e-4*min(dims)
  inside=(points[:,0]>=margin)&(points[:,0]<=p['width']-margin)
  if d==3:inside&=(points[:,1]>=margin)&(points[:,1]<=p['depth']-margin)
  for t in [0.,p['end_time']]:
   slope=np.array([p['rate_x']*t]+([p.get('rate_y',0)*t] if d==3 else []));norm=math.sqrt(1+float(slope@slope))
   if family==0:
    shift=points[:,:d-1]@slope;inside&=(points[:,-1]-shift>=margin*norm)&(p['height']+shift-points[:,-1]>=margin*norm)
   else:
    top=p['height']+t*p['rate_x']*(points[:,0]-p['width']/2);inside&=(points[:,1]>=margin)&(top-points[:,1]>=margin*norm)
 if not inside.all():fail('$.locations.probes','strictly interior for full time interval',np.flatnonzero(~inside).tolist())
