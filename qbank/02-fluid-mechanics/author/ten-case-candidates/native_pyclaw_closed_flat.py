"""One flat-bed, no-drag, reflective-wall shallow-water candidate.

Exact polygon integration transfers supplied P1 depth to native FV means.
Native PyClaw performs all evolution; point outputs use bilinear reconstruction.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import h5py
import numpy as np
from scipy.interpolate import RegularGridInterpolator
from elmer_flow_mesh import generate
from native_lowmach import sample
from native_closed_cavity import SOCKET,save,digest
from polytropic_reference import gmsh
from titan_resources import reservation

IMAGE='sha256:9553e81044dfb139789f41e711f890689d72632ea00e851f3c021d38af84bc3f'
CASE='ch02-2-9-2-01-gaussian_hump'


def clip(poly,axis,edge,sign):
    result=[]
    for a,b in zip(poly,np.roll(poly,-1,axis=0)):
        va=sign*(a[axis]-edge);vb=sign*(b[axis]-edge)
        if va>=0:result.append(a)
        if (va>=0)!=(vb>=0):result.append(a+(b-a)*va/(va-vb))
    return np.array(result)


def transfer(x,c,values,lengths,nx=64,ny=32):
    dx,dy=np.array(lengths)/[nx,ny];integral=np.zeros((nx,ny));covered=np.zeros((nx,ny))
    for tri in c:
        poly=np.column_stack([x[tri],values[tri]])
        lo=np.maximum(0,np.floor(x[tri].min(axis=0)/[dx,dy]).astype(int));hi=np.minimum([nx-1,ny-1],np.floor(x[tri].max(axis=0)/[dx,dy]).astype(int))
        for i in range(lo[0],hi[0]+1):
            for j in range(lo[1],hi[1]+1):
                cut=poly
                for axis,edge,sign in [(0,i*dx,1),(0,(i+1)*dx,-1),(1,j*dy,1),(1,(j+1)*dy,-1)]:
                    if len(cut)<3:break
                    cut=clip(cut,axis,edge,sign)
                for k in range(1,len(cut)-1):
                    a,b,d=cut[[0,k,k+1]];area=abs(np.linalg.det(np.array([b[:2]-a[:2],d[:2]-a[:2]])))/2
                    covered[i,j]+=area;integral[i,j]+=area*(a[2]+b[2]+d[2])/3
    assert np.max(np.abs(covered-dx*dy))<1e-9*dx*dy,'Input/native geometry coverage differs'
    return integral/(dx*dy)


def descriptor(q,loc,axis,unit,dim=1,input=False,integral=False):
    z={'array':q,'quantity':q,'location':loc,'time_axis':axis,'dtype':'float64','kind':'scalar' if dim==1 else 'vector','component_shape':[dim],'components':['value'] if dim==1 else list('xy'),'unit':unit,'value_kind':'integral' if integral else 'point'}
    if input:z['sampling']={'space':'piecewise_linear','time':'constant','extrapolation':'forbid'}
    return z


def prepare(job,e):
    s=e['detailed_spec'];assert e['design_id']==CASE and s['parameters']['drag_rate']['value']==0
    assert not s['geometry']['holes'] and all(b['operator']=='water_wall' for b in s['boundaries'])
    m=generate(s);x,c,b=m['x'],m['c'],m['b'];L=s['geometry']['bounding_lengths']
    bed=sample(s['domain_conditions']['bed']['expression'],x,0,s);h=sample(s['initial']['depth']['expression'],x,0,s);u=sample(s['initial']['velocity']['expression'],x,0,s)
    assert np.all(bed==0) and np.min(h)>0 and np.all(u==0)
    hn=transfer(x,c,h,L);q=np.zeros((3,*hn.shape));q[0]=hn
    np.savez(job/'native-input.npz',q=q,lengths=L,gravity=s['parameters']['gravity']['value'],times=s['output_times_s'])
    keep=np.ones(len(x),bool);keep[np.unique(b)]=False
    for _ in range(2):keep[np.unique(c[np.any(~keep[c],axis=1)])]=False
    ids=np.flatnonzero(keep);assert len(ids)>0
    inp=job/'input';inp.mkdir();gmsh(inp/'mesh.msh',x,c,b,2)
    locations={'domain':{'kind':'mesh','mesh':'main','entity':'node','ids':'nodes'},'observed':{'kind':'mesh','mesh':'main','entity':'node','ids':'observed'},'area':{'kind':'mesh','mesh':'main','entity':'element','dimension':2,'ids':'cells'},'wall':{'kind':'mesh','mesh':'main','entity':'element','dimension':1,'ids':'wall'},'volume':{'kind':'aggregate','source':'area','ids':'integral','operation':'sum'}}
    fields={};conditions=[]
    for key,qname,role,op,axis,unit,dim in [('bed','bed','material','geometry','constant','m',1),('depth0','depth','initial','assign','initial','m',1),('velocity0','velocity','initial','assign','initial','m/s',2)]:
        fields[key]=descriptor(qname,'domain',axis,unit,dim,True);fields[key]['array']=key;conditions.append({'role':role,'variable':qname,'operator':op,'location':'domain','data':{'value':{'field':key}}})
    conditions.append({'role':'boundary','variable':'water','operator':'water_wall','location':'wall','data':{'mode':{'option':'impermeable'}}})
    outputs={q:descriptor(q,'volume' if q=='water_volume' else 'observed','requested',unit,dim,integral=q=='water_volume') for q,unit,dim in [('depth','m',1),('velocity','m/s',2),('water_flux','m2/s',2),('water_volume','m3',1)]}
    save(inp/'problem.json',{'task':e['task'],'physics':{'model':e['model'],'parameters':s['parameters']},'spatial_dimension':2,'data_file':'input.h5','geometries':{},'meshes':{'main':{'file':'mesh.msh'}},'locations':locations,'time_axes':{'initial':'initial','constant':'constant','requested':'requested'},'fields':fields,'conditions':conditions,'outputs':outputs})
    with h5py.File(inp/'input.h5','w') as f:
        for key,a in {'nodes':np.arange(1,len(x)+1,dtype=np.int64),'observed':ids.astype(np.int64)+1,'cells':np.arange(1,len(c)+1,dtype=np.int64),'wall':np.arange(1,len(b)+1,dtype=np.int64)+len(c),'integral':np.array([1],dtype=np.int64),'initial':np.array([0.]),'constant':np.array([0.]),'requested':np.array(s['output_times_s']),'bed':bed[None,:,None],'depth0':h[None,:,None],'velocity0':u[None]}.items():f[key]=a
    np.savez(job/'adapter-data.npz',**m,observed=ids)
    save(job/'input-transfer.json',{'method':'Exact clipping of each public input triangle to native rectangles, exact affine depth integral on clipped subtriangles; initial velocity is exactly zero. Supplied nodal P1 input is the sole initial field.','native_shape':list(hn.shape),'native_input_sha256':digest(job/'native-input.npz'),'numerical_validation':False})
    return m,ids


def convert(job,e,m,ids):
    raw=np.load(job/'native-output.npz');times=raw['times'];assert np.array_equal(times,e['detailed_spec']['output_times_s']);points=m['x'][ids];hs=[];us=[];qs=[];volumes=[]
    for q in raw['q']:
        nodal=RegularGridInterpolator((raw['x'],raw['y']),np.moveaxis(q,0,-1),bounds_error=True)(points)
        h=nodal[:,0:1];flux=nodal[:,1:3];assert np.min(h)>0 and np.isfinite(nodal).all()
        hs.append(h);qs.append(flux);us.append(flux/h);volumes.append([[q[0].sum()*np.prod(np.array(e['detailed_spec']['geometry']['bounding_lengths'])/q.shape[1:])]])
    ref=job/'reference';ref.mkdir()
    with h5py.File(ref/'reference.h5','w') as f:
        for key,a in {'observed':ids.astype(np.int64)+1,'integral':np.array([1],dtype=np.int64),'requested':times,'depth':hs,'velocity':us,'water_flux':qs,'water_volume':volumes}.items():f[key]=a
    return {'reference_sha256':digest(ref/'reference.h5'),'frames':len(times),'mapping':'Native PyClaw Classic 2D HLLE, reflective walls and zero drag/flat bed. Exact P1-to-FV initial depth projection; bilinear continuous reconstruction of conservative native state at actual public mesh nodes; u=(hu)/h. Water volume is native FV area integral. No accuracy validation.'}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int,default=1);args=ap.parse_args();root=args.root
    p=next(args.snapshot.glob('qbank/02-fluid-mechanics/*/fully-wet-transient/author/chapter02-ten-20261020/design.json'));freeze=json.loads((args.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text());assert digest(p)==freeze['designs'][p.relative_to(args.snapshot).as_posix()];d=json.loads(p.read_text());e={**next(e for e in d['proposed_cases'] if e['design_id']==CASE),'task':d['task'],'model':d['model']};job=root/'cases'/CASE
    if (job/'status.json').exists():return
    job.mkdir();save(job/'design.json',e);state={'design_id':CASE,'status':'queued'};save(job/'status.json',state);name='ch02pyclaw-'+str(time.time_ns())
    try:
        with reservation(root,name):
            m,ids=prepare(job,e);runtime=Path(__file__).with_name('pyclaw_closed_flat_runtime.py');shutil.copy2(runtime,job/runtime.name)
            cmd=['docker','--host',SOCKET,'run','--name',name,'--network','none','--cpus','1','--memory','768m','--user',f'{os.getuid()}:{os.getgid()}','-e','OMP_NUM_THREADS=1','-e','OPENBLAS_NUM_THREADS=1','-v',f'{job}:/work','-w','/work',IMAGE,'python',runtime.name]
            save(job/'execution.json',{'producer':'unmodified Clawpack/PyClaw 5.9.0 Classic 2D shallow_hlle_2D','image':IMAGE,'source_url':'https://github.com/clawpack/clawpack/tree/v5.9.0','script_sha256':digest(Path(__file__)),'native_configuration_script_sha256':digest(runtime),'command':cmd,'start_unix':time.time(),'numerical_validation':False});state.update(status='running',container=name);save(job/'status.json',state)
            with (job/'solver.log').open('w') as log:cp=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
            assert cp.returncode==0,f'native exit {cp.returncode}'
            runtime_record=json.loads((job/'native-runtime.json').read_text());record=json.loads((job/'execution.json').read_text());record['binary_sha256']=runtime_record['riemann_binary_sha256'];save(job/'execution.json',record)
            state.update(convert(job,e,m,ids));save(job/'reference/grading.json',json.loads((p.parents[1]/'grading-template.json').read_text()));state['status']='unvalidated_candidate'
    except Exception as ex:state.update(status='needs_attention',error=repr(ex))
    state['ended_unix']=time.time();save(job/'status.json',state)


if __name__=='__main__':main()
