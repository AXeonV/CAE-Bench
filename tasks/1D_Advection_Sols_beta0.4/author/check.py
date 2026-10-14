"""Grade a local submission and measure process-tree time and RSS."""
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

TASK=Path(__file__).resolve().parents[1]


def check(program,output):
    config=json.loads((TASK/'judge-config.json').read_text())
    rows=[]
    for path in sorted((TASK/'cases').glob('*/problem.json')):
        logs=output/path.parent.name;logs.mkdir(parents=True,exist_ok=True)
        result=logs/'result.h5'
        if result.exists():result.unlink()
        env=os.environ.copy();env.update(PYTHONUTF8='1')
        start=time.perf_counter();peak=0;failure=None
        with (logs/'stdout.log').open('wb') as stdout,(logs/'stderr.log').open('wb') as stderr:
            process=subprocess.Popen([sys.executable,str(program.resolve()),'--input',str(path.resolve()),
                '--output',str(result.resolve())],cwd=logs,env=env,stdout=stdout,stderr=stderr)
            monitor=psutil.Process(process.pid)
            while process.poll() is None:
                try:
                    peak=max(peak,sum(p.memory_info().rss for p in [monitor,*monitor.children(recursive=True)] if p.is_running()))
                except (psutil.NoSuchProcess,psutil.AccessDenied):pass
                if time.perf_counter()-start>config['timeout_seconds']:failure='timeout'
                if config.get('memory_mb') and peak>config['memory_mb']*1024**2:failure='memory_limit'
                if failure:
                    for child in monitor.children(recursive=True):child.kill()
                    process.kill();break
                time.sleep(0.01)
            process.wait()
        grade={'status':failure or 'runtime_error','score':0} if failure or process.returncode else grade_files(
            path,result,TASK/'reference'/path.parent.name/'reference.h5',atol=config['atol'],rtol=config['rtol'])
        row={'case':path.parent.name,'wall_seconds':time.perf_counter()-start,'peak_rss_mib':peak/1024**2,**grade}
        rows.append(row);print(json.dumps({k:v for k,v in row.items() if k!='fields'}),flush=True)
    if not rows:raise ValueError('No cases generated')
    summary={'score':sum(r['score']==1 for r in rows),'total_cases':len(rows),
        'max_wall_seconds':max(r['wall_seconds'] for r in rows),
        'max_peak_rss_mib':max(r['peak_rss_mib'] for r in rows),'cases':rows}
    write_json(output/'report.json',summary)
    return summary


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--program',type=Path,default=Path(__file__).with_name('baseline.py'))
    ap.add_argument('--output',type=Path,default=TASK.parents[1]/'runs'/TASK.name/'baseline')
    args=ap.parse_args();report=check(args.program,args.output)
    print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2))
    sys.exit(0 if report['score']==report['total_cases'] else 1)
