"""Finite native UMFPACK repair for explicitly archived iterative-linear failures."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
from native_closed_cavity import digest, save
from native_thermal_statistics import run


def execute(root,snapshot,workers,authorization,summary):
    proof=json.loads((root/'maintenance'/authorization).read_text());ids=[a['design_id'] for a in proof['attempts']];assert 1<=len(ids)<=10 and len(set(ids))==len(ids)
    for a in proof['attempts']:
        assert Path(a['archived_failed_case']).is_dir()
        assert not (root/'cases'/a['design_id']).exists(), 'Never repeat an existing repair'
    p=next(snapshot.glob('qbank/02-fluid-mechanics/*/thermal-statistics-3d/author/chapter02-ten-20261020/design.json'));freeze=json.loads((snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text());assert digest(p)==freeze['designs'][p.relative_to(snapshot).as_posix()]
    d=json.loads(p.read_text());tasks=[({**e,'task':d['task'],'model':d['model']},json.loads((p.parents[1]/'grading-template.json').read_text())) for e in d['proposed_cases'] if e['design_id'] in ids];assert len(tasks)==len(ids)
    with ProcessPoolExecutor(max_workers=min(workers,len(ids))) as pool:
        states=list(pool.map(run,[root]*len(ids),[e for e,g in tasks],[g for e,g in tasks],[True]*len(ids)))
    save(root/'maintenance'/summary,states)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int,default=4);args=ap.parse_args()
    execute(args.root,args.snapshot,args.workers,'thermal-statistics-linear-repair-authorization.json','thermal-statistics-linear-repair-summary.json')


if __name__=='__main__':main()
