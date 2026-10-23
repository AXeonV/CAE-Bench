"""Serialize material programs, call the real C++ API driver, and store its observations."""
import argparse,subprocess,tempfile
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem,write_result

def programs(problem):
 a=problem.arrays;result=[]
 for i in range(len(a['program_ids'])):
  value=lambda k:float(a[k][0,i,0])
  n=lambda k:int(value(k))
  positive=list(zip(a['positive_stress'][0,i,:n('positive_count')],a['positive_strain'][0,i,:n('positive_count')]))
  negative=list(zip(a['negative_stress'][0,i,:n('negative_count')],a['negative_strain'][0,i,:n('negative_count')]))
  result.append({'kind':n('material_kind'),'positive':positive,'negative':negative,'pinch':a['pinching'][0,i], 'beta':value('beta'),
   'history':a['history'][0,i,:n('history_count')],'probes':a['trials'][0,i,:n('trial_count')],'delta':value('return_delta'),
   'continuation':a['continuation'][0,i,:n('continuation_count')],'rollback_probe':value('rollback_probe')})
 return result

def serialize(items):
 lines=[str(len(items))]
 for p in items:
  lines.append(' '.join(map(str,[p['kind'],len(p['positive']),len(p['negative']),*p['pinch'],p['beta']])))
  for side in ('positive','negative'):lines.append(' '.join(format(float(x),'.17g') for pair in p[side] for x in pair))
  for key in ('history','probes'):lines.append(' '.join([str(len(p[key])),*[format(float(x),'.17g') for x in p[key]]]))
  lines.append(format(p['delta'],'.17g'))
  lines.append(' '.join([str(len(p['continuation'])),*[format(float(x),'.17g') for x in p['continuation']]]))
  lines.append(format(p['rollback_probe'],'.17g'))
 return '\n'.join(lines)+'\n'

def run(input_path,output_path):
 problem=load_problem(input_path);items=programs(problem)
 with tempfile.TemporaryDirectory() as tmp:
  inp=Path(tmp)/'input.txt';out=Path(tmp)/'output.txt';inp.write_text(serialize(items))
  process=subprocess.run(['/opt/material-build/material_driver',str(inp),str(out)],capture_output=True,text=True)
  if process.returncode:raise RuntimeError(f'Trusted material driver failed {process.returncode}: {process.stderr}')
  raw=np.loadtxt(out).reshape(len(items),6,4)
 write_result(output_path,problem,{name:raw[:,:,j][None] for j,name in enumerate(('strain','stress','tangent','work_density'))})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();run(args.input,args.output)
