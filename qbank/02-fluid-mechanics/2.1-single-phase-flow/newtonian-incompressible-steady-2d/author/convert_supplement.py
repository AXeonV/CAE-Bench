"""Read actual Lethe VTU fields, compare meshes, and emit contract assets."""
from pathlib import Path
import argparse, base64, hashlib, json, shutil, xml.etree.ElementTree as ET, zlib
import h5py
import numpy as np
from prepare_supplement import specifications,inside,build_mesh,wall_velocity


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def vtu(path):
    tree=ET.parse(path); out={}
    for parent in ('Points','PointData'):
        for a in tree.findall('.//'+parent+'/DataArray'):
            text=''.join(a.text.split())
            blocks=int(np.frombuffer(base64.b64decode(text[:8])[:4],dtype='<u4')[0])
            header_size=4*(3+blocks); encoded_size=4*((header_size+2)//3)
            header=np.frombuffer(base64.b64decode(text[:encoded_size]),dtype='<u4')
            raw=base64.b64decode(text[encoded_size:]); pos=0; payload=b''
            for length in header[3:]:
                payload+=zlib.decompress(raw[pos:pos+int(length)]);pos+=int(length)
            dtype={'Float32':'<f4','Float64':'<f8'}[a.get('type')]
            value=np.frombuffer(payload,dtype=dtype).astype(float)
            out[a.get('Name','xyz')]=value.reshape(-1,int(a.get('NumberOfComponents','1')))
    return out


def probes(s):
    xmax=max(b[2] for b in s['boxes']);ymax=max(b[3] for b in s['boxes'])
    return np.array([(x,y) for x in np.arange(.5,xmax,.5) for y in np.arange(.5,ymax,.5)
                     if all(inside(x+dx,y+dy,s) for dx,dy in [(.01,.01),(-.01,.01),(.01,-.01),(-.01,-.01)])])


def sample(raw,xy):
    result={}
    for key in ('velocity','pressure','velocity_gradient'):
        values=[]
        for point in xy:
            hit=np.all(np.abs(raw['xyz'][:,:2]-point)<1e-7,axis=1)
            if not hit.any():raise ValueError(('Missing exact VTU node',point))
            # Continuous Q2 velocity/Q1 pressure have identical duplicated traces.
            if key!='velocity_gradient' and np.ptp(raw[key][hit],axis=0).max()>1e-6:
                raise ValueError(('Discontinuous value',key,point))
            values.append(raw[key][hit].mean(axis=0))
        result[key]=np.array(values)
    result['velocity']=result['velocity'][:,:2]
    result['pressure']-=result['pressure'][0]
    g=result['velocity_gradient'].reshape(-1,3,3)[:,:2,:2]
    d=(g+g.transpose(0,2,1))/2
    result['shear_rate']=np.sqrt(2*np.einsum('nij,nij->n',d,d))[:,None]
    return result


def field(quantity,location,kind='scalar',unit='',value_kind='point',array=None):
    c=2 if kind=='vector' else 1
    return dict(array=array or quantity,quantity=quantity,location=location,time_axis='steady',
                dtype='float64',kind=kind,component_shape=[c],unit=unit,value_kind=value_kind,
                components=['x','y'] if c==2 else ['value'])


def write_case(s,xy,ref,source,meshdir,policy,input_n=4):
    name=s['name']; inp=source/'cases'/name; reference=source/'reference'/name
    inp.mkdir(parents=True,exist_ok=True);reference.mkdir(parents=True,exist_ok=True)
    xyz,quads,cell_ids,boundary=build_mesh(s,input_n,meshdir)
    shutil.copyfile(meshdir/'mesh.msh',inp/'mesh.msh')
    arrays=dict(clock=np.array([0.]),probe_ids=np.arange(1001,1001+len(xy),dtype=np.int64),
                probe_xy=xy,pin_ids=np.array([7],dtype=np.int64),pin_xy=xy[:1],
                node_ids=np.arange(1,len(xyz)+1,dtype=np.int64),domain_ids=np.array(cell_ids,dtype=np.int64))
    locations=dict(domain=dict(kind='mesh',mesh='fluid',entity='element',dimension=2,ids='domain_ids',physical_group=dict(dimension=2,tag=100)),
                   nodes=dict(kind='mesh',mesh='fluid',entity='node',ids='node_ids'),
                   probes=dict(kind='points',ids='probe_ids',coordinates='probe_xy'),
                   pin=dict(kind='points',ids='pin_ids',coordinates='pin_xy'))
    conditions=[];fields={}
    for k,b in boundary.items():
        key=f'wall_{k}'
        locations[key]=dict(kind='mesh',mesh='fluid',entity='element',dimension=1,ids=key+'_ids',physical_group=dict(dimension=1,tag=k))
        arrays[key+'_ids']=np.array(b['ids'],dtype=np.int64)
        ux,uy=wall_velocity(s,k);data={};operator='no_slip'
        if k in s.get('slip',[]):operator='slip'
        elif ux or uy:
            operator='moving_wall';data={'velocity':{'field':key+'_motion'}}
            ids=sorted(set(v for edge in b['edges'] for v in edge))
            locations[key+'_nodes']=dict(kind='mesh',mesh='fluid',entity='node',ids=key+'_node_ids')
            arrays[key+'_node_ids']=np.array(ids,dtype=np.int64)
            f=field('wall_speed',key+'_nodes','vector','m/s','point',key+'_velocity')
            f['sampling']=dict(space='piecewise_linear',time='constant',extrapolation='forbid')
            fields[key+'_motion']=f
            lo,hi=np.array(b['bounds']);axis=0 if hi[0]>lo[0] else 1
            ramp=np.ones(len(ids)) if name=='lid-square' else np.minimum(1,np.minimum((xyz[np.array(ids)-1,axis]-lo[axis])/.5,(hi[axis]-xyz[np.array(ids)-1,axis])/.5))
            arrays[key+'_velocity']=ramp[None,:,None]*np.array([ux,uy])[None,None,:]
        conditions.append(dict(role='boundary',variable='flow',operator=operator,location=key,data=data))
    if 'force' in s:
        f=field('acceleration','nodes','vector','m/s2',array='acceleration')
        f['sampling']=dict(space='piecewise_linear',time='constant',extrapolation='forbid');fields['body_force']=f
        x,y=xyz[:,0],xyz[:,1]
        # Restricted expressions from the explicit specification, not user code.
        components=[np.broadcast_to(eval(e,{'__builtins__':{}},{'x':x,'y':y}),x.shape) for e in s['force']]
        arrays['acceleration']=np.stack(components,axis=-1)[None]
        conditions.append(dict(role='source',variable='velocity',operator='acceleration',location='domain',data={'value':{'field':'body_force'}}))
    outputs={q:field(q,'probes',k,u) for q,k,u in [('velocity','vector','m/s'),('pressure','scalar','Pa'),('density','scalar','kg/m3'),('dynamic_viscosity','scalar','Pa.s'),('shear_rate','scalar','1/s')]}
    nu=s.get('nu',.1)
    problem=dict(task='newtonian-incompressible-steady-2d',spatial_dimension=2,contract_version=2,profile='cfd-2.1',data_file='input.h5',geometries={},meshes={'fluid':{'file':'mesh.msh'}},
                 locations=locations,time_axes={'steady':'clock'},fields=fields,outputs=outputs,conditions=conditions,
                 analysis=dict(type='steady',compressibility='incompressible',flow_regime='laminar',temperature=dict(value=300.,unit='K'),
                               pressure=dict(representation='gauge',reference_pressure=dict(value=101325.,unit='Pa')),
                               pressure_gauge=dict(kind='point',location='pin',value=dict(value=0.,unit='Pa'))),
                 materials={'liquid':dict(region='domain',density=dict(kind='constant',parameters={'density':dict(value=1.,unit='kg/m3')}),
                                         viscosity=dict(kind='newtonian',parameters={'dynamic_viscosity':dict(value=nu,unit='Pa.s')}))})
    (inp/'problem.json').write_text(json.dumps(problem,indent=2)+'\n')
    with h5py.File(inp/'input.h5','w') as h:
        for key,value in arrays.items():h[key]=value
    with h5py.File(reference/'reference.h5','w') as h:
        h['clock']=arrays['clock'];h['probe_ids']=arrays['probe_ids']
        for q in outputs:
            a=ref[q] if q in ref else np.full((len(xy),1),1. if q=='density' else nu)
            h[q]=a[None].astype(np.float64)
    grading=dict(version=1,checks=[dict(id='all_outputs',evaluator='direct_outputs',reference='reference.h5',policy=policy)])
    (reference/'grading.json').write_text(json.dumps(grading,indent=2)+'\n')


def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('source',type=Path);p.add_argument('evidence',type=Path);p.add_argument('policy',type=Path);args=p.parse_args()
    args.evidence.mkdir(parents=True,exist_ok=True);policy=json.loads(args.policy.read_text())
    catalog=[]
    for s in specifications():
        xy=probes(s);levels=[4,8,16]+([32,64] if s['name']=='lid-square' else [])
        sampled={};record=dict(name=s['name'],definition=s,probes=len(xy),levels={})
        for n in levels:
            d=args.root/'runs'/s['name']/f'n{n}'
            paths=sorted(d.glob('solution.*.00000.vtu'));path=paths[-1]
            sampled[n]=sample(vtu(path),xy)
            execution=json.loads((d/'execution.json').read_text())
            if execution['returncode']!=0:raise ValueError('Failed solver')
            record['levels'][str(n)]={**execution,'raw_vtu_sha256':sha(path),'configuration_sha256':sha(d/'case.prm'),'solver_mesh_sha256':sha(d/'solver.msh')}
            dest=args.evidence/'runs'/s['name']/f'n{n}';dest.mkdir(parents=True,exist_ok=True)
            for file in ('case.prm','solver.log','execution.json','definition.json','resource.txt'):
                if (d/file).exists():shutil.copyfile(d/file,dest/file)
        record['comparison']={}
        for a,b in zip(levels,levels[1:]):
            metrics={}
            for q in ('velocity','pressure','shear_rate'):
                delta=np.abs(sampled[a][q]-sampled[b][q]);rule=policy['quantities'][q]['rule']
                tolerance=rule['atol']+rule['rtol']*np.abs(sampled[b][q])
                metrics[q]=dict(max_abs=float(delta.max()),max_tolerance_fraction=float((delta/tolerance).max()))
            record['comparison'][f'{a}-{b}']=metrics
        last=record['comparison'][f'{levels[-2]}-{levels[-1]}']
        record['accepted']=all(v['max_tolerance_fraction']<.25 for v in last.values())
        if not record['accepted']:
            print('NEEDS REFINEMENT',s['name'],last,flush=True)
        # Export anyway to permit diagnostics; upload requires accepted=True for ALL.
        meshdir=args.root/'input-meshes'/s['name'];meshdir.mkdir(parents=True,exist_ok=True)
        write_case(s,xy,sampled[levels[-1]],args.source,meshdir,policy)
        record['input_files']={p.name:sha(p) for p in (args.source/'cases'/s['name']).iterdir()}
        record['reference_files']={p.name:sha(p) for p in (args.source/'reference'/s['name']).iterdir()}
        catalog.append(record)
    (args.evidence/'numerical-validation.json').write_text(json.dumps(catalog,indent=2)+'\n')
    print('accepted',sum(c['accepted'] for c in catalog),'/',len(catalog))


if __name__=='__main__':main()
