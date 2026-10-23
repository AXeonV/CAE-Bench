"""NGSolve Taylor-Hood transient producer, adapted from the official IMEX tutorial.

Source: https://docu.ngsolve.org/latest/i-tutorials/unit-3.2-navierstokes/navierstokes.html
Uses the documented mixed weak form and IMEX Euler update. Changes are the
authorized square geometry/lid initial-boundary data and exact pressure gauge
(NumberSpace Lagrange multiplier, not a pressure boundary condition).
"""
import argparse, json, time
from pathlib import Path
import numpy as np
from ngsolve import (Mesh, VectorH1, H1, NumberSpace, GridFunction, BilinearForm,
                     CoefficientFunction, InnerProduct, grad, div, dx, Integrate, SetNumThreads)
from netgen.geom2d import SplineGeometry

def solve(index, level, factor, output, order=2):
    started=time.time();SetNumThreads(1)
    nu,tend=(.01,10.) if index==12 else (.1,.5)
    geo=SplineGeometry()
    # Resolve the known discontinuous-lid corner singularities geometrically,
    # rather than deleting near-corner observations or smoothing the lid.
    hcorner=.002/(2**level)
    vertices=[geo.AppendPoint(px,py,maxh=hcorner) for px,py in ((0,0),(1,0),(1,1),(0,1))]
    for j,label in enumerate(('bottom','right','lid','left')):
        geo.Append(['line',vertices[j],vertices[(j+1)%4]],bc=label)
    mesh=Mesh(geo.GenerateMesh(maxh=.1/(2**level)))
    V=VectorH1(mesh,order=order,dirichlet='.*');Q=H1(mesh,order=order-1);R=NumberSpace(mesh)
    X=V*Q*R
    (u,p,c),(v,q,d)=X.TnT()
    gfu=GridFunction(X);vel,pres,_=gfu.components
    # The corner has no unique lid trace. A nodal endpoint convention is retained
    # under refinement; all published observations are strictly interior.
    vel.Set(CoefficientFunction((1,0)),definedon=mesh.Boundaries('lid'))
    stokes=(nu*InnerProduct(grad(u),grad(v))-div(u)*q-div(v)*p+c*q+d*p)*dx
    a=BilinearForm(X);a+=stokes;a.Assemble()
    dt=.004/(2**level)/factor
    steps=int(np.ceil(tend/dt));dt=tend/steps
    mstar=BilinearForm(X);mstar+=InnerProduct(u,v)*dx+dt*stokes;mstar.Assemble()
    inv=mstar.mat.Inverse(X.FreeDofs(),inverse='umfpack')
    conv=BilinearForm(X,nonassemble=True);conv+=(grad(u)*u)*v*dx
    res=gfu.vec.CreateVector()
    for k in range(steps):
        conv.Apply(gfu.vec,res)
        res.data+=a.mat*gfu.vec
        gfu.vec.data-=dt*(inv*res)
        if k%1000==0:print(json.dumps(dict(step=k,total=steps,seconds=time.time()-started)),flush=True)
    x=(np.arange(41)+.5)/41;xx,yy=np.meshgrid(x,x)
    pts=mesh(xx.ravel(),yy.ravel())
    uv=np.asarray(vel(pts));pp=np.asarray(pres(pts))
    np.savez(output,x=x,y=x,u=uv[:,0].reshape(41,41),v=uv[:,1].reshape(41,41),
             p=pp.reshape(41,41),time=tend,dt=dt,ndof=X.ndof,velocity_order=order,
             divergence_l2=float(np.sqrt(Integrate(div(vel)**2,mesh))),
             pressure_integral=float(Integrate(pres,mesh)),wall_seconds=time.time()-started)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--index',type=int,required=True)
    ap.add_argument('--level',type=int,required=True);ap.add_argument('--factor',type=int,default=1)
    ap.add_argument('--output',required=True);ap.add_argument('--order',type=int,default=2);a=ap.parse_args()
    solve(a.index,a.level,a.factor,Path(a.output),a.order)
