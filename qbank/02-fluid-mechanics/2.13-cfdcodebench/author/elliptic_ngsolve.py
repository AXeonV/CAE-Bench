"""Independent NGSolve elliptic checks of separation-of-variables references.

Official source weak-form producer: NGSolve i-tutorials unit-1.1-poisson. Fixed
coefficients, rectangles and boundary values are adapted to the public problems.
C16 is a steady comparison with an explicit exponentially small terminal-time
correction bound; it is never silently substituted as the transient reference.
"""
import json,time
import numpy as np
from ngsolve import Mesh,H1,GridFunction,BilinearForm,LinearForm,CoefficientFunction,grad,dx,x,y,exp,SetNumThreads
from netgen.geom2d import SplineGeometry
from catalog import WORK,DOMAINS

def solve(index,level):
    started=time.time();SetNumThreads(1);a,b,c,d=DOMAINS[index-1]
    geo=SplineGeometry();geo.AddRectangle((a,c),(b,d),bcs=['bottom','right','top','left'])
    mesh=Mesh(geo.GenerateMesh(maxh=.1/2**level))
    V=H1(mesh,order=3,dirichlet='left|right' if index==10 else '.*')
    u,v=V.TnT();gfu=GridFunction(V)
    if index==10:gfu.Set(y,definedon=mesh.Boundaries('right'))
    if index==15:
        gfu.Set(mesh.BoundaryCF(dict(left=10,right=40,bottom=20,top=0)),definedon=mesh.Boundaries('.*'))
    source=CoefficientFunction(0)
    if index==14:
        source=-100*exp(-((x-.5)**2+(y-.25)**2)/(.005))+100*exp(-((x-1.5)**2+(y-.75)**2)/(.005))
    elif index==16:source=200*exp(-(x*x+y*y)/.02)
    A=BilinearForm(V);A+=grad(u)*grad(v)*dx;A.Assemble()
    f=LinearForm(V);f+=source*v*dx;f.Assemble()
    gfu.vec.data+=A.mat.Inverse(V.FreeDofs(),inverse='umfpack')*(f.vec-A.mat*gfu.vec)
    xx=a+(np.arange(41)+.5)*(b-a)/41;yy=c+(np.arange(41)+.5)*(d-c)/41
    X,Y=np.meshgrid(xx,yy);values=np.asarray(gfu(mesh(X.ravel(),Y.ravel()))).ravel()
    if index==16:values+=1
    out=WORK/'independent-elliptic'/f'C{index:02}'/f'L{level}';out.mkdir(parents=True,exist_ok=True)
    np.save(out/'values.npy',values)
    record=dict(index=index,level=level,order=3,maxh=.1/2**level,ndof=V.ndof,wall_seconds=time.time()-started)
    (out/'process.json').write_text(json.dumps(record,indent=2));print(json.dumps(record),flush=True)

if __name__=='__main__':
    for index in (10,14,15,16):
        for level in (0,1,2):solve(index,level)
