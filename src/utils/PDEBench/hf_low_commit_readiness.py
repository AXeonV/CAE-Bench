"""Run local integration checks and bind successful evidence to exact code bytes."""
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[3]


def main():
    path=Path(__file__).with_name('hf_low_commit_launch.py')
    spec=importlib.util.spec_from_file_location('low_launcher',path);launcher=importlib.util.module_from_spec(spec);spec.loader.exec_module(launcher)
    before=launcher.inventory();reports=[]
    scratch=ROOT/'runs/test-tmp';scratch.mkdir(parents=True,exist_ok=True)
    env={**os.environ,'PYTHONPATH':str(ROOT/'src'),'TMPDIR':str(scratch)}
    for pattern,name in [('test_pdebench_*.py','low-commit-tests.log'),('test_data_pool.py','low-commit-pool-tests.log')]:
        log=ROOT/'runs/pdebench-cloud-trial'/name
        with log.open('w') as output:
            result=subprocess.run([str(ROOT/'.venv/bin/python'),'-m','unittest','discover','-s','tests','-p',pattern,'-q'],
                cwd=ROOT,env=env,stdout=output,stderr=subprocess.STDOUT,timeout=180)
        text=log.read_text();count=re.search(r'Ran (\d+) tests? in ([0-9.]+)s',text)
        if result.returncode or not count or '\nOK' not in text:raise RuntimeError('Local checks failed; see '+str(log))
        reports.append({'pattern':pattern,'tests':int(count[1]),'seconds':float(count[2]),'log':str(log)})
    if launcher.inventory()!=before:raise RuntimeError('Code changed while checks were running')
    evidence={'passed':True,'code_inventory':before,'reports':reports,'no_paid_calibration_jobs':True,
        'numerical_pdebench_payload_downloaded':False,
        'scope':'Actual SDK HTTP gating/429/lost-success; real synthetic atomic prepared publication, crash restore, fixed-revision consume, verified progress; case binding preservation; five-way slot bound; shared pool regressions'}
    target=ROOT/'runs/pdebench-cloud-trial/low-commit-readiness.json';target.write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(evidence,indent=2))


if __name__=='__main__':main()
