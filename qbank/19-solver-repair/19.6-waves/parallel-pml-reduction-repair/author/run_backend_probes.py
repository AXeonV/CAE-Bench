"""Run each trusted-backend fault probe in its own disposable container."""
import argparse,json,subprocess,time
from pathlib import Path
TASK=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--logs',type=Path,required=True);p.add_argument('--expected-archive');p.add_argument('--expected-judge');a=p.parse_args();a.logs.mkdir(parents=True,exist_ok=True);rows=[]
    if a.expected_archive:
        deadline=time.monotonic()+300
        while True:
            r=subprocess.run(['docker','run','--rm','--network','none','caeoj-specfem661-probes:preflight','python','-c',"import hashlib;from pathlib import Path;print(hashlib.sha256(Path('/tests/agent.zip').read_bytes()).hexdigest())"],text=True,capture_output=True)
            if r.returncode==0 and r.stdout.strip()==a.expected_archive:break
            if time.monotonic()>deadline:raise RuntimeError('Expected final probe image did not become available')
            time.sleep(5)
    image=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}','caeoj-specfem661-probes:preflight'],text=True).strip()
    judge_sha=subprocess.check_output(['docker','run','--rm','--network','none',image,'python','-c',"import hashlib;from pathlib import Path;print(hashlib.sha256(Path('/tests/judge.py').read_bytes()).hexdigest())"],text=True).strip()
    if a.expected_judge:assert judge_sha==a.expected_judge,(judge_sha,a.expected_judge)
    for mode in ['valid','syntax','extra','symlink','compiler','baseline-runtime','runtime-timeout']:
        cmd=['docker','run','--rm','--name','caeoj-specfem661-probe-'+mode,'--network','none','--cpus','4','--memory','4g',image,'python','/opt/backend_probe.py',mode]
        start=time.monotonic();r=subprocess.run(cmd,text=True,capture_output=True,timeout=300)
        (a.logs/(mode+'.stdout.json')).write_text(r.stdout);(a.logs/(mode+'.stderr.log')).write_text(r.stderr)
        if r.returncode:raise RuntimeError(mode+': '+r.stdout+'\n'+r.stderr)
        row=json.loads(r.stdout);row['elapsed_seconds']=time.monotonic()-start;rows.append(row)
        (TASK/'author/data-evidence/backend-probes.json').write_text(json.dumps({'passed':len(rows)==7 and all(x['passed'] for x in rows),'complete':len(rows)==7,'image_id':image,'expected_agent_zip_sha256':a.expected_archive,'judge_sha256':judge_sha,'probes':rows},indent=2))
        print(mode,'passed',round(row['elapsed_seconds'],3),flush=True)
