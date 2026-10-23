"""Install the exact exam offline, move SDK source away, run real public samples."""
import argparse,hashlib,json,subprocess
from pathlib import Path
TASK=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,required=True);a=p.parse_args();archive=a.archive.resolve()
    code="""import json,subprocess,sys,shutil,zipfile,os
from pathlib import Path
p=Path('/tmp/exam');p.mkdir();zipfile.ZipFile('/audit/exam.zip').extractall(p)
r=subprocess.run([sys.executable,'-m','pip','install','.'],cwd=p,text=True,capture_output=True);assert r.returncode==0,r.stdout+'\\n'+r.stderr
shutil.move(p/'src','/tmp/moved-sdk-source');os.chdir('/tmp');import caeoj;assert 'site-packages' in caeoj.__file__,caeoj.__file__
rows=[];task=p/'qbank/19-solver-repair/19.6-waves/parallel-pml-reduction-repair';os.chdir(task)
for sample in sorted((task/'samples').iterdir()):
 output=Path('/tmp')/('sample-'+sample.name+'.h5');command=[sys.executable,'public/run_case.py','--input','samples/'+sample.name+'/input/problem.json','--output',str(output)];r=subprocess.run(command,text=True,capture_output=True);assert r.returncode==0,r.stdout+'\\n'+r.stderr
 grading=[sys.executable,'-m','caeoj','grade','--input','samples/'+sample.name+'/input/problem.json','--output',str(output),'--grading','samples/'+sample.name+'/reference/grading.json'];g=subprocess.run(grading,text=True,capture_output=True);d=json.loads(g.stdout);assert d['score']==1,d;rows.append({'sample':sample.name,'exit_code':r.returncode,'score':d['score'],'working_directory':str(task),'run_command':command,'grade_command':grading})
r=subprocess.run([sys.executable,'-m','pip','check'],text=True,capture_output=True);assert r.returncode==0,r.stdout+r.stderr
print(json.dumps({'ordinary_offline_install':True,'sdk_source_moved':True,'installed_module':caeoj.__file__,'samples':rows,'pip_check':r.stdout.strip()}))
"""
    cmd=['docker','run','--rm','--network','none','--cpus','4','--memory','4g','-v',str(archive)+':/audit/exam.zip:ro','caeoj-specfem661-reference:production','python','-c',code]
    r=subprocess.run(cmd,text=True,capture_output=True,timeout=300)
    if r.returncode:raise RuntimeError(r.stdout+'\n'+r.stderr)
    report={'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'image':'caeoj-specfem661-reference:production','command':cmd,**json.loads(r.stdout)}
    (TASK/'author/data-evidence/public-install.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
