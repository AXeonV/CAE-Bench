"""Trusted affine-origin and constant-gauge normalization of declared outputs.

No solver, interpolation, phase alignment, fitted scale, or candidate code imports.
"""
import math
import numpy as np

def _transform(values, transform, weights):
    result=np.asarray(values,dtype='float64').copy()
    with np.errstate(over='ignore',invalid='ignore'):
        result-=transform['offset']
        if transform['remove_mean']:
            scale=np.max(np.abs(result),axis=1,keepdims=True)
            scaled=np.divide(result,scale,out=np.zeros_like(result),where=scale!=0)
            w=weights/np.sum(weights)
            mean=np.sum(scaled*w[None,:,None],axis=1,keepdims=True)
            # The exact weighted mean is a convex combination. Clamp rounding
            # drift, then center before restoring scale (DBL_MAX gauges stay
            # finite whenever the centered field is representable).
            mean=np.clip(mean,np.min(scaled,axis=1,keepdims=True),np.max(scaled,axis=1,keepdims=True))
            result=(scaled-mean)*scale
    return result

def prepare(problem,check,assets):
    from caeoj.validation import check_result, ContractError
    from caeoj.grading_policy import resolve_policy
    from caeoj.grading_metrics import evaluate_observation
    if set(check)!={'id','evaluator','reference','policy','transforms','weight_field'}:
        raise ValueError('Invalid normalized_outputs parameters')
    transforms=check['transforms'];outputs=problem.manifest['outputs']
    if set(transforms)!=set(outputs):raise ValueError('Transforms must exactly cover outputs')
    weight_name=check['weight_field'];wspec=problem.manifest['fields'].get(weight_name)
    if not wspec or wspec['kind']!='scalar' or wspec['dtype']!='float64':raise ValueError('Missing scalar weights')
    weights=problem.arrays[wspec['array']][0,:,0]
    if not np.all(np.isfinite(weights)) or np.any(weights<=0):raise ValueError('Weights must be finite and positive')
    weights=weights/weights.max() # Scale-safe mean, independent of candidate.
    policy=resolve_policy(check['policy'],problem)
    reference=assets.h5(check['reference'])
    diagnostics=check_result(problem,reference)
    if not diagnostics['valid']:raise ContractError(diagnostics)
    assets.used.setdefault(check['reference'],set()).update(reference)
    expected={}
    for name,spec in outputs.items():
        t=transforms[name]
        if (set(t)!={'offset','remove_mean'} or type(t['remove_mean']) is not bool or
            type(t['offset']) not in (int,float) or not math.isfinite(t['offset'])):
            raise ValueError('Invalid fixed normalization')
        if spec['dtype']!='float64' or spec['location']!=wspec['location']:
            raise ValueError('Normalized fields must share scalar weight location')
        expected[name]=_transform(reference[spec['array']],t,weights)
        if not np.all(np.isfinite(expected[name])):raise ValueError('Reference normalization overflows')
    def evaluate(result):
        fields={}
        for name,spec in outputs.items():
            actual=_transform(result[spec['array']],transforms[name],weights)
            if not np.all(np.isfinite(actual)):
                fields[name]={'passed':False,'reason':'normalization_overflow'};continue
            loc=problem.manifest['locations'][spec['location']]
            record=evaluate_observation(actual,expected[name],policy['fields'][name],
                ids=problem.arrays[loc['ids']],times=problem.arrays[problem.manifest['time_axes'][spec['time_axis']]],
                weights={weight_name:weights})
            record['normalization']=transforms[name]
            fields[name]=record
        return {'passed':all(f['passed'] for f in fields.values()),'fields':fields}
    return evaluate
