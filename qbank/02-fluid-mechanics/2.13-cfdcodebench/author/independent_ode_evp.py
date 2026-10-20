"""Independent verification only, never selected as a reference producer.

C17: adaptive first-order flux BVP vs quadrature representation.
C23: independently derived regular-polynomial divergence-free Galerkin EVP vs
the author's Dedalus disk EVP. See derivation in author/README.md. Uses velocity
wall factors and r^(m+/-1), r^m regularity, not a truncated singular inner wall.
"""
import json
import numpy as np
from numpy.polynomial.legendre import Legendre,leggauss
from scipy.integrate import solve_bvp
from scipy.linalg import null_space,eig
from catalog import WORK

def cess():
    def mu(y):
        d=np.minimum(y,2-y)
        return .5/395*(1+np.sqrt(1+(.426*395)**2*(2*d-d*d)**2*(3-4*d+2*d*d)**2*(-np.expm1(-395*d/25.4))**2/9))
    def ode(x,y):return np.vstack((y[1]/mu(x),-np.ones_like(x)))
    x=np.linspace(0,2,101);results=[]
    for tolerance in (1e-5,1e-7,1e-9):
        sol=solve_bvp(ode,lambda ya,yb:np.array([ya[0],yb[0]]),x,np.zeros((2,len(x))),tol=tolerance,max_nodes=50000)
        if not sol.success:raise ValueError(sol.message)
        xx=np.linspace(0,2,201)
        results.append(dict(tolerance=tolerance,nodes=len(sol.x),max_residual=float(sol.rms_residuals.max()),u=sol.sol(xx)[0].tolist()))
    return results

def pipe(N):
    m=5;k=1;nu=1e-4
    # s=r^2. Integrals r dr = ds/2. Trial helical components v+=ur+i*ut,
    # v-=ur-i*ut and w have powers m+1,m-1,m and common wall factor1-s.
    q,w=leggauss(2*N+16);s=(q+1)/2;r=np.sqrt(s);weights=w/4
    P=np.column_stack([Legendre.basis(j)(q) for j in range(N)])
    Ps=np.column_stack([2*Legendre.basis(j).deriv()(q) for j in range(N)])
    F=(1-s[:,None])*P;Fs=-P+(1-s[:,None])*Ps
    B=np.zeros((3*N,3*N),complex);K=B.copy();U=B.copy();S=B.copy()
    V=[]
    for j,power in enumerate((m+1,m-1,m)):
        v=r[:,None]**power*F
        dr=power*r[:,None]**(power-1)*F+2*r[:,None]**(power+1)*Fs
        weight=.5 if j<2 else 1.
        sl=slice(j*N,(j+1)*N)
        B[sl,sl]=v.T@((weight*weights)[:,None]*v)
        K[sl,sl]=dr.T@((weight*weights)[:,None]*dr)+v.T@((weight*weights*(power*power/r**2+k*k))[:,None]*v)
        U[sl,sl]=v.T@((weight*weights*(1-r*r))[:,None]*v)
        V.append(v)
    S[2*N:,:N]=V[2].T@((weights*r)[:,None]*V[0])
    S[2*N:,N:2*N]=V[2].T@((weights*r)[:,None]*V[1])
    # Exact polynomial divergence / r^m:
    # (m+1)F_plus+s F_plus' + F_minus' + i*k F_w.
    z,_=leggauss(N+1);ss=(z+1)/2
    pp=np.column_stack([Legendre.basis(j)(z) for j in range(N)])
    ps=np.column_stack([2*Legendre.basis(j).deriv()(z) for j in range(N)])
    ff=(1-ss[:,None])*pp;fp=-pp+(1-ss[:,None])*ps
    C=np.column_stack(((m+1)*ff+ss[:,None]*fp,fp,1j*k*ff))
    Z=null_space(C,rcond=1e-12)
    A=Z.conj().T@(-nu*K-1j*k*U+S)@Z;M=Z.conj().T@B@Z
    values,vectors=eig(A,M)
    finite=np.flatnonzero(np.isfinite(values));idx=finite[np.argmax(values[finite].real)]
    val=values[idx];v=vectors[:,idx]
    residual=np.linalg.norm(A@v-val*(M@v))/(np.linalg.norm(A@v)+abs(val)*np.linalg.norm(M@v))
    return dict(order=N,eigenvalue_real=float(val.real),eigenvalue_imag=float(val.imag),
        generalized_residual=float(residual),divergence_nullspace_residual=float(np.linalg.norm(C@Z)/np.linalg.norm(C)),
        subspace_dimension=Z.shape[1],mass_condition=float(np.linalg.cond(M)))

def main():
    result=dict(cess=cess(),pipe=[pipe(n) for n in (16,24,32,48)])
    path=WORK/'independent-ode-evp.json';path.write_text(json.dumps(result,indent=2))
    print(json.dumps(result['pipe'],indent=2))

if __name__=='__main__':main()
