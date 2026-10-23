"""Serialize declarations and adapt genuine Meep observations without solving or correcting."""
import argparse,json,subprocess
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem,write_result
DRIVER='/opt/meep-repair-build/bin/cylindrical-driver'
def serialize(problem):
 p={n:r['value'] for n,r in problem.manifest['physics']['parameters'].items()};values=[p[n] for n in ['radius','half_height','radial_pml','axial_pml','resolution','mode','source_amplitude']]+[50,10,80]
 return ' '.join(format(float(x),'.17g') for x in values)+'\n'
def adapt(raw):
 r=json.loads(raw);return {'spectral_flux':np.asarray(r['flux'],dtype='float64').reshape(1,3,1),'observed_dft':np.asarray(r['fields'],dtype='float64').reshape(1,1,12),'time_step':np.asarray([[[r['dt']]]],dtype='float64'),'window_end':np.asarray([[[r['time']]]],dtype='float64')}
def run(input_path,output_path):
 problem=load_problem(input_path);p=subprocess.run([DRIVER],input=serialize(problem),text=True,capture_output=True)
 if p.returncode:raise RuntimeError(f'Actual Meep driver failed {p.returncode}: {p.stdout}\n{p.stderr}')
 write_result(output_path,problem,adapt(p.stdout))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.input,a.output)
