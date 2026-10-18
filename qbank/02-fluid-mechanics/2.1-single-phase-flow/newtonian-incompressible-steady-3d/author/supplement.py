"""Produce and compare native Elmer FlowSolver/OpenFOAM simpleFoam cases.

This module generates meshes, native inputs and storage conversions. It does not
assemble a momentum/continuity discretization. Run --help for the staged workflow.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

import gmsh
import numpy as np
from scipy.interpolate import LinearNDInterpolator, RegularGridInterpolator

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT/'src'))
from caeoj.sdk import load_problem, write_result
from caeoj.storage import write_hdf5
from caeoj.case_grading import grade_case
from caeoj_tools.grading_policy import author_policy, write_direct_grading

TASK = 'newtonian-incompressible-steady-3d'
TASK_DIR = Path(__file__).resolve().parent.parent
ELMER_IMAGE = 'sha256:49e9458cc3b1ea3d7e7383c32056af59b0f718e74b0f30adbe3e1bccc0e7b059'
FOAM_IMAGE = 'sha256:d6e27c56bb5f598bc93597fdf671d6e9d06534b1851885f1b093e3cc627ea67e'
FACE_NODES = ((0,4,7,3),(1,2,6,5),(0,1,5,4),(3,7,6,2),(0,3,2,1),(4,5,6,7))


def save(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def catalog():
    """Each group varies physical response/geometry, not just file identities."""
    cases=[]
    groups=[('hydrostatic',18),('couette',20),('periodic-duct',20),('cavity',24),('plug',18)]
    for family,count in groups:
        for j in range(count):
            idx=len(cases)+1
            lengths=np.array([(1.,1.,1.),(2.,1.,.5),(.5,1.,2.),(1.,.5,1.5),(1.5,1.,.75)][j%5])
            axis=j%3
            # Proper rotations preserve equations, while exercising all global components.
            rotation=np.roll(np.eye(3),axis,axis=0)
            angle=(0.,.23,-.41)[(j//3)%3]
            c,s=np.cos(angle),np.sin(angle)
            rotation=np.array([[c,-s,0],[s,c,0],[0,0,1]])@rotation
            rho=(1.,10.,1000.)[(j//2)%3]
            speed=(.03,.06,.12,.24)[j%4]
            reynolds=(.1,1.,5.,20.,50.)[(j//4)%5]
            mu=rho*speed*min(lengths)/reynolds
            if family=='hydrostatic' and j>=12:mu=max(mu,rho*max(lengths)**2)
            geometry='box'
            if family in ('periodic-duct','cavity') and j>=count-8:
                geometry=('obstacle','two-obstacles','baffle','off-center')[j%4]
            item=dict(name=f'{idx:03d}-{family}-{j+1:02d}',family=family,variant=j,
                      lengths=lengths.tolist(),origin=[-.4+.07*(j%3),.3,-.2],rotation=rotation.tolist(),
                      density=rho,viscosity=mu,speed=speed,reynolds_target=reynolds,
                      geometry=geometry,input_mesh=('tet','hex','prism','pyramid','mixed')[j%5],
                      pressure_kind='absolute' if j%5==0 else 'gauge',
                      pressure_value=101325. if j%5==0 else (0.,2.,-1.)[j%3],
                      gauge_kind='point' if j%2 else 'mean',
                      source_parts=2 if j%4==0 else 1)
            if family=='cavity':item['input_mesh']='tet'
            if family=='couette' and j>=14:item['input_mesh']='tet'
            if family in ('hydrostatic','plug') and np.linalg.norm(settings(item)[2])>0:item['input_mesh']='tet'
            cases.append(item)
    assert len(cases)==100
    return cases


def run_batch(work,solvers,indices=None,workers=2):
    from native import elmer,foam,execute,NativeField,AnalyticField,outputs,reusable_run
    items=catalog()
    if indices:items=[c for i,c in enumerate(items,1) if i in indices]
    generated=work/'generated';evidence=work/'evidence';jobs=work/'native'
    code_id=hashlib.sha256(Path(__file__).read_bytes()+(Path(__file__).parent/'native.py').read_bytes()).hexdigest()[:12]
    evidence.mkdir(parents=True,exist_ok=True)
    # Gmsh owns process-global state; generation/validation is intentionally serial.
    for c in items:
        problem=generated/'cases'/c['name']/'problem.json'
        input_case(c,problem.parent)
    policy=author_policy(TASK_DIR)
    def one(c):
        case=c['name'];path=generated/'cases'/case/'problem.json';problem=load_problem(path)
        record=dict(case=case,configuration=c,code_id=code_id,attempts=[],passed=False)
        for n in ((16,24,32) if c['geometry']=='two-obstacles' else (12,24,32)):
            try:
                current=[]
                reference=generated/'reference'/case;reference.mkdir(parents=True,exist_ok=True)
                for sid,prepare in [('elmer',elmer),('openfoam',foam)]:
                    folder=jobs/case/code_id/f'{sid}-n{n}';prepare(c,problem,folder,n)
                    cached=reusable_run(folder,sid,jobs/case)
                    if cached:folder,run=cached
                    else:run=execute(solvers,sid,folder)
                    field=NativeField(c,folder,n,sid)
                    result=outputs(c,problem,field)
                    output=reference/'reference.h5' if sid=='elmer' else reference/'independent.h5'
                    write_result(output,problem,result)
                    current.append(dict(run=run,output_sha256=hashlib.sha256(output.read_bytes()).hexdigest()))
                write_direct_grading(reference,policy)
                report=grade_case(path,reference/'independent.h5',reference/'grading.json')
                from caeoj.sdk import load_result
                a=load_result(problem,reference/'reference.h5');b=load_result(problem,reference/'independent.h5')
                errors={}
                for spec in problem.manifest['outputs'].values():
                    key=spec['array'];rule=policy['quantities'][spec['quantity']]['rule']
                    delta=np.abs(a[key]-b[key]);budget=rule['atol']+rule['rtol']*np.abs(a[key])
                    errors[key]=dict(max_abs=float(delta.max()),max_budget_ratio=float((delta/budget).max()))
                maximum=max(v['max_budget_ratio'] for v in errors.values());analytic_error=None
                try:
                    exact=outputs(c,problem,AnalyticField(c));ratios=[]
                    for spec in problem.manifest['outputs'].values():
                        key=spec['array'];rule=policy['quantities'][spec['quantity']]['rule'];ratios.append(float(np.max(abs(a[key]-exact[key])/(rule['atol']+rule['rtol']*abs(exact[key])))))
                    analytic_error=max(ratios)
                except ValueError:pass
                record['attempts'].append(dict(n=n,runs=current,cross_score=report['score'],errors=errors,max_budget_ratio=maximum,producer_analytic_budget_ratio=analytic_error))
                if report['score']==1 and (maximum<=.35 or analytic_error is not None and analytic_error<=.25):
                    record.update(passed=True,n=n)
                    # Exercise the actual comparator with a complete wrong answer.
                    wrong={s['array']:a[s['array']].copy() for s in problem.manifest['outputs'].values()}
                    velocity=next(s['array'] for s in problem.manifest['outputs'].values() if s['quantity']=='velocity')
                    wrong[velocity][...,0]+=.1
                    write_result(reference/'negative.h5',problem,wrong)
                    assert grade_case(path,reference/'negative.h5',reference/'grading.json')['score']==0
                    (reference/'negative.h5').unlink()
                    assert grade_case(path,reference/'reference.h5',reference/'grading.json')['score']==1
                    break
            except Exception as exc:
                record['attempts'].append(dict(n=n,error=str(exc)))
                # A native interface failure is not cured by a larger mesh.
                if 'failed with' in str(exc):break
            finally:save(evidence/(case+'.json'),record)
        print(json.dumps(dict(case=case,passed=record['passed'],last=record['attempts'][-1].get('error',record['attempts'][-1].get('max_budget_ratio')))),flush=True)
        return record
    gmsh.initialize([],readConfigFiles=False)
    try:
        with ThreadPoolExecutor(max_workers=workers) as executor:results=list(executor.map(one,items))
    finally:gmsh.finalize()
    save(work/'summary.json',dict(total=len(results),passed=sum(r['passed'] for r in results),cases=results))
    return results


def transform(c, points):
    return np.asarray(points)@np.asarray(c['rotation']).T+np.asarray(c['origin'])


def box_grid(c,n):
    """Conforming voxel geometry, shared by both independent native solvers."""
    def hole(x):
        if c['geometry']=='box':return False
        if c['geometry']=='obstacle':return np.all((x>.25)&(x<.5))
        if c['geometry']=='two-obstacles':return (.25<x[1]<.5 and .25<x[2]<.5 and (.125<x[0]<.375 or .625<x[0]<.875))
        if c['geometry']=='baffle':return .25<x[0]<.5 and 0<x[1]<.5 and .25<x[2]<.75
        return .5<x[0]<.75 and .25<x[1]<.5 and .25<x[2]<.75
    logical=np.array([(i,j,k) for k in range(n+1) for j in range(n+1) for i in range(n+1)],float)/n
    node=lambda i,j,k:i+(n+1)*(j+(n+1)*k)
    cells=[]
    for k in range(n):
        for j in range(n):
            for i in range(n):
                if hole((np.array([i,j,k])+.5)/n):continue
                cells.append([node(i,j,k),node(i+1,j,k),node(i+1,j+1,k),node(i,j+1,k),node(i,j,k+1),node(i+1,j,k+1),node(i+1,j+1,k+1),node(i,j+1,k+1)])
    used=np.unique(cells);remap={v:i for i,v in enumerate(used)}
    cells=np.array([[remap[v] for v in cell] for cell in cells]);logical=logical[used]
    points=transform(c,logical*np.asarray(c['lengths']))
    pending={};internal=[]
    for owner,cell in enumerate(cells):
        for face in FACE_NODES:
            ids=tuple(cell[list(face)]);key=tuple(sorted(ids))
            if key in pending:
                other,vertices=pending.pop(key);internal.append((other,owner,vertices))
            else:pending[key]=(owner,ids)
    boundaries={i:[] for i in range(1,8)}
    for owner,ids in pending.values():
        center=logical[list(ids)].mean(axis=0);bc=7
        for ax in range(3):
            if abs(center[ax])<1e-10:bc=2*ax+1
            if abs(center[ax]-1)<1e-10:bc=2*ax+2
        boundaries[bc].append((owner,ids))
    internal.sort(key=lambda f:(f[0],f[1]))
    return points,cells,boundaries,internal,logical


def settings(c):
    j=c['variant'];family=c['family'];R=np.asarray(c['rotation']);U=c['speed'];L=np.asarray(c['lengths'])
    bcs={b:'no_slip' for b in range(1,8)};acc=np.zeros(3);H=np.zeros((3,3))
    lids={}
    if family=='hydrostatic':
        acc[(j//3)%3]=(1.,-1.,.2)[j%3]
        if j<6:bcs[2]='pressure_outlet'
        elif j<12:bcs[2]='traction'
        else:H=np.diag([.3,-.15,.2])*((j-11)/6)
    elif family=='couette':
        for b in (1,2,5,6):bcs[b]='periodic'
        bcs[4]='moving_wall';lids[4]=[U,0,U*(.5 if j%3==0 else 0)]
        if j%3==1:bcs[3]='moving_wall';lids[3]=[-.4*U,0,.25*U]
        if j>=10:acc[1]=.1*((j%3)-1)
        if j>=14:bcs[1]=bcs[2]='traction'
    elif family=='periodic-duct':
        bcs[1]=bcs[2]='periodic';acc[0]=12*c['viscosity']*U/(c['density']*L[1]**2)
        if j%3==0:bcs[5]=bcs[6]='slip'
        if j%3==1:bcs[5]=bcs[6]='symmetry'
        if j%4==0:bcs[4]='moving_wall';lids[4]=[.3*U,0,0]
    elif family=='cavity':
        bcs[4]='moving_wall';lids[4]=[U,0,0]
        if j%3==1:bcs[3]='moving_wall';lids[3]=[-.7*U,0,0]
        if j%3==2:bcs[6]='moving_wall';lids[6]=[0,.7*U,0]
    elif family=='plug':
        bcs[1]='flow_rate' if j%2 else 'velocity';bcs[2]='pressure_outlet' if j%3 else 'traction'
        for b in (3,4,5,6):bcs[b]='slip' if j%3 else 'symmetry'
        lids[1]=[U,0,0];acc[1]=(0.,-.2,0.)[j%3]
    return bcs,lids,R@acc,R@H@R.T


def tangential_load(c,b):
    """Specified Cartesian traction of the classical plane Couette family."""
    if c['family']!='couette' or c['variant']<14:return np.zeros(3)
    bcs,lids,_,_=settings(c);R=np.asarray(c['rotation'])
    delta=R@(np.asarray(lids.get(4,[0,0,0]))-np.asarray(lids.get(3,[0,0,0])))
    grad=np.outer(delta,R[:,1])/c['lengths'][1]
    normal=R[:,(b-1)//2]*(1 if b%2==0 else -1)
    return c['viscosity']*(grad+grad.T)@normal


def lid_values(c,b,logical):
    bcs,lids,_,_=settings(c);v=np.asarray(lids.get(b,[0,0,0]),float)
    values=np.tile(v,(len(logical),1))
    if c['family']=='cavity' and b in lids:
        axes=[a for a in range(3) if a!=(b-1)//2]
        shape=np.prod([4*logical[:,a]*(1-logical[:,a]) for a in axes],axis=0)
        values*=shape[:,None]
    return values@np.asarray(c['rotation']).T


def element_data(c,n=4):
    """Gmsh native API writes standard first-order MSH 4.1 ASCII."""
    points,hexes,faces,_,logical=box_grid(c,n);points=list(points);logical=list(logical)
    elements=[];surface=[];kind=c['input_mesh']
    tets=((0,1,2,6),(0,2,3,6),(0,3,7,6),(0,7,4,6),(0,4,5,6),(0,5,1,6))
    for index,h in enumerate(hexes):
        if kind=='tet':elements.extend((4,[h[k] for k in t]) for t in tets)
        elif kind=='prism':elements.extend([(6,list(h[[0,1,2,4,5,6]])),(6,list(h[[0,2,3,4,6,7]]))])
        elif kind=='pyramid' or (kind=='mixed' and index%2):
            center=len(points);points.append(np.mean(np.asarray(points)[h],axis=0));logical.append(np.mean(np.asarray(logical)[h],axis=0))
            for f in FACE_NODES:elements.append((7,list(reversed(h[list(f)]))+[center]))
        else:elements.append((5,list(h)))
    for b,group in faces.items():
        for _,quad in group:
            q=list(quad)
            if kind=='tet':
                # Six-tetrahedron split uses the diagonal joining min/max cube tags.
                lo=q.index(min(q));q=q[lo:]+q[:lo]
                surface.extend([(b,2,[q[0],q[1],q[2]]),(b,2,[q[0],q[2],q[3]])])
            elif kind=='prism' and np.ptp(np.asarray(logical)[q,2])<1e-12:
                lo=q.index(min(q));q=q[lo:]+q[:lo];surface.extend([(b,2,[q[0],q[1],q[2]]),(b,2,[q[0],q[2],q[3]])])
            else:surface.append((b,3,q))
    return np.array(points),elements,surface,np.array(logical)


def input_case(c,folder):
    folder.mkdir(parents=True,exist_ok=True)
    points,cells,faces,logical=element_data(c,n=8 if c['geometry']=='two-obstacles' else 4)
    gmsh.initialize([],readConfigFiles=False);gmsh.option.setNumber('General.Terminal',0)
    try:
        gmsh.model.add('case');gmsh.model.addDiscreteEntity(3,1)
        for b in sorted({b for b,_,_ in faces}):gmsh.model.addDiscreteEntity(2,b)
        tags=np.arange(1,len(points)+1,dtype=np.int64)*3+17
        gmsh.model.mesh.addNodes(3,1,tags,points.ravel())
        cellids=np.arange(1,len(cells)+1,dtype=np.int64)*7+100
        for typ in sorted({t for t,_ in cells}):
            indices=[i for i,(t,_) in enumerate(cells) if t==typ]
            gmsh.model.mesh.addElementsByType(1,typ,cellids[indices],np.concatenate([tags[cells[i][1]] for i in indices]))
        faceids=np.arange(1,len(faces)+1,dtype=np.int64)*11+int(cellids[-1])+100
        for b in sorted({b for b,_,_ in faces}):
            for typ in sorted({t for bb,t,_ in faces if bb==b}):
                indices=[i for i,(bb,t,_) in enumerate(faces) if bb==b and t==typ]
                gmsh.model.mesh.addElementsByType(b,typ,faceids[indices],np.concatenate([tags[faces[i][2]] for i in indices]))
            gmsh.model.addPhysicalGroup(2,[b],b+10)
        gmsh.model.addPhysicalGroup(3,[1],1)
        gmsh.option.setNumber('Mesh.MshFileVersion',4.1);gmsh.option.setNumber('Mesh.Binary',0);gmsh.write(str(folder/'mesh.msh'))
    finally:gmsh.finalize()
    arrays={'cells':cellids,'times':np.array([0.]),'single':np.array([5],dtype=np.int64)}
    locations={'domain':dict(kind='mesh',mesh='main',entity='element',dimension=3,ids='cells',physical_group=dict(dimension=3,tag=1))}
    for b in sorted({b for b,_,_ in faces}):
        name=f'face{b}';arrays[name+'_ids']=faceids[[i for i,(bb,_,_) in enumerate(faces) if bb==b]]
        locations[name]=dict(kind='mesh',mesh='main',entity='element',dimension=2,ids=name+'_ids',physical_group=dict(dimension=2,tag=b+10))
    probes=np.array([[.14,.17,.21],[.34,.61,.41],[.61,.17,.66],[.81,.71,.84],[.53,.83,.16],[.15,.42,.78]])
    # Interior cell centers selected from the actual connected domain, away from faces.
    _,_,_,_,fine=box_grid(c,4)
    # The fixed probes avoid all four obstacle layouts; explicit containment is checked below.
    if c['geometry']!='box':probes=np.array([[.14,.17,.21],[.81,.71,.84],[.53,.83,.16],[.15,.42,.78]])
    arrays['probe_ids']=np.arange(1,len(probes)+1,dtype=np.int64)*13
    arrays['probe_xyz']=transform(c,probes*np.array(c['lengths']))
    locations['probes']=dict(kind='points',ids='probe_ids',coordinates='probe_xyz')
    gauge=np.array([[.125,.125,.125]])
    arrays['gauge_ids']=np.array([77],dtype=np.int64);arrays['gauge_xyz']=transform(c,gauge*np.array(c['lengths']))
    locations['gauge']=dict(kind='points',ids='gauge_ids',coordinates='gauge_xyz')
    def field(array,quantity,location,unit,vector=False,space=None):
        s=dict(array=array,quantity=quantity,location=location,time_axis='steady',dtype='float64',kind='vector' if vector else 'scalar',component_shape=[3] if vector else [1],components=list('xyz') if vector else ['value'],unit=unit,value_kind='point' if locations[location]['kind']=='points' or locations[location].get('entity')=='node' else 'average')
        if space:s['sampling']=dict(space=space,time='constant',extrapolation='forbid')
        return s
    const=lambda v,u:dict(value=float(v),unit=u)
    bcs,lids,acc,H=settings(c);fields={};conditions=[]
    node_locations={}
    def node_field(b,name,quantity,unit,values,vector=True):
        indices=np.unique([i for bb,_,f in faces if bb==b for i in f]);loc='nodes'+str(b)
        if loc not in locations:
            arrays[loc+'_ids']=tags[indices];locations[loc]=dict(kind='mesh',mesh='main',entity='node',ids=loc+'_ids')
        arrays[name]=np.asarray(values(indices)).reshape(1,len(indices),3 if vector else 1)
        fields[name]=field(name,quantity,loc,unit,vector,'piecewise_linear')
        return dict(field=name)
    for b in sorted({b for b,_,_ in faces}):
        op=bcs[b];data={};name=f'face{b}'
        if op in ('moving_wall','velocity'):
            if c['family']=='cavity':data['velocity']=node_field(b,'drive'+str(b),'velocity','m/s',lambda i:lid_values(c,b,logical[i]))
            else:
                key='drive'+str(b);count=len(arrays[name+'_ids']);arrays[key]=lid_values(c,b,np.zeros((count,3)))[None]
                fields[key]=field(key,'velocity',name,'m/s',True,'uniform');data['velocity']=dict(field=key)
        if op=='flow_rate':
            data=dict(rate=const(c['speed']*c['lengths'][1]*c['lengths'][2],'m3/s'),shape=const(1.,'1'))
            if c['variant']%4==1:
                key='flow_total';count=len(arrays[name+'_ids']);arrays[key]=np.full((1,count,1),data['rate']['value']);fields[key]=field(key,'prescribed_total_rate',name,'m3/s',space='uniform');data['rate']=dict(field=key)
            if c['variant']%4==3:
                key='inlet_shape';count=len(arrays[name+'_ids']);arrays[key]=np.full((1,count,1),2.5);fields[key]=field(key,'inlet_weight',name,'1',space='piecewise_constant');data['shape']=dict(field=key)
        if op in ('traction','pressure_outlet'):
            pfun=lambda xyz:c['pressure_value']+c['density']*((xyz-np.array(c['origin']))@acc)
            if c['input_mesh']=='tet':
                if op=='pressure_outlet':data['pressure']=node_field(b,'load'+str(b),'pressure','Pa',lambda i:pfun(points[i]),False)
                else:
                    normal=np.array(c['rotation'])[:,(b-1)//2]*(1 if b%2==0 else -1)
                    data['traction']=node_field(b,'load'+str(b),'traction','Pa',lambda i:-pfun(points[i])[:,None]*normal+tangential_load(c,b))
            else:
                # Hydrostatic boundary values are constant only when gravity is tangentially zero.
                # Use zero tangential acceleration for non-simplex natural-boundary cases.
                if np.linalg.norm(acc)>0:raise ValueError('Nonuniform natural boundary requires tetrahedral input')
                if op=='pressure_outlet':data['pressure']=const(c['pressure_value'],'Pa')
                else:
                    key='load'+str(b);normal=np.array(c['rotation'])[:,(b-1)//2]*(1 if b%2==0 else -1)
                    arrays[key]=np.tile(-c['pressure_value']*normal,(1,len(arrays[name+'_ids']),1));fields[key]=field(key,'traction',name,'Pa',True,'uniform');data['traction']=dict(field=key)
            if op=='pressure_outlet':data['backflow']=dict(option='forbid')
        if op=='periodic':
            partner=b+1 if b%2 else b-1;translation=np.array(c['rotation'])[:,(b-1)//2]*c['lengths'][(b-1)//2]*(1 if b%2 else -1)
            data=dict(partner=dict(location=f'face{partner}'),**{'translation_'+a:const(v,'m') for a,v in zip('xyz',translation)})
        conditions.append(dict(role='boundary',variable='flow',location=name,operator=op,data=data))
    if np.linalg.norm(acc)>0 or np.linalg.norm(H)>0:
        if np.linalg.norm(H)>0:
            arrays['node_ids']=tags;locations['nodes']=dict(kind='mesh',mesh='main',entity='node',ids='node_ids');loc='nodes'
            values=acc+(points-np.array(c['origin']))@H.T;space='piecewise_linear'
        else:loc='domain';values=np.tile(acc,(len(cells),1));space='uniform'
        for part in range(c['source_parts']):
            key='acceleration'+str(part);arrays[key]=values[None]/c['source_parts'];fields[key]=field(key,'body_acceleration',loc,'m/s2',True,space)
            conditions.append(dict(role='source',variable='velocity',location='domain',operator='acceleration',data=dict(value=dict(field=key))))
    output_loc='probes'
    if c['family']=='couette' or (c['family']=='hydrostatic' and c['variant']<12):
        if c['variant']%3==1:
            arrays['node_ids']=tags;locations['nodes']=dict(kind='mesh',mesh='main',entity='node',ids='node_ids');output_loc='nodes'
        elif c['variant']%3==2:output_loc='domain'
    outputs={}
    for q,u,v in [('velocity','m/s',True),('pressure','Pa',False),('density','kg/m3',False),('dynamic_viscosity','Pa.s',False)]:outputs[q]=field('answer_'+q,q,output_loc,u,v)
    if c['family'] in ('couette','plug') or (c['family']=='hydrostatic' and c['variant']<12):
        outputs['surface_traction']=field('answer_traction','traction','face2','Pa',True)
        locations['volume_mean']=dict(kind='aggregate',source='domain',ids='single',operation='mean')
        outputs['mean_pressure']=field('answer_mean_pressure','pressure','volume_mean','Pa')
    if c['family'] in ('hydrostatic','couette','plug'):
        outputs['shear']=field('answer_shear','shear_rate','probes','1/s')
    if c['family'] in ('couette','plug') or (c['family']=='hydrostatic' and c['variant']<12):
        for b in (3,4):
            locations['total'+str(b)]=dict(kind='aggregate',source='face'+str(b),ids='single',operation='sum')
            for q,u,v in [('force','N',True),('volume_flow','m3/s',False),('mass_flow','kg/s',False)]:
                key=q+str(b);outputs[key]=field('answer_'+key,q,'total'+str(b),u,v);outputs[key]['value_kind']='integral'
    if c['family']=='plug':
        for b in (1,2):
            locations['total'+str(b)]=dict(kind='aggregate',source='face'+str(b),ids='single',operation='sum')
            for q,u in [('volume_flow','m3/s'),('mass_flow','kg/s')]:
                key=q+str(b);outputs[key]=field('answer_'+key,q,'total'+str(b),u);outputs[key]['value_kind']='integral'
    pressure=dict(representation=c['pressure_kind'])
    if pressure['representation']=='gauge':pressure['reference_pressure']=const(101325.,'Pa')
    analysis=dict(type='steady',compressibility='incompressible',flow_regime='laminar',temperature=const(300.+c['variant'],'K'),pressure=pressure)
    if not any(op in ('pressure_outlet','traction') for op in bcs.values()):analysis['pressure_gauge']=dict(kind=c['gauge_kind'],location='domain' if c['gauge_kind']=='mean' else 'gauge',value=const(c['pressure_value'],'Pa'))
    m=dict(task=TASK,spatial_dimension=3,contract_version=2,profile='cfd-2.1',data_file='input.h5',geometries={},meshes=dict(main=dict(file='mesh.msh')),locations=locations,time_axes=dict(steady='times'),fields=fields,outputs=outputs,conditions=conditions,analysis=analysis,materials=dict(fluid=dict(region='domain',density=dict(kind='constant',parameters=dict(density=const(c['density'],'kg/m3'))),viscosity=dict(kind='newtonian',parameters=dict(dynamic_viscosity=const(c['viscosity'],'Pa.s'))))))
    referenced={s['ids'] for s in locations.values()}|{s['coordinates'] for s in locations.values() if 'coordinates' in s}|{'times'}|{s['array'] for s in fields.values()}
    arrays={k:v for k,v in arrays.items() if k in referenced}
    save(folder/'problem.json',m);write_hdf5(folder/'input.h5',arrays)
    return load_problem(folder/'problem.json')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['catalog','inputs','run']);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--solvers',type=Path);parser.add_argument('--only',type=int,nargs='+');parser.add_argument('--workers',type=int,default=2);args=parser.parse_args()
    items=catalog()
    if args.command=='catalog':save(args.output,items)
    elif args.command=='run':
        if not args.solvers:parser.error('run requires --solvers')
        run_batch(args.output,args.solvers,args.only,args.workers)
    else:
        for item in items:
            input_case(item,args.output/'cases'/item['name']);print(item['name'],flush=True)
        save(args.output/'catalog.json',items)
