"""Transport only; all numerical results come from the real library driver."""
import argparse,json,subprocess
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem,write_result


def serialize(problem):
    from caeoj.validation import read_mesh,resolve_file
    a=problem.arrays;p={n:v['value'] for n,v in problem.manifest['physics']['parameters'].items()}
    p['targets']=a['target_coordinates'].tolist()
    if p['operation']==0:
        p.update(sources=a['source_coordinates'].tolist(),strength=a['strength'][0].tolist())
    else:
        mesh=read_mesh(resolve_file(problem.path.parent,'surface.msh','.msh'),geometry=True)
        ids=a['node_ids'].tolist();indices={int(n):i for i,n in enumerate(ids)}
        p.update(vertices=np.asarray([mesh['node_coordinates'][int(n)] for n in ids],dtype='float64').tolist(),triangles=[[indices[n] for n in row[1]] for _,row in sorted(mesh['connectivity'].items())],density=a['density'][0].tolist())
    return json.dumps(p,allow_nan=False)


def adapt(raw):
    return {n:np.asarray(v,dtype='float64')[None,:,:] for n,v in json.loads(raw).items()}


def run(input_path,output_path):
    problem=load_problem(input_path)
    process=subprocess.run(['/opt/bempp-env/bin/python','/opt/repair-driver/driver.py'],input=serialize(problem),text=True,capture_output=True)
    if process.returncode:raise RuntimeError(f'Actual Bempp driver failed {process.returncode}: {process.stderr}')
    write_result(output_path,problem,adapt(process.stdout))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.input,a.output)
