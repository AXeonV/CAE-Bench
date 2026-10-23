"""Closed steady concentration profiles, independent of the real Elmer assembly."""
import numpy as np
E=1.602176634e-19
KB=1.380649e-23
def reference(problem,discrete=False):
 m=problem.manifest;p=m['physics']['parameters'];bc={(c['variable'],c['location']):c['data']['value']['value'] for c in m['conditions']};mesh=problem.meshes['main']
 xy=np.array([mesh['node_coordinates'][int(tag)][:2] for tag in problem.arrays['node_ids']]);s=(xy[:,1]-xy[:,1].min())/np.ptp(xy[:,1]);t0,t1=bc['temperature','bottom'],bc['temperature','top'];phi0,phi1=bc['potential','bottom'],bc['potential','top'];c0=bc['concentration','bottom'];D=p['diffusivity']['value'];DT=p['soret_diffusivity']['value']
 if p['mode']['value']==0:
  a=p['ion_charge']['value']*E*(phi1-phi0)/(KB*t0)
  if discrete and a!=0:
   x=sorted(xy[:,0]);width=x[-1]-x[0];nx=1+sum(b-a>width*1e-8 for a,b in zip(x,x[1:]));nx-=1;ny=len(mesh['elements'][2])//nx;a=2*ny*np.arctanh(a/(2*ny))
  weight=s if a==0 else np.expm1(-a*s)/np.expm1(-a)
  c=c0+(bc['concentration','top']-c0)*weight
 else:c=c0-DT/D*(t1-t0)*s
 return {'concentration':c[None,:,None],'temperature':(t0+(t1-t0)*s)[None,:,None],'potential':(phi0+(phi1-phi0)*s)[None,:,None]}
