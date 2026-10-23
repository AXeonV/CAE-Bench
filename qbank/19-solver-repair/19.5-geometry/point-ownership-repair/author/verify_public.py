"""Verify ordinary offline installation and actual native public samples."""
import argparse,hashlib,json,os,subprocess,sys,zipfile
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--archive',type=Path,required=True);args=parser.parse_args()
work=Path('/tmp/ownership-public-install');work.mkdir()
with zipfile.ZipFile(args.archive) as source:source.extractall(work)
logs=Path('/tmp/ownership-public-install-logs');logs.mkdir()
def command(arguments,label,accepted_codes=(0,)):
    run=subprocess.run(arguments,cwd=work,text=True,capture_output=True)
    (logs/(label+'.stdout.log')).write_text(run.stdout)
    (logs/(label+'.stderr.log')).write_text(run.stderr)
    if run.returncode not in accepted_codes:raise RuntimeError(label+': '+run.stderr[-4000:])
    return run.stdout
command([sys.executable,'-m','pip','install','.'],'ordinary-pip-install')
(work/'src').rename(work/'disabled-sdk-source')
installed=command([sys.executable,'-c','import caeoj.sdk;print(caeoj.sdk.__file__)'],'installed-location').strip()
assert 'site-packages' in installed
task=work/'qbank/19-solver-repair/19.5-geometry/point-ownership-repair'
results=[]
for name,expected in [('01',0),('02',1)]:
    sample=task/'samples'/name;output=work/('sample-'+name+'.h5')
    command([sys.executable,str(task/'public/run_case.py'),'--input',str(sample/'input/problem.json'),'--output',str(output)],'sample-'+name)
    graded=json.loads(command([sys.executable,'-m','caeoj','grade','--input',str(sample/'input/problem.json'),
      '--output',str(output),'--grading',str(sample/'reference/grading.json')],'grade-'+name,accepted_codes=(0,1)))
    assert graded['score']==expected,graded
    results.append({'sample':name,'native_baseline_run_exit_code':0,'grade':graded['score'],
                    'expected':expected,'result_sha256':hashlib.sha256(output.read_bytes()).hexdigest()})
check=command([sys.executable,'-m','pip','check'],'pip-check').strip()
print(json.dumps({'passed':True,'zip_sha256':hashlib.sha256(args.archive.read_bytes()).hexdigest(),
 'ordinary_offline_pip_install':True,'sdk_source_moved':True,'installed_sdk':installed,'pip_check':check,'samples':results}))
