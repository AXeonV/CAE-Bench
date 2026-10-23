"""Run only bounded supervisor regression tests in an isolated Linux container."""
from pathlib import Path
import subprocess,json,hashlib
root=Path(__file__).resolve().parents[3];out=Path(__file__).resolve().parent
docker='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
image=subprocess.check_output([docker,'image','inspect','caeoj-bempp20-runtime:base','--format','{{.Id}}'],text=True).strip()
script="import subprocess,sys,tempfile,zipfile,runpy; p=tempfile.mkdtemp(); zipfile.ZipFile('/review/dist/complex-helmholtz-fmm-repair-agent.zip').extractall(p); subprocess.run([sys.executable,'-m','pip','install','--no-cache-dir',p],check=True); sys.argv=['unittest','discover','-s','tests','-p','test_harbor_process_cleanup.py','-v']; runpy.run_module('unittest',run_name='__main__')"
command=[docker,'run','--rm','--network','none','--cpus','4','--memory','4g','-v',str(root)+':/review:ro','-e','PYTHONPATH=/review/src','-w','/review',image,'python','-c',script]
p=subprocess.run(command,capture_output=True,text=True,timeout=55)
(out/'supervisor-regression.stdout.log').write_text(p.stdout,encoding='utf-8');(out/'supervisor-regression.stderr.log').write_text(p.stderr,encoding='utf-8')
record={'command':command,'image_id':image,'returncode':p.returncode,'test_sha256':hashlib.sha256((root/'tests/test_harbor_process_cleanup.py').read_bytes()).hexdigest(),'judge_sha256_lf':hashlib.sha256((root/'src/utils/harbor/tests/judge.py').read_bytes().replace(b'\r\n',b'\n')).hexdigest(),'stdout':p.stdout,'stderr':p.stderr}
(out/'supervisor-regression.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(p.stderr);assert p.returncode==0
