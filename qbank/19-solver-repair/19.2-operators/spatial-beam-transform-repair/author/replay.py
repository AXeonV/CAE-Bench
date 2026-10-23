"""Replay actual Kratos element and validate with independent Timoshenko matrices."""
import argparse,hashlib,importlib.util,json,subprocess,time
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem,write_result
from caeoj.case_grading import grade_case
from caeoj_tools.grading_policy import author_policy,write_direct_grading
from independent import independent,closed_tip,frame
TASK=Path(__file__).resolve().parents[1]
DOCKER='C:/Program Files/Docker/Docker/resources/bin/docker.exe'

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result

def exact(problem):
    a=problem.arrays;values={name:[] for name in problem.manifest['outputs']};closed=[]
    for i in range(len(a['beam_ids'])):
        x=a['endpoints'][0,i];axis=a['section_axis'][0,i];mat=[a[name][0,i,0] for name in adapter.MATERIAL];b=a['body_acceleration'][0,i]
        K,f=independent(x,axis,mat,b);L,_=frame(x,axis);inv=np.tile([1.,1.,1.,1/L,1/L,1/L],2);K*=inv[:,None]*inv[None,:];f*=inv
        tip=np.linalg.solve(K[6:,6:],f[6:]+a['tip_load'][0,i])
        if np.all(b==0):closed.append(float(np.max(np.abs(tip-closed_tip(x,axis,mat,a['tip_load'][0,i])))))
        for name,value in [('lhs_combined',K.ravel()),('lhs_separate',K.ravel()),('rhs_combined',f),('rhs_separate',f),('tip_displacement',tip)]:values[name].append(value)
    return {name:np.asarray(value)[None] for name,value in values.items()},max(closed,default=0.)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--image',required=True);p.add_argument('--mode',choices=['reference','defect','upstream'],required=True);args=p.parse_args()
    adapter=module('beam_adapter',TASK/'public/run_case.py');checker=module('beam_checker',TASK/'extension/caeoj_task_ext/beam_repair.py')
    image=json.loads(subprocess.check_output([DOCKER,'image','inspect',args.image]))[0]['Id']
    report={'mode':args.mode,'image_id':image,'reference_producer':'actual pinned Kratos element with documented source repair; independent matrices are validators only','cases':[]}
    for path in sorted((TASK/'cases').glob('*/problem.json')):
        problem=load_problem(path);errors=[];checker.check(problem,errors)
        if errors:raise ValueError((path,errors))
        directory=TASK.parents[3]/'runs/authoring/repair-22/kratos-replay'/args.mode/path.parent.name;directory.mkdir(parents=True,exist_ok=True)
        (directory/'input.txt').write_text(adapter.serialize(problem),encoding='utf-8')
        command=[DOCKER,'run','--rm','--network','none','--cpus','2','--memory','4g','--user','1000:1000','--mount',f'type=bind,source={directory.resolve()},target=/job',image,'/opt/beam-build/beam_driver','/job/input.txt','/job/output.txt']
        started=time.monotonic();process=subprocess.run(command,capture_output=True,text=True,timeout=45);elapsed=time.monotonic()-started
        (directory/'stdout.log').write_text(process.stdout);(directory/'stderr.log').write_text(process.stderr)
        if process.returncode:raise RuntimeError((path,process.returncode,process.stderr))
        values=adapter.adapt(problem,(directory/'output.txt').read_text());expected,closed_error=exact(problem);checks={}
        for name,value in values.items():
            atol,rtol=(1e-4,1e-9) if name.startswith('lhs') else (1e-8,1e-9) if name.startswith('rhs') else (1e-11,1e-8)
            error=np.abs(value-expected[name]);ratio=error/(atol+rtol*np.abs(expected[name]));checks[name]={'max_absolute_error':float(error.max()),'max_tolerance_fraction':float(ratio.max()),'passed':bool(np.all(ratio<=1))}
        target=TASK/'reference'/path.parent.name if args.mode=='reference' else directory;target.mkdir(parents=True,exist_ok=True)
        output=target/('reference.h5' if args.mode=='reference' else 'result.h5');write_result(output,problem,values)
        if args.mode=='reference':
            if not all(v['passed'] for v in checks.values()):raise ValueError((path,checks))
            write_direct_grading(target,author_policy(TASK))
        grading=TASK/'reference'/path.parent.name/'grading.json';score=grade_case(path,output,grading)['score'] if grading.exists() else None
        report['cases'].append({'case':path.parent.name,'seconds':elapsed,'score':score,'checks':checks,'closed_tip_max_absolute_error_m':closed_error,'driver_input_sha256':hashlib.sha256((directory/'input.txt').read_bytes()).hexdigest(),'result_sha256':hashlib.sha256(output.read_bytes()).hexdigest()})
        (TASK/'author/data-evidence'/(args.mode+'-replay.json')).write_text(json.dumps(report,indent=2)+'\n')
        print(path.parent.name,args.mode,score,flush=True)
