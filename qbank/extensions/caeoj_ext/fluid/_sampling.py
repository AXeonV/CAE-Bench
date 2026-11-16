"""Explicit signal derivative used by contract extension helpers."""
import numpy as np

def reduced_time_derivative(times, values, time):
    """Linear sample derivative: right trace at knots, left at final endpoint."""
    t=np.asarray(times,dtype=float);v=np.asarray(values,dtype=float)
    if t.ndim!=1 or not len(t) or v.shape[0]!=len(t) or not np.all(np.isfinite(t)) or not np.all(np.isfinite(v)) or not np.isfinite(time):
        raise ValueError('Finite ordered samples with leading time axis required')
    if len(t)==1:return np.zeros_like(v[0])
    if np.any(np.diff(t)<=0) or time<t[0] or time>t[-1]:raise ValueError('Ordered interval coverage required')
    i=min(int(np.searchsorted(t,time,side='right'))-1,len(t)-2)
    return (v[i+1]-v[i])/(t[i+1]-t[i])
