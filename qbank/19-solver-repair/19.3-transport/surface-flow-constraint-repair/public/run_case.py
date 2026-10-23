"""Neutral input/output adapter; the installed Cantera driver owns every prediction."""
import argparse,json,subprocess,sys
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem,write_result
FIELDS=['species_order', 'temperature', 'pressure', 'inlet_speed', 'surface_area_to_volume', 'site_density', 'adsorption_rate', 'desorption_rate', 'conversion_rate', 'distance', 'inlet_mole_fractions']
SLICES={'mass_fractions': [0, 3], 'coverages': [3, 5], 'pressure': [5, 6], 'density': [6, 7], 'speed': [7, 8]}
def serialize(p):
 a=p.arrays;tokens=[str(len(a['state_ids']))]
 for i in range(len(a['state_ids'])):
  for k in FIELDS:tokens.extend(str(v) for v in a[k][0,i])
 return ' '.join(tokens)+'\n'
def run(input_path,output_path,driver='/opt/cantera1655-build/bin/flow-driver'):
 p=load_problem(input_path);r=subprocess.run([driver],input=serialize(p),text=True,capture_output=True)
 if r.returncode:sys.stderr.write(r.stderr);raise RuntimeError(f'Cantera driver exited {r.returncode}')
 y=np.asarray(json.loads(r.stdout),dtype='float64');write_result(output_path,p,{k:y[None,:,a:b] for k,(a,b) in SLICES.items()})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--driver',default='/opt/cantera1655-build/bin/flow-driver');a=p.parse_args();run(a.input,a.output,a.driver)
