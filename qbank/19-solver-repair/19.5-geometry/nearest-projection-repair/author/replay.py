"""Produce observations using the actual library; independently verify its returned geometry."""
import argparse,hashlib,importlib.util,json,subprocess,time
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem,write_result
from caeoj.case_grading import grade_case
from caeoj_tools.grading_policy import author_policy,write_direct_grading
from independent import evaluate
TASK=Path(__file__).resolve().parents[1]

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--dataset',type=Path,required=True);parser.add_argument('--image',required=True);parser.add_argument('--docker',default='docker');parser.add_argument('--mode',choices=['reference','defect','validation'],required=True);args=parser.parse_args()
    adapter=module('projection_adapter',TASK/'public/run_case.py');checker=module('projection_contract',TASK/'extension/caeoj_task_ext/projection.py')
    image=json.loads(subprocess.check_output([args.docker,'image','inspect',args.image]))[0]['Id']
    report={'mode':args.mode,'image_id':image,'cases':[],'reference_producer':'actual pinned preCICE query::Index; affine enumeration is independent validation only',
       'input_payload_sha256_definition':'SHA256 of exact UTF8 JSON passed to the real C++ driver',
       'driver_sha256':hashlib.sha256((TASK/'public/driver.cpp').read_bytes()).hexdigest()}
    for path in sorted((args.dataset/'cases').glob('*/problem.json')):
        problem=load_problem(path);errors=[];checker.check(problem,errors)
        if errors:raise ValueError(errors)
        text=adapter.serialize(problem);expected=evaluate(json.loads(text))
        cmd=[args.docker,'run','--rm','--network','none','--cpus','4','--memory','8g','--user','1000:1000','-i',image,'/opt/precice-repair-build/bin/projection-driver']
        start=time.monotonic();proc=subprocess.run(cmd,input=text,capture_output=True,text=True,timeout=30);elapsed=time.monotonic()-start
        log=args.dataset/'replay'/args.mode/path.parent.name;log.mkdir(parents=True,exist_ok=True)
        for name,data in [('input.json',text),('stdout.json',proc.stdout),('stderr.log',proc.stderr)]: (log/name).write_text(data,encoding='utf-8')
        if proc.returncode:raise RuntimeError(str(path)+': '+proc.stderr)
        actual=adapter.adapt(proc.stdout);exact=adapter.adapt(json.dumps(expected));checks={}
        for name,value in actual.items():
            atol=1e-9 if name=='weights' else 1e-8;ratio=np.abs(value-exact[name])/(atol+1e-8*np.abs(exact[name]));checks[name]={'max_absolute_error':float(np.max(np.abs(value-exact[name]))),'max_tolerance_fraction':float(np.max(ratio)),'passed':bool(np.all(ratio<=1))}
        target=args.dataset/'reference'/path.parent.name if args.mode=='reference' else log;target.mkdir(parents=True,exist_ok=True)
        out=target/('reference.h5' if args.mode=='reference' else 'result.h5');write_result(out,problem,actual)
        if args.mode=='reference':
            if not all(x['passed'] for x in checks.values()):raise ValueError((path,checks))
            write_direct_grading(target,author_policy(TASK))
        grade=grade_case(path,out,args.dataset/'reference'/path.parent.name/'grading.json')
        report['cases'].append({'case':path.parent.name,'queries':len(problem.arrays['probe_ids']),'command':cmd,'elapsed_seconds':elapsed,'score':grade['score'],'checks':checks,
          'input_assets':{n:hashlib.sha256((path.parent/n).read_bytes()).hexdigest() for n in ['problem.json','input.h5','source.msh']},
          'input_payload_sha256':hashlib.sha256(text.encode()).hexdigest(),'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
        (args.dataset/(args.mode+'-report.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(path.parent.name,args.mode,grade['score'],flush=True)
