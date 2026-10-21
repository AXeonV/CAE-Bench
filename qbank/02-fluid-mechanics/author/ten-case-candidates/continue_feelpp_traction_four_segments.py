"""Finite four native BDF1 continuations sharing the original absolute4h deadline.
Stock solver only; partial or failed trajectories never become candidates.
"""
import argparse,csv,hashlib,json,os,re,shutil,subprocess,sys,time
from pathlib import Path
import numpy as np
from native_closed_cavity import SOCKET,save
from titan_resources import reservation
from feelpp_batch_point_columns import remap_batch_row
sys.path.insert(0,str(Path(__file__).parent/'feelpp-transient2d-bundle-v3'))
from finish_feelpp_powerlaw import fields_from_native_points
from native_elmer_incompressible import package
CASE='ch02-2-1-8-06-power_law_traction'
PHASES=[(.1,.173,8),(.173,.397,23),(.397,.719,33),(.719,1.,29)]
def metadata_time(output,field):
 return float((output/'fluid.ts'/field/'metadata').read_text().split()[-1])
def archive_segment(job,label,steps):
 output=job/'native/output/np_8';archive=job/'native-segments'/label;assert not archive.exists();archive.mkdir(parents=True)
 reasons=[int(x) for x in re.findall(r'convergence reason\s*:\s*(-?\d+)',(output/'logs/rank-000000.log').read_text())];assert len(reasons)==steps and all(x in (2,3,4) for x in reasons)
 for name in ['journal.json','fluid.mesh.path']:shutil.copy2(output/name,archive/name)
 for name in ['cfd.cfg','cfd.json']:shutil.copy2(job/'native'/name,archive/name)
 for name in ['native-solver.log','execution.json','status.json']:shutil.copy2(job/name,archive/name)
 for fld in ['velocity','pressure']:shutil.copy2(output/'fluid.ts'/fld/'metadata',archive/(fld+'-metadata'))
 shutil.move(str(output/'logs'),str(archive/'logs'));shutil.move(str(output/'fluid.measures'),str(archive/'fluid.measures'))
 report={'archive':str(archive.relative_to(job)),'native_steps':steps,'native_convergence_reasons':reasons,'last_native_time':metadata_time(output,'velocity'),'solver_seconds':json.loads((archive/'status.json').read_text())['finished_unix']-json.loads((archive/'execution.json').read_text())['start_unix'],'measures_sha256':hashlib.sha256((archive/'fluid.measures/values.csv').read_bytes()).hexdigest()};save(archive/'completion.json',report);return report

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int);a=ap.parse_args();job=a.root/'cases'/CASE;output=job/'native/output/np_8'
 state=json.loads((job/'status.json').read_text());ex=json.loads((job/'execution.json').read_text());assert state['status']=='native_checkpoint_pending_continuation' and abs(state['last_native_time']-.1)<1e-10
 old=json.loads(subprocess.check_output(['docker','--host',SOCKET,'inspect',state['container']]))[0];assert not old['State']['Running'] and old['State']['Pid']==0 and old['State']['ExitCode']==0 and old['Image']==ex['image'] and any(v['Source']==str(job) and v['Destination']=='/work' for v in old['Mounts'])
 deadline=ex['absolute_solve_deadline_unix'];assert deadline-time.time()>6000
 plan=json.loads((job/'parallel-numerical-plan.json').read_text());layout=json.loads((job/'native-batch-point-layout.json').read_text());assert plan['absolute_solve_deadline_unix']==deadline
 reports=[archive_segment(job,'reviewed-ramp-0.04-to-0.1',6)];save(job/'native-segment-reports.json',reports)
 try:
  for phase,(start,end,nsteps) in enumerate(PHASES,1):
   assert abs(metadata_time(output,'velocity')-start)<1e-10 and abs(metadata_time(output,'pressure')-start)<1e-10
   estimate_per_step=max(50.,reports[-1]['solver_seconds']/reports[-1]['native_steps'])
   remaining=sum(x[2] for x in PHASES[phase-1:]);assert remaining*estimate_per_step*1.25+120<deadline-time.time(), 'Remaining native trajectory no longer fits original4h deadline'
   cfg=job/'native/cfd.cfg';text=cfg.read_text();text=re.sub(r'(?m)^ts.time-final=.*$',f'ts.time-final={end+1e-9:.17g}',text);text=re.sub(r'(?m)^ts.time-step=.*$',f'ts.time-step={(end-start)/nsteps:.17g}',text);assert 'ts.restart=true' in text and 'reuse-jac=false' in text and 'reuse-prec.rebuild-at-first-newton-step=true' in text;cfg.write_text(text)
   name=f'ch02feelpp-traction-reusepc-phase{phase}';cmd=list(ex['command']);cmd[cmd.index('--name')+1]=name;cmd[cmd.index('--user')+1]=f'{os.getuid()}:{os.getgid()}';assert subprocess.run(['docker','--host',SOCKET,'inspect',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode!=0
   with reservation(a.root,name,cpu=8,memory_limit_bytes=16*1024**3,workload='parallel_long'):
    runex={**ex,'command':cmd,'start_unix':time.time(),'solver_budget_seconds':int(deadline-time.time()),'absolute_solve_deadline_unix':deadline,'native_segment':phase,'native_segment_start':start,'native_segment_end':end,'native_segment_steps':nsteps,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()};save(job/'execution.json',runex)
    state.update(status='running',container=name,segment=phase,native_exit_code=None,reference_produced=False);state.pop('error',None);save(job/'status.json',state)
    try:
     with (job/'native-solver.log').open('w') as out:ret=subprocess.run(cmd,stdout=out,stderr=subprocess.STDOUT,timeout=max(1,deadline-time.time()))
    except subprocess.TimeoutExpired:
     ident=json.loads(subprocess.check_output(['docker','--host',SOCKET,'inspect',name]))[0];assert ident['Image']==ex['image'] and any(v['Source']==str(job) and v['Destination']=='/work' for v in ident['Mounts']);save(job/'aggregate-budget-stop-identity.json',ident);subprocess.run(['docker','--host',SOCKET,'stop','--time','30',ident['Id']],check=True);state.update(status='stopped_runtime_limit',reason='Original absolute4h deadline reached');save(job/'status.json',state);return
    if json.loads((job/'status.json').read_text())['status']=='stopped_runtime_limit':return
    state['native_exit_code']=ret.returncode;assert ret.returncode==0, 'Native continuation failed; no automatic retry'
    journal=json.loads((output/'journal.json').read_text());alg=journal['Toolboxes']['fluid']['Algebraic Solver'];assert alg['KSP']['type']=='gmres' and alg['KSP in SNES']['reuse-prec'] and alg['KSP in SNES']['rtol']==1e-8 and not alg['SNES']['reuse-jac']
    assert abs(metadata_time(output,'velocity')-end)<1e-10 and abs(metadata_time(output,'pressure')-end)<1e-10
    state.update(status='native_checkpoint_pending_continuation',last_native_time=end,finished_unix=time.time());save(job/'status.json',state)
    reports.append(archive_segment(job,f'phase-{phase}',nsteps));save(job/'native-segment-reports.json',reports)
  state.update(status='native_raw_complete_pending_package',native_exit_code=0);save(job/'status.json',state)
 except Exception as error:
  if json.loads((job/'status.json').read_text()).get('status')=='stopped_runtime_limit':return
  state.update(status='needs_attention',error=repr(error),finished_unix=time.time());save(job/'status.json',state);return
 try:
  matches=[]
  freeze=json.loads((a.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text())
  for p in a.snapshot.glob('qbank/02-fluid-mechanics/*/generalized-newtonian-incompressible-transient-3d/author/chapter02-ten-20261020/design.json'):
   assert hashlib.sha256(p.read_bytes()).hexdigest()==freeze['designs'][p.relative_to(a.snapshot).as_posix()];record=json.loads(p.read_text());matches.extend((p,record,e) for e in record['proposed_cases'] if e['design_id']==CASE)
  assert len(matches)==1;p,record,entry=matches[0];entry={**entry,'task':record['task']};requested=entry['detailed_spec']['output_times_s'];m=dict(np.load(job/'adapter-data.npz'));pointmap=json.loads((job/'native-point-map.json').read_text());frames={}
  for report in reports[1:]:
   path=job/report['archive']/'fluid.measures/values.csv'
   with path.open() as f:
    for row in csv.DictReader(f):
     t=float(row['time'])
     for index,target in enumerate(requested):
      if abs(t-target)<1e-10:
       assert index not in frames;frames[index]=fields_from_native_points(remap_batch_row(row,layout,3),m,pointmap,entry)
  assert set(frames)==set(range(4)) and abs(metadata_time(output,'velocity')-1.)<1e-10
  mesh=json.loads((job/reports[-1]['archive']/'journal.json').read_text())['Mesh']['fluid'];assert mesh['n_elements']==len(m['c']) and mesh['n_points']==len(m['x']) and len(mesh['partitioning']['n_elements'])==8 and all(0<v<len(m['c']) for v in mesh['partitioning']['n_elements'])
  prior=job/'before-reviewed-pc-reuse/native/output/np_8/logs/rank-000000.log';reasons0=[int(v) for v in re.findall(r'convergence reason\s*:\s*(-?\d+)',prior.read_text())];assert len(reasons0)==4 and all(v in (2,3,4) for v in reasons0)
  assert len(reasons0)+sum(x['native_steps'] for x in reports)==103
  fields={q:np.concatenate([frames[k][q] for k in range(4)],axis=0) for q in frames[0]};result=package(job,entry,m,m['groups'],native_cell_frames=fields);save(job/'reference/grading.json',json.loads((p.parents[1]/'grading-template.json').read_text()))
  save(job/'native-to-contract.json',{'scope':'Unvalidated candidate from unmodified native solver and nativeBDF checkpoints; exact requested physical frames, no interpolation or physical changes.','physical_output_times':requested,'native_total_completed_steps':103,'native_segment_reports':reports,'initial_native_completed_reasons':reasons0,'native_point_map_sha256':hashlib.sha256((job/'native-point-map.json').read_bytes()).hexdigest(),'native_batch_layout_sha256':hashlib.sha256((job/'native-batch-point-layout.json').read_bytes()).hexdigest(),'absolute_solve_deadline_unix':deadline,'numerical_validation':False})
  state.update(result,status='unvalidated_candidate',reference_produced=True,finished_unix=time.time());save(job/'status.json',state)
 except Exception as error:
  state.update(status='native_raw_complete_pending_package',packaging_error=repr(error),reference_produced=False,finished_unix=time.time());save(job/'status.json',state)
if __name__=='__main__':main()
