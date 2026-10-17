"""Preserve the withdrawn branch, then start the requested branch at HF main.

Does not upload data. Existing unexpected branch state is a hard stop.
"""
from pathlib import Path
import json
from huggingface_hub import HfApi

api=HfApi(); repo='jimzhouzzy2006/CAE-Bench-OJ'; branch='cases/2-1-1-supplement'
main=api.repo_info(repo,repo_type='dataset',revision='main').sha
refs={b.name:b.target_commit for b in api.list_repo_refs(repo,repo_type='dataset').branches}
prior=refs.get(branch)
archive=None
if prior and prior!=main:
    if prior!='b4ed7ab0763284bd213b00cbd2bcb8f7528f7f18':
        raise RuntimeError('Unexpected branch state; inspect concurrent changes')
    archive='archive/2-1-1-withdrawn-20261017'
    api.create_branch(repo,repo_type='dataset',branch=archive,revision=prior,exist_ok=True)
    assert api.repo_info(repo,repo_type='dataset',revision=archive).sha==prior
    api.delete_branch(repo,repo_type='dataset',branch=branch)
if prior!=main:
    api.create_branch(repo,repo_type='dataset',branch=branch,revision=main)
assert api.repo_info(repo,repo_type='dataset',revision=branch).sha==main
out=Path(__file__).parent/'data-evidence/supplement-20261017/hf-start.json'
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(dict(repo=repo,main_start=main,branch=branch,branch_start=main,
                               previous_branch=prior,preserved_as=archive),indent=2)+'\n')
print(out.read_text())
