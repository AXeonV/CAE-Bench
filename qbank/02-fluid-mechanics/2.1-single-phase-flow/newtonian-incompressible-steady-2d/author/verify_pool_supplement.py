"""Use the existing pool transport for isolated local/fixed-commit validation."""
from pathlib import Path
import argparse,json,re
from caeoj_tools import data_pool as pool
from audit_supplement import audit

p=argparse.ArgumentParser();p.add_argument('bundle',type=Path);p.add_argument('destination',type=Path);p.add_argument('report',type=Path)
p.add_argument('--revision');p.add_argument('--cache',type=Path);args=p.parse_args()
choice=pool.manifest(args.bundle/'selection.json')
if args.revision:
    assert re.fullmatch('[a-f0-9]{40}',args.revision),'Remote validation requires a fixed commit'
    store=pool.HubStore(choice['repository']['repo_id'],revision=args.revision,cache_dir=args.cache)
else:
    store=pool.LocalStore(args.bundle/'repository')
args.destination.mkdir(parents=True,exist_ok=False)
pool.write_json(args.destination/'data-manifest.json',choice)
assembly=pool.assemble(args.destination,choice,store)
verified=pool.verify(args.destination,strict=True)
assert verified['valid'],verified
rows=audit(args.destination)
report=dict(revision=args.revision,assembly=assembly,strict_verify=verified,actual_inputs_and_grading=rows)
args.report.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(revision=args.revision,valid=verified['valid'],cases=len(rows))))
