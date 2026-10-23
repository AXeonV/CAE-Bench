"""Neutral protocol adapter for the fixed installed PyBaMM driver."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
from caeoj.sdk import load_problem,write_result


def serialize(problem):
    request={name:entry['value'] for name,entry in problem.manifest['physics']['parameters'].items()}
    states=[]
    for index in range(len(problem.arrays['state_ids'])):
        state={}
        for name in problem.manifest['fields']:
            array=problem.arrays[name][0,index]
            state[name]=array[0].item() if len(array)==1 else array.tolist()
        states.append(state)
    request['states']=states
    return json.dumps(request)


def run(input_path,output_path):
    problem=load_problem(input_path)
    process=subprocess.run([sys.executable,'/opt/repair-driver/driver.py'],input=serialize(problem),text=True,capture_output=True)
    if process.returncode:
        sys.stderr.write(process.stderr)
        raise RuntimeError(f'Trusted library driver exited {process.returncode}')
    fields={name:np.asarray(value,dtype='float64')[None,:,:] for name,value in json.loads(process.stdout).items()}
    write_result(output_path,problem,fields)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();run(args.input,args.output)
