from pathlib import Path
import hashlib,json,subprocess,time,argparse
r=Path(__file__).resolve().parents[3];t=r/'qbank/19-solver-repair/19.6-waves/complex-helmholtz-fmm-repair';archive=r/'dist'/f'{t.name}-agent.zip'
parser=argparse.ArgumentParser();parser.add_argument('--label',default='offline-install-v1');args=parser.parse_args()
out=t/'author/data-evidence'/args.label;out.mkdir(parents=True,exist_ok=True)
script='''import json,sys,subprocess,tempfile,zipfile,pathlib,shutil,hashlib,os
with tempfile.TemporaryDirectory() as temp:
 package=pathlib.Path(temp)/'package';zipfile.ZipFile('/input/agent.zip').extractall(package)
 subprocess.run([sys.executable,'-m','pip','install','--no-cache-dir',str(package)],check=True)
 shutil.move(package/'src',pathlib.Path(temp)/'removed-source')
 os.chdir(temp)
 from caeoj.sdk import load_problem,load_result
 from caeoj.case_grading import grade_case
 import caeoj_task_ext.helmholtz as checker
 assert not checker.__file__.startswith(str(package))
 rows=[];task=pathlib.Path('/task')
 for p in sorted((task/'cases').glob('*/problem.json')):
  problem=load_problem(p);load_result(problem,task/'reference'/p.parent.name/'reference.h5');rows.append(p.parent.name)
 samples=[]
 for sample in sorted((task/'samples').iterdir()):
  p=sample/'input/problem.json';problem=load_problem(p);load_result(problem,sample/'reference/reference.h5')
  work=pathlib.Path(temp)/('sample-'+sample.name);work.mkdir();work.chmod(0o777)
  output=work/'result.h5'
  cmd=['setpriv','--reuid=1000','--regid=1000','--clear-groups',sys.executable,str(package/'qbank/19-solver-repair/19.6-waves/complex-helmholtz-fmm-repair/public/run_case.py'),'--input',str(p),'--output',str(output)]
  proc=subprocess.run(cmd,cwd=work,text=True,capture_output=True,timeout=600)
  (work/'stdout.log').write_text(proc.stdout);(work/'stderr.log').write_text(proc.stderr)
  score=grade_case(p,output,sample/'reference/grading.json')['score'] if proc.returncode==0 else 0
  samples.append(dict(sample=sample.name,command=cmd,returncode=proc.returncode,score=score,stderr=proc.stderr))
 print('OFFLINE_RESULT='+json.dumps(dict(passed=True,cases=rows,samples=samples,installed_checker=checker.__file__,installed_checker_sha256=hashlib.sha256(pathlib.Path(checker.__file__).read_bytes()).hexdigest())))
'''
# Parent temporary directory must permit the unprivileged actual library process.
script=script.replace("package=pathlib.Path(temp)","pathlib.Path(temp).chmod(0o755)\n package=pathlib.Path(temp)")
image=json.loads(subprocess.check_output(['C:/Program Files/Docker/Docker/resources/bin/docker.exe','image','inspect','caeoj-bempp20-runtime:base']))[0]['Id']
cmd=['C:/Program Files/Docker/Docker/resources/bin/docker.exe','run','--rm','--network','none','--cpus','4','--memory','4g','-v',str(archive)+':/input/agent.zip:ro','-v',str(t)+':/task:ro',image,'python','-c',script]
record={'command':cmd,'zip_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'started_unix':time.time()}
with (out/'stdout.log').open('w',encoding='utf-8') as stdout,(out/'stderr.log').open('w',encoding='utf-8') as stderr:
 p=subprocess.Popen(cmd,stdout=stdout,stderr=stderr,text=True);record.update(pid=p.pid,phase='running');(out/'state.json').write_text(json.dumps(record,indent=2),encoding='utf-8');code=p.wait()
record.update(returncode=code,phase='finished',elapsed_seconds=time.time()-record['started_unix']);(out/'state.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
assert code==0,(out/'stderr.log').read_text()
result=json.loads(next(line.removeprefix('OFFLINE_RESULT=') for line in (out/'stdout.log').read_text().splitlines() if line.startswith('OFFLINE_RESULT=')))
assert result['installed_checker_sha256']==hashlib.sha256((t/'extension/caeoj_task_ext/helmholtz.py').read_bytes()).hexdigest()
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(len(result['cases']),[(v['returncode'],v['score']) for v in result['samples']])
