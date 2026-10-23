"""Convert public beam arrays, call the genuine C++ element, and normalize units."""
import argparse
from pathlib import Path
import subprocess
import tempfile
import numpy as np
from caeoj.sdk import load_problem,write_result
MATERIAL=('young_modulus','poisson_ratio','area','inertia_y','inertia_z','torsion_constant','shear_area_y','shear_area_z','density')


def serialize(problem):
    a=problem.arrays;n=len(a['beam_ids']);lines=[str(n)]
    for i in range(n):
        values=[*a['endpoints'][0,i],*a['section_axis'][0,i],*[a[name][0,i,0] for name in MATERIAL],*a['body_acceleration'][0,i]]
        lines.append(' '.join(format(float(v),'.17g') for v in values))
    return '\n'.join(lines)+'\n'


def adapt(problem,raw):
    a=problem.arrays;n=len(a['beam_ids']);rows=raw.splitlines()
    if len(rows)!=4*n:raise ValueError('Unexpected trusted driver result')
    fields={name:[] for name in ('lhs_combined','rhs_combined','lhs_separate','rhs_separate','tip_displacement')}
    for i in range(n):
        L=np.linalg.norm(a['endpoints'][0,i,3:]-a['endpoints'][0,i,:3])
        inv=np.tile([1.,1.,1.,1/L,1/L,1/L],2)
        K=np.fromstring(rows[4*i],sep=' ').reshape(12,12)*inv[:,None]*inv[None,:]
        f=np.fromstring(rows[4*i+1],sep=' ')*inv
        Ks=np.fromstring(rows[4*i+2],sep=' ').reshape(12,12)*inv[:,None]*inv[None,:]
        fs=np.fromstring(rows[4*i+3],sep=' ')*inv
        for name,value in [('lhs_combined',K.ravel()),('rhs_combined',f),('lhs_separate',Ks.ravel()),('rhs_separate',fs),('tip_displacement',np.linalg.solve(K[6:,6:],f[6:]+a['tip_load'][0,i]))]:fields[name].append(value)
    return {name:np.asarray(value,dtype='float64')[None] for name,value in fields.items()}


def run(input_path,output_path):
    problem=load_problem(input_path)
    with tempfile.TemporaryDirectory() as temp:
        inp=Path(temp)/'input.txt';out=Path(temp)/'output.txt';inp.write_text(serialize(problem))
        process=subprocess.run(['/opt/beam-build/beam_driver',str(inp),str(out)],capture_output=True,text=True)
        if process.returncode:raise RuntimeError(f'Trusted beam driver failed {process.returncode}: {process.stderr}')
        fields=adapt(problem,out.read_text())
    write_result(output_path,problem,fields)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();run(args.input,args.output)
