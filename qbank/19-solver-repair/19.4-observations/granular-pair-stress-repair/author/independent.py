"""Independent all-pairs contact mechanics; author audit only, never the driver."""
import numpy as np
def solve(p):
    a=p.arrays;s={k:v['value'] for k,v in p.manifest['physics']['parameters'].items()};s['tally_mode']={0:'global',1:'particle',2:'both'}[s['tally_mode']];x=a['position'][0];r=a['diameter'][0,:,0]/2;mass=4*np.pi/3*a['material_density'][0,:,0]*r**3
    force=np.zeros_like(x);torque=np.zeros_like(x);virial=np.zeros((len(x),3,3))
    for i in range(len(x)):
        for j in range(i+1,len(x)):
            d=x[i]-x[j];dist=np.linalg.norm(d)
            if dist>=r[i]+r[j]:continue
            n=d/dist;dv=a['velocity'][0,i]-a['velocity'][0,j];vn=dv@n;meff=mass[i]*mass[j]/(mass[i]+mass[j]);fn=s['normal_stiffness']*(r[i]+r[j]-dist)-meff*s['normal_damping']*vn
            slip=dv-vn*n-np.cross(r[i]*a['angular_velocity'][0,i]+r[j]*a['angular_velocity'][0,j],n)
            tangential=-meff*s['tangential_damping']*slip;pair=fn*n+tangential
            assert fn>0 and np.linalg.norm(tangential)<=.8*s['friction']*fn+1e-12
            force[i]+=pair;force[j]-=pair
            torque[i]-=r[i]*np.cross(n,tangential);torque[j]-=r[j]*np.cross(n,tangential)
            w=np.outer(d,pair)/2;virial[i]+=w;virial[j]+=w
    select=lambda z:np.array([z[0,0],z[1,1],z[2,2],z[0,1],z[0,2],z[1,2]])
    out={'force':force[None],'torque':torque[None]}
    if s['tally_mode']!='global':out['particle_virial']=np.array([select(z) for z in virial])[None]
    if s['tally_mode']!='particle':out['pressure_tensor']=select(virial.sum(axis=0))[None,None]/s['box_length']**3
    return out
