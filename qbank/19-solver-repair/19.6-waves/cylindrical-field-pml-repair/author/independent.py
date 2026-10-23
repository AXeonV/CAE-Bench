"""Independent finite-window complex DTFT and continuum corroboration; no FDTD solver."""
import numpy as np,math
def evaluate(trace,dt):
 values=trace[:,1::2]+1j*trace[:,2::2];times=np.repeat(trace[:,0,None],6,axis=1);times[:,3:]-=.5*dt;coefs=dt/np.sqrt(2*np.pi)*np.sum(values*np.exp(2j*np.pi*times),axis=0)
 return np.stack([coefs.real,coefs.imag],axis=1).reshape(12)
def continuum(parameters):
 r=parameters['radius'];z=parameters['half_height'];res=parameters['resolution'];a=parameters['source_amplitude'];c=z/math.hypot(r,z);cap=(4-3*c-c**3)/8;total=math.pi**3*a*a*50**2/(12*res*res)
 return np.array([cap,1-2*cap,cap])*total

def nearfield(parameters,point_rz):
 r,z=point_rz;x=np.array([r,0.,z]);distance=np.linalg.norm(x);normal=x/distance;k=2*np.pi;res=parameters['resolution'];m=parameters['mode'];amplitude=parameters['source_amplitude'];q=np.pi*amplitude*50/(4*res)*np.array([1.,1j*m,0.],dtype=complex);G=np.exp(1j*k*distance)/(4*np.pi*distance)
 E=G*((1j*k-1/distance-1j/(k*distance**2))*q+(-1j*k+3/distance+3j/(k*distance**2))*normal*np.dot(normal,q));H=G*(1j*k-1/distance)*np.cross(normal,q)
 return np.r_[E,H]
