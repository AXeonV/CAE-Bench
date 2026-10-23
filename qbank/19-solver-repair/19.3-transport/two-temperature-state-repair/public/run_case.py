"""Neutral JSON/HDF5 adapter for the installed Cantera driver."""
import argparse,json,subprocess,sys
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem,write_result

def serialize(problem):
 a=problem.arrays;n=len(a['state_ids']);tokens=[str(n)]
 for i in range(n):
  for k in ['mode','temperature','electron_temperature','constraint_value','final_electron_temperature','mole_fractions']:
   tokens.extend(str(v) for v in a[k][0,i])
 return ' '.join(tokens)+'\n'
def run(input_path,output_path,driver='/opt/cantera-source/build/bin/plasma-driver'):
 p=load_problem(input_path)
 r=subprocess.run([driver],input=serialize(p),text=True,capture_output=True)
 if r.returncode:
  sys.stderr.write(r.stderr);raise RuntimeError(f'Cantera driver exited {r.returncode}')
 y=np.asarray(json.loads(r.stdout),dtype='float64')
 write_result(output_path,p,{'pressure':y[None,:,0:1],'electron_pressure':y[None,:,1:2],
 'density':y[None,:,2:3],'concentrations':y[None,:,3:6]})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--input',type=Path,required=True);a.add_argument('--output',type=Path,required=True)
 a.add_argument('--driver',default='/opt/cantera-source/build/bin/plasma-driver');v=a.parse_args();run(v.input,v.output,v.driver)
