"""One explicitly bounded cold repair, after original failure is archived.

No change to physical data, LRR closure, stopping tolerances or iteration cap.
"""
import argparse
import json
from pathlib import Path
from native_closed_cavity import digest, save
from native_isothermal_rans import run


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int,default=1);args=ap.parse_args()
    proof=json.loads((args.root/'maintenance/isothermal-rans-pressure-repair-authorization.json').read_text())
    assert Path(proof['archived_failed_case']).is_dir()
    assert not (args.root/'cases'/proof['design_id']).exists(), 'Never repeat or replace an existing repair attempt'
    p=next(args.snapshot.glob('qbank/02-fluid-mechanics/*/isothermal-rans-3d/author/chapter02-ten-20261020/design.json'))
    freeze=json.loads((args.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text());assert digest(p)==freeze['designs'][p.relative_to(args.snapshot).as_posix()]
    d=json.loads(p.read_text());e=next(e for e in d['proposed_cases'] if e['design_id']==proof['design_id'])
    state=run(args.root,{**e,'task':d['task'],'model':d['model']},json.loads((p.parents[1]/'grading-template.json').read_text()),True)
    save(args.root/'maintenance/isothermal-rans-pressure-repair-summary.json',state)


if __name__=='__main__':main()
