"""Preserve identities, invoke the actual ownership API and serialize its results."""
import argparse,json,subprocess
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem,write_result
from caeoj.validation import read_mesh,resolve_file

def serialize(problem):
    m=problem.manifest;a=problem.arrays;d=m['spatial_dimension']
    mesh=read_mesh(resolve_file(problem.path.parent,'source.msh','.msh'),geometry=True)
    ids=list(map(int,a['node_ids']));rows={tag:i for i,tag in enumerate(ids)}
    cells=[(int(tag),[rows[int(n)] for n in nodes]) for tag,(kind,nodes) in sorted(mesh['connectivity'].items()) if kind==(2 if d==2 else 4)]
    parameters=m['physics']['parameters']
    return json.dumps({'dimension':d,'mode':parameters['mode']['value'],'padding':parameters['padding']['value'],
      'vertices':[mesh['node_coordinates'][tag][:d].tolist() for tag in ids],
      'cell_ids':[tag for tag,_ in cells],'cells':[nodes for _,nodes in cells],
      'queries':a['probe_coordinates'].tolist()},separators=(',',':'),allow_nan=False)

def adapt(text):
    rows=json.loads(text)
    return {name:np.asarray([[[r[name]] for r in rows]],dtype='float64') for name in ['owned','cell_id','distance']}

def run(input_path,output_path):
    problem=load_problem(input_path)
    process=subprocess.run(['/opt/dolfinx-repair-build/bin/ownership_driver'],input=serialize(problem),capture_output=True,text=True)
    if process.returncode:raise RuntimeError(f'Trusted ownership driver failed {process.returncode}: {process.stderr}')
    write_result(output_path,problem,adapt(process.stdout))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();run(args.input,args.output)
