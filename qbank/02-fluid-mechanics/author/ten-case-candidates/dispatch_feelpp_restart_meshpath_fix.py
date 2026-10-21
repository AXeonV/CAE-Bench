"""One source-confirmed mesh-path index repair, before any resumed native step."""
import argparse,json,subprocess,time,hashlib,re,csv
from pathlib import Path
from native_closed_cavity import SOCKET,save
from titan_resources import reservation
CASE='ch02-2-1-8-06-power_law_traction'
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--snapshot',type=Path,required=True);p.add_argument('--workers',type=int);a=p.parse_args();job=a.root/'cases'/CASE;st=json.loads((job/'status.json').read_text());ex=json.loads((job/'execution.json').read_text());assert st['status']=='needs_attention' and st['native_exit_code']==134
 log=job/'native-solver.log';assert 'setupRestart' in log.read_text() and 'SNES Residual norm' not in log.read_text();deadline=ex['absolute_solve_deadline_unix'];assert deadline-time.time()>1800
 info=json.loads(subprocess.check_output(['docker','--host',SOCKET,'inspect',st['container']]))[0];assert not info['State']['Running'] and info['State']['Pid']==0 and info['Image']==ex['image'] and any(x['Source']==str(job) and x['Destination']=='/work' for x in info['Mounts'])
 archive=job/'mesh-path-startup-failure';assert not archive.exists();archive.mkdir();save(archive/'status.json',st);save(archive/'execution.json',ex);save(archive/'container.json',info);log.rename(archive/'native-solver.log')
 index=job/'native/output/np_8/fluid.mesh.path';assert not index.exists();index.write_text('/work/native/restart-mesh/fluid.mesh.json\n')
 name=st['container']+'-meshpath';cmd=list(ex['command']);cmd[cmd.index('--name')+1]=name;assert subprocess.run(['docker','--host',SOCKET,'inspect',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode!=0
 with reservation(a.root,name,cpu=8,memory_limit_bytes=16*1024**3,workload='parallel_long'):
  st.update(status='running',container=name,native_exit_code=None,reference_produced=False);ex.update(command=cmd,start_unix=time.time(),solver_budget_seconds=int(deadline-time.time()),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),startup_repair='ModelMesh::setupRestart requires rootRepository/fluid.mesh.path even when Meshes.Import filename supplied. Saved exact8rank partition index restored; prior attempt failed before any native step.');save(job/'status.json',st);save(job/'execution.json',ex)
  try:
   with log.open('w') as out:ret=subprocess.run(cmd,stdout=out,stderr=subprocess.STDOUT,timeout=max(1,deadline-time.time()))
   if json.loads((job/'status.json').read_text())['status']=='stopped_runtime_limit':return
   st.update(status='needs_attention',native_exit_code=ret.returncode)
   if ret.returncode==0:
    output=job/'native/output/np_8';reasons=[int(v) for v in re.findall(r'convergence reason\s*:\s*(-?\d+)',(output/'logs/rank-000000.log').read_text())];assert len(reasons)==6 and all(v in (2,3,4) for v in reasons)
    with (output/'fluid.measures/values.csv').open() as f:times=[float(row['time']) for row in csv.DictReader(f)]
    assert abs(times[0]-.04)<1e-10 and abs(times[-1]-.1)<1e-10
    st.update(status='native_checkpoint_pending_continuation',last_native_time=times[-1],native_positive_convergence_reasons=reasons,scope='Only original ramp continuation0.04..0.1; not full candidate.')
  except Exception as error:
   st.update(status='needs_attention',error=repr(error))
   if isinstance(error,subprocess.TimeoutExpired):
    live=json.loads(subprocess.check_output(['docker','--host',SOCKET,'inspect',name]))[0];assert live['Image']==ex['image'] and any(x['Source']==str(job) and x['Destination']=='/work' for x in live['Mounts']);save(job/'aggregate-budget-stop-identity.json',live);subprocess.run(['docker','--host',SOCKET,'stop','--time','30',live['Id']],check=True);st['status']='stopped_runtime_limit'
  if json.loads((job/'status.json').read_text())['status']=='stopped_runtime_limit':return
  st['finished_unix']=time.time();save(job/'status.json',st)
if __name__=='__main__':main()
