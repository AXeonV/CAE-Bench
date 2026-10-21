"""One reviewed native checkpoint continuation with a source-confirmed PC change.
No automatic retries, no budget reset, no full-reference claim for a partial segment.
"""
import argparse,csv,hashlib,json,shutil,subprocess,sys,time,re
from pathlib import Path
from native_closed_cavity import SOCKET,save
from titan_resources import reservation
CASE='ch02-2-1-8-06-power_law_traction'
OLD_ID='f57f1bb6f684daaf716b7cffeaaf38bb23afd123ae1e60ff3361020aceb53a68'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int);a=ap.parse_args();job=a.root/'cases'/CASE
 old=json.loads((job/'status.json').read_text());ex=json.loads((job/'execution.json').read_text());deadline=ex['absolute_solve_deadline_unix'];assert deadline-time.time()>3600
 assert old['status']=='stopped_runtime_limit'
 info=json.loads(subprocess.check_output(['docker','--host',SOCKET,'inspect',OLD_ID]))[0]
 assert info['Id']==OLD_ID and not info['State']['Running'] and info['State']['Pid']==0 and info['Image']==ex['image']
 assert info['State']['StartedAt']=='2026-10-21T20:47:26.267136006Z' and any(v['Source']==str(job) and v['Destination']=='/work' for v in info['Mounts'])
 for fld in ['velocity','pressure']:
  base=job/'native/output/np_8/fluid.ts'/fld;meta=(base/'metadata').read_text();assert abs(float(meta.split()[-1])-.04)<1e-12 and (base/f'{fld}-4.h5').exists()
 archive=job/'before-reviewed-pc-reuse';assert not archive.exists();archive.mkdir();save(archive/'immutable-container.json',info)
 for name in ['native','native-solver.log','status.json','execution.json','parallel-numerical-plan.json']:shutil.move(str(job/name),str(archive/name))
 native=job/'native';native.mkdir()
 for p in (archive/'native').iterdir():
  if p.is_file():shutil.copy2(p,native/p.name)
 output=native/'output/np_8';output.mkdir(parents=True);shutil.copytree(archive/'native/output/np_8/fluid.ts',output/'fluid.ts')
 restart=native/'restart-mesh';restart.mkdir()
 for name in ['fluid.mesh.json','fluid.mesh.h5']:shutil.copy2(archive/'native/output/np_8'/name,restart/name)
 meshinfo=json.loads((restart/'fluid.mesh.json').read_text());assert meshinfo['mesh']['partition']['n']==8
 modelpath=native/'cfd.json';model=json.loads(modelpath.read_text());model['Meshes']['fluid']['Import']={'filename':'/work/native/restart-mesh/fluid.mesh.json','partition':False,'number-of-partition':8}
 points=model['PostProcess']['fluid']['Measures']['Points'];batch={};layout={}
 for prefix,group in [('midpoint_','midpoints'),('vertex_','vertices')]:
  keys=sorted(k for k in points if k.startswith(prefix));assert keys;layout[group]=keys;batch[group]={'coord':[points[k]['coord'] for k in keys],'fields':points[keys[0]]['fields'],'include_coordinates':1,'output':{'type':'values'}}
 model['PostProcess']['fluid']['Measures']['Points']=batch;save(modelpath,model);save(job/'native-batch-point-layout.json',{'groups':layout,'scope':'Only native batch output schema; original point coordinates and fields unchanged.'})
 cfg=native/'cfd.cfg';text=cfg.read_text();assert 'ksp-type=preonly' in text
 text=text.replace('[fluid]','ts.restart=true\nts.restart.at-last-save=true\n[fluid]',1).replace('ksp-type=preonly','ksp-type=gmres')
 text+='reuse-jac=false\nreuse-prec=true\nreuse-prec.rebuild-at-first-newton-step=true\nsnes-ksp-rtol=1e-8\nsnes-ksp-maxit=1000\nsnes-stol=1e-8\n';cfg.write_text(text)
 plan=json.loads((archive/'parallel-numerical-plan.json').read_text());plan.update(native_checkpoint_time=.04,native_checkpoint_iteration=4,checkpoint_remaining_ramp_steps=6,reviewed_linear_solver='GMRES with one MUMPS LU preconditioner build per time-step; rebuild Jacobian each Newton update; native SNES lag Jacobian1 and lag preconditioner-2',absolute_solve_deadline_unix=deadline,old_budget_not_reset=True,native_saved_partition_sha256=hashlib.sha256((restart/'fluid.mesh.h5').read_bytes()).hexdigest(),numerical_validation=False);save(job/'parallel-numerical-plan.json',plan)
 name='ch02feelpp-traction-reviewed-reusepc-segment0';cmd=list(ex['command']);cmd[cmd.index('--name')+1]=name
 assert subprocess.run(['docker','--host',SOCKET,'inspect',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode!=0
 state={**old,'status':'running','container':name,'native_exit_code':None,'reference_produced':False,'reviewed_correction':'Native checkpoint restoration and source-confirmed preconditioner configuration. Same original absolute4h deadline.'};state.pop('reason',None)
 with reservation(a.root,name,cpu=8,memory_limit_bytes=16*1024**3,workload='parallel_long'):
  execution={**ex,'command':cmd,'start_unix':time.time(),'solver_budget_seconds':int(deadline-time.time()),'absolute_solve_deadline_unix':deadline,'checkpoint_parent_id':OLD_ID,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()};save(job/'execution.json',execution);save(job/'status.json',state)
  try:
   with (job/'native-solver.log').open('w') as out:ret=subprocess.run(cmd,stdout=out,stderr=subprocess.STDOUT,timeout=max(1,deadline-time.time()))
   current=json.loads((job/'status.json').read_text())
   if current['status']=='stopped_runtime_limit':return
   state.update(native_exit_code=ret.returncode,status='needs_attention')
   if ret.returncode==0:
    reasons=[int(v) for v in re.findall(r'convergence reason\s*:\s*(-?\d+)',(output/'logs/rank-000000.log').read_text())];assert len(reasons)==6 and all(v in (2,3,4) for v in reasons)
    with (output/'fluid.measures/values.csv').open() as f:times=[float(row['time']) for row in csv.DictReader(f)]
    assert abs(times[0]-.04)<1e-10 and abs(times[-1]-.1)<1e-10
    state.update(status='native_checkpoint_pending_continuation',last_native_time=times[-1],native_positive_convergence_reasons=reasons,scope='Original ramp completed from native0.04 checkpoint; not full trajectory or reference.')
  except Exception as error:
   state.update(status='needs_attention',error=repr(error))
   if isinstance(error,subprocess.TimeoutExpired):
    live=json.loads(subprocess.check_output(['docker','--host',SOCKET,'inspect',name]))[0];assert live['Image']==ex['image'] and any(v['Source']==str(job) and v['Destination']=='/work' for v in live['Mounts']);save(job/'aggregate-budget-stop-identity.json',live);subprocess.run(['docker','--host',SOCKET,'stop','--time','30',live['Id']],check=True);state['status']='stopped_runtime_limit'
  current=json.loads((job/'status.json').read_text())
  if current['status']=='stopped_runtime_limit':return
  state['finished_unix']=time.time();save(job/'status.json',state)
if __name__=='__main__':main()
