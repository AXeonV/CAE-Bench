"""Compile unchanged numerical loops from sourced teaching programs for checks.

Adapters correct target-time bookkeeping and explicitly record grid/CFL values.
Numba is a compiler here, not the reference method. These independent checks do
not produce the selected analytic references. Original source text is immutable.
"""
import ast,json,time
import numpy as np
from numba import njit
from pathlib import Path
from catalog import WORK,IDS

def function_from_statements(name,args,body,namespace):
    fn=ast.FunctionDef(name=name,args=ast.arguments(posonlyargs=[],args=[ast.arg(arg=a) for a in args],kwonlyargs=[],kw_defaults=[],defaults=[]),body=body,decorator_list=[])
    module=ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[]))
    exec(compile(module,'<audited-source-loop>','exec'),namespace)
    return njit(namespace[name])

def main():
    source=WORK/'upstream/CFDCodeBench/PDE_Benchmark/solution'
    tree=ast.parse((source/f'{IDS[4]}.py').read_text(encoding='utf-8'))
    loop=next(n for n in tree.body if isinstance(n,ast.For))
    loop.body=[n for n in loop.body if not isinstance(n,ast.If)] # Remove plots only.
    ret=ast.parse('return u').body[0]
    f=function_from_statements('lax',['u','unp1','nx','T','nu'],[loop,ret],{'np':np})
    out=WORK/'independent-source-checks';out.mkdir(exist_ok=True)
    for N in (2049,4097,8193):
        x=np.linspace(0,2*np.pi,N);dx=x[1]-x[0];steps=int(np.ceil(5/(.4*dx)));dt=5/steps
        u=np.sin(x)+.5*np.sin(.5*x);started=time.time();u=f(u,np.zeros_like(u),N,steps,dt/dx)
        np.savez(out/f'C05-N{N}.npz',x=x,u=u,time=5.,dt=dt,wall_seconds=time.time()-started)
        print('C05',N,steps,time.time()-started,flush=True)
    tree=ast.parse((source/f'{IDS[1]}.py').read_text(encoding='utf-8'))
    loop=next(n for n in tree.body if isinstance(n,ast.For))
    f=function_from_statements('diffusion',['u','nx','nt','nu','dt','dx'],[loop,ast.parse('return u').body[0]],{'numpy':np})
    for N in (201,401,801):
        x=np.linspace(0,2,N);dx=x[1]-x[0];steps=int(np.ceil(.0333/(.2*dx*dx/.3)));dt=.0333/steps
        u=np.ones(N);u[(x>=.5)&(x<=1)]=2;started=time.time();u=f(u,N,steps,.3,dt,dx)
        np.savez(out/f'C02-N{N}.npz',x=x,u=u,time=.0333,dt=dt,wall_seconds=time.time()-started)
        print('C02',N,steps,time.time()-started,flush=True)
    # Original diffuse(nt) runs nt+1 steps and its caller is diffuse(50), not
    # the unused nt=17 declaration. Select the numerical statements only and
    # supply an exact-time nt count, preserving this explicit source difference.
    tree=ast.parse((source/f'{IDS[7]}.py').read_text(encoding='utf-8'))
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='diffuse')
    loop=next(n for n in fn.body if isinstance(n,ast.For));loop.iter=ast.parse('range(nt)',mode='eval').body
    f=function_from_statements('diffusion2d',['u','nt','nu','dt','dx','dy'],[loop,ast.parse('return u').body[0]],{'numpy':np})
    for N in (61,121,241):
        x=np.linspace(0,2,N);dx=x[1]-x[0];steps=int(np.ceil(.3777/(.24*dx*dx/.05)));dt=.3777/steps
        u=np.ones((N,N));u[np.ix_((x>=.5)&(x<=1),(x>=.5)&(x<=1))]=2
        started=time.time();u=f(u,steps,.05,dt,dx,dx)
        np.savez(out/f'C08-N{N}.npz',x=x,y=x,u=u,time=.3777,dt=dt,wall_seconds=time.time()-started)
        print('C08',N,steps,time.time()-started,flush=True)

if __name__=='__main__':main()
