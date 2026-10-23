"""Real MOOSE production; independently audit every requested material and FE output."""
import argparse,hashlib,importlib.util,json,subprocess,sys,time
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem,write_result
from caeoj.case_grading import grade_case
from caeoj_tools.grading_policy import author_policy,write_direct_grading
from independent import reference
from policy import policy_for
TASK=Path(__file__).resolve().parents[1];ROOT=TASK.parents[3];DOCKER='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
sys.path.insert(0,str(TASK/'public'));import run_case
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--image',required=True);parser.add_argument('--mode',choices=['reference','defect','upstream'],required=True);parser.add_argument('--case');parser.add_argument('--resume',action='store_true');args=parser.parse_args()
    checker=module('public_contract',TASK/'extension/caeoj_task_ext/grand_potential.py');image=json.loads(subprocess.check_output([DOCKER,'image','inspect',args.image]))[0]['Id'];policy=author_policy(TASK)
    report={'mode':args.mode,'image_id':image,'producer':'Genuine GrandPotentialSinteringMaterial, DerivativeParsedMaterial, Reaction, MatReaction and MatBodyForce; actual libMesh DOF map, native PETSc analytic Jacobian and residual, actual material property API.','hash_semantics':{'native_input_sha256':'Exact UTF-8 case.i bytes; not input HDF5 bytes.','result_sha256':'Actual HDF5 from native observations: reference/<case>/reference.h5 for reference, authoring replay/<mode>/<case>/result.h5 otherwise.'},'cases':[]}
    paths=sorted((TASK/'cases').glob('*/problem.json'))
    if args.case:paths=[p for p in paths if p.parent.name==args.case]
    report_path=TASK/'author/data-evidence'/(args.mode+'-replay.json')
    if args.resume and report_path.exists():
        previous=json.loads(report_path.read_text())
        if previous['image_id']!=image:raise ValueError('Resume image differs')
        report=previous
    report.update(total_cases_selected=len(paths),complete=False)
    finished={row['case'] for row in report['cases']}
    for path in paths:
        if path.parent.name in finished:continue
        problem=load_problem(path);policy=policy_for(problem);errors=[];checker.check(problem,errors)
        if errors:raise ValueError((str(path),errors))
        directory=ROOT/'runs/authoring/repair-22/moose-30236-replay'/args.mode/path.parent.name;directory.mkdir(parents=True,exist_ok=True);columns,names,length=run_case.prepare(problem,directory)
        native='source /environment && exec '+run_case.MOOSE+' -i case.i '+' '.join(run_case.PETSC_OPTIONS)
        container='moose30236-'+args.mode+'-'+path.parent.name
        cmd=[DOCKER,'run','--rm','--name',container,'--network','none','--cpus','2','--memory','4g','--user','1000:1000','--mount',f'type=bind,source={directory.resolve()},target=/job','--workdir','/job','--entrypoint','/bin/bash',image,'-lc',native]
        started=time.monotonic()
        try:result=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
        finally:subprocess.run([DOCKER,'rm','-f',container],capture_output=True,timeout=20)
        elapsed=time.monotonic()-started
        (directory/'stdout.log').write_text(result.stdout,newline='\n');(directory/'stderr.log').write_text(result.stderr,newline='\n')
        if result.returncode:raise RuntimeError((path.parent.name,result.returncode,result.stdout[-1600:],result.stderr[-1600:]))
        values=run_case.extract(problem,directory,result.stdout,columns,names,length);exact=reference(problem);checks={}
        for name,v in values.items():
            entry=policy['quantities'][problem.manifest['outputs'][name]['quantity']]['rule'];err=abs(v-exact[name]);ratio=err/(entry['atol']+entry['rtol']*abs(exact[name]));checks[name]={'max_absolute_error':float(err.max()),'max_tolerance_fraction':float(ratio.max()),'passed':bool(np.all(ratio<=1))}
        target=TASK/'reference'/path.parent.name if args.mode=='reference' else directory;target.mkdir(parents=True,exist_ok=True);output=target/('reference.h5' if args.mode=='reference' else 'result.h5');write_result(output,problem,values)
        if args.mode=='reference':
            if not all(c['passed'] for c in checks.values()):raise ValueError((path.parent.name,checks))
            write_direct_grading(target,policy)
        grading=TASK/'reference'/path.parent.name/'grading.json';score=grade_case(path,output,grading)['score'] if grading.exists() else None
        report['cases'].append({'case':path.parent.name,'programs':len(problem.arrays['program_ids']),'seconds_including_container_start':elapsed,'score':score,'checks':checks,'native_input_sha256':hashlib.sha256((directory/'case.i').read_bytes()).hexdigest(),'native_stdout_sha256':hashlib.sha256((directory/'stdout.log').read_bytes()).hexdigest(),'result_sha256':hashlib.sha256(output.read_bytes()).hexdigest()})
        (TASK/'author/data-evidence'/(args.mode+'-replay.json')).write_text(json.dumps(report,indent=2)+'\n',newline='\n');print(path.parent.name,args.mode,score,elapsed,flush=True)
    report['complete']=True
    (TASK/'author/data-evidence'/(args.mode+'-replay.json')).write_text(json.dumps(report,indent=2)+'\n',newline='\n')
