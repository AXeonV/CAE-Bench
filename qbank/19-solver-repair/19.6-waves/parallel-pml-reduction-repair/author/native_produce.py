"""Run the immutable genuine solver; preserve raw input, logs and seismograms."""
import argparse,importlib.util,json,time,hashlib
from pathlib import Path
from caeoj.sdk import load_problem,write_result
TASK=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('wave_adapter',TASK/'public/run_case.py');adapter=importlib.util.module_from_spec(s);s.loader.exec_module(adapter)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--dataset',type=Path,required=True);p.add_argument('--build',type=Path,default=Path('/opt/specfem/bin').parent)
    p.add_argument('--mode',choices=['reference','original'],required=True);a=p.parse_args();report=[]
    for path in sorted((a.dataset/'cases').glob('*/problem.json')):
        problem=load_problem(path);dest=a.dataset/'replay'/a.mode/path.parent.name;dest.mkdir(parents=True,exist_ok=True)
        adapter.prepare(problem,dest);start=time.monotonic();row={'case':path.parent.name,'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        try:
            result=adapter.execute(problem,dest,a.build,native_timeout=90 if a.mode=='original' else None)
            target=a.dataset/'reference'/path.parent.name if a.mode=='reference' else dest;target.mkdir(parents=True,exist_ok=True)
            output=target/('reference.h5' if a.mode=='reference' else 'result.h5');write_result(output,problem,{'wave_response':result})
            row.update(status='completed',output_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),max_abs=float(abs(result).max()))
        except Exception as e:
            row.update(status='failed',error=str(e));(dest/'failure.txt').write_text(str(e))
            if a.mode=='reference':raise
        row['elapsed_seconds']=time.monotonic()-start;report.append(row)
        (a.dataset/(a.mode+'-replay.json')).write_text(json.dumps(report,indent=2));print(row['case'],row['status'],round(row['elapsed_seconds'],3),flush=True)
