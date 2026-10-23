"""Real fixed-source production and baseline replay, with explicit full checker."""
from pathlib import Path
import argparse,importlib.util,json,subprocess,shutil,time,uuid
import numpy as np
from caeoj.sdk import load_problem,load_result
from caeoj.case_grading import grade_case
from caeoj_tools.assembly import runtime_materials
from caeoj_tools.grading_policy import author_policy,write_direct_grading
Q=Path(__file__).resolve().parents[1];ROOT=Q.parents[3];W=ROOT/'work/repair-22/su2-2602'
def module(path):
    s=importlib.util.spec_from_file_location('checker',path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=['reference','baseline'],required=True);parser.add_argument('--docker',default='docker');parser.add_argument('--only',default='');args=parser.parse_args()
    files,runtime=runtime_materials({Q.name:Q},ROOT);stage=W/'runtime'
    for name,data in files.items():
        path=stage/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    checker=module(Q/'extension/caeoj_task_ext/reconstruction.py')
    image='caeoj-su22602-reference:fixed' if args.mode=='reference' else 'caeoj-su22602-core:base'
    imageid=json.loads(subprocess.check_output([args.docker,'image','inspect',image]))[0]['Id'];report={'mode':args.mode,'image':imageid,'runtime_id':runtime['id'],'cases':[]}
    for path in sorted((Q/'cases').glob('*/problem.json')):
        if args.only and path.parent.name[:2] not in args.only.split(','):continue
        p=load_problem(path);errors=[];checker.check(p,errors)
        if errors:raise ValueError((path,errors))
        log=W/'formal-replay'/args.mode/path.parent.name;log.mkdir(parents=True,exist_ok=True)
        cmd=[args.docker,'run','--rm','--network','none','--cpus','4','--memory','8g','--user','1000:1000','-v',str(Q)+':/task:ro','-v',str(stage/'src')+':/runtime:ro','-v',str(W)+':/cache:ro','-v',str(log)+':/outputs','-e','PYTHONPATH=/runtime',imageid,'python','/task/public/run_case.py','--input','/task/cases/'+path.parent.name+'/problem.json','--output','/outputs/result.h5','--driver','/cache/driver-'+('fixed' if args.mode=='reference' else 'baseline')]
        cmd+=['--artifacts','/outputs/native']
        container='su22602-'+args.mode+'-'+uuid.uuid4().hex[:10];cmd[2:2]=['--name',container]
        start=time.monotonic()
        with (log/'stdout.log').open('w') as stdout,(log/'stderr.log').open('w') as stderr:
            proc=subprocess.Popen(cmd,text=True,stdout=stdout,stderr=stderr)
            state={'container_name':container,'host_cli_pid':proc.pid,'status':'running','timeout_seconds':905,'command':cmd};(log/'run-state.json').write_text(json.dumps(state,indent=2)+'\n')
            try:code=proc.wait(timeout=905)
            except subprocess.TimeoutExpired:
                state.update(status='outer-timeout-container-status-required',elapsed_seconds=time.monotonic()-start);(log/'run-state.json').write_text(json.dumps(state,indent=2)+'\n');raise
        state.update(status='completed',exit_code=code,elapsed_seconds=time.monotonic()-start);(log/'run-state.json').write_text(json.dumps(state,indent=2)+'\n')
        record={'case':path.parent.name,'exit_code':code,'seconds':time.monotonic()-start}
        if code:
            if args.mode=='reference':raise RuntimeError((path,(log/'stderr.log').read_text()[-3000:]))
            record['score']=0
        else:
            values=load_result(p,log/'result.h5')
            if p.manifest['physics']['parameters']['operation']['value']==0:
                a=p.arrays;d=p.manifest['spatial_dimension'];par=p.manifest['physics']['parameters'];cp=par['gamma']['value']*par['gas_constant']['value']/(par['gamma']['value']-1)
                target=a['enthalpy']+cp*(values['temperature']-a['temperature'])+.5*np.sum(values['velocity']**2-a['velocity']**2,axis=2,keepdims=True)
                record['independent_H_increment_max_error']=float(np.max(abs(values['enthalpy']-target)))
                if args.mode=='reference' and record['independent_H_increment_max_error']>1e-7:raise ValueError(record)
            if args.mode=='reference':
                target=Q/'reference'/path.parent.name;target.mkdir(parents=True,exist_ok=True);shutil.copyfile(log/'result.h5',target/'reference.h5');write_direct_grading(target,author_policy(Q))
            record['score']=grade_case(path,log/'result.h5',Q/'reference'/path.parent.name/'grading.json')['score']
        report['cases'].append(record);(Q/'author/data-evidence'/(args.mode+('-subset' if args.only else '')+'-replay.json')).write_text(json.dumps(report,indent=2)+'\n');print(record,flush=True)
    if args.mode=='reference' and not args.only:
        for i,name in [('01','01-unlimited'),('02','06-fallback')]:
            dest=Q/'samples'/i;shutil.copytree(Q/'cases'/name,dest/'input',dirs_exist_ok=True);shutil.copytree(Q/'reference'/name,dest/'reference',dirs_exist_ok=True);(dest/'output').mkdir(exist_ok=True);shutil.copyfile(dest/'reference/reference.h5',dest/'output/result.h5')
