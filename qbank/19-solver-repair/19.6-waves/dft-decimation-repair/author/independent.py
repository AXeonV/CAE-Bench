"""Mathematical DTFT of actual time samples; not a Maxwell field solver."""
import numpy as np
def expected_stride(parameters,frequencies,dt):
 k=parameters['decimation']
 if k:return k
 if parameters['chi2']!=0 or parameters['chi3']!=0:return 1
 width=np.sqrt(-2*np.log(1e-7))/(np.pi*parameters['envelope_width'])
 return max(1,int(np.floor(1/(dt*(np.max(np.abs(frequencies))+abs(parameters['source_frequency'])+width/2)))))
def evaluate(trace,frequencies,parameters):
 dt=.5/parameters['resolution'];stride=expected_stride(parameters,frequencies,dt);steps=np.arange(1,len(trace)+1);selected=steps%stride==0;times=trace[selected,0];out=np.empty((len(frequencies),4))
 for k,offset in [(0,0.),(1,-dt/2)]:
  values=np.exp(2j*np.pi*frequencies[:,None]*(times[None,:]+offset))@trace[selected,k+1]*(stride*dt/np.sqrt(2*np.pi));out[:,2*k]=values.real;out[:,2*k+1]=values.imag
 return out,stride
