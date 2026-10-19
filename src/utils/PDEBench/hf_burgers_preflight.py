# /// script
# requires-python = ">=3.11"
# dependencies = ["huggingface_hub>=1.0,<2", "numpy>=2,<3", "h5py>=3.13,<4"]
# ///
"""Bounded evaluation of a published Cole-Hopf formula, not a PDE time solver.

The source numeric initial values are explicitly reinterpreted as cell constants.
Comparisons are diagnostic, not a retroactive certification of archived fields.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time

RUNTIME_ZIP = ''
FORMULA_SOURCE = 'https://math.nyu.edu/~tabak/PDEs/The_Burgers-Equation.pdf'


def cole_hopf_averages(initial, diffusivity, times, modes=64):
    """Periodic heat Fourier series with exact exponential segment integrals.

    Remove mean by Galilean translation. phi0=exp(-integral(u0-mean)/2mu),
    phi_t=mu phi_xx, u=mean-2mu d_x log(phi). Cell integrals telescope.
    This is the periodic specialization of the cited transform, derived here;
    truncation diagnostics exclude floating-point certification.
    """
    import numpy as np
    u=np.asarray(initial,dtype=np.float64);n=len(u);mu=float(diffusivity)
    if n<2 or mu<=0 or not np.isfinite(u).all() or any(t<=0 for t in times):
        raise ValueError('Positive diffusivity/times and finite initial cells required')
    dx=1/n;mean=u.mean();v=u-mean
    potential=np.concatenate(([0.],np.cumsum(v)*dx))[:-1]
    exponent=-potential/(2*mu);exponent-=exponent.max()
    amplitude=np.exp(exponent)
    k=np.arange(-modes,modes+1);omega=2*np.pi*k
    rate=v[:,None]/(2*mu)+1j*omega[None,:]
    segment=np.full(rate.shape,dx,dtype=np.complex128)
    np.divide(-np.expm1(-rate*dx),rate,out=segment,where=np.abs(rate)>1e-14)
    coefficients=np.sum(amplitude[:,None]*np.exp(-1j*np.arange(n)[:,None]*dx*omega)*segment,axis=0)
    constant=float(coefficients[modes].real)
    outputs=[];bounds=[];minimum=[]
    for t in times:
        x=np.arange(n+1)*dx-mean*t
        factors=coefficients*np.exp(-mu*omega*omega*t)
        phi=(np.exp(1j*x[:,None]*omega)@factors).real
        min_phi=float(phi.min())
        if min_phi<=1e-9*constant: raise ValueError('Cole-Hopf evaluation poorly conditioned')
        values=mean-2*mu*n*np.diff(np.log(phi))
        a=mu*(2*np.pi)**2*t
        tail=2*constant*np.exp(-a*(modes+1)**2)/(-np.expm1(-a*(2*modes+3)))
        bound=float(4*mu*n*(-np.log1p(-tail/min_phi))) if tail<min_phi else None
        outputs.append(values);bounds.append(bound);minimum.append(min_phi/constant)
    return np.asarray(outputs),{'fourier_truncation_cell_average_bound':bounds,
        'minimum_phi_over_mean':minimum,'floating_point_error_certified':False}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('repo-id','revision','prefix','source-revision','source-prefix'):p.add_argument('--'+name,required=True)
    p.add_argument('--preflight',action='store_true')
    args=p.parse_args(argv)
    if not os.environ.get('JOB_ID'):p.error('Numeric source reads require budgeted HF Job')
    import signal
    signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(TimeoutError('Reference preflight deadline')))
    signal.alarm(20*60)
    import numpy as np,h5py
    from huggingface_hub import HfApi,hf_hub_download
    start=time.monotonic()
    report_path=hf_hub_download(args.repo_id,args.source_prefix+'/report.json',repo_type='dataset',revision=args.source_revision)
    source_report=json.loads(Path(report_path).read_text())
    report={'status':'running','job_id':os.environ['JOB_ID'],'formula_source':FORMULA_SOURCE,
        'periodic_specialization':'Mean removal, periodic heat Fourier series, exact exponential initial-segment integrals, cell-average log ratios',
        'interpretation':'Published initial values define a NEW piecewise-constant periodic initial field.',
        'scope':'Six higher-viscosity parameter files; three source trajectories each; three archived times.',
        'limitations':['Neither interpretation of the Nu label is assumed proven by this comparison.',
            'Archived point/cell-average semantics and original smooth initial field remain unresolved.',
            'Mode refinement and truncation estimates exclude certified floating-point error.',
            'No claim for lower-viscosity files, no new official case, no PDE time-stepping reference solver.'],
        'records':[]}
    for source in source_report['sources']:
        if source['family']!='burgers' or float(source['attrs']['Nu'])<.1:continue
        path=hf_hub_download(args.repo_id,args.source_prefix+'/burgers/'+source['file']+'.subset.h5',
            repo_type='dataset',revision=args.source_revision)
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=source['subset_sha256']:raise ValueError('Subset checksum mismatch')
        label=float(source['attrs']['Nu'])
        with h5py.File(path,'r') as data:
            times=data['t-coordinate'][[1,10,100]].astype(np.float64)
            for row in (0,4,9):
                initial=data['tensor'][row,0].astype(np.float64)
                archived=np.asarray(data['tensor'][row],dtype=np.float64)[[1,10,100]]
                record={'file':source['file'],'source_index':int(data['source_indices'][row]),
                    'Nu_attribute':label,'times':times.tolist(),'hypotheses':{}}
                for name,mu in (('Nu',label),('Nu_over_pi',label/np.pi)):
                    try:
                        coarse,_=cole_hopf_averages(initial,mu,times,32)
                        fine,bounds=cole_hopf_averages(initial,mu,times,64)
                        record['hypotheses'][name]={'diffusivity':mu,
                            'mode_refinement_max_abs':float(abs(coarse-fine).max()),
                            'archive_difference_max_abs_by_time':abs(fine-archived).max(axis=1).tolist(),
                            'mean_error_max_abs':float(abs(fine.mean(axis=1)-initial.mean()).max()),**bounds}
                    except ValueError as exc:record['hypotheses'][name]={'status':'ill_conditioned','reason':str(exc)}
                report['records'].append(record)
    report.update(status='formula_diagnostic_completed',source_trajectories=len(report['records']),
        elapsed_seconds=time.monotonic()-start,reference_certification='not_complete')
    root=Path('/tmp/burgers-formula-report');root.mkdir()
    (root/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    commit=HfApi().upload_folder(repo_id=args.repo_id,repo_type='dataset',revision=args.revision,
        folder_path=root,path_in_repo=args.prefix,commit_message='Record bounded published-formula Burgers diagnostic')
    print(json.dumps({'status':report['status'],'report_revision':commit.oid,'source_trajectories':report['source_trajectories'],'elapsed_seconds':report['elapsed_seconds']}),flush=True)
    return 0


if __name__=='__main__':raise SystemExit(main())
