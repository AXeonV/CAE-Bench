"""Independent steady-state elimination and closed separable-flow integral; never reference producer."""
import math
import numpy as np
MULTI=False
def evaluate(a):
 n=len(a['state_ids']);out={k:[] for k in ['mass_fractions','coverages','pressure','density','speed']}
 if MULTI:out.update({k:[] for k in ['direct_concentrations','direct_density','direct_rates','surface_concentrations']})
 for i in range(n):
  scalar=lambda k:float(a[k][0,i,0])
  T,P,u,area,n0,ka,kd,kc,z=[scalar(k) for k in ['temperature','pressure','inlet_speed','surface_area_to_volume','site_density','adsorption_rate','desorption_rate','conversion_rate','distance']]
  x=a['inlet_mole_fractions'][0,i];ct=P/(8314.46261815324*T);C0=x[0]*ct;K=kd+kc
  if ka==0 or kc==0 or C0==0 or z==0:C=C0
  elif not MULTI:
   target=area/u*kc*n0*ka*z;lo=0.;hi=target/K
   for _ in range(100):
    v=(lo+hi)/2;res=ka*C0*(-math.expm1(-v))+K*v
    if res>target:hi=v
    else:lo=v
   C=C0*math.exp(-(lo+hi)/2)
  else:
   beta0=2*ka*n0*C0/K;s0=2/(1+math.sqrt(1+4*beta0));target=z*area*kc*ka*n0*n0/(u*K);lo=0.;hi=target
   for _ in range(100):
    v=(lo+hi)/2;s=2/(1+math.sqrt(1+4*beta0*math.exp(-v)))
    residual=v-math.log(s/s0)+(1/s0-1/s)+(1/(s0*s0)-1/(s*s))
    if residual>target:hi=v
    else:lo=v
   C=C0*math.exp(-(lo+hi)/2)
  if MULTI:
   beta=2*ka*n0*C/K;ts=2/(1+math.sqrt(1+4*beta));ta=beta*ts*ts
  else:ta=ka*C/(ka*C+K);ts=1-ta
  out['mass_fractions'].append([C/ct,x[1]+x[0]-C/ct,x[2]])
  out['coverages'].append([ts,ta]);out['pressure'].append([P]);out['density'].append([ct*15.999]);out['speed'].append([u])
  if MULTI:
   theta=a['initial_coverages'][0,i].copy()
   if scalar('coverage_mode')==0:theta/=theta.sum()
   cs=n0*theta/np.array([1,2]);direct=[ka*C0*cs[0]*cs[0],kd*cs[1],kc*cs[1]]
   out['direct_concentrations'].append(cs);out['direct_density'].append([cs@np.array([195.084,2*195.084+15.999])]);out['direct_rates'].append(direct);out['surface_concentrations'].append(n0*np.array([ts,ta])/np.array([1,2]))
 return {k:np.asarray(v,dtype='float64')[None] for k,v in out.items()}
