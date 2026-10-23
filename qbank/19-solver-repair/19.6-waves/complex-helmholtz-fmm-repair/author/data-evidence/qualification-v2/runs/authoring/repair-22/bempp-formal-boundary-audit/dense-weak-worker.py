"""Trusted transport adapter: real Bempp API calls and identity mappings only."""
import contextlib,json,sys,os,tempfile

# Resource setup only. Numerical calls below retain the original library APIs.
_cache=tempfile.TemporaryDirectory(prefix='bempp-kernel-cache-')
os.environ.update(OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='1',NUMBA_NUM_THREADS='4',POCL_MAX_PTHREAD_COUNT='4',NUMBA_CACHE_DIR=_cache.name+'/numba',POCL_CACHE_DIR=_cache.name+'/pocl')

with contextlib.redirect_stdout(sys.stderr):
    import numpy as np
    import bempp.api as bempp
    from bempp.api.fmm.exafmm import ExafmmInterface
    from bempp.api.fmm.helpers import dense_interaction_evaluator


def split(value):
    a=np.asarray(value)
    if a.ndim==1:a=a[:,None]
    return np.stack([a.real,a.imag],axis=-1).reshape(a.shape[0],-1).tolist()


def solve(payload):
    p=bempp.GLOBAL_PARAMETERS
    p.quadrature.regular=6;p.quadrature.singular=8
    p.fmm.expansion_order=10;p.fmm.ncrit=16
    p.fmm.dense_evaluation=False;p.fmm.near_field_representation='numba_evaluate'
    k=complex(payload['wavenumber_real'],payload['wavenumber_imag'])
    points=np.asarray(payload['targets'],dtype=np.float64)
    if payload['operation']==0:
        sources=np.asarray(payload['sources'],dtype=np.float64)
        q=np.asarray(payload['strength'],dtype=np.float64)
        charge=q[:,0]+1j*q[:,1]
        # A real float preserves the library's original real-k public path.
        wave=k.real if k.imag==0 else k
        api=ExafmmInterface(sources,points,'helmholtz',wavenumber=wave,expansion_order=10,ncrit=16)
        fast=api.evaluate(charge)
        local=dense_interaction_evaluator(points,sources,charge,'helmholtz',np.array([k.real,k.imag]))
        return {'fmm_potential':split(fast[:,0]),'fmm_gradient':split(fast[:,1:]),'local_potential':split(local[:,0]),'local_gradient':split(local[:,1:])}
    vertices=np.asarray(payload['vertices'],dtype=np.float64)
    triangles=np.asarray(payload['triangles'],dtype=np.uint32)
    grid=bempp.Grid(vertices.T,triangles.T)
    space=bempp.function_space(grid,'P',1)
    rho=np.asarray(payload['density'],dtype=np.float64)
    nodal=rho[:,0]+1j*rho[:,1]
    coeff=np.empty(space.global_dof_count,dtype=np.complex128)
    mapping=np.empty(grid.number_of_vertices,dtype=np.int64)
    for e in range(grid.number_of_elements):
        for j in range(3):mapping[grid.elements[j,e]]=space.local2global[e,j]
    coeff[mapping]=nodal
    out={}
    for name in ['single_layer','double_layer','hypersingular']:
        op=getattr(bempp.operators.boundary.helmholtz,name)(space,space,space,k,assembler='dense',device_interface='numba')
        value=op.weak_form()@coeff
        out['boundary_'+name]=split(value[mapping])
    gf=bempp.GridFunction(space,coefficients=coeff)
    for name in ['single_layer','double_layer']:
        op=getattr(bempp.operators.potential.helmholtz,name)(space,points.T,k,assembler='dense',device_interface='numba')
        out['potential_'+name]=split(op.evaluate(gf).ravel())
    return out


if __name__=='__main__':
    if '--health' in sys.argv:
        import exafmm,pyopencl
        assert callable(ExafmmInterface) and pyopencl.get_platforms()
        print(json.dumps({'runtime':'ready','native':exafmm.__file__}))
    else:
        payload=json.load(sys.stdin)
        with contextlib.redirect_stdout(sys.stderr):result=solve(payload)
        print(json.dumps(result,allow_nan=False))
