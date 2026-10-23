"""Check EOS acceptance boundaries without changing any frozen input or answer."""
from pathlib import Path
import hashlib,importlib.util,json
import numpy as np
from caeoj.sdk import load_problem,load_result

Q=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('reconstruction_contract',Q/'extension/caeoj_task_ext/reconstruction.py')
checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)


def check(problem):
    errors=[];checker.check(problem,errors);return errors


if __name__=='__main__':
    rows=[]
    for path in sorted((Q/'cases').glob('*/problem.json')):
        p=load_problem(path);assert not check(p);load_result(p,Q/'reference'/path.parent.name/'reference.h5')
        row={'case':path.parent.name,'full_checker_valid':True,'reference_contract_valid':True}
        par={k:v['value'] for k,v in p.manifest['physics']['parameters'].items()}
        if par['operation']==0:
            a=p.arrays;original=a['density'].copy()
            rho=a['pressure']/(par['gas_constant']*a['temperature']);tolerance=1e-12+1e-12*abs(rho)
            for ratio,accepted in [(.99,True),(1.01,False)]:
                a['density'][:]=original;a['density'][0,0,0]=rho[0,0,0]+ratio*tolerance[0,0,0]
                errors=check(p);assert bool(errors)!=accepted,(path,ratio,errors)
            a['density'][:]=original;a['density'][0,0,0]*=1.01
            assert any('density' in str(error) for error in check(p))
            a['density'][:]=original;assert not check(p)
            cp=par['gamma']*par['gas_constant']/(par['gamma']-1)
            offset=a['enthalpy']-cp*a['temperature']-.5*np.sum(a['velocity']**2,axis=2,keepdims=True)
            row.update(eos_tolerance_inside_accepted=True,eos_tolerance_outside_rejected=True,
                       density_percent_mismatch_rejected=True,stage_enthalpy_offset_max_abs=float(abs(offset).max()))
        rows.append(row)
    result={'passed':True,'atol_kg_m3':1e-12,'rtol':1e-12,'cases':rows,
            'checker_sha256':hashlib.sha256((Q/'extension/caeoj_task_ext/reconstruction.py').read_bytes()).hexdigest(),
            'DATA_sha256':hashlib.sha256((Q/'DATA.md').read_bytes()).hexdigest()}
    (Q/'author/data-evidence/eos-contract-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'passed':True,'cases':len(rows),'direct_eos_boundaries':7}))
