"""One finite frozen case using unmodified Thetis nonlinear shallow water."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import traceback
import h5py
import numpy as np
from elmer_flow_mesh import generate
from native_lowmach import sample
from native_closed_cavity import SOCKET,save,digest
from native_pyclaw_closed_flat import descriptor
from polytropic_reference import gmsh
from stage_native_thetis import IMAGE,COMMIT
from titan_resources import reservation
CASE='ch02-2-9-2-08-friction_decay'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int,default=1);a=ap.parse_args();r=a.root
    stage=r/'maintenance/thetis-native-stage';proof=json.loads((stage/'stage.json').read_text());assert proof['status']=='native_solver_imported_pending_case_adapter' and proof['commit']==COMMIT
    for name,sha in proof['distribution_sha256'].items():assert digest(stage/'wheels'/name)==sha
    p=next(a.snapshot.glob('qbank/02-fluid-mechanics/*/fully-wet-transient/author/chapter02-ten-20261020/design.json'));freeze=json.loads((a.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text());assert digest(p)==freeze['designs'][p.relative_to(a.snapshot).as_posix()];d=json.loads(p.read_text());e=next(e for e in d['proposed_cases'] if e['design_id']==CASE);s=e['detailed_spec']
    assert not s['sources'] and all(b['operator']=='water_wall' for b in s['boundaries'])
    j=r/'cases'/CASE;assert not j.exists(),'Inspect existing native attempt; no automatic repeat';j.mkdir();save(j/'design.json',{**e,'task':d['task'],'model':d['model']});state={'design_id':CASE,'status':'queued'};save(j/'status.json',state);name='ch02thetis-friction-'+str(time.time_ns())[-9:]
    try:
        with reservation(r,name):
            m=generate(s);x,c,b=m['x'],m['c'],m['b'];n=len(x)
            h=sample(s['initial']['depth']['expression'],x,0,s);u=sample(s['initial']['velocity']['expression'],x,0,s);bed=sample(s['domain_conditions']['bed']['expression'],x,0,s);assert np.min(h)>0 and np.all(bed==0)
            keep=np.ones(n,bool);keep[np.unique(b)]=False
            for _ in range(2):keep[np.unique(c[np.any(~keep[c],axis=1)])]=False
            ids=np.flatnonzero(keep);assert len(ids)>0
            np.savez(j/'native-input.npz',x=x,c=c,b=b,h=h,u=u,observed=ids,times=s['output_times_s'],end=s['time_interval_s'][1],gravity=s['parameters']['gravity']['value'],density=s['parameters']['density']['value'],drag=s['parameters']['drag_rate']['value'])
            # Same coordinates, connectivity and IDs in the native MSH2 reader.
            lines=['$MeshFormat','2.2 0 8','$EndMeshFormat','$Nodes',str(n)]+[f'{i+1} {v[0]:.17g} {v[1]:.17g} 0' for i,v in enumerate(x)]+['$EndNodes','$Elements',str(len(c)+len(b))]
            lines += [f'{i+1} 2 2 1 1 '+' '.join(str(k+1) for k in v) for i,v in enumerate(c)]
            lines += [f'{len(c)+i+1} 1 2 2 2 '+' '.join(str(k+1) for k in v) for i,v in enumerate(b)]
            (j/'native-mesh.msh').write_text('\n'.join(lines+['$EndElements'])+'\n')
            inp=j/'input';inp.mkdir();gmsh(inp/'mesh.msh',x,c,b,2)
            arrays={'nodes':np.arange(1,n+1,dtype=np.int64),'observed':ids.astype(np.int64)+1,'cells':np.arange(1,len(c)+1,dtype=np.int64),'wall':np.arange(1,len(b)+1,dtype=np.int64)+len(c),'integral':np.array([1],dtype=np.int64),'initial':np.array([0.]),'constant':np.array([0.]),'requested':np.array(s['output_times_s']),'bed':bed[None,:,None],'depth0':h[None,:,None],'velocity0':u[None]}
            locations={'domain':{'kind':'mesh','mesh':'main','entity':'node','ids':'nodes'},'observed':{'kind':'mesh','mesh':'main','entity':'node','ids':'observed'},'area':{'kind':'mesh','mesh':'main','entity':'element','dimension':2,'ids':'cells'},'wall':{'kind':'mesh','mesh':'main','entity':'element','dimension':1,'ids':'wall'},'volume':{'kind':'aggregate','source':'area','ids':'integral','operation':'sum'}}
            fields={};conditions=[]
            for key,quantity,role,op,axis,unit,dim in [('bed','bed','material','geometry','constant','m',1),('depth0','depth','initial','assign','initial','m',1),('velocity0','velocity','initial','assign','initial','m/s',2)]:
                fields[key]=descriptor(quantity,'domain',axis,unit,dim,input=True);fields[key]['array']=key;conditions.append({'role':role,'variable':quantity,'operator':op,'location':'domain','data':{'value':{'field':key}}})
            conditions.append({'role':'boundary','variable':'water','operator':'water_wall','location':'wall','data':{'mode':{'option':'impermeable'}}})
            outputs={v:descriptor(v,'volume' if v=='water_volume' else 'observed','requested',unit,dim,integral=v=='water_volume') for v,unit,dim in [('depth','m',1),('velocity','m/s',2),('water_flux','m2/s',2),('water_volume','m3',1)]}
            save(inp/'problem.json',{'task':d['task'],'physics':{'model':d['model'],'parameters':s['parameters']},'spatial_dimension':2,'data_file':'input.h5','geometries':{},'meshes':{'main':{'file':'mesh.msh'}},'locations':locations,'time_axes':{'initial':'initial','constant':'constant','requested':'requested'},'fields':fields,'conditions':conditions,'outputs':outputs})
            with h5py.File(inp/'input.h5','w') as f:
                for k,v in arrays.items():f[k]=v
            runtime=Path(__file__).with_name('thetis_friction_runtime.py');shutil.copy2(runtime,j/runtime.name)
            cmd=['docker','--host',SOCKET,'run','--name',name,'--network','none','--cpus','1','--memory','2g','--user',f'{os.getuid()}:{os.getgid()}','-e','HOME=/tmp','-e','OMP_NUM_THREADS=1','-e','OPENBLAS_NUM_THREADS=1','-e','XDG_CACHE_HOME=/work/cache','-e','PYTHONPATH=/vendor','-v',f'{j}:/work','-v',f'{stage}/vendor:/vendor:ro',IMAGE,'python3','/work/'+runtime.name]
            save(j/'execution.json',{'command':cmd,'image':IMAGE,'thetis_commit':COMMIT,'producer_sha256':digest(Path(__file__)),'runtime_sha256':digest(runtime),'distribution_sha256':proof['distribution_sha256'],'scope':'Native Thetis nonlinear all-wet shallow water plus native LinearDragTerm, no custom PDE/source; constant datum bathymetry1, physical depth1+eta, zero physical bed. Native closed slip walls.','numerical_validation':False})
            state.update(status='running',container=name);save(j/'status.json',state)
            with (j/'solver.log').open('w') as log:cp=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
            assert cp.returncode==0,f'native exit{cp.returncode}'
            raw=np.load(j/'native-output.npz');assert np.allclose(raw['times'],s['output_times_s'],atol=1e-9,rtol=0)
            ref=j/'reference';ref.mkdir()
            with h5py.File(ref/'reference.h5','w') as f:
                for k in ['observed','requested','integral']:f[k]=arrays[k]
                for k in outputs:assert np.isfinite(raw[k]).all();f[k]=raw[k]
            save(ref/'grading.json',json.loads((p.parents[1]/'grading-template.json').read_text()));state.update(status='unvalidated_candidate',reference_sha256=digest(ref/'reference.h5'),mapping=json.loads((j/'native-runtime.json').read_text()),frames=len(s['output_times_s']))
    except Exception as ex:state.update(status='needs_attention',error=repr(ex),traceback=traceback.format_exc())
    state['ended_unix']=time.time();save(j/'status.json',state)
if __name__=='__main__':main()
