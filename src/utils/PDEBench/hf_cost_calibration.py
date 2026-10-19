# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["huggingface_hub>=1.0,<2", "numpy>=2,<3", "h5py>=3.13,<4", "fsspec[http]>=2025.3", "jax[cpu]==0.4.38"]
# ///
"""Measured cloud I/O and pinned upstream solver replay; never certifies cases."""
import argparse,ast,hashlib,json,os,signal,subprocess,sys,time
from pathlib import Path

FORMULA_PY = ''
REV='4ff3e3a4aa1561721b5571fa3a048a0a463e0568'
UPSTREAM={
 'utils.py':('pdebench/data_gen/data_gen_NLE/utils.py','fc3a848a12e79e89bb53898944fe96ccbc44236b22ce4b6a705eda00a8018d71'),
 'burgers.py':('pdebench/data_gen/data_gen_NLE/BurgersEq/burgers_multi_solution_Hydra.py','905f01f0c60749665f9b55e0a58e4894df0c3fad62eea1b9a6ffbeae60ca6c50'),
 'cns.py':('pdebench/data_gen/data_gen_NLE/CompressibleFluid/CFD_multi_Hydra.py','5d3fc091cf901b7d1b8a51f985fc8e197e90a591cbccd1d8e687d80ac8e0d697')}


def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
 return h.hexdigest()


def solver_ast(text,family):
 """Retain upstream numerical kernels, return evolve before random init/I/O."""
 tree=ast.parse(text);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
 main.decorator_list=[]
 stop=None
 for i,n in enumerate(main.body):
  if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==('u' if family=='burgers' else 'Q') for t in n.targets):
   stop=i;break
 if stop is None:raise ValueError('Pinned upstream entry structure changed')
 main.body=main.body[:stop]+[ast.Return(value=ast.Name(id='evolve',ctx=ast.Load()))]
 tree.body=[n for n in tree.body if not (isinstance(n,ast.Import) and any(x.name=='hydra' for x in n.names))
            and not (isinstance(n,ast.ImportFrom) and n.module=='omegaconf')]
 return ast.fix_missing_locations(tree)


def child(config_path):
 if not os.environ.get('JOB_ID'):raise RuntimeError('HF Job required')
 os.environ.update(JAX_PLATFORMS='cpu',JAX_ENABLE_X64='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
 import types,importlib.util
 import numpy as np,h5py,jax,jax.numpy as jnp
 cfg=json.loads(Path(config_path).read_text());root=Path(cfg['upstream_dir']);family=cfg['source']['family']
 # Pure indexing API compatibility; numerical expressions and stencils unchanged.
 tree=ast.parse((root/'utils.py').read_text())
 class IndexAPI(ast.NodeTransformer):
  count=0
  def visit_Attribute(self,n):
   self.generic_visit(n)
   if n.attr=='loc':n.attr='at';self.count+=1
   return n
 compatibility=IndexAPI();tree=ast.fix_missing_locations(compatibility.visit(tree))
 utility=types.ModuleType('utils');sys.modules['utils']=utility
 exec(compile(tree,str(root/'utils.py'),'exec'),utility.__dict__)
 space={'__name__':'pinned_upstream'}
 exec(compile(solver_ast((root/('burgers.py' if family=='burgers' else 'cns.py')).read_text(),family),'pinned_upstream','exec'),space)
 with h5py.File(cfg['subset'],'r') as f:
  rows=[0] if cfg.get('single') else [0,9];times=np.asarray(f['t-coordinate']);x=np.asarray(f['x-coordinate']);n=len(x);dx=float(np.median(np.diff(x)))
  parameters=dict(nx=n,xL=float(x[0]-dx/2),xR=float(x[-1]+dx/2),ini_time=0.,
   fin_time=round(float(times[-1]),6),dt_save=round(float(times[1]-times[0]),6),show_steps=100,if_rand_param=False)
  if family=='burgers':
   parameters.update(epsilon=float(cfg['source']['attrs']['Nu']),CFL=.25)
   initial=np.asarray(f['tensor'][rows,0],dtype=np.float64);archived=np.asarray(f['tensor'][rows],dtype=np.float64)
   wrapped=types.SimpleNamespace(multi=types.SimpleNamespace(**parameters))
  else:
   import re
   eta=float(re.search(r'Eta([^_]+)',cfg['source']['file']).group(1));zeta=float(re.search(r'Zeta([^_]+)',cfg['source']['file']).group(1))
   parameters.update(ny=1,nz=1,yL=-1.,yR=1.,zL=-1.,zR=1.,CFL=.3,gamma=5/3,p_floor=1e-4,eta=eta,zeta=zeta,
    bc='periodic' if '_periodic_' in cfg['source']['file'] else 'trans',if_second_order=1.)
   initial=np.zeros((len(rows),5,n+4,5,5),dtype=np.float64)
   for axis,key in ((0,'density'),(1,'Vx'),(4,'pressure')):initial[:,axis,2:-2,2,2]=f[key][rows,0]
   archived={key:np.asarray(f[key][rows],dtype=np.float64) for key in ('density','Vx','pressure')}
   wrapped=types.SimpleNamespace(args=types.SimpleNamespace(**parameters))
 evolve=space['main'](wrapped);run=jax.jit(jax.vmap(evolve));array=jnp.asarray(initial)
 begin=time.monotonic();run=run.lower(array).compile();compile_seconds=time.monotonic()-begin
 Path(cfg['output']).write_text(json.dumps({'status':'compile_completed','compile_seconds':compile_seconds,'batch_cases':len(rows),'parameters':parameters})+'\n')
 begin=time.monotonic();output=jax.block_until_ready(run(array));first_solve=time.monotonic()-begin;first=compile_seconds+first_solve
 warm=[]
 def timing_checkpoint():
  data={'status':'running','cold_compile_and_solve_seconds':first,'compile_seconds':compile_seconds,'first_solve_seconds':first_solve,'warm_batch_solve_seconds':warm,'batch_cases':len(rows),'frames':len(times),'cells':n,'parameters':parameters}
  if warm:data['warm_seconds_per_trajectory']=sum(warm)/len(warm)/len(rows)
  Path(cfg['output']).write_text(json.dumps(data,indent=2)+'\n')
 timing_checkpoint()
 for _ in range(0 if cfg.get('single') else 2):
  begin=time.monotonic();output=jax.block_until_ready(run(array));warm.append(time.monotonic()-begin);timing_checkpoint()
 if family=='burgers':
  values=np.asarray(output);finite=bool(np.isfinite(values).all());diff={'tensor':float(np.max(abs(values-archived)))}
 else:
  last=np.asarray(output[0]);values={key:np.asarray(output[i]).squeeze((-1,-2)) for i,key in ((1,'density'),(2,'Vx'),(5,'pressure'))}
  finite=all(np.isfinite(v).all() for v in values.values());diff={k:float(np.max(abs(v-archived[k]))) for k,v in values.items()}
  if not np.allclose(last,parameters['fin_time'],atol=1e-7):raise RuntimeError('Solver failed to reach final time')
 result={'status':'completed','source_indices':[0] if cfg.get('single') else [0,9999],'batch_cases':len(rows),'frames':len(times),'cells':n,'parameters':parameters,
  'cold_compile_and_solve_seconds':first,'compile_seconds':compile_seconds,'first_solve_seconds':first_solve,'warm_batch_solve_seconds':warm,'warm_seconds_per_trajectory':sum(warm)/len(warm)/len(rows) if warm else None,
  'finite':finite,'archive_difference_max_abs':diff,'jax_version':jax.__version__,'jax_x64':bool(jax.config.jax_enable_x64),
  'utils_loc_to_at_replacements':compatibility.count,'reference_certified':False,
  'limits':'Same published solver with archived numeric initial values; not original smooth initial state or independent high-accuracy validation.'}
 if family=='burgers':
  result['effective_diffusivity']=parameters['epsilon']/np.pi
 Path(cfg['output']).write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')


def mechanical(args,report,persist):
 import fsspec,h5py,numpy as np
 from huggingface_hub import HfApi,hf_hub_url,hf_hub_download
 api=HfApi();root=Path('/tmp/cost-io');root.mkdir();fs=fsspec.filesystem('http',client_kwargs={'trust_env':True})
 for number,source in enumerate(report['sources']):
  path=root/'payload.h5';start=time.monotonic();keys=['tensor'] if source['family']!='compressible' else ['density','Vx','pressure']
  row={'family':source['family'],'file':source['file'],'records':256,'source_spans':[[0,127],[5000,5127]],
       'source_dtype':{k:v['dtype'] for k,v in source['fields'].items()},'whole_source_checksum_verified':False}
  url=hf_hub_url(source['repo_id'],source['file'],repo_type='dataset',revision=source['revision'])
  with fs.open(url,'rb',block_size=8*1024**2,cache_type='blockcache',cache_options={'maxblocks':8}) as stream:
   with h5py.File(stream,'r') as data,h5py.File(path,'w') as out:
    frames=source['fields'][keys[0]]['shape'][1];nx=1024;logical=0
    out['x-coordinate']=data['x-coordinate'][:];out['t-coordinate']=data['t-coordinate'][:frames]
    out['source_indices']=np.r_[0:128,5000:5128]
    for key in keys:
     # float64 matches the planned derived reference storage, not original bytes.
     target=out.create_dataset(key,(256,frames,nx),dtype='float64',chunks=(1,min(16,frames),nx),compression='gzip',compression_opts=1,shuffle=True)
     for first,last,offset in ((0,128,0),(5000,5128,128)):
      values=np.asarray(data[key][first:last],dtype=np.float64)
      if not np.isfinite(values).all():raise RuntimeError('Nonfinite measured source span')
      target[offset:offset+128]=values;logical+=values.nbytes
  extracted=time.monotonic();checksum=sha(path);hashed=time.monotonic();remote=args.prefix+'/source-payloads/'+str(number).zfill(2)+'.h5'
  receipt=api.upload_file(repo_id=args.repo_id,repo_type='dataset',revision=args.revision,path_or_fileobj=path,path_in_repo=remote,
   commit_message='Measure bounded source payload transfer '+str(number))
  uploaded=time.monotonic()
  # Fresh cache per source; no previously downloaded payload can satisfy this read.
  got=Path(hf_hub_download(args.repo_id,remote,repo_type='dataset',revision=receipt.oid,cache_dir=str(root/('cache-'+str(number)))))
  if sha(got)!=checksum:raise RuntimeError('Remote measured payload checksum mismatch')
  checked=time.monotonic()
  with h5py.File(got,'r') as data:
   for key in keys:
    for i in range(0,256,32):
     if not np.isfinite(data[key][i:i+32]).all():raise RuntimeError('Remote numeric read-back failed')
  finished=time.monotonic()
  row.update(logical_float64_bytes=logical,stored_bytes=path.stat().st_size,sha256=checksum,revision=receipt.oid,
   seconds={'extract_check_write':extracted-start,'hash':hashed-extracted,'upload':uploaded-hashed,'download_hash':checked-uploaded,'numeric_readback':finished-checked,'total':finished-start},
   status='source_transport_verified',case_certification=False)
  report['records'].append(row);persist();path.unlink();__import__('shutil').rmtree(root/('cache-'+str(number)))


def upstream_files(report):
 from urllib.request import urlopen
 root=Path('/tmp/cost-reference');root.mkdir()
 for name,(remote,expected) in UPSTREAM.items():
  path=root/name;path.write_bytes(urlopen('https://raw.githubusercontent.com/pdebench/PDEBench/'+REV+'/'+remote,timeout=60).read())
  if sha(path)!=expected:raise RuntimeError('Pinned upstream source digest differs')
 report['upstream']={'revision':REV,'files':UPSTREAM,'credit':'PDEBench numerical software developed by NEC Laboratories Europe GmbH; used internally for research timing; source not redistributed.'}
 return root


def references(args,report,persist):
 from urllib.request import urlopen
 from huggingface_hub import hf_hub_download
 root=upstream_files(report)
 for source in report['sources']:
  if source['family']=='advection':continue
  subset=hf_hub_download(args.repo_id,args.source_prefix+'/'+source['family']+'/'+source['file']+'.subset.h5',repo_type='dataset',revision=args.source_revision)
  if sha(subset)!=source['subset_sha256']:raise RuntimeError('Subset identity differs')
  config={'source':source,'subset':subset,'upstream_dir':str(root),'output':str(root/'child-result.json')}
  config_path=root/'child-config.json';config_path.write_text(json.dumps(config));Path(config['output']).unlink(missing_ok=True)
  start=time.monotonic();row={'family':source['family'],'file':source['file'],'child_wall_limit_seconds':75}
  try:
   child_run=subprocess.run([sys.executable,__file__,'--child-config',str(config_path)],capture_output=True,text=True,timeout=75,
     env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','JAX_PLATFORMS':'cpu','JAX_ENABLE_X64':'1'})
   if child_run.returncode or not Path(config['output']).exists():
    row.update(status='failed',error=child_run.stderr[-1600:])
   else:row.update(json.loads(Path(config['output']).read_text()))
  except subprocess.TimeoutExpired:
   if Path(config['output']).exists():row.update(json.loads(Path(config['output']).read_text()))
   row.update(status='censored_timeout',note='75 seconds include interpreter/JAX import, compilation and three batch solves; not a 75-second warm per-case lower bound.')
  row['child_elapsed_seconds']=time.monotonic()-start;report['records'].append(row);persist()


def auxiliary(args,report,persist):
 import base64,h5py,numpy as np
 from huggingface_hub import hf_hub_download
 space={'__name__':'formula_adapter'}
 exec(compile(base64.b64decode(FORMULA_PY),'published_formula_adapter','exec'),space)
 for source in report['sources']:
  if source['family']!='burgers':continue
  subset=hf_hub_download(args.repo_id,args.source_prefix+'/burgers/'+source['file']+'.subset.h5',repo_type='dataset',revision=args.source_revision)
  if sha(subset)!=source['subset_sha256']:raise RuntimeError('Subset checksum differs')
  with h5py.File(subset,'r') as f:
   times=np.asarray(f['t-coordinate'][1:],dtype=np.float64);mu=float(source['attrs']['Nu'])/np.pi
   for row in (0,9):
    initial=np.asarray(f['tensor'][row,0],dtype=np.float64);record={'family':'burgers','file':source['file'],'source_index':int(f['source_indices'][row]),'method':'published Cole-Hopf formula','frames':len(times)+1,'diffusivity':mu,'reference_certified':False}
    start=time.monotonic()
    try:
     a,coarse=space['cole_hopf_averages'](initial,mu,times,64)
     middle=time.monotonic();b,fine=space['cole_hopf_averages'](initial,mu,times,128)
     record.update(status='formula_evaluated',seconds_64_modes=middle-start,seconds_128_modes=time.monotonic()-middle,
      mode_refinement_max_abs=float(abs(a-b).max()),max_fourier_tail_bound=max(v for v in fine['fourier_truncation_cell_average_bound'] if v is not None),
      floating_point_error_certified=False)
    except ValueError as exc:record.update(status='ill_conditioned',reason=str(exc))
    record['elapsed_seconds']=time.monotonic()-start;report['records'].append(record)
  persist()
 # One complete high-viscosity replay, not an extrapolation from a short horizon.
 root=upstream_files(report);source=next(s for s in report['sources'] if s['family']=='burgers' and float(s['attrs']['Nu'])==4.)
 subset=hf_hub_download(args.repo_id,args.source_prefix+'/burgers/'+source['file']+'.subset.h5',repo_type='dataset',revision=args.source_revision)
 config={'source':source,'subset':subset,'upstream_dir':str(root),'output':str(root/'extreme-result.json'),'single':True}
 config_path=root/'extreme-config.json';config_path.write_text(json.dumps(config));start=time.monotonic()
 record={'family':'burgers','file':source['file'],'method':'upstream full-horizon single solve','child_wall_limit_seconds':1200}
 try:
  process=subprocess.run([sys.executable,__file__,'--child-config',str(config_path)],capture_output=True,text=True,timeout=1200,
   env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','JAX_PLATFORMS':'cpu','JAX_ENABLE_X64':'1'})
  if process.returncode:record.update(status='failed',error=process.stderr[-1600:])
  else:record.update(json.loads(Path(config['output']).read_text()))
 except subprocess.TimeoutExpired:record.update(status='censored_timeout')
 record['elapsed_seconds']=time.monotonic()-start;report['records'].append(record);persist()


def cns_focus(args,report,persist):
 from huggingface_hub import hf_hub_download
 root=upstream_files(report)
 for source in report['sources']:
  if source['family']!='compressible':continue
  subset=hf_hub_download(args.repo_id,args.source_prefix+'/compressible/'+source['file']+'.subset.h5',repo_type='dataset',revision=args.source_revision)
  if sha(subset)!=source['subset_sha256']:raise RuntimeError('Focus subset differs')
  config={'source':source,'subset':subset,'upstream_dir':str(root),'output':str(root/'focus-result.json'),'single':True}
  output=Path(config['output']);output.unlink(missing_ok=True);path=root/'focus-config.json';path.write_text(json.dumps(config));start=time.monotonic()
  record={'family':'compressible','file':source['file'],'child_wall_limit_seconds':90,'method':'Single full-horizon solve with separate compilation timing'}
  try:
   process=subprocess.run([sys.executable,__file__,'--child-config',str(path)],capture_output=True,text=True,timeout=90,
    env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','JAX_PLATFORMS':'cpu','JAX_ENABLE_X64':'1'})
   if process.returncode:record.update(status='failed',error=process.stderr[-1600:])
   else:record.update(json.loads(output.read_text()))
  except subprocess.TimeoutExpired:
   if output.exists():record.update(json.loads(output.read_text()))
   record.update(status='censored_timeout',note='Single-case timeout; compilation time is separately observed when available. No invented warm throughput.')
  record['elapsed_seconds']=time.monotonic()-start;report['records'].append(record);persist()


def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument('--child-config')
 for n in ('repo-id','revision','prefix','source-revision','source-prefix'):p.add_argument('--'+n)
 p.add_argument('--calibration-mode',choices=('mechanical','references','auxiliary','cns-focus'))
 args=p.parse_args(argv)
 if not os.environ.get('JOB_ID'):p.error('All numeric reads require HF Jobs')
 os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
 if args.child_config:return child(args.child_config)
 if not all(getattr(args,k) for k in ('repo_id','revision','prefix','source_revision','source_prefix','calibration_mode')):p.error('Incomplete calibration launch')
 from huggingface_hub import HfApi,hf_hub_download
 signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(TimeoutError('Calibration 26-minute internal deadline')));signal.alarm(8*60 if args.calibration_mode=='cns-focus' else 26*60)
 started=time.monotonic();api=HfApi()
 source=json.loads(Path(hf_hub_download(args.repo_id,args.source_prefix+'/report.json',repo_type='dataset',revision=args.source_revision)).read_text())
 report={'version':1,'job_id':os.environ['JOB_ID'],'mode':args.calibration_mode,'blas_threads':1,'status':'running','sources':source['sources'],'records':[],
  'limitations':['No formal case creation for Burgers/CNS, no hidden assumptions promoted to a public contract.',
   'Source transport is not complete case packaging/grading.', 'Solver replay is a same-source diagnostic, not independent reference certification.',
   'No full migration, LLM exam or local numerical downloads.']}
 path=Path('/tmp/calibration-report.json')
 def persist():
  report['elapsed_seconds']=time.monotonic()-started;path.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
  receipt=api.upload_file(repo_id=args.repo_id,repo_type='dataset',revision=args.revision,path_or_fileobj=path,path_in_repo=args.prefix+'/report.json',commit_message='Record measured '+args.calibration_mode+' milestone')
  print(json.dumps({'mode':args.calibration_mode,'records':len(report['records']),'report_revision':receipt.oid}),flush=True)
 try:
  {'mechanical':mechanical,'references':references,'auxiliary':auxiliary,'cns-focus':cns_focus}[args.calibration_mode](args,report,persist);report['status']='completed'
 except Exception as exc:report.update(status='failed',error=type(exc).__name__+': '+str(exc).split('?')[0]);raise
 finally:persist()
 signal.alarm(0)
 return 0

if __name__=='__main__':raise SystemExit(main())
