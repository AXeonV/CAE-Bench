"""Translate mesh identities and arrays, call the genuine Index, and write its results."""
import argparse
import json
from pathlib import Path
import subprocess
import numpy as np
from caeoj.sdk import load_problem,write_result
from caeoj.validation import read_mesh,resolve_file


def serialize(problem):
    m=problem.manifest;a=problem.arrays;d=m['spatial_dimension']
    mesh=read_mesh(resolve_file(problem.path.parent,m['meshes']['source']['file'],'.msh'),geometry=True)
    ids=list(map(int,a['node_ids']));rows={tag:i for i,tag in enumerate(ids)}
    primitives={1:[],2:[],4:[]}
    for tag,(kind,nodes) in sorted(mesh['connectivity'].items()):
        if kind in primitives:primitives[kind].append([rows[int(node)] for node in nodes])
    return json.dumps({'dimension':d,'mode':'nearest' if m['physics']['parameters']['mode']['value']==0 else 'cell',
       'vertices':[mesh['node_coordinates'][tag][:d].tolist() for tag in ids],
       'edges':primitives[1],'triangles':primitives[2],'tetrahedra':primitives[4],
       'queries':a['probe_coordinates'].tolist(),'values':a['nodal_values'][0].tolist()},separators=(',',':'),allow_nan=False)


def adapt(raw):
    rows=json.loads(raw)
    return {name:np.asarray([[r[key] if key!='distance' else [r[key]] for r in rows]],dtype='float64')
            for name,key in [('projection','point'),('distance','distance'),('weights','weights'),('mapped_values','value')]}


def run(input_path,output_path):
    problem=load_problem(input_path)
    process=subprocess.run(['/opt/precice-repair-build/bin/projection-driver'],input=serialize(problem),capture_output=True,text=True)
    if process.returncode:raise RuntimeError(f'Trusted projection driver failed {process.returncode}: {process.stderr}')
    write_result(output_path,problem,adapt(process.stdout))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();run(args.input,args.output)
