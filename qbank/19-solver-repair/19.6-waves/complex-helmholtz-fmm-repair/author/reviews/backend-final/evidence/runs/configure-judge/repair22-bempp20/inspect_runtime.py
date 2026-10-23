"""Cheap read-only base-image inspection; no library import/build/solver run."""
from pathlib import Path
import subprocess,json,hashlib
out=Path(__file__).resolve().parent
docker='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
code='''from pathlib import Path
import os,json,hashlib,struct,shutil
root=Path('/opt/bempp-env')
files=list(root.rglob('*'))
writable=[str(p) for p in [root,*files] if os.access(p,os.W_OK)]
mode_writable=[]
for p in [root,*files]:
 s=p.stat();mask=0o200 if s.st_uid==os.geteuid() else (0o020 if s.st_gid in [os.getegid(),*os.getgroups()] else 0o002)
 if s.st_mode & mask:mode_writable.append(str(p))
native=[p for p in files if p.is_file() and p.name.endswith('.so') and 'exafmm' in str(p)]
sources=Path('/opt/upstream/bempp-cl-84345ee9ee314c85750f045c7ad38090f5ea5f26/bempp/api/fmm')
pycs={}
for name in ['exafmm','fmm_assembler','helpers']:
 p=sources/'__pycache__'/(name+'.cpython-311.pyc')
 pycs[str(p)]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'flags':struct.unpack('<I',p.read_bytes()[4:8])[0]}
assert all(v['flags']==3 for v in pycs.values())
assert native and not writable and not mode_writable
print(json.dumps({'uid':os.geteuid(),'venv_entries_checked':len(files)+1,'venv_writable':writable,'venv_mode_writable':mode_writable,'native_exafmm':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'writable':os.access(p,os.W_OK),'mode':oct(p.stat().st_mode & 0o777),'uid':p.stat().st_uid,'gid':p.stat().st_gid} for p in native],'base_pyc':pycs,'disk_free_tmp':shutil.disk_usage('/tmp').free}))
'''
inspect=subprocess.run([docker,'image','inspect','caeoj-bempp20-runtime:base','--format','{{.Id}}'],capture_output=True,text=True,check=True)
command=[docker,'run','--rm','--network','none','--cpus','4','--memory','4g','--user','1000:1000','--read-only',inspect.stdout.strip(),'/opt/bempp-env/bin/python','-I','-c',code]
p=subprocess.run(command,capture_output=True,text=True,timeout=45)
e={'image_id':inspect.stdout.strip(),'command':command,'returncode':p.returncode,'stderr':p.stderr,'result':json.loads(p.stdout) if p.returncode==0 else p.stdout}
(out/'runtime-readonly-inspection.json').write_text(json.dumps(e,indent=2)+'\n',encoding='utf-8')
assert p.returncode==0,p.stderr
print(json.dumps(e['result']))
