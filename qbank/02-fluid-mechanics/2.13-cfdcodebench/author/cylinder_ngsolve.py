"""Independent mixed weak-form annulus verification, NGSolve configuration.

Psi has Dirichlet data on both circles; omega has Dirichlet data only outside.
Testing Poisson with omega's space makes d_n psi=0 at the inner circle natural.
Testing transport with psi's space adds no spurious omega wall condition.
Initial harmonic psi is computed with ordinary Dirichlet Poisson, preserving
the explicitly authorized original zero interior vorticity startup.
"""
import argparse,json,time
import numpy as np
from ngsolve import Mesh,H1,GridFunction,BilinearForm,CoefficientFunction,grad,dx,y,SetNumThreads
from netgen.geom2d import SplineGeometry

def solve(level,factor,output):
    started=time.time();SetNumThreads(1)
    geo=SplineGeometry();geo.AddCircle((0,0),10,bc='outer',leftdomain=1,rightdomain=0)
    geo.AddCircle((0,0),.5,bc='inner',leftdomain=0,rightdomain=1,maxh=.03/2**level)
    mesh=Mesh(geo.GenerateMesh(maxh=1/2**level)).Curve(3)
    V=H1(mesh,order=2,dirichlet='inner|outer');W=H1(mesh,order=2,dirichlet='outer');X=V*W
    (psi,omega),(v,z)=X.TnT();gfu=GridFunction(X);pg,wg=gfu.components
    pg.Set(mesh.BoundaryCF(dict(inner=0,outer=y)),definedon=mesh.Boundaries('inner|outer'))
    a0=BilinearForm(V);p0,v0=V.TnT();a0+=grad(p0)*grad(v0)*dx;a0.Assemble()
    pg.vec.data-=a0.mat.Inverse(V.FreeDofs(),inverse='umfpack')*(a0.mat*pg.vec)
    nu=.005;dt=.002/2**level/factor;steps=int(np.ceil(10/dt));dt=10/steps
    a=BilinearForm(X);a+=(grad(psi)*grad(z)-omega*z+nu*grad(omega)*grad(v))*dx;a.Assemble()
    ms=BilinearForm(X);ms+=(omega*v+dt*(grad(psi)*grad(z)-omega*z+nu*grad(omega)*grad(v)))*dx;ms.Assemble()
    inv=ms.mat.Inverse(X.FreeDofs(),inverse='umfpack')
    conv=BilinearForm(X,nonassemble=True)
    conv+=(grad(psi)[1]*grad(omega)[0]-grad(psi)[0]*grad(omega)[1])*v*dx
    res=gfu.vec.CreateVector()
    for k in range(steps):
        conv.Apply(gfu.vec,res);res.data+=a.mat*gfu.vec;gfu.vec.data-=dt*(inv*res)
        if k%1000==0:
            print(json.dumps(dict(step=k,total=steps,seconds=time.time()-started,max_coefficient=float(np.max(np.abs(wg.vec.FV().NumPy()))))),flush=True)
            if not np.all(np.isfinite(gfu.vec.FV().NumPy())):raise ValueError('Nonfinite mixed annular solution')
    faces=.5+9.5*(.5-.5*np.cos(np.linspace(0,np.pi,65)))
    rr=(faces[1:]+faces[:-1])/2;phi=(np.arange(64)+.5)*2*np.pi/64
    P,R=np.meshgrid(phi,rr);pts=mesh((R*np.cos(P)).ravel(),(R*np.sin(P)).ravel())
    np.savez(output,psi=20+np.asarray(pg(pts)).ravel(),omega=np.asarray(wg(pts)).ravel(),
             time=10.,dt=dt,ndof=X.ndof,level=level,wall_seconds=time.time()-started)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--level',type=int,default=0);a.add_argument('--factor',type=int,default=1);a.add_argument('--output',required=True)
    o=a.parse_args();solve(o.level,o.factor,o.output)
