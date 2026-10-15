"""Convert entire official samples to Gmsh/JSON/HDF5 without recomputing answers."""
from caeoj.storage import write_hdf5
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import gmsh
import h5py
import numpy as np

from caeoj.grading import grade_files
from caeoj.sdk import load_problem, write_result
from caeoj.validation import GMSH_LOCK, write_json
from download import DEFAULT, TASK, download, verify


def mesh(path):
    with GMSH_LOCK:
        gmsh.initialize([], readConfigFiles=False)
        try:
            gmsh.option.setNumber('General.Terminal',0)
            gmsh.model.add('periodic-interval')
            left=gmsh.model.geo.addPoint(0,0,0)
            right=gmsh.model.geo.addPoint(1,0,0)
            line=gmsh.model.geo.addLine(left,right)
            gmsh.model.geo.synchronize()
            gmsh.model.mesh.setTransfiniteCurve(line,1025)
            gmsh.model.addPhysicalGroup(1,[line],1,'cells')
            gmsh.model.mesh.generate(1)
            gmsh.option.setNumber('Mesh.MshFileVersion',4.1)
            gmsh.option.setNumber('Mesh.SaveAll',1)
            gmsh.write(str(path))
            tags,coordinates,_=gmsh.model.mesh.getNodes()
            coords=dict(zip(map(int,tags),coordinates.reshape(-1,3)[:,0]))
            types,blocks,connectivity=gmsh.model.mesh.getElements(1)
            centers={}
            for kind,ids,nodes in zip(types,blocks,connectivity):
                if kind!=1: raise ValueError('Expected first-order line cells')
                for tag,pair in zip(ids,nodes.reshape(-1,2)):
                    centers[int(tag)]=sum(coords[int(node)] for node in pair)/2
            ids=np.array(sorted(centers),dtype=np.int64)
            return ids,np.array([centers[int(tag)] for tag in ids])
        finally: gmsh.finalize()


def field(array,axis):
    return {'array':array,'quantity':'state','location':'cells','time_axis':axis,
        'dtype':'float64','kind':'scalar','component_shape':[1],
        'components':['value'],'unit':'1','value_kind':'average'}


def generate(source=DEFAULT,destination=TASK):
    source=verify(source) if Path(source).exists() else download(source)
    destination=Path(destination)
    provenance=json.loads((TASK/'author/SOURCE.json').read_text())
    with h5py.File(source,'r') as stream:
        x=stream['x-coordinate'][...].astype('float64')
        all_times=stream['t-coordinate'][...].astype('float64')
        # Historical generator allocates one more coordinate than actual frames.
        # The unused trailing 2.01 coordinate remains in the raw source archive.
        if len(all_times)!=202 or abs(all_times[-1]-2.01)>1e-6: raise ValueError('Unknown time-coordinate mismatch')
        times=all_times[:201]
        if abs(times[-1]-2)>1e-6: raise ValueError('Missing final official frame')
        for index in range(12):
            name=f'{index+1:02d}-official-{index:04d}'
            directory=destination/'cases'/name
            directory.mkdir(parents=True,exist_ok=True)
            ids,centers=mesh(directory/'mesh.msh')
            mapping=np.argmin(abs(centers[:,None]-x),axis=1)
            if len(set(map(int,mapping)))!=1024 or np.max(abs(x[mapping]-centers))>1e-8:
                raise ValueError('Gmsh and official cell centers do not match')
            data=stream['tensor'][index,...].astype('float64')
            manifest={'task':TASK.name,'spatial_dimension':1,'data_file':'input.h5',
                'geometries':{},'meshes':{'main':{'file':'mesh.msh'}},
                'locations':{'cells':{'kind':'mesh','mesh':'main','entity':'element',
                    'dimension':1,'ids':'cell_ids','physical_group':{'dimension':1,'tag':1}}},
                'time_axes':{'initial':'initial_times','output':'times'},
                'fields':{'initial_state':field('initial_values','initial')},
                'outputs':{'state':field('state','output')},
                'physics':{'model':'advection_1d','parameters':{'velocity':{'value':0.8,'unit':'m/s'}}},
                'conditions':[{'role':'initial','variable':'state','location':'cells','operator':'assign',
                    'data':{'value':{'field':'initial_state'}}},
                    {'role':'boundary','variable':'state','location':'cells','operator':'periodic',
                    'data':{'period':{'value':1.0,'unit':'m'}}}]}
            write_hdf5(directory / 'input.h5', {'cell_ids': ids, 'times': times, 'initial_times': np.array([times[0]]), 'initial_values': data[0, mapping][None, :, None]}, compression="gzip")
            write_json(directory/'problem.json',manifest)
            p=load_problem(directory/'problem.json')
            ref=destination/'reference'/name
            write_result(ref/'reference.h5',p,{'state':data[:,mapping,None]})
            write_json(ref/'certificate.json',{'source_sample_index':index,
                'source_shape':[201,1024],'source_dtype':'float32',
                'source_sha256':provenance['samples'][index]['sha256'],
                'source_index_by_cell_row':mapping.tolist(),
                'reference_kind':'unmodified complete official trajectory; exact float64 cast'})
            print(name,flush=True)
    config=json.loads((TASK/'judge-config.json').read_text())
    for number,case in enumerate(sorted((destination/'cases').iterdir())[:2],1):
        sample=destination/'samples'/f'{number:02d}'
        shutil.copytree(case,sample/'input',dirs_exist_ok=True)
        output=sample/'output/result.h5';output.parent.mkdir(parents=True,exist_ok=True)
        reference=destination/'reference'/case.name/'reference.h5'
        shutil.copyfile(reference,output)
        result=grade_files(sample/'input/problem.json',output,reference,
            atol=config['atol'],rtol=config['rtol'])
        if result['score']!=1:raise ValueError('Official public sample failed grading')
        write_json(sample/'verification.json',result)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,default=DEFAULT)
    parser.add_argument('--output',type=Path,default=TASK)
    args=parser.parse_args();generate(args.source,args.output)
