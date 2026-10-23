"""Produce references by actual pinned PyBaMM execution; independently check all states."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import time
import numpy as np
from caeoj.sdk import load_problem, write_result
from caeoj.case_grading import grade_case
from caeoj_tools.grading_policy import author_policy, write_direct_grading

TASK=Path(__file__).resolve().parents[1]
SUBDIR='src/pybamm/models/submodels/thermal'


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset',type=Path,required=True)
    parser.add_argument('--image',required=True)
    parser.add_argument('--docker',default='docker')
    parser.add_argument('--mode',choices=['reference','defect','validation'],required=True)
    parser.add_argument('--fixed-source-dir',type=Path)
    parser.add_argument('--case',action='append')
    args=parser.parse_args()
    adapter=module('hys_adapter',TASK/'public/run_case.py')
    checker=module('hys_contract',TASK/'extension/caeoj_task_ext/hysteresis.py')
    image=json.loads(subprocess.check_output([args.docker,'image','inspect',args.image]))[0]['Id']
    report_path=args.dataset/(args.mode+'-report.json')
    prior=json.loads(report_path.read_text('utf-8')) if args.case and report_path.exists() else None
    report={'mode':args.mode,'image_id':image,'cases':[],
            'input_sha256_definition':'SHA256 of UTF-8 JSON payload serialized by public/run_case.py and passed unchanged to the actual solver driver; not the raw input.h5 file digest',
            'reference_producer':'actual pinned PyBaMM submodels, not author independent algebra',
            'driver_sha256':hashlib.sha256((TASK/'public/driver.py').read_bytes()).hexdigest(),
            'source_overlays_sha256':{}}
    mounts=['--mount','type=bind,source='+str((TASK/'public/driver.py').resolve())+',target=/opt/repair-driver/driver.py,readonly']
    if args.fixed_source_dir:
        if args.mode!='reference':raise ValueError('No oracle source overlays in defect mode')
        for name in ['base_thermal.py']:
            path=(args.fixed_source_dir/name).resolve()
            report['source_overlays_sha256'][name]=hashlib.sha256(path.read_bytes()).hexdigest()
            mounts+=['--mount',f'type=bind,source={path},target=/opt/pybamm-build/source/{SUBDIR}/{name},readonly']
    for path in sorted((args.dataset/'cases').glob('*/problem.json')):
        if args.case and path.parent.name not in args.case:continue
        problem=load_problem(path)
        errors=[]
        checker.check(problem,errors)
        if errors:raise ValueError((str(path),errors))
        command=[args.docker,'run','--rm','--network','none','--cpus','4','--memory','8g',
                 '--user','1000:1000',*mounts,'-i',image,'/opt/solver-venv/bin/python','/opt/repair-driver/driver.py']
        start=time.monotonic()
        text=adapter.serialize(problem)
        execution=subprocess.run(command,input=text,capture_output=True,text=True,timeout=45)
        elapsed=time.monotonic()-start
        log=args.dataset/'replay'/args.mode/path.parent.name
        log.mkdir(parents=True,exist_ok=True)
        (log/'input.json').write_text(text,encoding='utf-8')
        (log/'stdout.json').write_text(execution.stdout,encoding='utf-8')
        (log/'stderr.log').write_text(execution.stderr,encoding='utf-8')
        if execution.returncode:raise RuntimeError(str(path)+': '+execution.stderr)
        values={name:np.asarray(array,dtype='float64')[None,:,:] for name,array in json.loads(execution.stdout).items()}
        expected=json.loads((args.dataset/'independent-checks'/(path.parent.name+'.json')).read_text(encoding='utf-8'))
        checks={}
        for name,value in values.items():
            exact=np.asarray(expected[name])
            atol=1e-8 if name=='area_heat' else 1e-9 if name=='cell_heat' else 1e-6
            ratio=np.abs(value-exact)/(atol+1e-8*np.abs(exact))
            checks[name]={'max_absolute_error':float(np.max(np.abs(value-exact))),
                          'max_tolerance_fraction':float(np.max(ratio)),'passed':bool(np.all(ratio<=1))}
        target=args.dataset/'reference'/path.parent.name if args.mode=='reference' else log
        target.mkdir(parents=True,exist_ok=True)
        output=target/('reference.h5' if args.mode=='reference' else 'result.h5')
        write_result(output,problem,values)
        if args.mode=='reference':
            if not all(c['passed'] for c in checks.values()):raise ValueError((path,checks))
            write_direct_grading(target,author_policy(TASK))
        grade=grade_case(path,output,args.dataset/'reference'/path.parent.name/'grading.json')
        report['cases'].append({'case':path.parent.name,'elapsed_seconds':elapsed,'score':grade['score'],
                                'command':command,'checks':checks,'input_sha256':hashlib.sha256(text.encode()).hexdigest(),
                                'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest()})
        if prior:
            report['cases']=[row for row in prior['cases'] if row['case'] not in args.case]+report['cases']
            report['cases'].sort(key=lambda row:row['case'])
            prior=None
        (args.dataset/(args.mode+'-report.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print(path.parent.name,args.mode,grade['score'],flush=True)
