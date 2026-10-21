"""Bounded first native BDF segment of frozen3D transient traction.
Later continuation is conditional on checkpoint review and the SAME absolute4h deadline.
No accuracy validation; partial trajectory is never a candidate.
"""
import argparse,csv,hashlib,json,re,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'feelpp-transient3d-segment-bundle-v1'))
import native_feelpp_powerlaw_first as source
from native_closed_cavity import save,SOCKET
from titan_resources import reservation
CASE='ch02-2-1-8-06-power_law_traction'
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--snapshot',type=Path,required=True);p.add_argument('--workers',type=int);a=p.parse_args();source.CASE=CASE;source.RANKS=8
 job,meshinfo=source.prepare(a.root,a.snapshot);cfg=job/'native/cfd.cfg';s=cfg.read_text();assert s.count('ts.time-final=1\n')==2
 cfg.write_text(s.replace('ts.time-final=1\n','ts.time-final=0.100000001\n').replace('ts.time-step=0.001\n','ts.time-step=0.01\n'))
 plan=json.loads((job/'parallel-numerical-plan.json').read_text());start=time.time();plan.update(native_time_scheme='BDF1',dt_seconds=.01,expected_time_steps=103,first_segment_steps=10,first_segment_end=.1,segment_schedule=[{'start':0.,'end':.1,'steps':10,'dt':.01},{'start':.1,'end':.173,'steps':8,'dt':.073/8},{'start':.173,'end':.397,'steps':23,'dt':.224/23},{'start':.397,'end':.719,'steps':33,'dt':.322/33},{'start':.719,'end':1.,'steps':29,'dt':.281/29}],absolute_solve_deadline_unix=start+14300,aggregate_maximum_seconds=14400,continuation_policy='No automatic continuation/retry. Review native BDF1 checkpoint and same frozen mesh/ranks. All later segments inherit this absolute deadline including idle time; no budget resets.103steps proposed maximum dt.01; no temporal accuracy claim. First segment ends at original ramp corner. Every requested output remains an exact native endpoint; physical history still original0..1.',source_evidence=['feelpp-native-stage/source/tsbase.cpp','feelpp-native-stage/source/tsbase.hpp','feelpp-native-stage/source/bdf.hpp','feelpp-native-stage/source/fluidmechanicscreate.cpp'])
 save(job/'parallel-numerical-plan.json',plan)
 name='ch02feelpp-3d-transient-'+hashlib.sha256(CASE.encode()).hexdigest()[:10]+'-segment0'
 command=['docker','--host',SOCKET,'run','--name',name,'--network','none','--cpus','8','--memory','16g','--label','ch02.workload=parallel_long','--user','0:0','-e','HOME=/tmp','-e','OMP_NUM_THREADS=1','-e','OPENBLAS_NUM_THREADS=1','-v',f'{job.resolve()}:/work','-w','/work/native','--entrypoint','/bin/bash',source.IMAGE,'-c','mpirun --allow-run-as-root --oversubscribe -np 8 /usr/bin/feelpp_toolbox_fluid --config-file /work/native/cfd.cfg']
 state={'design_id':CASE,'status':'running','container':name,'producer':'unmodified Feel++ CFD toolbox v0.111.0','numerical_validation':False,'reference_produced':False,'segment':0,**meshinfo}
 try:
  with reservation(a.root,name,cpu=8,memory_limit_bytes=16*1024**3,workload='parallel_long'):
   save(job/'execution.json',{'command':command,'image':source.IMAGE,'native_ranks':8,'start_unix':start,'solver_budget_seconds':14300,'absolute_solve_deadline_unix':start+14300,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()});save(job/'status.json',state)
   with (job/'native-solver.log').open('w') as out:result=subprocess.run(command,stdout=out,stderr=subprocess.STDOUT,timeout=max(1,start+14300-time.time()))
   current=json.loads((job/'status.json').read_text())
   if current['status']=='stopped_runtime_limit':return
   state.update(native_exit_code=result.returncode,status='needs_attention')
   if result.returncode==0:
    output=job/'native/output/np_8';reasons=[int(v) for v in re.findall(r'convergence reason\s*:\s*(-?\d+)',(output/'logs/rank-000000.log').read_text())];assert len(reasons)==10 and all(v in (2,3,4) for v in reasons)
    with (output/'fluid.measures/values.csv').open() as f:times=[float(row['time']) for row in csv.DictReader(f)]
    assert abs(times[-1]-.1)<1e-10 and (output/'fluid.ts/velocity/metadata').exists() and (output/'fluid.ts/pressure/metadata').exists()
    state.update(status='native_checkpoint_pending_continuation',last_native_time=times[-1],native_positive_convergence_reasons=reasons,scope='Only original ramp segment0..0.1 computed. Remaining exact-time segments require reviewed native restart; no full candidate produced.')
 except Exception as ex:
  state.update(status='needs_attention',error=repr(ex))
  if isinstance(ex,subprocess.TimeoutExpired):
   info=json.loads(subprocess.check_output(['docker','--host',SOCKET,'inspect',name]))[0];assert info['Image']==source.IMAGE and any(m['Source']==str(job) and m['Destination']=='/work' for m in info['Mounts']);save(job/'timeout-container-identity.json',info);subprocess.run(['docker','--host',SOCKET,'stop','--time','30',info['Id']],check=True);state['status']='stopped_runtime_limit'
 current=json.loads((job/'status.json').read_text()) if (job/'status.json').exists() else {}
 if current.get('status')=='stopped_runtime_limit':return
 state['finished_unix']=time.time();save(job/'status.json',state)
if __name__=='__main__':main()
