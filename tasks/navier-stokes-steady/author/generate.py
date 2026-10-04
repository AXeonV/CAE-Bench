"""Build both task banks, analytic/published references and complete public samples."""
import argparse
import json
from pathlib import Path
import shutil
import numpy as np
from caeoj.sdk import load_problem, write_result
from caeoj.grading import grade_files
from caeoj.validation import write_json
from catalog import cases, time_scale
from mesh import generate_mesh
from oracle import initial_channel, vortex, reference, cavity_observations
from case_document import write_case_document

ROOT = Path(__file__).resolve().parents[1]


def field(name, location, axis, quantity, vector=False, unit='m/s'):
    return {'array':name,'quantity':quantity,'location':location,'time_axis':axis,
            'dtype':'float64','kind':'vector' if vector else 'scalar',
            'component_shape':[2] if vector else [1],
            'components':['x','y'] if vector else ['value'],'unit':unit,'value_kind':'point'}


def constant(value,unit):
    return {'value':float(value),'unit':unit}


def generate_case(case, destination, transient):
    directory=destination/'cases'/case.name
    ids,xy,groups=generate_mesh(case,directory)
    times=np.array(case.epochs if transient else [0],dtype=np.float64)
    if transient:
        times*=time_scale(case)
    arrays={'node_ids':ids,'times':times,'condition_times':np.array([0.0])}
    locations={'nodes':{'kind':'mesh','mesh':'main','entity':'node','ids':'node_ids'},
               'domain':{'kind':'mesh','mesh':'main','entity':'node','ids':'node_ids',
                         'physical_group':{'dimension':2,'tag':1}}}
    for side,tag in zip(('left','right','bottom','top'),range(2,6)):
        arrays[side+'_ids']=groups[(1,tag)]
        locations[side]={'kind':'mesh','mesh':'main','entity':'node','ids':side+'_ids',
                         'physical_group':{'dimension':1,'tag':tag}}
    fields={}
    parameters={name:constant(value,unit) for name,value,unit in [
        ('density',case.rho,'kg/m3'),('dynamic_viscosity',case.rho*case.nu,'Pa.s'),
        ('x0',case.origin[0],'m'),('y0',case.origin[1],'m'),
        ('length_x',case.size[0],'m'),('length_y',case.size[1],'m')]}
    conditions=[]
    acceleration=np.zeros((1,len(ids),2))
    acceleration[0,:,case.axis]=case.acceleration
    arrays['acceleration']=acceleration
    fields['acceleration']=field('acceleration','domain','conditions','acceleration',True,'m/s2')
    conditions.append({'role':'source','variable':'velocity','location':'domain',
                       'operator':'acceleration','data':{'value':{'field':'acceleration'}}})
    if case.family in ('channel','periodic'):
        periodic_axes=(0,1) if case.family=='periodic' else (case.axis,)
        for axis in periodic_axes:
            slave,master=('right','left') if axis==0 else ('top','bottom')
            conditions.append({'role':'boundary','variable':'velocity_pressure','location':slave,
                'operator':'periodic','data':{'master_physical_tag':{
                    'value':int(locations[master]['physical_group']['tag']),'unit':'1'}}})
    else:
        periodic_axes=()
    walls=[s for s in ('left','right','bottom','top')
           if not (s in ('left','right') and 0 in periodic_axes)
           and not (s in ('bottom','top') and 1 in periodic_axes)]
    for side in walls:
        name=side+'_velocity'
        values=np.zeros((1,len(arrays[side+'_ids']),2))
        if case.family=='cavity':
            if side==case.lid:
                coords=xy[np.searchsorted(ids,arrays[side+'_ids'])]
                tangent=0 if side in ('top','bottom') else 1
                interior=(coords[:,tangent]>case.origin[tangent]+1e-10)&(coords[:,tangent]<case.origin[tangent]+case.size[tangent]-1e-10)
                values[0,interior,tangent]=case.lid_sign*case.upper
        else:
            lower=side in ('bottom','left')
            values[0,:,case.axis]=case.lower if lower else case.upper
        arrays[name]=values
        fields[name]=field(name,side,'conditions','velocity',True)
        conditions.append({'role':'boundary','variable':'velocity','location':side,
                           'operator':'dirichlet','data':{'value':{'field':name}}})
    # Pressure is a Lagrange multiplier; fix its spatial mean, not a wall value.
    conditions.append({'role':'boundary','variable':'pressure','location':'domain',
                       'operator':'mean','data':{'value':constant(0,'Pa')}})
    initial=None
    if transient:
        arrays['initial_times']=np.array([0.0])
        if case.family=='periodic':
            initial=vortex(case,xy,[0.0])[0][0]
        else:
            initial=np.zeros((len(ids),2))
            s=(xy[:,1-case.axis]-case.origin[1-case.axis])/case.size[1-case.axis]
            initial[:,case.axis]=initial_channel(case,s)
        arrays['initial_velocity']=initial[None,:,:]
        fields['initial_velocity']=field('initial_velocity','nodes','initial','velocity',True)
        conditions.append({'role':'initial','variable':'velocity','location':'nodes',
                           'operator':'assign','data':{'value':{'field':'initial_velocity'}}})
    if case.family=='cavity':
        vertical,horizontal,*_=cavity_observations(case)
        arrays['vertical_ids']=np.arange(17,dtype=np.int64)
        arrays['horizontal_ids']=np.arange(17,dtype=np.int64)
        arrays['vertical_coordinates']=vertical
        arrays['horizontal_coordinates']=horizontal
        locations['vertical']={'kind':'points','ids':'vertical_ids','coordinates':'vertical_coordinates'}
        locations['horizontal']={'kind':'points','ids':'horizontal_ids','coordinates':'horizontal_coordinates'}
        outputs={'u_centerline':field('u_centerline','vertical','output','velocity_x'),
                 'v_centerline':field('v_centerline','horizontal','output','velocity_y')}
    else:
        outputs={'velocity':field('velocity','nodes','output','velocity',True),
                 'pressure':field('pressure','nodes','output','pressure',unit='Pa')}
    axes={'output':'times','conditions':'condition_times'}
    if transient: axes['initial']='initial_times'
    manifest={'task':destination.name,'spatial_dimension':2,'data_file':'input.npz',
        'geometries':{'rectangle':{'file':'mesh.geo','format':'gmsh-geo'}},
        'meshes':{'main':{'file':'mesh.msh','geometry':'rectangle'}},'locations':locations,
        'time_axes':axes,'fields':fields,'outputs':outputs,
        'physics':{'model':'incompressible_navier_stokes','parameters':parameters},'conditions':conditions}
    np.savez_compressed(directory/'input.npz',**arrays)
    write_json(directory/'problem.json',manifest)
    problem=load_problem(directory/'problem.json')
    values,certificate=reference(case,xy,times,initial)
    refdir=destination/'reference'/case.name
    write_result(refdir/'reference.npz',problem,values)
    record={'case':case.name,'family':case.family,'nodes':len(ids),'triangles':2*case.n**2,
            'recipe':case.__dict__,'output_times_s':times.tolist(),'reference':certificate}
    write_json(refdir/'analytic.json',record)
    return record


def generate(destination=ROOT,transient=False,selected=None):
    destination=Path(destination)
    items=[c for c in cases(transient) if selected is None or c.name in selected]
    records=[generate_case(c,destination,transient) for c in items]
    write_json(destination/'reference/catalog.json',records)
    if selected is None:
        sample_cases=['01-rest','04-start-combined','14-advected-vortex'] if transient else ['01-rest','04-couette-poiseuille']
        config=json.loads((destination/'judge-config.json').read_text(encoding='utf-8'))
        for i,name in enumerate(sample_cases,1):
            sample=destination/'samples'/f'{i:02d}'
            shutil.copytree(destination/'cases'/name,sample/'input',dirs_exist_ok=True)
            (sample/'output').mkdir(parents=True,exist_ok=True)
            target=sample/'output/result.npz'
            ref=destination/'reference'/name/'reference.npz'
            shutil.copyfile(ref,target)
            report=grade_files(sample/'input/problem.json',target,ref,atol=config['atol'],rtol=0)
            if report['score']!=1: raise RuntimeError('Sample grading failed')
            write_json(sample/'verification.json',{'case':name,**report})
    write_case_document(destination,records,transient)
    return len(records)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=ROOT);ap.add_argument('--case',action='append')
    args=ap.parse_args();print('Generated',generate(args.output,False,args.case),'steady cases')
