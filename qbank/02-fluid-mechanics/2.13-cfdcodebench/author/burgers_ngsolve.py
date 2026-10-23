"""Independent existing NGSolve IMEX convection-diffusion weak-form check.

Fixed u=v invariant subspace of the sourced two-dimensional viscous problem.
Adapts official NGSolve transient diffusion/IMEX weak-form time integration;
the author CFDPython program remains the primary producer.
"""
import json,time
import numpy as np
from ngsolve import Mesh,H1,GridFunction,BilinearForm,CoefficientFunction,grad,dx,x,y,IfPos,SetNumThreads
from netgen.geom2d import SplineGeometry
from catalog import WORK

def solve(level):
    started=time.time();SetNumThreads(1)
    geo=SplineGeometry();geo.AddRectangle((0,0),(2,2),bc='wall')
    mesh=Mesh(geo.GenerateMesh(maxh=.05/2**level));V=H1(mesh,order=3,dirichlet='wall')
    u,v=V.TnT();gfu=GridFunction(V)
    initial=1+IfPos(x-.5,IfPos(1-x,IfPos(y-.5,IfPos(1-y,1,0),0),0),0)
    gfu.Set(initial)
    dt=.00005/(2**level);steps=int(np.ceil(.027/dt));dt=.027/steps
    a=BilinearForm(V);a+=.01*grad(u)*grad(v)*dx;a.Assemble()
    ms=BilinearForm(V);ms+=(u*v+dt*.01*grad(u)*grad(v))*dx;ms.Assemble()
    inv=ms.mat.Inverse(V.FreeDofs(),inverse='umfpack')
    conv=BilinearForm(V,nonassemble=True);conv+=u*(grad(u)[0]+grad(u)[1])*v*dx
    res=gfu.vec.CreateVector()
    for k in range(steps):
        conv.Apply(gfu.vec,res);res.data+=a.mat*gfu.vec;gfu.vec.data-=dt*(inv*res)
    xx=(np.arange(41)+.5)*2/41;X,Y=np.meshgrid(xx,xx)
    q=np.asarray(gfu(mesh(X.ravel(),Y.ravel()))).ravel()
    out=WORK/'independent-burgers'/f'L{level}';out.mkdir(parents=True,exist_ok=True)
    np.save(out/'values.npy',q)
    record=dict(order=3,maxh=.05/2**level,ndof=V.ndof,dt=dt,time=.027,wall_seconds=time.time()-started)
    (out/'process.json').write_text(json.dumps(record,indent=2));print(json.dumps(record),flush=True)

if __name__=='__main__':
    for level in (0,1,2):solve(level)
