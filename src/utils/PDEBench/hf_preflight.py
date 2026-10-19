"""Helpers for the bounded cloud preflight; not a second migration launcher.

Numerical arrays are opened only inside a budgeted HF Job. The existing pool
builder, transport, verifier and grader own case identity and consumption.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

STATE = {'version':1, 'status':'running', 'stages':{}, 'limitations':[
    'Experimental transport, not production CLI format migration.',
    'No full 250000-record migration, formal selection change, or LLM benchmark.',
    'Burgers/CNS diagnostics do not certify numerical reference precision.',
    'Limited child process checks are not a Harbor cgroup/container acceptance run.']}


def progress(args, stage, data):
    from huggingface_hub import HfApi
    STATE['job_id']=os.environ['JOB_ID']; STATE['stages'][stage]=data
    path=Path('/tmp/preflight-progress.json')
    path.write_text(json.dumps(STATE,indent=2,allow_nan=False)+'\n')
    commit=HfApi().upload_file(repo_id=args.repo_id,repo_type='dataset',revision=args.revision,
        path_or_fileobj=path,path_in_repo=args.prefix+'/progress.json',commit_message='Record bounded preflight milestone: '+stage)
    print(json.dumps({'stage':stage,'report_revision':commit.oid}),flush=True)


def exercise_transport(args,bundle,label,*,recovery=False):
    from caeoj_tools import data_pool as pool
    from caeoj.case_grading import grade_case
    start=time.monotonic()
    output=Path('/tmp/preflight-'+label+'-shards')
    catalog=pool.shard_bundle(bundle,output)
    built=time.monotonic()
    prefix=args.prefix+'/'+label
    interrupted=None
    if recovery:
        # A separate process really exits after an acknowledged remote write.
        code='''import sys
from caeoj_tools import data_pool as p
try:
 p.upload_shards(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],interrupt_after=1)
except InterruptedError:
 sys.exit(75)
raise SystemExit("interruption was not reached")
'''
        child=subprocess.run([sys.executable,'-c',code,str(output),args.repo_id,args.revision,prefix],timeout=300)
        if child.returncode!=75: raise RuntimeError('Expected interrupted uploader child exit 75')
        from huggingface_hub import HfApi
        names=HfApi().list_repo_files(args.repo_id,repo_type='dataset',revision=args.revision)
        if prefix+'/transport.json' in names: raise RuntimeError('Prematurely published transport root')
        interrupted={'child_exit_code':75,'root_absent_before_resume':True}
    receipt=pool.upload_shards(output,args.repo_id,args.revision,prefix)
    if recovery and receipt['skipped_files']!=1: raise RuntimeError('Recovery did not skip committed archive')
    uploaded=time.monotonic()
    backing=pool.HubStore(args.repo_id,receipt['revision'],cache_dir='/tmp/preflight-'+label+'-remote-cache')
    store=pool.ShardStore(backing,prefix,'/tmp/preflight-'+label+'-extracted')
    choice=pool.manifest(bundle/'selection.json')
    # Read through ordinary select before assembly, not a hand-built bypass.
    cid=next(iter(choice['cases'].values()))['case_id']
    one=pool.select(choice,store,['one='+cid],[])
    single=Path('/tmp/preflight-'+label+'-single');single.mkdir()
    pool.write_json(single/'data-manifest.json',one)
    pool.assemble(single,one,store);pool.verify(single,strict=True)
    single_downloaded=len(store.loaded)
    if single_downloaded!=1: raise RuntimeError('Single-case fetch loaded multiple shards')
    # Repeat get/assembly is idempotent; then consume every actual case.
    second=pool.assemble(single,one,store)
    if second['changed']!=0: raise RuntimeError('Repeated assembly rewrote unchanged files')
    assembled=Path('/tmp/preflight-'+label+'-assembled');assembled.mkdir()
    pool.write_json(assembled/'data-manifest.json',choice)
    pool.assemble(assembled,choice,store);pool.verify(assembled,strict=True)
    accepted=0
    for case in sorted((assembled/'cases').iterdir()):
        reference=assembled/'reference'/case.name
        if grade_case(case/'problem.json',reference/'reference.h5',reference/'grading.json')['status']!='accepted':
            raise RuntimeError('Remote shard case did not grade accepted')
        accepted+=1
    return {'cases':accepted,'remote_revision':receipt['revision'],'remote_prefix':prefix,
        'physical_files':len(list(output.rglob('*.tar')))+len(list(output.rglob('*.json'))),
        'logical_files':sum(1 for p in (bundle/'repository').rglob('*') if p.is_file()),
        'shards':len(catalog['shards']),'physical_bytes':sum(p.stat().st_size for p in output.rglob('*') if p.is_file()),
        'single_case_downloaded_shards':single_downloaded,'single_case_download_bytes':next(s['archive']['size_bytes'] for s in catalog['shards'] if s['archive']['path']==next(iter(store.loaded))),
        'single_case_range_read':False,'repeat_assembly_changed':second['changed'],
        'recovery':interrupted,'upload_receipt':receipt,
        'seconds':{'shard_pack':built-start,'upload_including_recovery':uploaded-built,
                   'remote_assembly_and_grade':time.monotonic()-uploaded,'total':time.monotonic()-start}}


def limited_solver_cases(runtime,assembled):
    """Contract-permitted formula submission under explicit process limits."""
    from caeoj.case_grading import grade_case
    script=Path('/tmp/preflight-formula-submission.py')
    script.write_text('''import os,resource,sys
import numpy as np
from caeoj.sdk import load_problem,write_result
os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:2])
resource.setrlimit(resource.RLIMIT_CPU,(120,120))
resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
p=load_problem(sys.argv[1])
u=p.arrays['initial_state'][0,:,0]
t=p.arrays['times']
b=p.manifest['physics']['parameters']['velocity']['value']
s=t*b*len(u);k=np.floor(s).astype(np.int64);f=s-k
v=np.asarray([(1-a)*np.roll(u,int(j))+a*np.roll(u,int(j)+1) for j,a in zip(k,f)])[...,None]
write_result(sys.argv[2],p,{'state':v})
print(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
''')
    entries=sorted((assembled/'cases').iterdir())
    result=[]
    for number in (0,len(entries)//2,len(entries)-1):
        directory=entries[number];out=Path('/tmp/preflight-solver-'+directory.name+'.h5')
        start=time.monotonic()
        child=subprocess.run([sys.executable,str(script),str(directory/'problem.json'),str(out)],
            env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'},text=True,capture_output=True,timeout=120)
        if child.returncode: raise RuntimeError('Limited formula submission failed: '+child.stderr[-1500:])
        if out.stat().st_size>16777216: raise RuntimeError('Output exceeds declared cap')
        ref=assembled/'reference'/directory.name
        grade=grade_case(directory/'problem.json',out,ref/'grading.json')
        if grade['status']!='accepted': raise RuntimeError('Limited submission incorrect')
        result.append({'case':directory.name,'status':grade['status'],'elapsed_seconds':time.monotonic()-start,
            'maximum_rss_kib':int(child.stdout.strip()),'output_bytes':out.stat().st_size})
    return {'cases':result,'cpu_affinity_count':2,'cpu_seconds_limit':120,'virtual_memory_bytes_limit':2*1024**3,
            'wall_seconds_limit':120,'method':'contract-permitted periodic translation formula',
            'scope':'Limited process inside HF Job; not Harbor container or filesystem isolation certification'}


def prepare_source(args,source_report,runtime):
    if not os.environ.get('JOB_ID'): raise RuntimeError('HF Job required')
    import signal
    signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(TimeoutError('Preflight internal 45-minute deadline')))
    signal.alarm(45*60)
    import fsspec,h5py,numpy as np
    from huggingface_hub import hf_hub_download,hf_hub_url
    from caeoj_tools import data_pool as pool
    # First reuse the exact existing 80-case pool, without rebuilding references.
    prefix='migration-trials/pdebench/2026-10-18/transport-cases'
    report_commit='04065771416ce7714cf61ec1f22a28005a422f59'
    path=hf_hub_download(args.repo_id,prefix+'/validation-selection.json',repo_type='dataset',revision=report_commit)
    choice=pool.manifest(path)
    old=Path('/tmp/preflight-existing80');old.mkdir()
    pool.write_json(old/'data-manifest.json',choice)
    old_store=pool.HubStore(args.repo_id,'182d3e1af1774632c29b5ad6e7a5457cc74e88a1',cache_dir='/tmp/preflight-old-cache')
    pool.assemble(old,choice,old_store)
    pool.verify(old,strict=True)
    for name,selection in choice['cases'].items():
        descriptor=pool.bound(old_store,choice['repository']['path'],selection['case'])
        certificate=descriptor['origin'].get('certificate_identity')
        if certificate is None: raise RuntimeError('Existing source provenance missing')
        pool.write_json(old/'reference'/name/'certificate.json',certificate)
    bundle=Path('/tmp/preflight-existing80-bundle');pool.pack(old,bundle,choice)
    # pack keeps case identity; its selection uses stable input hashes.
    new=pool.manifest(bundle/'selection.json')
    if {v['case_id'] for v in new['cases'].values()}!={v['case_id'] for v in choice['cases'].values()}:
        raise RuntimeError('Case identity changed during transport repack')
    value=exercise_transport(args,bundle,'existing80',recovery=True)
    value['original_case_ids_preserved']=True
    progress(args,'existing80',value)
    progress(args,'limited_solver',limited_solver_cases(runtime,old))
    # A genuinely larger contiguous source slice; read full frames once in HF.
    source=next(s for s in source_report['sources'] if s['family']=='advection' and float(s['attrs']['beta'])==.1)
    record={**source}; start=time.monotonic();subset=Path('/tmp/preflight-advection1000.h5')
    from hf_migrate import extract_span
    extracted=extract_span(source,0,1000,subset)
    record.update(local_subset=str(subset),subset_sha256=pool.digest(subset),selected_indices=list(range(1000)))
    progress(args,'expanded_source',{'records':1000,'file':source['file'],'revision':source['revision'],
        'logical_field_bytes_read':extracted['logical_field_bytes_read'],'subset_bytes':subset.stat().st_size,
        'elapsed_seconds':time.monotonic()-start,'source_indices':[0,999],
        'whole_source_checksum_verified':False,'network_bytes_not_instrumented':True})
    return [record]


def audit_other_families(args,source_report):
    import numpy as np,h5py
    from huggingface_hub import hf_hub_download
    from caeoj_tools import data_pool as pool
    result={'scope':'All 120 Burgers and 50 CNS previously extracted trajectories; diagnostics only',
            'records':[],'reference_certification':'not_complete',
            'blocking_gaps':['No approved Burgers/CNS public task contract yet.',
                'Archived generator and HF publication are not a certified per-record precision bound.',
                'Point/cell-average interpretation, exact generation settings and boundary closure need binding.',
                'No independent reference solver run or calibrated grading tolerance in this preflight.']}
    for source in source_report['sources']:
        if source['family']=='advection': continue
        path=hf_hub_download(args.repo_id,args.source_prefix+'/'+source['family']+'/'+source['file']+'.subset.h5',
            repo_type='dataset',revision=args.source_revision)
        if pool.digest(path)!=source['subset_sha256']: raise RuntimeError('Other-family subset checksum mismatch')
        with h5py.File(path,'r') as data:
            x=data['x-coordinate'][:];t=data['t-coordinate'][:]
            if not np.all(np.diff(x)>0) or not np.all(np.diff(t)>0): raise RuntimeError('Nonmonotone source axes')
            keys=['tensor'] if source['family']=='burgers' else ['density','Vx','pressure']
            periodic=source['family']=='burgers' or '_periodic_' in source['file']
            for row,idx in enumerate(data['source_indices'][:]):
                arrays={k:np.asarray(data[k][row],dtype=np.float64) for k in keys}
                entry={'family':source['family'],'file':source['file'],'source_index':int(idx),
                       'finite':all(np.isfinite(a).all() for a in arrays.values()),
                       'frames':len(t),'periodic_from_source_name':periodic,
                       'minimum':{k:float(a.min()) for k,a in arrays.items()},'status':'diagnostic_only_not_certified'}
                if not entry['finite']: raise RuntimeError('Nonfinite source subset')
                if source['family']=='burgers':
                    u=arrays['tensor'];mean=u.mean(axis=1);energy=(u*u).mean(axis=1)
                    entry.update(mean_drift_max_abs=float(abs(mean-mean[0]).max()),
                        mean_square_increase_max=float(np.maximum(np.diff(energy),0).max()))
                else:
                    rho,v,p=(arrays[k] for k in keys)
                    entry['positive_density_and_pressure']=bool((rho>0).all() and (p>0).all())
                    if periodic:
                        mass=rho.mean(axis=1);momentum=(rho*v).mean(axis=1)
                        entry.update(density_mean_drift_max_abs=float(abs(mass-mass[0]).max()),
                            momentum_mean_drift_max_abs=float(abs(momentum-momentum[0]).max()))
                    else:
                        entry['conservation_check']='Not inferred from domain totals; boundary fluxes unavailable'
                result['records'].append(entry)
    result['burgers_records']=sum(r['family']=='burgers' for r in result['records'])
    result['cns_records']=sum(r['family']=='compressible' for r in result['records'])
    return result


def finish_preflight(args,source_report,runtime,generated,bundle,report,started):
    import signal
    from caeoj_tools import data_pool as pool
    from huggingface_hub import HfApi
    if len(report['records'])!=1000: raise RuntimeError('Expanded case count differs')
    progress(args,'construction1000',{'cases':len(report['records']),
        'construction_checks_seconds':sum(x['construction_and_checks_seconds'] for x in report['records']),
        'max_alternate_integral_error':max(x['alternate_integral_max_abs'] for x in report['records']),
        'contract':'All 1000 actual inputs loaded through SDK; all 201 times and 1024 cells checked; reference and wrong-output graded'})
    progress(args,'expanded1000',exercise_transport(args,bundle,'expanded1000'))
    progress(args,'other_families',audit_other_families(args,source_report))
    STATE['status']='preflight_completed';STATE['elapsed_seconds']=time.monotonic()-started
    STATE['disk_usage_bytes']=shutil.disk_usage('/tmp').used
    STATE['disk_usage_scope']='End-of-run filesystem occupancy, not peak measurement'
    reports=Path('/tmp/preflight-final');reports.mkdir()
    pool.write_json(reports/'report.json',STATE)
    pool.write_json(reports/'expanded-case-records.json',report)
    shutil.copyfile(bundle/'selection.json',reports/'validation-selection.json')
    commit=HfApi().upload_folder(repo_id=args.repo_id,repo_type='dataset',revision=args.revision,
        folder_path=reports,path_in_repo=args.prefix+'/reports',commit_message='Record bounded preflight results and complete case provenance')
    signal.alarm(0)
    print(json.dumps({'status':STATE['status'],'report_revision':commit.oid,'elapsed_seconds':STATE['elapsed_seconds']}),flush=True)
    return 0
