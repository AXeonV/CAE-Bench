"""Execute numerical candidates and independently grade; record RSS and elapsed time."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import psutil
from caeoj.grading import grade_files
from caeoj.validation import write_json

ROOT=Path(__file__).resolve().parents[1]


def run(root=ROOT,program=None,selected=None,output=None):
    root=Path(root);program=Path(program) if program else root/'author/baseline.py'
    config=json.loads((root/'judge-config.json').read_text(encoding='utf-8'))
    output=Path(output) if output else root.parents[1]/'runs'/root.name/'baseline'
    rows=[]
    for path in sorted((root/'cases').glob('*/problem.json')):
        if selected and path.parent.name not in selected: continue
        logs=output/path.parent.name;logs.mkdir(parents=True,exist_ok=True)
        result=logs/'result.npz'
        env=os.environ.copy();env.update(PYTHONUTF8='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
        start=time.perf_counter();peak=0;failure=None
        with (logs/'stdout.log').open('wb') as out,(logs/'stderr.log').open('wb') as err:
            process=subprocess.Popen([sys.executable,str(program.resolve()),'--input',str(path.resolve()),
                '--output',str(result.resolve())],cwd=logs,env=env,stdout=out,stderr=err)
            monitor=psutil.Process(process.pid)
            while process.poll() is None:
                try: peak=max(peak,sum(x.memory_info().rss for x in [monitor,*monitor.children(recursive=True)] if x.is_running()))
                except (psutil.NoSuchProcess,psutil.AccessDenied): pass
                if time.perf_counter()-start>config['timeout_seconds']:failure='timeout'
                if peak>config['memory_mb']*1024**2:failure='memory_limit'
                if failure:
                    for child in monitor.children(recursive=True):child.kill()
                    process.kill();break
                time.sleep(0.01)
            process.wait()
        report={'status':failure or 'runtime_error','score':0} if failure or process.returncode else grade_files(
            path,result,root/'reference'/path.parent.name/'reference.npz',atol=config['atol'],rtol=config['rtol'])
        row={'case':path.parent.name,'wall_seconds':time.perf_counter()-start,'peak_rss_mib':peak/1024**2,**report}
        rows.append(row);print(json.dumps({k:v for k,v in row.items() if k!='fields'}),flush=True)
    if not rows:raise ValueError('No cases selected')
    report={'score':sum(r['score']==1 for r in rows),'total_cases':len(rows),
        'max_wall_seconds':max(r['wall_seconds'] for r in rows),
        'max_peak_rss_mib':max(r['peak_rss_mib'] for r in rows),'cases':rows}
    write_json(output/'report.json',report)
    return report


def main(root=ROOT):
    ap=argparse.ArgumentParser();ap.add_argument('--program',type=Path);ap.add_argument('--case',action='append');ap.add_argument('--output',type=Path)
    args=ap.parse_args();r=run(root,args.program,args.case,args.output)
    print(json.dumps({k:v for k,v in r.items() if k!='cases'},indent=2));return 0 if r['score']==r['total_cases'] else 1


if __name__=='__main__':sys.exit(main())
