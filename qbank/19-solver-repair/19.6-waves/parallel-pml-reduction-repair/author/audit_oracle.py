"""Bind actual Harbor terminal, build records and every returned array to references."""
import argparse,hashlib,json,shutil
from pathlib import Path
import h5py,numpy as np
TASK=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--job',type=Path,required=True);p.add_argument('--label',required=True);a=p.parse_args()
    results=list(a.job.glob('*/result.json'));assert len(results)==1
    trial=results[0].parent;terminal=json.loads(results[0].read_text());assert not terminal.get('exception_info'),terminal.get('exception_info')
    verifier=trial/'verifier';report=json.loads((verifier/'report.json').read_text());assert report['complete'] and report['score']==report['total_cases']==report['completed_cases']==8
    rows=[]
    for row in report['cases']:
        actual=verifier/row['case']/'result.h5';reference=TASK/'reference'/row['case']/'reference.h5'
        with h5py.File(actual) as x,h5py.File(reference) as y:
            assert set(x)==set(y)
            for name in x:assert np.array_equal(x[name][:],y[name][:]),(row['case'],name)
        rows.append({'case':row['case'],'score':row['score'],'all_arrays_bitwise_equal':True,'returned_file_sha256':hashlib.sha256(actual.read_bytes()).hexdigest()})
    build={p.name:json.loads(p.read_text()) for p in (verifier/'build').glob('*report.json')}
    snapshot=json.loads((TASK.parents[3]/'runs/authoring/repair-22'/(a.job.name+'.json')).read_text())['task_sha256']
    record={'job':a.job.name,'exception_info':terminal.get('exception_info'),'reward':report['reward'],'passed':8,'total':8,'all_returned_arrays_equal':True,'cases':rows,'build':build,
            'configured_source_repair_sha256':snapshot['tests/source-repair.json'],'tested_agent_zip_sha256':snapshot['tests/agent.zip']}
    (TASK/'author/data-evidence'/('oracle-'+a.label+'.json')).write_text(json.dumps(record,indent=2));print(json.dumps({'job':a.job.name,'passed':8,'total':8,'exception_info':None,'all_arrays_equal':True}))
