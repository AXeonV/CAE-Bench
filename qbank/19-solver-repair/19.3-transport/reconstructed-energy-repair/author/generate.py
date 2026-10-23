"""Reproduce attributed independent edge-state and fixed-grid CFD families."""
from pathlib import Path
import importlib.util,json
import numpy as np
from caeoj.storage import write_hdf5
from caeoj.validation import write_json
Q=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('contract',Q/'extension/caeoj_task_ext/reconstruction.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
def save(name,d,parameters,arrays,locations):
    arrays['times']=np.array([0.]);fields,out=c.definitions(d,parameters['operation'])
    meta={'task':c.TASK,'spatial_dimension':d,'data_file':'input.h5','geometries':{},'meshes':{},'conditions':[],
          'physics':{'model':c.MODEL,'parameters':{k:{'value':v,'unit':'J/(kg*K)' if k=='gas_constant' else '1'} for k,v in parameters.items()}},
          'locations':locations,'time_axes':{'instant':'times'},'fields':c.specs(fields,True),'outputs':c.specs(out)}
    dest=Q/'cases'/name;dest.mkdir(parents=True,exist_ok=True);write_hdf5(dest/'input.h5',arrays);write_json(dest/'problem.json',meta)
def defaults():return {'operation':0,'gamma':1.4,'gas_constant':287.,'kappa':1/3,'relax':.8,'muscl':1,'limiter':0,'cfl':400.,'iterations':2000}
def generate():
    cases=json.loads((Q/'author/data-evidence/kernel-cases.json').read_text());origins=[]
    for i,x in enumerate(cases,1):
        d=x['dimension'];base=np.array(x['base']);grad=np.array(x['gradient']);p=defaults()
        for a,b in [('gamma','gamma'),('gas_constant','R'),('kappa','kappa'),('relax','relax'),('muscl','muscl'),('limiter','limiter')]:p[a]=x[b]
        arrays={'edge_ids':np.array([0],dtype='int64'),'end_ids':np.arange(2,dtype='int64'),
                'temperature':base[None,:,0:1],'velocity':base[None,:,1:d+1],'pressure':base[None,:,d+1:d+2],
                'density':base[None,:,d+2:d+3],'enthalpy':base[None,:,d+3:d+4],
                'gradient_temperature':grad[None,:,0,:],'gradient_velocity':grad[:,1:d+1,:].reshape(1,2,d*d),
                'gradient_pressure':grad[None,:,d+1,:],'limiters':np.array(x['limits'])[None],
                'displacement':np.array(x['dx'])[None,None,:]}
        name=f'{i:02d}-{x["kind"]}';save(name,d,p,arrays,{'edges':{'kind':'entities','ids':'edge_ids'},'ends':{'kind':'entities','ids':'end_ids'}})
        origins.append({'case':name,'origin':'Author-created intermediate reconstruction states motivated by SU2 issue2602/PR2608; true CConfig/CNSVariable and upstream templates.','family':x['kind']})
    for i,cfl,it in [(8,400.,2000),(9,300.,2500)]:
        p=defaults();p.update(operation=1,cfl=cfl,iterations=it)
        lines=(Q/'public/flatplate.su2').read_text().splitlines();j=next(k for k,line in enumerate(lines) if line.startswith('NPOIN'))
        coords=np.array([[float(x) for x in line.split()[:2]] for line in lines[j+1:j+13901]])
        j=next(k for k,line in enumerate(lines) if line.strip()=='MARKER_TAG= wall');n=int(lines[j+1].split('=')[1]);wallids=np.unique([int(x) for line in lines[j+2:j+2+n] for x in line.split()[1:3]])
        wallids=wallids[np.argsort(coords[wallids,0])]
        arrays={'node_ids':np.arange(13900,dtype='int64'),'wall_ids':np.arange(100,dtype='int64'),'diagnostic_ids':np.array([0],dtype='int64'),'node_coordinates':coords,'wall_coordinates':coords[wallids]}
        locations={'nodes':{'kind':'points','ids':'node_ids','coordinates':'node_coordinates'},'wall':{'kind':'points','ids':'wall_ids','coordinates':'wall_coordinates'},'diagnostic':{'kind':'entities','ids':'diagnostic_ids'}}
        name=f'{i:02d}-flatplate-cfl{int(cfl)}';save(name,2,p,arrays,locations)
        origins.append({'case':name,'origin':'Adapted fixed SU2 TestCases wallfunction flatplate, mesh pinned at TestCases790c80ec5b543487b5f8ecf8bb0f0e4d2cc67f3f; specified-discretization stability regression.','family':'full-cfd'})
    write_json(Q/'author/data-evidence/cases.json',origins)
if __name__=='__main__':generate()
