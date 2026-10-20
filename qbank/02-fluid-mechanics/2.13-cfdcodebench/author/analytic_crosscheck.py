"""Independent mathematical representations of the fixed analytic cases.

Image heat kernels versus sine coefficients; periodic convolution versus
Fourier integration; explicit rarefaction/shock interaction versus Hopf-Lax.
These checks do not turn a source solver replay into independent certification.
"""
import json
import numpy as np
from scipy.special import erf
from scipy.integrate import quad
from numpy.polynomial.legendre import leggauss
from catalog import WORK,catalog
from analytic import evaluate
from build_local import observation_grid,differences

def image_pulse(x,L,nu,t,images):
    width=np.sqrt(4*nu*t);value=np.zeros_like(x)
    for j in range(-images,images+1):
        value+=.5*(erf((1-x+2*j*L)/width)-erf((.5-x+2*j*L)/width)
                   -erf((1+x+2*j*L)/width)+erf((.5+x+2*j*L)/width))
    return value

def pulse_entropy_piecewise(x,y,t):
    z=(x+y)/2-t;delta=np.abs(x-y);a=.5+delta/2;b=1-delta/2
    width=np.maximum(b-a,0);last=np.where(t<=2*width,b+t/2,a+np.sqrt(2*width*t))
    q=1+np.where((z>=a)&(z<last),np.minimum((z-a)/t,1),0)
    return q

def main():
    allcases={c['index']:c for c in catalog()};rows={}
    for i in (1,2,4,7,8,9,11,13):
        c=allcases[i];xy,w=observation_grid(c);x=xy[:,0];y=xy[:,1] if c['dimension']==2 else None
        expected=evaluate(i,xy)
        if i==1:
            # Original author's explicit two-image Cole-Hopf expression, with
            # the same .14*pi target (the missing periodic images have tails).
            t=.14*np.pi;nu=.07;delta=np.column_stack((x-4*t,x-4*t-2*np.pi))
            g=np.exp(-delta**2/(4*nu*(1+t)))
            cross=dict(u=4+(g*delta).sum(axis=1)/((1+t)*g.sum(axis=1)))
        elif i==2:cross=dict(u=1+image_pulse(x,2,.3,.0333,8))
        elif i==4:
            L=10.;n=np.arange(-128,129);k=2*np.pi*n/L
            coeff=np.array([quad(lambda z:np.exp(-z*z)*np.cos(K*z),-5,5,epsabs=1e-13,limit=200)[0]/L for K in k])
            value=(np.exp(1j*(x[:,None]-10)*k)*coeff*np.exp(-.0005*k*k*10)).sum(axis=1).real
            cross=dict(u=value)
        elif i in (7,9):
            q=pulse_entropy_piecewise(x,y,.32 if i==7 else .4);cross=dict(u=q,v=q.copy())
        elif i==8:cross=dict(u=1+image_pulse(x,2,.05,.3777,8)*image_pulse(y,2,.05,.3777,8))
        elif i==11:
            # Exact characteristic backtracking with explicit edge/corner data.
            inside=(x>=1)&(x<=1.5)&(y>=1)&(y<=1.5)
            q=1+inside.astype(float)
            edges=inside&((x==1)|(x==1.5)|(y==1)|(y==1.5));q[edges]=1.5
            corner=inside&((x==1)|(x==1.5))&((y==1)|(y==1.5));q[corner]=1.25
            cross=dict(u=q)
        elif i==13:
            z,gauss=leggauss(256);z=z+1;P=z*(2-z)/.2
            heat=np.zeros_like(y);width=np.sqrt(4*.1*5)
            for j in range(-8,9):
                K=(np.exp(-(y[:,None]-z+4*j)**2/width**2)-np.exp(-(y[:,None]+z+4*j)**2/width**2))/(np.sqrt(np.pi)*width)
                heat+=K@(gauss*P)
            cross=dict(u=y*(2-y)/.2-heat)
        rows[f'C{i:02}']=differences(c,cross,expected,w)
    (WORK/'independent-analytic.json').write_text(json.dumps(rows,indent=2))
    print(json.dumps({k:max(vv['nrmse'] for vv in v.values()) for k,v in rows.items()},indent=2))

if __name__=='__main__':main()
