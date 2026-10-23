"""Run bounded compiler/runtime probes serially in real disposable environments."""
import argparse,json,subprocess,time,os,sys,shutil
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
Q=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--logs',type=Path,required=True);a=p.parse_args();a.logs.mkdir(parents=True,exist_ok=True)
 context=a.logs.parent/'backend-probe-context-v4'
 if (context/'backend_probe.py').read_bytes()!=(Q/'author/backend_probe.py').read_bytes():
  subprocess.run([sys.executable,str(Q/'author/prepare_backend_probes.py'),'--tests',str(Q.parents[3]/'runs/harbor/tasks'/Q.name/'tests'),'--context',str(context)],check=True)
 image=subprocess.check_output(['docker','image','inspect','caeoj-aspect6818-probes:final','--format','{{.Id}}'],text=True).strip()
 modes=['valid','runtime-timeout','syntax','baseline-runtime','protected-include','compiler','extra','symlink']
 free=shutil.disk_usage(a.logs).free
 workers=2 if free>=2200000000 else 1
 state={'pid':os.getpid(),'image':image,'phase':'running','max_parallel_containers':workers,'disk_free_at_start':free,'modes':modes}
 (a.logs/'state.json').write_text(json.dumps(state,indent=2))
 def run(mode):
  path=a.logs/(mode+'-state.json');local={'pid':os.getpid(),'image':image,'mode':mode,'phase':'starting','started_unix':time.time()}
  path.write_text(json.dumps(local,indent=2))
  raw=a.logs/(mode+'-raw');raw.mkdir(exist_ok=True)
  cmd=['docker','run','--rm','--name','caeoj-aspect6818-probe-'+mode,'--network','none','--cpus','4','--memory','8g','--mount','type=bind,source='+str(raw.resolve()).replace('\\','/')+',target=/logs',image,'python','/opt/backend_probe.py',mode]
  with (a.logs/(mode+'.stdout.json')).open('w') as out,(a.logs/(mode+'.stderr.log')).open('w') as err:
   process=subprocess.Popen(cmd,stdout=out,stderr=err);local['docker_cli_pid']=process.pid;local['phase']='running';local['command']=cmd;path.write_text(json.dumps(local,indent=2));code=process.wait()
  local.update(last_returncode=code,elapsed_seconds=time.time()-local['started_unix'],phase='complete' if code==0 else 'failed');path.write_text(json.dumps(local,indent=2))
  if code:raise RuntimeError(mode+' failed; inspect retained stdout/stderr')
  row=json.loads((a.logs/(mode+'.stdout.json')).read_text());row['elapsed_seconds']=local['elapsed_seconds'];return row
 rows=[]
 with ThreadPoolExecutor(max_workers=workers) as pool:
  futures={pool.submit(run,mode):mode for mode in modes}
  for future in as_completed(futures):
   row=future.result();rows.append(row)
   (Q/'author/data-evidence/backend-probes.json').write_text(json.dumps({'image':image,'max_parallel_containers':workers,'disk_free_at_start':free,'complete':len(rows)==8,'passed':len(rows)==8 and all(r['passed'] for r in rows),'probes':rows},indent=2))
   print(row['mode'],'passed',round(row['elapsed_seconds'],3),flush=True)
 state['phase']='complete';(a.logs/'state.json').write_text(json.dumps(state,indent=2))
