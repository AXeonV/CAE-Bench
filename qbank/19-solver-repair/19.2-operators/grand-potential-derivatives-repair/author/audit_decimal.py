"""80-digit numerical differentiation and Gauss integration of the public definitions.

Does not import the native adapter, patched source, or analytic derivative reference.
Checks every entry of all actual native HDF5 references, including exact zeros.
"""
import hashlib
import json
from decimal import Decimal as D, getcontext
from pathlib import Path

import h5py
import numpy as np
from caeoj.sdk import load_problem
from policy import policy_for

getcontext().prec = 80
TASK = Path(__file__).resolve().parents[1]
STEP = D('1e-15')
NAMES = ['void_minimum', 'solid_minimum', 'void_response', 'solid_response']


def material(p, q, w):
    phi, *eta = q
    h = D(0) if phi <= 0 else D(1) if phi >= 1 else phi**3 * (10 + phi * (-15 + 6 * phi))
    eq = p['equilibrium_constant']
    for i in range(4):
        eq += p[f'equilibrium_linear_{i}'] * eta[i]
        for j in range(i, 4):
            eq += p[f'equilibrium_hessian_{i}{j}'] * eta[i] * eta[j] / (2 if i == j else 1)
    va, kv, ks = (p[k] for k in ['atomic_volume', 'void_energy_coefficient', 'solid_energy_coefficient'])
    values = [h, (1-h)*eq, h/(va*kv), (1-h)/(va*ks)]
    extra = [w/(va*va*kv)+1/va, w/(va*va*ks)+eq/va,
             -w*w/(2*va*va*kv)-w/va, -w*w/(2*va*va*ks)-w*eq/va]
    return values, extra


def shifted(q, changes):
    r = list(q)
    for i, amount in changes:
        r[i] += amount
    return r


def state_reference(p, q, w, c):
    v, extra = material(p, q, w)
    result = {}
    for k, name in enumerate(NAMES):
        f = lambda x: material(p, x, w)[0][k]
        grad = [(f(shifted(q, [(i, STEP)]))-f(shifted(q, [(i, -STEP)])))/(2*STEP) for i in range(5)]
        hess = []
        for i in range(5):
            for j in range(5):
                if i == j:
                    entry = (f(shifted(q, [(i, STEP)]))-2*v[k]+f(shifted(q, [(i, -STEP)])))/STEP**2
                else:
                    entry = sum((D(si*sj)*f(shifted(q, [(i,si*STEP),(j,sj*STEP)]))
                                 for si in [-1,1] for sj in [-1,1]), D(0))/(4*STEP**2)
                hess.append(entry)
        result[name], result[name+'_gradient'], result[name+'_hessian'] = [v[k]], grad, hess
    for name, value in zip(['void_number_density','solid_number_density','void_grand_potential','solid_grand_potential'], extra):
        result[name] = [value]
    length = p['probe_length']
    # Separate nodal perturbations, interpolated at the two actual Gauss points.
    def residual(nodal_q, nodal_w, nodal_c):
        r = [D(0), D(0)]
        for xi in [-1/D(3).sqrt(), 1/D(3).sqrt()]:
            basis = [(1-xi)/2, (1+xi)/2]
            local_q = [sum((basis[n]*nodal_q[n][k] for n in range(2)), D(0)) for k in range(5)]
            local_w = sum((basis[n]*nodal_w[n] for n in range(2)), D(0))
            local_c = sum((basis[n]*nodal_c[n] for n in range(2)), D(0))
            a,b,cr,dr = material(p, local_q, local_w)[0]
            for row in range(2):
                r[row] += length/2*basis[row]*(local_c-a-b-(cr+dr)*local_w)
        return r
    result['constraint_residual'] = residual([q,q], [w,w], [c,c])
    for group in ['state','potential','concentration']:
        columns = []
        for k in range(5 if group == 'state' else 1):
            blocks = []
            # w has energy units: choose a relative-to-characteristic-energy step.
            step = STEP*p['atomic_volume']*min(p['void_energy_coefficient'],p['solid_energy_coefficient']) if group == 'potential' else STEP
            for col in range(2):
                pair = []
                for sign in [-1,1]:
                    nq, nw, nc = [list(q),list(q)], [w,w], [c,c]
                    if group == 'state': nq[col][k] += sign*step
                    elif group == 'potential': nw[col] += sign*step
                    else: nc[col] += sign*step
                    pair.append(residual(nq,nw,nc))
                blocks.append([(pair[1][row]-pair[0][row])/(2*step) for row in range(2)])
            columns.extend([blocks[col][row] for row in range(2) for col in range(2)])
        result['constraint_'+group+'_jacobian'] = columns
    return result


def main():
    report = {'precision_digits':80,'dimensionless_step':str(STEP),
              'method':'Independent central differences of public value polynomials and separately perturbed nodal two-point Gauss residuals. Endpoint differences cross the declared clamp; no source or analytic derivative implementation imported.',
              'cases':[], 'complete':False}
    for path in sorted((TASK/'cases').glob('*/problem.json')):
        problem = load_problem(path)
        p = {k:D(str(v['value'])) for k,v in problem.manifest['physics']['parameters'].items()}
        a = problem.arrays
        exact = []
        for i in range(len(a['program_ids'])):
            q = [D(str(a['phi'][0,i,0])), *[D(str(x)) for x in a['eta'][0,i]]]
            exact.append(state_reference(p,q,D(str(a['potential'][0,i,0])),D(str(a['concentration'][0,i,0]))))
        target = TASK/'reference'/path.parent.name/'reference.h5'
        policy = policy_for(problem)
        checks = {}
        with h5py.File(target) as h5:
            for name in exact[0]:
                actual = np.asarray(h5[name])
                rule = policy['quantities'][problem.manifest['outputs'][name]['quantity']]['rule']
                atol, rtol = D(str(rule['atol'])), D(str(rule['rtol']))
                fractions=[]; zero_count=0
                for i, state in enumerate(exact):
                    for j, ref in enumerate(state[name]):
                        fractions.append(abs(D(str(actual[0,i,j]))-ref)/(atol+rtol*abs(ref)))
                        zero_count += ref == 0
                checks[name]={'entries':len(fractions),'exact_zero_entries':zero_count,
                              'max_tolerance_fraction':float(max(fractions)), 'passed':max(fractions)<=1}
        report['cases'].append({'case':path.parent.name,'programs':len(exact),
                                'reference_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'checks':checks})
        print(path.parent.name, max(x['max_tolerance_fraction'] for x in checks.values()), flush=True)
    report['complete']=True
    report['passed']=all(c['passed'] for case in report['cases'] for c in case['checks'].values())
    (TASK/'author/data-evidence/decimal-audit.json').write_text(json.dumps(report,indent=2)+'\n',newline='\n')
    if not report['passed']:raise SystemExit(1)


if __name__ == '__main__':main()
