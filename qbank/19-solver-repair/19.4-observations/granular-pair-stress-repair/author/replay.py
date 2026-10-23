"""Real LAMMPS production with a strictly assembled SDK and independent pair audit."""
import argparse,importlib.util,json,subprocess,time,hashlib,shutil
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem,load_result
from caeoj_tools.assembly import runtime_materials
from caeoj_tools.grading_policy import author_policy,write_direct_grading
from caeoj.case_grading import grade_case
Q=Path(__file__).resolve().parents[1];ROOT=Q.parents[3];W=ROOT/'work/repair-22/lammps-4219'
def mod(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--docker',default='docker');p.add_argument('--mode',choices=['reference','baseline'],required=True);a=p.parse_args()
    files,runtime=runtime_materials({Q.name:Q},ROOT);stage=W/'runtime'
    for name,data in files.items():
        path=stage/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    checker=mod('checker',Q/'extension/caeoj_task_ext/granular_contact.py');ind=mod('independent',Q/'author/independent.py')
    image='caeoj-lammps4219-reference:fixed' if a.mode=='reference' else 'caeoj-lammps4219-core:base'
    imageid=json.loads(subprocess.check_output([a.docker,'image','inspect',image]))[0]['Id'];report={'mode':a.mode,'image':imageid,'runtime_id':runtime['id'],'producer':'actual LAMMPS gran/hooke/history/kk CPU Serial run 0','cases':[]}
    policy=json.loads((Q/'author/grading-template.json').read_text())['quantities']
    for path in sorted((Q/'cases').glob('*/problem.json')):
        problem=load_problem(path);errors=[];checker.check(problem,errors)
        if errors:raise ValueError((path,errors))
        log=W/'replay'/a.mode/path.parent.name;log.mkdir(parents=True,exist_ok=True)
        output=log/'result.h5'
        cmd=[a.docker,'run','--rm','--network','none','--cpus','4','--memory','8g','--user','1000:1000','-v',str(Q)+':/task:ro','-v',str(stage/'src')+':/runtime:ro','-v',str(log)+':/outputs','-e','PYTHONPATH=/runtime',imageid,'python','/task/public/run_case.py','--input','/task/cases/'+path.parent.name+'/problem.json','--output','/outputs/result.h5']
        start=time.monotonic();r=subprocess.run(cmd,text=True,capture_output=True,timeout=65);(log/'stdout.log').write_text(r.stdout);(log/'stderr.log').write_text(r.stderr)
        if r.returncode:raise RuntimeError(str(path)+r.stderr+r.stdout)
        values=load_result(problem,output);expected=ind.solve(problem);checks={}
        for k in problem.manifest['outputs']:
            v=values[k]
            rule=policy[problem.manifest['outputs'][k]['quantity']]['rule'];difference=abs(v-expected[k]);fraction=difference/(rule['atol']+rule['rtol']*abs(expected[k]));checks[k]={'max_absolute_error':float(difference.max()),'max_tolerance_fraction':float(fraction.max()),'passed':bool((fraction<=1).all())}
        if a.mode=='reference':
            if not all(v['passed'] for v in checks.values()):raise ValueError((path,checks))
            target=Q/'reference'/path.parent.name;target.mkdir(parents=True,exist_ok=True);shutil.copyfile(output,target/'reference.h5');write_direct_grading(target,author_policy(Q))
        grade=grade_case(path,output,Q/'reference'/path.parent.name/'grading.json')
        report['cases'].append({'case':path.parent.name,'score':grade['score'],'checks':checks,'elapsed_seconds':time.monotonic()-start,'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest()});(Q/'author/data-evidence'/(a.mode+'-replay.json')).write_text(json.dumps(report,indent=2)+'\n');print(path.parent.name,a.mode,grade['score'],flush=True)
    if a.mode=='reference':
        for n,name in [('01','01-elastic-both-off'),('02','02-single-both-off')]:
            root=Q/'samples'/n;shutil.copytree(Q/'cases'/name,root/'input',dirs_exist_ok=True);shutil.copytree(Q/'reference'/name,root/'reference',dirs_exist_ok=True);(root/'output').mkdir(exist_ok=True);shutil.copyfile(root/'reference/reference.h5',root/'output/result.h5')
