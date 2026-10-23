from pathlib import Path
import subprocess,json,time,shutil,os
r=Path(__file__).resolve().parents[3];w=r/'work/repair-22/bempp-20';t=r/'qbank/19-solver-repair/19.6-waves/complex-helmholtz-fmm-repair';out=r/'runs/authoring/repair-22/bempp-backend-probes-v4';out.mkdir(exist_ok=True)
context=w/'probe-context-v4';context.mkdir(exist_ok=True);shutil.copytree(r/'runs/harbor/tasks'/t.name/'tests',context/'tests',dirs_exist_ok=True)
worker=(w/'backend_probe.py').read_text()
worker=worker.replace("public/'samples/01/input'","public/('samples/'+os.environ.get('BEMPP_PROBE_SAMPLE','01')+'/input')")
worker=worker.replace("public/'samples/01/reference/grading.json'","public/('samples/'+os.environ.get('BEMPP_PROBE_SAMPLE','01')+'/reference/grading.json')")
(context/'backend_probe.py').write_text(worker,encoding='utf-8')
for name in ['exafmm','fmm_assembler','helpers']:shutil.copyfile(t/'author/generated'/f'{name}.py',context/f'{name}.py')
(context/'Dockerfile').write_text('FROM caeoj-bempp20-runtime:base\nCOPY tests/agent.zip /tmp/agent.zip\nRUN python -m zipfile -e /tmp/agent.zip /app && python -m pip install --no-cache-dir /app && mkdir -p /app/submission\nCOPY tests /tests\nCOPY exafmm.py fmm_assembler.py helpers.py /probe/\nCOPY backend_probe.py /opt/backend_probe.py\n',encoding='utf-8')
docker='C:/Program Files/Docker/Docker/resources/bin/docker.exe';rows=[]
def run(mode,cmd):
 start=time.time()
 with (out/(mode+'.stdout.log')).open('w') as a,(out/(mode+'.stderr.log')).open('w') as b:
  p=subprocess.Popen(cmd,stdout=a,stderr=b);(out/'state.json').write_text(json.dumps(dict(mode=mode,pid=p.pid,runner_pid=os.getpid(),phase='running')));code=p.wait()
 row=dict(mode=mode,command=cmd,returncode=code,elapsed_seconds=time.time()-start);rows.append(row);(out/'report.json').write_text(json.dumps(rows,indent=2));assert code==0,(mode,(out/(mode+'.stderr.log')).read_text())
run('image-build',[docker,'build','--network','none','-t','caeoj-bempp20-probes:v4',str(context)])
for mode in ['valid','syntax','extra','symlink','compiler','baseline-runtime','runtime-timeout']:
 run(mode,[docker,'run','--rm','--network','none','--cpus','4','--memory','4g','caeoj-bempp20-probes:v4','python','/opt/backend_probe.py',mode])
run('valid-surface',[docker,'run','--rm','--network','none','--cpus','4','--memory','4g','-e','BEMPP_PROBE_SAMPLE=02','caeoj-bempp20-probes:v4','python','/opt/backend_probe.py','valid'])
(out/'state.json').write_text(json.dumps(dict(phase='completed',runner_pid=os.getpid())))
