"""Native public upper-size corner; no surrogate solver or invented resource result."""
from pathlib import Path
import json,time,sys,subprocess
import numpy as np
from caeoj.storage import write_hdf5
from caeoj.sdk import load_problem
sys.path.insert(0,'/work/sdk-assembly-root/qbank/19-solver-repair/19.3-transport/deformed-tangential-boundary-repair/extension/caeoj_task_ext')
from deformed_tangential import check
W=Path('/work');Q=Path('/app/qbank/19-solver-repair/19.3-transport/deformed-tangential-boundary-repair');c=W/'resource-corner';c.mkdir(exist_ok=True)
m=json.loads((Q/'samples/01/input/problem.json').read_text());sample=json.loads((W/'formal/cases/09-wedge-negative/problem.json').read_text())
m=sample;p=m['physics']['parameters'];p['end_time']['value']=2.;p['time_step']['value']=.25;p['rate_x']['value']=-.075;p['refinement']['value']=6
points=np.array([[x,y] for x in np.linspace(.1,1.9,16) for y in np.linspace(.04,.3,8)],dtype='float64')
write_hdf5(c/'input.h5',{'probe_coordinates':points,'probe_ids':np.arange(128,dtype='int64')*7+3,'times':np.arange(9,dtype='float64')*.25})
(c/'problem.json').write_text(json.dumps(m,indent=2));problem=load_problem(c/'problem.json');errors=[];check(problem,errors);assert not errors,errors
command=['setpriv','--reuid=1000','--regid=1000','--clear-groups','--no-new-privs','python',str(Q/'public/run_case.py'),'--input',str(c/'problem.json'),'--output','/tmp/corner-result.h5','--executable','/work/aspect-reference.native']
start=time.monotonic()
try:
 r=subprocess.run(command,text=True,capture_output=True,timeout=60)
 report={'command':command,'seconds':time.monotonic()-start,'exit_code':r.returncode,'cpu_max':Path('/sys/fs/cgroup/cpu.max').read_text(),'memory_max':Path('/sys/fs/cgroup/memory.max').read_text(),'memory_peak':Path('/sys/fs/cgroup/memory.peak').read_text(),'frames':9,'points':128,'refinement':6,'stdout':r.stdout,'stderr':r.stderr}
 if r.returncode==0:(c/'result.h5').write_bytes(Path('/tmp/corner-result.h5').read_bytes())
except subprocess.TimeoutExpired as exc:
 report={'command':command,'seconds':time.monotonic()-start,'status':'timeout','frames':9,'points':128,'refinement':6}
(c/'resource-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
assert report.get('exit_code')==0,report
