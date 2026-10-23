import json,os,subprocess,sys
from pathlib import Path
out=Path(__file__).resolve().parent
q=out/'bundle/qbank/19-solver-repair/19.6-waves/complex-helmholtz-fmm-repair'
env=os.environ.copy();env['PYTHONPATH']=str(out/'installed')
records=[]
for s in ['01','02']:
    p=str(q/'samples'/s/'input/problem.json');r=str(q/'samples'/s/'reference/reference.h5');g=str(q/'samples'/s/'reference/grading.json')
    for args in [['info','--input',p],['validate-input',p],['validate-output','--input',p,'--output',r],['grade','--input',p,'--output',r,'--grading',g]]:
        proc=subprocess.run([sys.executable,'-m','caeoj',*args],env=env,cwd=out,capture_output=True,text=True)
        records.append({'sample':s,'args':args,'exit_code':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr})
        print(s,args[0],proc.returncode,proc.stdout[:180])
        assert proc.returncode==0
(out/'cli-checks.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
