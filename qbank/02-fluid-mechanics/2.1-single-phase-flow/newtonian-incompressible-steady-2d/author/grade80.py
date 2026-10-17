"""Consume independent full outputs against the fixed-commit assembled cases."""
from pathlib import Path
import argparse,json
from caeoj.sdk import load_problem,load_result
from caeoj.case_grading import grade_case


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('cases',type=Path);p.add_argument('evidence',type=Path);p.add_argument('report',type=Path);a=p.parse_args()
    comparisons=json.loads((a.evidence/'openfoam-comparison.json').read_text());selection=json.loads((a.cases/'data-manifest.json').read_text());records=[]
    for row in comparisons:
        name=row['name'];highest=max(map(int,row['levels']));problem=a.cases/'cases'/name/'problem.json';grading=a.cases/'reference'/name/'grading.json'
        for n in map(int,row['levels']):
            result=a.evidence/'openfoam'/name/f'n{n}'/'result.h5';load_result(load_problem(problem),result);grade=grade_case(problem,result,grading)
            if n==highest:assert grade['score']==1,(name,grade)
            records.append(dict(name=name,case_id=selection['cases'][name]['case_id'],level=n,final=n==highest,contract_valid=True,grading=grade))
    assert len([r for r in records if r['final']])==8
    a.report.write_text(json.dumps(dict(valid=True,contracts=len(records),final_passes=8,records=records),indent=2)+'\n')
    print(json.dumps(dict(contracts=len(records),final_passes=8,valid=True)))
