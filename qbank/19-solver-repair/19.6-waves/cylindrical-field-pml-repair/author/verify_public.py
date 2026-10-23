"""Ordinary offline install of the exact exam, then run and grade all samples."""
import argparse,hashlib,json,subprocess
from pathlib import Path
TASK=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,required=True);p.add_argument('--docker',default='docker');p.add_argument('--output',type=Path,default=TASK/'author/data-evidence/public-install.json');a=p.parse_args();archive=a.archive.resolve()
 code="""import json,subprocess,sys,shutil,zipfile,os
from pathlib import Path
p=Path('/tmp/exam');p.mkdir();zipfile.ZipFile('/audit/exam.zip').extractall(p)
r=subprocess.run([sys.executable,'-m','pip','install','.'],cwd=p,text=True,capture_output=True);assert r.returncode==0,r.stdout+'\\n'+r.stderr
shutil.move(p/'src','/tmp/moved-sdk-source');os.chdir('/tmp');import caeoj;assert 'site-packages' in caeoj.__file__,caeoj.__file__
rows=[];task=p/'qbank/19-solver-repair/19.6-waves/cylindrical-field-pml-repair'
for sample in sorted((task/'samples').iterdir()):
 output=Path('/tmp')/('sample-'+sample.name+'.h5');cmd=[sys.executable,str(task/'public/run_case.py'),'--input',str(sample/'input/problem.json'),'--output',str(output)];r=subprocess.run(cmd,text=True,capture_output=True);assert r.returncode==0,r.stdout+'\\n'+r.stderr
 g=subprocess.run([sys.executable,'-m','caeoj','grade','--input',str(sample/'input/problem.json'),'--output',str(output),'--grading',str(sample/'reference/grading.json')],text=True,capture_output=True);d=json.loads(g.stdout);assert d['score']==(0 if sample.name=='01' else 1),d;rows.append({'sample':sample.name,'run_exit_code':r.returncode,'grading_exit_code':g.returncode,'score':d['score'],'status':d['status']})
check=subprocess.run([sys.executable,'-m','pip','check'],text=True,capture_output=True);assert check.returncode==0,check.stdout+check.stderr
print(json.dumps({'ordinary_offline_pip_install':True,'sdk_source_moved':True,'installed_module':caeoj.__file__,'baseline_samples':rows,'pip_check':check.stdout.strip()}))
"""
 cmd=[a.docker,'run','--rm','--network','none','--cpus','4','--memory','4g','-v',str(archive)+':/audit/exam.zip:ro','caeoj-meep2338-runtime:base','python','-c',code];r=subprocess.run(cmd,capture_output=True,text=True,timeout=1500)
 if r.returncode:raise RuntimeError(r.stdout+'\n'+r.stderr)
 record={'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'network':'none','command':cmd,**json.loads(r.stdout)};a.output.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
