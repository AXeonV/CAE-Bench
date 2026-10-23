"""Execute in an offline baseline container with only the published ZIP mounted."""
import hashlib,json,os,subprocess,sys,zipfile
from pathlib import Path
archive=Path(sys.argv[1]);root=Path('/tmp/exam');root.mkdir()
with zipfile.ZipFile(archive) as bundle:bundle.extractall(root)
install=subprocess.run([sys.executable,'-m','pip','install',str(root)],capture_output=True,text=True)
if install.returncode:raise RuntimeError(install.stdout+'\n'+install.stderr)
# Installed tools must survive moving away the package source directory.
(root/'src').rename('/tmp/unavailable-sdk-source');os.chdir('/tmp')
task=root/'qbank/19-solver-repair/19.5-geometry/nearest-projection-repair';cases=[]
for sample in ['01','02']:
    inp=task/'samples'/sample/'input/problem.json';out=Path('/tmp')/('result-'+sample+'.h5')
    cmd=[sys.executable,str(task/'public/run_case.py'),'--input',str(inp),'--output',str(out)]
    result=subprocess.run(cmd,capture_output=True,text=True)
    if result.returncode:raise RuntimeError(result.stdout+'\n'+result.stderr)
    grade=subprocess.run([sys.executable,'-m','caeoj','grade','--input',str(inp),'--output',str(out),'--grading',str(task/'samples'/sample/'reference/grading.json')],capture_output=True,text=True)
    if grade.returncode not in (0,1):raise RuntimeError(grade.stdout+'\n'+grade.stderr)
    cases.append({'sample':sample,'run_returncode':result.returncode,'grade_returncode':grade.returncode,'grading':json.loads(grade.stdout)})
check=subprocess.run([sys.executable,'-m','pip','check'],capture_output=True,text=True);assert check.returncode==0,check.stdout
print(json.dumps({'zip_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'ordinary_offline_pip_install':True,'sdk_source_moved':True,'pip_check':check.stdout.strip(),'baseline_samples':cases}))
