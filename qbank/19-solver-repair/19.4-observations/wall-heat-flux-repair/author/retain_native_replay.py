"""Observe a second real execution of every frozen input, retaining the raw chain."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
import uuid
import numpy as np
from caeoj.sdk import load_problem,load_result

Q=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--docker',default='docker')
    parser.add_argument('--work',type=Path,required=True)
    args=parser.parse_args()
    args.work=args.work.resolve();args.work.mkdir(parents=True,exist_ok=True)
    image=json.loads((Q/'author/data-evidence/reference-replay.json').read_text())['image']
    runtime=Q.parents[3]/'work/repair-22/su2-2347/runtime/src'
    report={'image':image,'observer_sha256':hashlib.sha256((Q/'author/observe_native.py').read_bytes()).hexdigest(),
            'public_driver_sha256':hashlib.sha256((Q/'public/run_case.py').read_bytes()).hexdigest(),'cases':[]}
    for path in sorted((Q/'cases').glob('*/problem.json')):
        output=args.work/path.parent.name;output.mkdir(exist_ok=True)
        assert not (output/'result.h5').exists(),'Inspect existing output before replaying'
        name='su22347-native-'+uuid.uuid4().hex[:10]
        command=[args.docker,'run','--name',name,'--rm','--network','none','--cpus','2','--memory','4g',
                 '--user','1000:1000','-v',str(Q)+':/task:ro','-v',str(runtime)+':/runtime:ro',
                 '-v',str(output)+':/outputs','-e','PYTHONPATH=/runtime',image,'python',
                 '/task/author/observe_native.py','/task/cases/'+path.parent.name+'/problem.json']
        state={'command':command,'container_name':name,'started_unix':time.time()}
        with (output/'stdout.log').open('w') as stdout,(output/'stderr.log').open('w') as stderr:
            process=subprocess.Popen(command,stdout=stdout,stderr=stderr,text=True)
            state.update(status='running',host_cli_pid=process.pid)
            (output/'run-state.json').write_text(json.dumps(state,indent=2))
            try:code=process.wait(timeout=300)
            except subprocess.TimeoutExpired:
                state.update(status='outer-timeout-container-status-required')
                (output/'run-state.json').write_text(json.dumps(state,indent=2));raise
        state.update(status='completed',exit_code=code,elapsed_seconds=time.time()-state['started_unix'])
        (output/'run-state.json').write_text(json.dumps(state,indent=2))
        assert code==0,(output/'stderr.log').read_text()
        problem=load_problem(path)
        actual=load_result(problem,output/'result.h5');reference=load_result(problem,Q/'reference'/path.parent.name/'reference.h5')
        errors={key:float(np.max(abs(actual[key]-value))) for key,value in reference.items()}
        for key,value in reference.items():np.testing.assert_allclose(actual[key],value,rtol=1e-12,atol=1e-8)
        native={p.relative_to(output/'native').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (output/'native').rglob('*') if p.is_file()}
        for required in ['restart.csv','surface.csv','history.csv','config.cfg','mesh.su2','stdout.log','stderr.log']:assert required in native,required
        report['cases'].append({'case':path.parent.name,'passed':True,'seconds':state['elapsed_seconds'],
                                'reference_max_abs_errors':errors,'native_sha256':native})
        (Q/'author/data-evidence/retained-native-replay.json').write_text(json.dumps(report,indent=2)+'\n')
        print(report['cases'][-1]['case'],state['elapsed_seconds'],flush=True)
