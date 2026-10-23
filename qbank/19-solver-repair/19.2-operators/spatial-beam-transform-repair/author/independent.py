"""Independent linear Timoshenko beam matrix from virtual work.

Used only for validation; references must be produced by the actual library.
"""
import numpy as np


def frame(x, axis):
    t=np.asarray(x[3:])-np.asarray(x[:3]); L=np.linalg.norm(t); t=t/L
    n=np.asarray(axis,dtype=float); n=n-n.dot(t)*t; n/=np.linalg.norm(n)
    return L,np.vstack((t,n,np.cross(t,n)))


def independent(x, axis, material, acceleration):
    E,nu,A,Iy,Iz,J,Ay,Az,rho=material
    G=E/(2*(1+nu)); L,R=frame(x,axis)
    K=np.zeros((12,12)); f=np.zeros(12)
    for ids,c in [([0,6],E*A/L),([3,9],G*J/L)]:
        K[np.ix_(ids,ids)] += c*np.array([[1.,-1.],[-1.,1.]])
    for ids,I,As in [([1,5,7,11],Iz,Ay),([2,4,8,10],Iy,Az)]:
        phi=12*E*I/(G*As*L**2)
        K[np.ix_(ids,ids)] += E*I/(L**3*(1+phi))*np.array([
            [12,6*L,-12,6*L], [6*L,(4+phi)*L*L,-6*L,(2-phi)*L*L],
            [-12,-6*L,12,-6*L],[6*L,(2-phi)*L*L,-6*L,(4+phi)*L*L]])
    q=rho*A*(R@acceleration)
    f[[0,6]]=q[0]*L/2;f[[1,7]]=q[1]*L/2;f[[2,8]]=q[2]*L/2
    f[[5,11]]=np.array([1,-1])*q[1]*L**2/12
    f[[4,10]]=np.array([1,-1])*q[2]*L**2/12
    D=np.diag([1.,-1.,1.]); Q=np.zeros((12,12))
    for start in [0,6]:Q[start:start+3,start:start+3]=R
    for start in [3,9]:Q[start:start+3,start:start+3]=D@R
    return Q.T@K@Q,Q.T@f


def closed_tip(x,axis,material,normalized_load):
    E,nu,A,Iy,Iz,J,Ay,Az,rho=material;G=E/(2*(1+nu));L,R=frame(x,axis)
    force=R@normalized_load[:3];moment=R@(normalized_load[3:]*L)
    Fx,Fy,Fz=force;Mx,My,Mz=moment
    u=np.array([Fx*L/(E*A),Fy*(L**3/(3*E*Iz)+L/(G*Ay))+Mz*L**2/(2*E*Iz),Fz*(L**3/(3*E*Iy)+L/(G*Az))-My*L**2/(2*E*Iy)])
    theta=np.array([Mx*L/(G*J),-Fz*L**2/(2*E*Iy)+My*L/(E*Iy),Fy*L**2/(2*E*Iz)+Mz*L/(E*Iz)])
    return np.r_[R.T@u,L*(R.T@theta)]
