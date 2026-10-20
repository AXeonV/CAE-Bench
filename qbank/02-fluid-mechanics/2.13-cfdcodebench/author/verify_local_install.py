"""Exercise actual local cases through an already normally installed public CLI."""
import argparse,hashlib,json,subprocess
from pathlib import Path
from catalog import ROOT,WORK,catalog

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--python',type=Path,default=ROOT/'runs/install-check/cfdcodebench-20261019/venv/Scripts/python.exe');a=ap.parse_args()
    out=WORK/'installed-real-cases';out.mkdir(exist_ok=True);rows=[]
    for c in catalog():
        case=WORK/'local-pool'/c['task']/f"C{c['index']:02}-base";input=case/'input/problem.json';ref=case/'reference/reference.h5';grading=ref.with_name('grading.json')
        if not ref.exists():rows.append(dict(index=c['index'],status='reference_pending'));continue
        digest=hashlib.sha256(ref.read_bytes()).hexdigest();result=[]
        commands=[['validate-input',str(input)],['validate-output','--input',str(input),'--output',str(ref)],['grade','--input',str(input),'--output',str(ref),'--grading',str(grading)]]
        for command in commands:
            p=subprocess.run([str(a.python),'-I','-m','caeoj',*command],cwd=out,capture_output=True,text=True,encoding='utf-8',errors='replace')
            (out/f"C{c['index']:02}-{command[0]}.json").write_text(p.stdout,encoding='utf-8')
            result.append(dict(command=command[0],returncode=p.returncode))
            if p.returncode:raise RuntimeError(p.stderr+p.stdout)
        if hashlib.sha256(ref.read_bytes()).hexdigest()!=digest:raise ValueError('Reference changed during consumption audit')
        rows.append(dict(index=c['index'],status='passed',reference_sha256=digest,commands=result))
    report=dict(normal_install='runs/install-check/cfdcodebench-20261019/summary.json',purpose='real input/reference/grading consumption only; not numerical certification or benchmark',rows=rows)
    (out/'summary.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(dict(passed=sum(r['status']=='passed' for r in rows),reference_pending=sum(r['status']=='reference_pending' for r in rows))))
if __name__=='__main__':main()
