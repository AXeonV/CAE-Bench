"""One reviewed endpoint correction. Preserve all previous raw evidence; no retry loop."""
import argparse,hashlib,json,math,shutil,subprocess,sys,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,str(Path(__file__).parent/'feelpp-transient2d-bundle-v3'))
from finish_feelpp_powerlaw import finish
from native_closed_cavity import SOCKET,save
from titan_resources import reservation
CASES=['ch02-2-1-6-01-power_law_channel','ch02-2-1-6-06-power_law_traction']
def run(root,snapshot,cid):
 job=root/'cases'/cid;old=json.loads((job/'status.json').read_text());ex=json.loads((job/'execution.json').read_text())
 assert old['status']=='native_raw_complete_pending_package' and old['native_exit_code']==0
 info=json.loads(subprocess.check_output(['docker','--host',SOCKET,'inspect',old['container']]))[0]
 assert not info['State']['Running'] and info['State']['Pid']==0 and info['State']['ExitCode']==0
 assert info['Image']==ex['image'] and any(x['Source']==str(job) and x['Destination']=='/work' for x in info['Mounts'])
 assert ex['native_ranks']==8 and '-np 8 ' in ex['command'][-1]
 archive=job/'before-endpoint-correction';assert not archive.exists();archive.mkdir()
 save(archive/'immutable-container.json',info)
 for name in ['native','native-solver.log','execution.json','status.json','parallel-numerical-plan.json']:
  shutil.move(str(job/name),str(archive/name))
 native=job/'native';native.mkdir()
 for p in (archive/'native').iterdir():
  if p.is_file() and p.suffix in ['.json','.cfg','.msh']:shutil.copy2(p,native/p.name)
 cfg=native/'cfd.cfg';text=cfg.read_text();assert text.count('ts.time-final=1\n')==2
 cfg.write_text(text.replace('ts.time-final=1\n','ts.time-final=1.000000001\n'))
 plan=json.loads((archive/'parallel-numerical-plan.json').read_text());plan.update(expected_time_steps=1000,solver_endpoint=1.000000001,physical_output_end=1.0,endpoint_reason='Fixed-version TSBase::isFinished compares time>Tf; accumulated dt reaches1.0000000000000007. Epsilon endpoint includes1.0 step, excludes1.001; frozen physical output times unchanged.',previous_attempt_elapsed_seconds=old['finished_unix']-ex['start_unix'])
 save(job/'parallel-numerical-plan.json',plan)
 name=old['container']+'-endpoint';command=list(ex['command']);command[command.index('--name')+1]=name
 assert subprocess.run(['docker','--host',SOCKET,'inspect',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode!=0
 budget=14300-math.ceil(plan['previous_attempt_elapsed_seconds']);assert budget>7200
 newex={**ex,'command':command,'start_unix':time.time(),'solver_budget_seconds':budget,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'previous_attempt_container_id':info['Id'],'aggregate_maximum_seconds':14400,'correction':'Reviewed floating endpoint correction only; prior successful raw solve retained, no physics/timestep/mesh change.'}
 status={**old,'container':name,'status':'running','reference_produced':False,'native_exit_code':None};status.pop('packaging_error',None)
 with reservation(root,name,cpu=8,memory_limit_bytes=8*1024**3,workload='parallel_long'):
  newex['start_unix']=time.time();save(job/'execution.json',newex);save(job/'status.json',status)
  try:
   with (job/'native-solver.log').open('w') as out:ret=subprocess.run(command,stdout=out,stderr=subprocess.STDOUT,timeout=budget)
   current=json.loads((job/'status.json').read_text())
   if current['status']=='stopped_runtime_limit':return
   status.update(status='native_raw_complete_pending_package' if ret.returncode==0 else 'needs_attention',native_exit_code=ret.returncode,finished_unix=time.time());save(job/'status.json',status)
  except subprocess.TimeoutExpired:
   live=json.loads(subprocess.check_output(['docker','--host',SOCKET,'inspect',name]))[0]
   assert live['Image']==ex['image'] and any(x['Source']==str(job) and x['Destination']=='/work' for x in live['Mounts'])
   save(job/'aggregate-budget-stop-identity.json',live)
   subprocess.run(['docker','--host',SOCKET,'stop','--time','30',live['Id']],check=True)
   status.update(status='stopped_runtime_limit',finished_unix=time.time(),reason='Aggregate prior and corrected solve budget exhausted');save(job/'status.json',status);return
 if status['status']=='native_raw_complete_pending_package':
  try:finish(root,snapshot,case_id=cid)
  except Exception as error:status['packaging_error']=repr(error);save(job/'status.json',status)
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--snapshot',type=Path,required=True);p.add_argument('--workers',type=int);a=p.parse_args()
 with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(lambda cid:run(a.root,a.snapshot,cid),CASES))
if __name__=='__main__':main()
