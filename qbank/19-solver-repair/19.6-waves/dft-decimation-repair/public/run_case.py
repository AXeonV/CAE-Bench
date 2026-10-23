"""Serialize declarations, call real Meep, and write its actual observations."""
import argparse,json,subprocess
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem,write_result
DRIVER='/opt/meep-repair-build/bin/dft-driver'
def serialize(problem):
 p={n:r['value'] for n,r in problem.manifest['physics']['parameters'].items()};freq=problem.arrays['frequency'][0,:,0];point=float(problem.arrays['probe_coordinates'][0,0])
 values=[p['length'],p['resolution'],p['pml_width'],p['source_frequency'],1/p['envelope_width'],p['source_amplitude'],p['cutoff'],p['after_sources'],p['chi2'],p['chi3'],p['nonlinear_lo'],p['nonlinear_hi'],p['num_chunks'],p['decimation'],point,len(freq),*freq]
 return ' '.join(format(float(x),'.17g') for x in values)+'\n'
def adapt(raw):
 r=json.loads(raw);nf=len(r['spectrum']);return {'observed_dft':np.asarray([r['spectrum']],dtype='float64'),'sampling_stride':np.full((1,nf,1),r['stride'],dtype='float64'),'time_step':np.full((1,nf,1),r['dt'],dtype='float64'),'window_end':np.full((1,nf,1),r['final_time'],dtype='float64')}
def run(input_path,output_path):
 problem=load_problem(input_path);p=subprocess.run([DRIVER],input=serialize(problem),text=True,capture_output=True)
 if p.returncode:raise RuntimeError(f'Actual Meep driver failed {p.returncode}: {p.stdout}\n{p.stderr}')
 write_result(output_path,problem,adapt(p.stdout))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.input,a.output)
