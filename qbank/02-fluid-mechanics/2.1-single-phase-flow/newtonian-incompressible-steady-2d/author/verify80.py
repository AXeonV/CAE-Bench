"""Fixed-commit isolated assembly and actual positive grading via existing pool API."""
from pathlib import Path
import argparse,json,re
from huggingface_hub import snapshot_download
from caeoj_tools import data_pool as pool
from caeoj.sdk import load_problem,load_result
from caeoj.case_grading import grade_case


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('selection',type=Path);p.add_argument('destination',type=Path);p.add_argument('report',type=Path)
    p.add_argument('--revision',required=True);p.add_argument('--cache',type=Path,required=True);p.add_argument('--include-existing',type=Path);p.add_argument('--expected-cases',type=int,choices=[80,100],default=80);a=p.parse_args()
    assert re.fullmatch('[a-f0-9]{40}',a.revision)
    value=pool.manifest(a.selection);assert len(value['cases'])==a.expected_cases
    if a.include_existing:
        old=pool.manifest(a.include_existing);assert old['repository']==value['repository'] and not set(old['cases'])&set(value['cases'])
        value={**value,'cases':{**old['cases'],**value['cases']},'samples':{}}
    # Parallel cache warming is the official SDK; all validation remains in HubStore.
    snapshot_download(value['repository']['repo_id'],repo_type='dataset',revision=a.revision,cache_dir=a.cache,
                      allow_patterns=[value['repository']['path']+'/pool/**'],max_workers=8)
    store=pool.HubStore(value['repository']['repo_id'],revision=a.revision,cache_dir=a.cache)
    a.destination.mkdir(parents=True,exist_ok=False);pool.write_json(a.destination/'data-manifest.json',value)
    assembly=pool.assemble(a.destination,value,store);verified=pool.verify(a.destination,strict=True);assert verified['valid']
    grades=[]
    for name,entry in value['cases'].items():
        case=a.destination/'cases'/name;reference=a.destination/'reference'/name
        result=reference/'reference.h5';load_result(load_problem(case/'problem.json'),result)
        grade=grade_case(case/'problem.json',result,reference/'grading.json');assert grade['score']==1,(name,grade)
        grades.append(dict(name=name,case_id=entry['case_id'],grade=grade))
    report=dict(revision=a.revision,cases=len(grades),assembly=assembly,strict_verify=verified,positive_grading=grades,valid=True)
    a.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(revision=a.revision,cases=len(grades),valid=True)))
