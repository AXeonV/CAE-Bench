"""Produce references only by executing the pinned real library image."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,subprocess,time,uuid
import numpy as np
from caeoj.sdk import load_problem,write_result
from caeoj.case_grading import grade_case
from caeoj_tools.grading_policy import author_policy,write_direct_grading
TASK=Path(__file__).resolve().parents[1]


def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v


def point_audit(payload,actual):
    sources=np.asarray(payload['sources']);targets=np.asarray(payload['targets']);q=np.asarray(payload['strength']);q=q[:,0]+1j*q[:,1]
    k=complex(payload['wavenumber_real'],payload['wavenumber_imag']);diff=targets[:,None,:]-sources[None,:,:];r=np.linalg.norm(diff,axis=-1)
    kernel=np.exp(1j*k*r)/(4*np.pi*r)
    u=kernel@q;grad=np.einsum('ts,tsc,s->tc',kernel*(1j*k-1/r)/r,diff,q)
    out={}
    for method in ['fmm','local']:
        for name,value in [('potential',u[:,None]),('gradient',grad)]:
            expected=np.stack([value.real,value.imag],axis=-1).reshape(len(targets),-1)
            seen=actual[method+'_'+name][0];delta=abs(seen-expected);ratio=delta/(1e-7+2e-6*abs(expected))
            out[method+'_'+name]={'max_absolute_error':float(delta.max()),'max_tolerance_fraction':float(ratio.max()),'passed':bool(np.all(ratio<=1))}
    return out


def replay(dataset,image,docker,mode,resume):
    adapter=module('bempp_adapter',TASK/'public/run_case.py');contract=module('bempp_contract',TASK/'extension/caeoj_task_ext/helmholtz.py')
    image_id=json.loads(subprocess.check_output([docker,'image','inspect',image]))[0]['Id'];driver_sha=hashlib.sha256((TASK/'public/driver.py').read_bytes()).hexdigest()
    report={'mode':mode,'image_id':image_id,'driver_sha256':driver_sha,'producer':'actual pinned Bempp API plus genuine native ExaFMM; mathematical audit never produces reference','cases':[]}
    previous=dataset/(mode+'-report.json');cached={}
    if resume and previous.exists():
        saved=json.loads(previous.read_text());assert saved['image_id']==image_id and saved['driver_sha256']==driver_sha and saved['mode']==mode
        report=saved;cached={v['case']:v for v in saved['cases']}
    for path in sorted((dataset/'cases').glob('*/problem.json')):
        problem=load_problem(path);errors=[];contract.check(problem,errors);assert not errors,(path,errors)
        payload=adapter.serialize(problem);assets={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in path.parent.iterdir() if p.name in ['problem.json','input.h5','surface.msh']}
        if path.parent.name in cached:
            assert cached[path.parent.name]['input_assets']==assets
            continue
        log=(dataset/'replay'/mode/path.parent.name).resolve();log.mkdir(parents=True,exist_ok=True)
        container='bempp20-'+uuid.uuid4().hex[:12]
        cmd=[docker,'run','--rm','--name',container,'--network','none','--cpus','4','--memory','4g','--user','1000:1000','--read-only','--tmpfs','/tmp:rw,size=768m','-e','HOME=/tmp','-i',image_id,'/opt/bempp-env/bin/python','/opt/repair-driver/driver.py']
        start=time.monotonic()
        try:result=subprocess.run(cmd,input=payload,text=True,capture_output=True,timeout=660)
        except subprocess.TimeoutExpired:
            subprocess.run([docker,'rm','--force',container],capture_output=True);raise
        elapsed=time.monotonic()-start
        for name,value in [('payload.json',payload),('stdout.json',result.stdout),('stderr.log',result.stderr)]: (log/name).write_bytes(value.encode())
        row={'case':path.parent.name,'command':cmd,'elapsed_seconds':elapsed,'returncode':result.returncode,'input_assets':assets,'payload_sha256':hashlib.sha256(payload.encode()).hexdigest(),'stdout_sha256':hashlib.sha256(result.stdout.encode()).hexdigest()}
        if result.returncode:
            if mode=='reference':raise RuntimeError((path,result.stderr))
            row.update(score=0,failure='actual native API/runtime failure')
        else:
            actual=adapter.adapt(result.stdout);target=dataset/'reference'/path.parent.name if mode=='reference' else log;target.mkdir(parents=True,exist_ok=True)
            out=target/('reference.h5' if mode=='reference' else 'result.h5');write_result(out,problem,actual)
            if mode=='reference':write_direct_grading(target,author_policy(TASK))
            row['score']=grade_case(path,out,dataset/'reference'/path.parent.name/'grading.json')['score'];row['output_sha256']=hashlib.sha256(out.read_bytes()).hexdigest()
            if problem.manifest['physics']['parameters']['operation']['value']==0:
                row['independent_point_audit']=point_audit(json.loads(payload),actual)
                if mode=='reference':assert all(v['passed'] for v in row['independent_point_audit'].values()),row
            if mode=='reference':assert row['score']==1 and elapsed<600,row
        report['cases'].append(row);previous.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(path.parent.name,mode,row['score'],elapsed,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--dataset',type=Path,required=True);p.add_argument('--image',required=True);p.add_argument('--docker',default='docker');p.add_argument('--mode',choices=['reference','defect'],required=True);p.add_argument('--resume',action='store_true');a=p.parse_args();replay(a.dataset,a.image,a.docker,a.mode,a.resume)
