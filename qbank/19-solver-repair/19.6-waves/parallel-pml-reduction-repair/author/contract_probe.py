"""Independent DATA-derived valid/invalid variants using actual candidate inputs."""
import argparse,copy,importlib.util,json,shutil,tempfile
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem
from caeoj.storage import write_hdf5
from caeoj.validation import ContractError,write_json
TASK=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--dataset',type=Path,required=True);a=p.parse_args()
    s=importlib.util.spec_from_file_location('wave_contract',TASK/'extension/caeoj_task_ext/parallel_wave.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
    tests=[('ordinary',True,None),('nonconsecutive_probe_ids',True,lambda m,x:x.update(probe_ids=x['probe_ids']*7+300)),
       ('reverse_probe_coordinates',True,lambda m,x:x.update(probe_coordinates=x['probe_coordinates'][::-1])),
       ('descending_cell_ids',False,lambda m,x:x.update(cell_ids=x['cell_ids'][::-1],pml_region=x['pml_region'][:,::-1,:])),
       ('frequency_zero',False,lambda m,x:m['physics']['parameters']['frequency'].update(value=0)),
       ('wrong_density_unit',False,lambda m,x:m['physics']['parameters']['density'].update(unit='1')),
       ('missing_processes',False,lambda m,x:m['physics']['parameters'].pop('processes')),
       ('noninteger_processes',False,lambda m,x:m['physics']['parameters']['processes'].update(value=3.0)),
       ('time_origin_wrong',False,lambda m,x:x.update(times=x['times']+.001)),
       ('static_label_wrong',False,lambda m,x:x.update(static_time=np.array([.1]))),
       ('source_zero',False,lambda m,x:x['source_amplitude'].__setitem__((0,0,0),0)),
       ('probe_on_wall',False,lambda m,x:x['probe_coordinates'].__setitem__((0,1),0)),
       ('probe_at_source',False,lambda m,x:x['probe_coordinates'].__setitem__(0,x['source_coordinates'][0])),
       ('sh_pml_forbidden',False,lambda m,x:x['pml_region'].__setitem__((0,0,0),2)),
       ('pml_unknown_flag',False,lambda m,x:x['pml_region'].__setitem__((0,0,0),3))]
    original=a.dataset/'cases/02-isolated-master-sh';q=load_problem(original/'problem.json');report=[]
    for name,expected,mutate in tests:
        m=copy.deepcopy(q.manifest);x={k:v.copy() for k,v in q.arrays.items()}
        if mutate:mutate(m,x)
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp);shutil.copyfile(original/'mesh.msh',dest/'mesh.msh');write_json(dest/'problem.json',m);write_hdf5(dest/'input.h5',x)
            try:problem=load_problem(dest/'problem.json');e=[];c.check(problem,e);valid=not e
            except ContractError:valid=False
        if valid!=expected:raise ValueError((name,expected,valid))
        report.append({'variant':name,'expected_valid':expected,'actual_valid':valid})
    (TASK/'author/data-evidence/contract-probes.json').write_text(json.dumps({'passed':True,'checks':report},indent=2));print(len(report),'DATA-derived variant checks passed')
