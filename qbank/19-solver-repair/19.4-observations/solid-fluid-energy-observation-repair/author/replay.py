"""Replay the actual pinned native MOOSE observer; convert only genuine CSV values."""
from pathlib import Path
import argparse,csv,hashlib,importlib.util,json,subprocess,sys,time
import numpy as np
from caeoj.sdk import load_problem,write_result
ROOT=Path(__file__).resolve().parents[5];TASK=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('native',TASK/'public/run_case.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
DOCKER='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--image',default='caeoj-moose22074-prototype:upstream2022');parser.add_argument('--mode',default='reference');args=parser.parse_args()
 image=json.loads(subprocess.check_output([DOCKER,'image','inspect',args.image]))[0]['Id'];records=[]
 for case in sorted((TASK/'cases').iterdir()):
  if not (case/'problem.json').exists():continue
  problem=load_problem(case/'problem.json');p={k:v['value'] for k,v in problem.manifest['physics']['parameters'].items()};p.update(native.model_settings(problem.manifest['physics']['model']))
  d=ROOT/'runs/authoring/repair-22/moose-22074-native-replay'/args.mode/case.name;d.mkdir(parents=True,exist_ok=True);text=native.prepare(p,problem.arrays,d);start=time.monotonic()
  r=subprocess.run([DOCKER,'run','--rm','--network','none','--cpus','2','--memory','4g','--user','1000:1000','--mount',f'type=bind,source={d},target=/job','--workdir','/job','--entrypoint','/bin/bash',image,'-lc',native.ENV+'exec '+native.APP+' -i case.i'],capture_output=True,text=True,timeout=120)
  (d/'stdout.log').write_text(r.stdout,newline='\n');(d/'stderr.log').write_text(r.stderr,newline='\n');item={'case':case.name,'returncode':r.returncode,'elapsed_seconds':time.monotonic()-start,'native_input_sha256':hashlib.sha256(text.encode()).hexdigest()}
  if not r.returncode:
   values=native.extract(d,p,problem.arrays['times']);out=TASK/'reference'/case.name/'reference.h5';out.parent.mkdir(parents=True,exist_ok=True)
   if args.mode=='reference':write_result(out,problem,values);item['result_sha256']=hashlib.sha256(out.read_bytes()).hexdigest()
   item['observations']={k:v.ravel().tolist() for k,v in values.items()}
  records.append(item);print(case.name,r.returncode,round(item['elapsed_seconds'],3),flush=True)
 report={'native_image_id':image,'mode':args.mode,'passed':sum(x['returncode']==0 for x in records),'total':len(records),'cases':records};out=TASK/'author/data-evidence'/f'{args.mode}-replay.json';out.parent.mkdir(exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n',newline='\n')
 if args.mode=='reference' and report['passed']!=report['total']:raise RuntimeError('Actual native reference failures; inspect raw case logs')
if __name__=='__main__':main()
