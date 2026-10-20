"""One finite native UMFPACK repair for four archived iterative-linear failures."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
from native_closed_cavity import digest, save
from native_thermal_statistics import run


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int,default=4);args=ap.parse_args()
    proof=json.loads((args.root/'maintenance/thermal-statistics-linear-repair-authorization.json').read_text());ids=[a['design_id'] for a in proof['attempts']];assert len(ids)==4 and len(set(ids))==4
    for a in proof['attempts']:
        assert Path(a['archived_failed_case']).is_dir()
        assert not (args.root/'cases'/a['design_id']).exists(), 'Never repeat an existing repair'
    p=next(args.snapshot.glob('qbank/02-fluid-mechanics/*/thermal-statistics-3d/author/chapter02-ten-20261020/design.json'));freeze=json.loads((args.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text());assert digest(p)==freeze['designs'][p.relative_to(args.snapshot).as_posix()]
    d=json.loads(p.read_text());tasks=[({**e,'task':d['task'],'model':d['model']},json.loads((p.parents[1]/'grading-template.json').read_text())) for e in d['proposed_cases'] if e['design_id'] in ids];assert len(tasks)==4
    with ProcessPoolExecutor(max_workers=min(args.workers,4)) as pool:
        states=list(pool.map(run,[args.root]*4,[e for e,g in tasks],[g for e,g in tasks],[True]*4))
    save(args.root/'maintenance/thermal-statistics-linear-repair-summary.json',states)


if __name__=='__main__':main()
