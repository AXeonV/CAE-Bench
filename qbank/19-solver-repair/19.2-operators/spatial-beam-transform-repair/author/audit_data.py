"""Audit all assembled cases and references through the installed task SDK."""
import argparse,copy,json,tempfile
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem,load_result
from caeoj.storage import write_hdf5
from caeoj.case_grading import grade_case
TASK=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('--inputs-only',action='store_true');args=p.parse_args();report={'stage':'inputs-only' if args.inputs_only else 'all-input-reference-and-grading','cases':[]}
    for path in sorted((TASK/'cases').glob('*/problem.json')):
        problem=load_problem(path)
        item={'case':path.parent.name,'input_valid':True}
        if not args.inputs_only:
            ref=TASK/'reference'/path.parent.name;load_result(problem,ref/'reference.h5');grade=grade_case(path,ref/'reference.h5',ref/'grading.json');assert grade['score']==1;item['reference_self_grade']=grade['score']
        report['cases'].append(item)
    fixture=TASK/'cases/01-aligned-public';meta=json.loads((fixture/'problem.json').read_text());arrays=load_problem(fixture/'problem.json').arrays;mutations=[]
    def reject(name,edit):
        m=copy.deepcopy(meta);a={k:v.copy() for k,v in arrays.items()};edit(m,a)
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);(d/'problem.json').write_text(json.dumps(m));write_hdf5(d/'input.h5',a)
            try:load_problem(d/'problem.json')
            except (ValueError,RuntimeError) as e:mutations.append({'variant':name,'rejected':True,'exception':type(e).__name__});return
            raise AssertionError('Accepted invalid public declaration: '+name)
    reject('parallel_section_axis',lambda m,a:a['section_axis'].__setitem__((0,0),[1,0,0]))
    reject('zero_length',lambda m,a:a['endpoints'].__setitem__((0,0,slice(3,6)),a['endpoints'][0,0,:3]))
    reject('negative_density',lambda m,a:a['density'].__setitem__((0,0,0),-1))
    reject('excess_shear_area',lambda m,a:a['shear_area_y'].__setitem__((0,0,0),2*a['area'][0,0,0]))
    reject('wrong_acceleration_unit',lambda m,a:m['fields']['body_acceleration'].__setitem__('unit','N'))
    reject('missing_material',lambda m,a:m['fields'].pop('density'))
    report['negative_variants']=mutations
    (TASK/'author/data-evidence'/('input-contract-audit.json' if args.inputs_only else 'data-audit.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'cases':len(report['cases']),'negative_variants':len(mutations),'stage':report['stage']}))
if __name__=='__main__':main()

