"""Evaluate sourced separation-of-variables / characteristic / entropy formulas.

This module evaluates closed mathematical representations, not a new PDE time
marcher. Formula derivations and sources are recorded in author/README.md.
Independent original solver replays and refinement evidence are kept separately.
"""
import numpy as np
from scipy.integrate import quad, solve_ivp
from scipy.optimize import brentq
from scipy.special import erf

def pulse_heat(x,L,nu,t,modes):
    n=np.arange(1,modes+1)[:,None];k=n*np.pi/L
    coef=2/L*(np.cos(k*.5)-np.cos(k*1))/k
    return (coef*np.exp(-nu*k*k*t)*np.sin(k*x[None,:])).sum(axis=0)

def sinh_ratio(k,a,L):
    return np.exp(k*(a-L))*(-np.expm1(-2*k*a))/(-np.expm1(-2*k*L))

def sod(x,t):
    # Exact ideal-gas Riemann solution: Toro, Riemann Solvers and Numerical
    # Methods for Fluid Dynamics, section 4.3; no wall wave reaches this domain.
    g=1.4;rL,rR,pL,pR=1.,.125,1.,.1
    cL,cR=np.sqrt(g*pL/rL),np.sqrt(g*pR/rR)
    def wave(p,r,p0,c):
        if p>p0:return (p-p0)*np.sqrt(2/((g+1)*r)/(p+(g-1)/(g+1)*p0))
        return 2*c/(g-1)*((p/p0)**((g-1)/(2*g))-1)
    p=brentq(lambda p:wave(p,rL,pL,cL)+wave(p,rR,pR,cR),.01,2,xtol=1e-14)
    u=(wave(p,rR,pR,cR)-wave(p,rL,pL,cL))/2
    rhoLs=rL*(p/pL)**(1/g)
    rhoRs=rR*((p/pR)+(g-1)/(g+1))/((g-1)/(g+1)*(p/pR)+1)
    cs=cL*(p/pL)**((g-1)/(2*g))
    shock=cR*np.sqrt((g+1)/(2*g)*p/pR+(g-1)/(2*g))
    xi=x/t;rho=np.empty_like(x);vel=np.empty_like(x);pres=np.empty_like(x)
    for j,z in enumerate(xi):
        if z < -cL:r,v,P=rL,0.,pL
        elif z<u-cs:
            v=2/(g+1)*(cL+z);c=2/(g+1)*(cL-(g-1)*z/2)
            r=rL*(c/cL)**(2/(g-1));P=pL*(c/cL)**(2*g/(g-1))
        elif z<u:r,v,P=rhoLs,u,p
        elif z<shock:r,v,P=rhoRs,u,p
        else:r,v,P=rR,0.,pR
        rho[j],vel[j],pres[j]=r,v,P
    return dict(rho=rho,u=vel,E=pres/((g-1)*rho)+vel**2/2)

def entropy_periodic(x,t,density=2048):
    # Lax-Oleinik / Hopf-Lax minimizer. Account for the nonzero mean by the
    # lifted periodic primitive, never force its primitive to be periodic.
    L=2*np.pi
    def u0(y):z=y%L;return np.sin(z)+.5*np.sin(.5*z)
    def potential(y):
        n=np.floor(y/L);z=y-n*L
        return 2*n+2-np.cos(z)-np.cos(.5*z)
    result=[]
    for z in x:
        grid=np.linspace(z-2*t,z+2*t,density+1)
        f=grid+t*u0(grid)-z
        roots=[brentq(lambda y:y+t*u0(y)-z,a,b,xtol=1e-14)
               for a,b,fa,fb in zip(grid[:-1],grid[1:],f[:-1],f[1:]) if fa*fb<0]
        roots += list(grid[f==0])
        values=np.array([(z-y)**2/(2*t)+potential(y) for y in roots])
        if not len(values):raise ValueError('Missing Hopf-Lax stationary point')
        y=roots[int(np.argmin(values))];result.append((z-y)/t)
    return np.array(result)

def entropy_patch(x,y,t):
    # Along each fixed x-y diagonal, the scalar law is 1D Burgers with a finite
    # height-2 pulse on height-1 background. Hopf-Lax for its piecewise-linear
    # primitive: minimizers are stationary points in three segments or breaks.
    s=(x+y)/2;z=np.abs(x-y);a=.5+z/2;b=1-z/2
    width=np.maximum(0,b-a);b=a+width
    candidates=np.stack((np.minimum(s-t,a),np.clip(s-2*t,a,b),np.maximum(s-t,b),a,b))
    V=candidates+np.clip(candidates-a,0,width)
    action=(s-candidates)**2/(2*t)+V
    # Equal minima select the smaller footpoint? Right trace of shock selects
    # larger footpoint, so reverse before argmin to break exact ties correctly.
    rev=np.flip(candidates,axis=0);rv=np.flip(action,axis=0)
    j=np.argmin(rv,axis=0)
    foot=np.take_along_axis(rev,j[None,:],axis=0)[0]
    return (s-foot)/t

def gaussian_modes(L,origin,center,sigma,modes):
    n=np.arange(1,modes+1);k=n*np.pi/L
    # Exact integral of Gaussian times sine on a finite interval. Use stable
    # real Gaussian quadrature here because complex erf can overflow at high k.
    return np.array([2/L*quad(lambda z:np.exp(-.5*((z-center)/sigma)**2)*np.sin(K*(z-origin)),
                            origin,origin+L,epsabs=2e-13,limit=300)[0] for K in k])

def evaluate(index,coordinates,modes=256):
    x=coordinates[:,0];y=coordinates[:,1] if coordinates.shape[1]>1 else None
    if index==1:
        t=.14*np.pi;nu=.07;L=2*np.pi;shift=(x-4*t)%L
        delta=shift[:,None]-L*np.arange(-4,6)[None,:]
        a=-delta**2/(4*nu*(1+t));a-=a.max(axis=1,keepdims=True)
        w=np.exp(a)
        return dict(u=4+(w*delta).sum(axis=1)/(w.sum(axis=1)*(1+t)))
    if index==2:return dict(u=1+pulse_heat(x,2,.3,.0333,modes))
    if index==3:return sod(x,.25)
    if index==4:
        # Periodic Gaussian convolution / heat semigroup. Images beyond +/-4
        # have a rigorous Gaussian tail at this time and length.
        t=10.;den=1+4*.0005*t
        delta=x[:,None]-t+10*np.arange(-4,5)[None,:]
        # Original finite-interval Gaussian differs from its periodic image
        # sum only by the explicitly bounded tails beyond |x|=5 (<1.4e-11).
        return dict(u=np.sum(np.exp(-delta**2/den),axis=1)/np.sqrt(den))
    if index==5:return dict(u=entropy_periodic(x,5.,modes*8))
    if index in (7,9):
        q=entropy_patch(x,y,.32 if index==7 else .4);return dict(u=q,v=q.copy())
    if index==8:return dict(u=1+pulse_heat(x,2,.05,.3777,modes)*pulse_heat(y,2,.05,.3777,modes))
    if index==10:
        n=np.arange(1,modes+1,2)[:,None];k=n*np.pi
        return dict(p=.25*x+np.sum(-4/k**2*np.cos(k*y)*sinh_ratio(k,x,2),axis=0))
    if index==11:
        def indicator(z):return np.where((z>.5)&(z<1),1.,np.where((z==.5)|(z==1),.5,0.))
        return dict(u=1+indicator(x-.5)*indicator(y-.5))
    if index==13:
        n=np.arange(1,modes+1,2)[:,None];k=n*np.pi/2
        return dict(u=y*(2-y)/(.2)-np.sum(4*4/(.1*np.pi**3*n**3)*np.sin(k*y)*np.exp(-.1*k*k*5),axis=0))
    if index==14:
        n=np.arange(1,modes+1);kx=n*np.pi/2;ky=n*np.pi
        c=[]
        for cx,cy in ((.5,.25),(1.5,.75)):
            c.append(100*np.outer(gaussian_modes(2,0,cx,.05,modes),gaussian_modes(1,0,cy,.05,modes)))
        coeff=-(c[0]-c[1])/(kx[:,None]**2+ky[None,:]**2)
        return dict(p=np.einsum('in,ij,jn->n',np.sin(kx[:,None]*x),coeff,np.sin(ky[:,None]*y),optimize=True))
    if index==15:
        n=np.arange(1,modes+1,2)[:,None]
        k=n*np.pi/4;h=n*np.pi/5
        T=np.sum(4/(n*np.pi)*np.sin(k*y)*(10*sinh_ratio(k,5-x,5)+40*sinh_ratio(k,x,5)),axis=0)
        T+=np.sum(4*20/(n*np.pi)*np.sin(h*x)*sinh_ratio(h,4-y,4),axis=0)
        return dict(T=T)
    if index==16:
        n=np.arange(1,modes+1);k=n*np.pi/2
        c=gaussian_modes(2,-1,0,.1,modes);lam=k[:,None]**2+k[None,:]**2
        coeff=200*np.outer(c,c)*(np.exp(-lam*3)-np.expm1(-lam*3)/lam)
        return dict(T=1+np.einsum('in,ij,jn->n',np.sin(k[:,None]*(x+1)),coeff,np.sin(k[:,None]*(y+1)),optimize=True))
    if index==17:
        def viscosity(z):
            d=min(z,2-z)
            return .5/395*(1+np.sqrt(1+(.426*395)**2*(2*d-d*d)**2*(3-4*d+2*d*d)**2*(-np.expm1(-395*d/25.4))**2/9))
        u=np.array([quad(lambda z:(1-z)/viscosity(z),0,min(Y,2-Y),epsabs=2e-11,epsrel=1e-12,limit=300)[0] for Y in x])
        return dict(u=u)
    if index==24:
        eps=1e-7
        def fun(r,y):return (y[1],-2*y[1]/r-y[0]**3)
        def zero(r,y):return y[0]
        zero.terminal=True;zero.direction=-1
        solution=solve_ivp(fun,(eps,8),(1-eps**2/6,-eps/3),method='DOP853',rtol=2e-13,atol=2e-14,dense_output=True,events=zero,max_step=.02)
        R=solution.t_events[0][0]
        f=R*solution.sol(np.maximum(R*x,eps))[0];f[x==0]=R;f[x==1]=0
        return dict(f=f)
    raise KeyError(index)
