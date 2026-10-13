"""Independent references for contracted one-dimensional continuous problems.

The zero-mean initial primitive is piecewise linear, so its exponential
convolved with a periodic heat kernel has closed-form Gaussian interval
integrals. Cell means follow from differences of log(heat solution), including
the Galilean shift for a nonzero initial mean. No official trajectory is used.
"""
import numpy as np
from scipy.special import log_ndtr, logsumexp
from scipy.fft import rfft, irfft
from caeoj.sdk import write_result, load_result
from .storage import PreparationError

def interval_log_probability(a,b):
    # Reflect upper-tail intervals before subtracting the CDFs.
    positive=a>0
    lo=np.where(positive,-b,a)
    hi=np.where(positive,-a,b)
    large=log_ndtr(hi);small=log_ndtr(lo)
    with np.errstate(divide='ignore',invalid='ignore'):
        return large+np.log(-np.expm1(small-large))

def burgers_average(initial,times,kappa,tail_log=45):
    if kappa<=0 or not np.isfinite(kappa):raise ValueError('Positive finite kappa required')
    u=np.asarray(initial,dtype=float).reshape(-1)
    n=len(u);dx=1/n;mean=u.mean()
    edges=np.arange(n+1)*dx
    slopes=-(u-mean)/(2*kappa)
    logs=np.concatenate(([0.],np.cumsum(slopes)*dx))[:-1]
    result=[]
    for t in times:
        if t<0 or not np.isfinite(t):raise ValueError('Finite nonnegative times required')
        if t==0:result.append(u.copy());continue
        x=(edges-mean*t)%1
        sigma=np.sqrt(2*kappa*t)
        images=int(np.ceil(np.sqrt(.25+4*kappa*t*tail_log)))+1
        all_logs=[]
        for start in range(0,n+1,32):
            points=x[start:start+32,None]
            totals=[]
            for winding in range(-images,images+1):
                center=points-winding+2*kappa*t*slopes
                a=(edges[:-1]-center)/sigma
                b=(edges[1:]-center)/sigma
                terms=logs+slopes*(points-winding-edges[:-1])+kappa*t*slopes**2+interval_log_probability(a,b)
                totals.append(logsumexp(terms,axis=1))
            all_logs.extend(logsumexp(totals,axis=0))
        result.append(mean-2*kappa/dx*np.diff(all_logs))
    return np.asarray(result)[...,None]

def write_burgers_reference(problem,path):
    initial=problem.arrays['initial_state'].reshape(-1)
    times=problem.arrays['times']
    kappa=problem.manifest['physics']['parameters']['diffusion_coefficient']['value']
    value=burgers_average(initial,times,kappa,45)
    wider=burgers_average(initial,times,kappa,55)
    discrepancy=float(np.max(np.abs(value-wider)))
    mass_error=float(np.max(np.abs(value.mean(axis=1)-initial.mean())))
    # A bound on omitted image integrals relative to the included nearest image,
    # valid pointwise in the integration variable independently of phi_0.
    bounds=[]
    for t in times[times>0]:
        images=int(np.ceil(np.sqrt(.25+4*kappa*t*55)))+1
        relative=2*np.exp(-(images**2-.25)/(4*kappa*t))/(-np.expm1(-2*images/(4*kappa*t)))
        bounds.append(float(4*kappa*len(initial)*np.log1p(relative)))
    if (not np.isfinite(wider).all() or discrepancy>1e-8 or mass_error>1e-10 or
        wider.min()<initial.min()-1e-8 or wider.max()>initial.max()+1e-8):
        raise PreparationError('Cole–Hopf reference failed integral/mass/maximum-principle checks')
    write_result(path,problem,{'state':wider})
    load_result(problem,path)
    return {'kind':'analytic_cole_hopf_cell_integrals',
            'method':'Periodic Gaussian convolution of piecewise-exponential Cole–Hopf initial data; log differences give cell averages; Galilean mean shift',
            'error_evidence':{'image_tail_absolute_bound':max(bounds,default=0.),
                              'wider_image_sum_max_difference':discrepancy,
                              'cell_mean_mass_error':mass_error,
                              'scope':'Analytic integral with Gaussian-tail bound and floating-point consistency checks; not a bound on all floating-point error'},
            'official_trajectory_used':False}


def logistic_diffusion(initial,times,nu,rate,refine,steps):
    """Conservative periodic FV diffusion semigroup + exact logistic Strang steps.

    Repeating cell averages preserves the contracted piecewise-constant initial
    field at every refinement. Output averages aggregate the refined cells.
    """
    n=len(initial)*refine;dx=1/n
    u=np.repeat(initial,refine).astype(float)
    eigenvalues=-4*nu*np.sin(np.pi*np.arange(n//2+1)/n)**2/dx**2
    initial_scale=1/(len(initial)**2*max(nu,1e-300))
    output=[];last=0.
    for t in times:
        # Resolve the initial diffusion layer rather than applying a full
        # reaction half-step to a discontinuous initial field for too long.
        # Thereafter grow smoothly, with an explicit maximum step.
        while last<t:
            # The schedule depends on the original grid and time-resolution
            # parameter, not the refined grid: space-only checks therefore
            # use exactly the same internal times.
            dt=min(t-last,1/steps,(initial_scale+last)*8/steps)
            heat=np.exp(eigenvalues*dt);reaction=np.expm1(rate*dt/2)
            u=u*(1+reaction)/(1+u*reaction)
            u=irfft(rfft(u)*heat,n=n)
            u=u*(1+reaction)/(1+u*reaction)
            last=min(t,last+dt)
        output.append(u.reshape(-1,refine).mean(axis=1));last=t
    return np.asarray(output)[...,None]


def write_logistic_reference(problem,path):
    initial=problem.arrays['initial_state'].reshape(-1);times=problem.arrays['times']
    parameters=problem.manifest['physics']['parameters']
    nu=parameters['diffusivity']['value'];rate=parameters['reaction_rate']['value']
    history=[];previous=None;previous_difference=None
    target=2e-6  # Reference preparation target, not an Agent grading threshold.
    for refine in (2,4,8,16,32,64,128):
        steps=64*refine
        value=logistic_diffusion(initial,times,nu,rate,refine,steps)
        difference=None if previous is None else float(np.max(np.abs(value-previous)))
        history.append({'refinement':refine,'maximum_time_step':1/steps,
                        'successive_max_difference':difference})
        if (difference is not None and previous_difference is not None and difference<target and
            (difference<.4*previous_difference or difference<1e-12)):
            spatial=logistic_diffusion(initial,times,nu,rate,refine//2,steps)
            temporal=logistic_diffusion(initial,times,nu,rate,refine,steps//2)
            space_difference=float(np.max(np.abs(value-spatial)))
            time_difference=float(np.max(np.abs(value-temporal)))
            if max(space_difference,time_difference)<target:break
        previous=value;previous_difference=difference
    else:
        raise PreparationError('Logistic reference did not meet space/time refinement checks')
    if not np.isfinite(value).all() or value.min()<-1e-10 or value.max()>1+1e-10:
        raise PreparationError('Logistic reference violated [0,1] invariant interval')
    # The output at t=0 is the original input, without averaging roundoff.
    value[0]=initial[:,None]
    write_result(path,problem,{'state':value});load_result(problem,path)
    return {'kind':'independent_convergence_checked_numerical_reference',
            'method':'Periodic conservative finite-volume diffusion, exponential semigroup, exact logistic reaction with Strang splitting; small initial-layer steps grow smoothly to the maximum step',
            'error_evidence':{'refinement_history':history,'space_only_max_difference':space_difference,
                              'time_only_max_difference':time_difference,'preparation_target':target,
                              'scope':'Measured spatial and temporal refinement, not a rigorous continuum error bound; grading tolerances remain uncalibrated'},
            'official_trajectory_used':False}
