"""One finite scheduling-hold watcher, never retries a failed or active native solve."""
import pathlib,json,time,subprocess,re,datetime,hashlib
r=pathlib.Path('/home/zhouzhiyu/code/docker/chapter02-ten-reference-candidates-20261020');m=r/'maintenance';job=r/'cases/ch02-2-1-8-06-power_law_traction';sock='unix:///home/zhouzhiyu/code/docker/qbank/maintenance/solver-images/local/daemon/run/docker.sock'
stop=min(time.time()+1800,1792629946.1018815)
controller=json.loads((m/'feelpp-traction-reviewed-forecast-two-segments-queue.json').read_text())
def original_live():
 try:return (pathlib.Path('/proc')/str(controller['pid'])/'stat').read_text().rsplit(')',1)[1].split()[19]==str(controller['starttime'])
 except FileNotFoundError:return False
while time.time()<stop:
 state=json.loads((job/'status.json').read_text())
 if state.get('segment',0)>=4 or state['status'] in ('unvalidated_candidate','native_raw_complete_pending_package','stopped_runtime_limit'):break
 if original_live():time.sleep(min(30,max(0,stop-time.time())));continue
 if not (state['status']=='needs_attention' and state.get('error')=="AssertionError('Remaining native trajectory no longer fits original4h deadline')" and state.get('native_exit_code')==0 and state.get('segment')==3 and abs(state.get('last_native_time',0)-.719)<1e-10):break
 ex=json.loads((job/'execution.json').read_text());deadline=ex['absolute_solve_deadline_unix'];assert deadline==1792629946.1018815
 info=json.loads(subprocess.check_output(['docker','--host',sock,'inspect',state['container']]))[0]
 assert not info['State']['Running'] and info['State']['Pid']==0 and info['State']['ExitCode']==0 and info['Image']==ex['image'] and any(x['Source']==str(job) and x['Destination']=='/work' for x in info['Mounts'])
 reports=json.loads((job/'native-segment-reports.json').read_text());assert len(reports)==4 and sum(x['native_steps'] for x in reports)==70
 text=(job/reports[-1]['archive']/'native-solver.log').read_text();times=re.findall(r'(?m)^\[(2026-\d+-\d+ :\d+:\d+:\d+) - \[fluid\] \] #0 SNES',text);dates=[datetime.datetime.strptime(x,'%Y-%m-%d :%H:%M:%S') for x in times];recent=[(b-a).total_seconds() for a,b in zip(dates,dates[1:])][-5:]
 review={'at_unix':time.time(),'action':'review_final_native_phase_scheduling_hold','recent_complete_step_seconds':recent,'remaining_steps':29,'remaining_wall_seconds':deadline-time.time(),'original_deadline_unix':deadline,'verified_stopped_container_id':info['Id'],'hard_limit_changed':False,'native_failure_retry':False,'numerical_validation':False}
 if len(recent)<5 or max(recent)*29+60>=deadline-time.time():
  review['dispatch']='not_dispatched_recent_pace_does_not_support_budget';(m/'feelpp-final-phase-watcher-review.json').write_text(json.dumps(review,indent=2)+'\n');break
 p=r/'scripts/continue_feelpp_traction_final_measured_phase.py';approved=json.loads((m/'approved-queues.json').read_text());q=next(x for x in approved['queues'] if x['name']=='feelpp-traction-final-measured-phase');assert q['script_sha256']==hashlib.sha256(p.read_bytes()).hexdigest()
 marker=m/'feelpp-traction-final-measured-phase-queue.json';assert not marker.exists();cmd=['/home/zhouzhiyu/venvs/caeoj/bin/python',str(p),'--root',str(r),'--snapshot',str(r/'snapshots/design-v8')]
 with (m/'feelpp-traction-final-measured-phase.log').open('w') as out:proc=subprocess.Popen(cmd,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
 start=(pathlib.Path('/proc')/str(proc.pid)/'stat').read_text().rsplit(')',1)[1].split()[19];marker.write_text(json.dumps({'pid':proc.pid,'starttime':start,'command':cmd,'launched_unix':time.time(),'deadline_unix':deadline,'scope':'Single remaining native phase, only scheduling-hold correction after verified exited parent and exact0.719checkpoint. Same hard deadline.'},indent=2)+'\n');review.update(dispatch='started_once',pid=proc.pid);(m/'feelpp-final-phase-watcher-review.json').write_text(json.dumps(review,indent=2)+'\n');break
(m/'feelpp-final-phase-watcher-ended.json').write_text(json.dumps({'finished_unix':time.time(),'scope':'One bounded scheduling check, no native failure retry or runtime reset.'},indent=2)+'\n')
