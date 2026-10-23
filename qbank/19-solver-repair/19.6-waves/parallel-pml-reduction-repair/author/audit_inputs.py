"""Enumerate actual contracts, inputs and genuine mesher partition databases."""
import argparse,hashlib,importlib.util,json,struct
from pathlib import Path
from caeoj.sdk import load_problem,load_result
from caeoj.case_grading import grade_case
TASK=Path(__file__).resolve().parents[1]
def records(path):
    b=path.read_bytes();o=0;rows=[]
    while o<len(b):
        n=struct.unpack_from('<i',b,o)[0]
        if struct.unpack_from('<i',b,o+4+n)[0]!=n:raise ValueError('Unformatted record framing changed')
        rows.append(b[o+4:o+4+n]);o+=n+8
    return rows
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--dataset',required=True,type=Path);a=p.parse_args()
    s=importlib.util.spec_from_file_location('wave_contract',TASK/'extension/caeoj_task_ext/parallel_wave.py');contract=importlib.util.module_from_spec(s);s.loader.exec_module(contract)
    result=[]
    for path in sorted((a.dataset/'cases').glob('*/problem.json')):
        problem=load_problem(path);errors=[];contract.check(problem,errors)
        if errors:raise ValueError(errors)
        grade=grade_case(path,a.dataset/'reference'/path.parent.name/'reference.h5',a.dataset/'reference'/path.parent.name/'grading.json')
        if grade['score']!=1:raise ValueError(grade)
        databases=[]
        for db in sorted((a.dataset/'replay/reference'/path.parent.name/'OUTPUT_FILES').glob('Database*.bin')):
            r=records(db);nspec=struct.unpack('<i',r[2])[0]
            # save_databases_materials writes (i,indic,13 doubles), then nspec
            # element rows. The next record is the real interface header.
            k=[i for i,x in enumerate(r) if len(x)==112 and struct.unpack_from('<ii',x)==(1,1)][-1]
            ninterface,maxsize=struct.unpack('<ii',r[k+1+nspec])
            databases.append({'rank':int(db.stem[-5:]),'elements':nspec,'interfaces':ninterface,'max_interface_records':maxsize,'sha256':hashlib.sha256(db.read_bytes()).hexdigest()})
        expected_processes=problem.manifest['physics']['parameters']['processes']['value']
        if len(databases)!=expected_processes:raise ValueError('Incomplete genuine mesher databases')
        result.append({'case':path.parent.name,'all_arrays':{k:{'dtype':str(v.dtype),'shape':list(v.shape)} for k,v in problem.arrays.items()},'native_partition':databases,'reference_grade':grade['score']})
    samples=[]
    for path in sorted((a.dataset/'samples').glob('*/input/problem.json')):
        problem=load_problem(path);load_result(problem,path.parent.parent/'output/result.h5');samples.append(str(path))
    report={'cases':result,'samples':samples,'passed':True,'scope':'all 8 actual inputs, exact reference grades, 2 public complete outputs, actual original mesher interface headers; does not certify continuum accuracy'}
    (TASK/'author/data-evidence/input-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps({r['case']:[d['interfaces'] for d in r['native_partition']] for r in result},indent=2))
