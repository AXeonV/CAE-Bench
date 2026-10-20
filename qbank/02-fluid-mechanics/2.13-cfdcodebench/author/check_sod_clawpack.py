"""Run the pinned Clawpack exact Euler solver, independent of formula evaluator.

Only interactive imports are omitted. The legacy fsolve 1-element root array is
explicitly converted to a scalar for NumPy2 compatibility; numerical equations
and wave/state evaluation are unchanged. Preserve the pinned source and license.
"""
import ast,json
import numpy as np
from scipy.optimize import fsolve
from catalog import WORK,catalog
from build_local import observation_grid,differences
from analytic import evaluate

def scalar_fsolve(*args,**kwargs):
    answer=fsolve(*args,**kwargs)
    if kwargs.get('full_output'):
        root,info,ier,message=answer
        if np.asarray(root).size!=1:raise ValueError('Not a scalar Riemann root')
        return float(root.item()),info,ier,message
    return answer

def main():
    path=WORK/'sources/clawpack-exact_solvers-euler.py'
    tree=ast.parse(path.read_text(encoding='utf-8'))
    module=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[])
    ns=dict(np=np,fsolve=scalar_fsolve)
    exec(compile(module,str(path),'exec'),ns)
    ql=ns['primitive_to_conservative'](1,0,1);qr=ns['primitive_to_conservative'](.125,0,.1)
    states,speeds,reval,types=ns['exact_riemann_solution'](ql,qr)
    c=catalog()[2];xy,w=observation_grid(c);q=reval(xy[:,0]/.25)
    values=dict(rho=q[0],u=q[1]/q[0],E=q[2]/q[0])
    result=dict(comparison=differences(c,values,evaluate(3,xy),w),wave_types=types,
                maximum_wave_distance=.25*max(abs(float(z)) for sp in speeds for z in np.asarray(sp).ravel()),
                wall_distance=1,source_revision='5b171f11fd7a3e810ee7a74a4d9f2dff01d65a6e')
    (WORK/'clawpack-sod-comparison.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
