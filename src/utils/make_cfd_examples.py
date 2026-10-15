"""Create small CFD 2.1 contract examples with an exact uniform-rest reference.

These exercise the I/O profile, not general CFD solver accuracy or task coverage.
"""
import argparse
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import gmsh
import numpy as np
from caeoj.cfd import material_density
from caeoj.storage import write_hdf5
from caeoj.validation import GMSH_LOCK, write_json
from caeoj.sdk import load_problem, write_result


def make_example(destination, dimension=2, transient=False, viscosity='newtonian', compressible=False):
    destination=Path(destination)
    if destination.exists() and any(destination.iterdir()):raise FileExistsError(f'Refusing to overwrite nonempty directory: {destination}')
    destination.mkdir(parents=True,exist_ok=True)
    with GMSH_LOCK:
        owned=not gmsh.isInitialized()
        if owned:gmsh.initialize([],readConfigFiles=False)
        previous=gmsh.model.getCurrent();terminal=gmsh.option.getNumber('General.Terminal')
        model='cfd_example_'+str(id(destination))
        saved_options={key:gmsh.option.getNumber(key) for key in ('Mesh.MshFileVersion','Mesh.Binary')}
        try:
            gmsh.option.setNumber('General.Terminal',0);gmsh.model.add(model)
            if dimension==2:domain=gmsh.model.occ.addRectangle(0,0,0,1,1)
            else:domain=gmsh.model.occ.addBox(0,0,0,1,1,1)
            gmsh.model.occ.synchronize()
            gmsh.model.addPhysicalGroup(dimension,[domain],1)
            faces=gmsh.model.getBoundary([(dimension,domain)],oriented=False)
            regions={}
            for dim,tag in faces:
                center=gmsh.model.occ.getCenterOfMass(dim,tag)
                label=next(('xyz'[axis]+('_min' if center[axis]<.5 else '_max')) for axis in range(dimension) if abs(center[axis])<1e-12 or abs(center[axis]-1)<1e-12)
                group=2+len(regions);gmsh.model.addPhysicalGroup(dim,[tag],group);regions[label]=(group,tag)
            gmsh.model.mesh.setSize(gmsh.model.getEntities(0),.8)
            gmsh.model.mesh.generate(dimension)
            gmsh.option.setNumber('Mesh.MshFileVersion',4.1);gmsh.option.setNumber('Mesh.Binary',0)
            gmsh.write(str(destination/'mesh.msh'))
            cell_ids=np.sort(np.concatenate(gmsh.model.mesh.getElements(dimension,domain)[1])).astype('int64')
            boundaries={label:np.sort(np.concatenate(gmsh.model.mesh.getElements(dimension-1,tag)[1])).astype('int64') for label,(group,tag) in regions.items()}
        finally:
            if owned:gmsh.finalize()
            else:
                gmsh.model.setCurrent(model);gmsh.model.remove()
                if previous:gmsh.model.setCurrent(previous)
                gmsh.option.setNumber('General.Terminal',terminal)
                for key,value in saved_options.items():gmsh.option.setNumber(key,value)
    def const(value,unit):return {'value':value,'unit':unit}
    def field(array,quantity,location,axis,kind,unit,sampling=None,value_kind='average'):
        value={'array':array,'quantity':quantity,'location':location,'time_axis':axis,'dtype':'float64','kind':kind,'component_shape':[dimension] if kind=='vector' else [1], 'components':list('xyz'[:dimension]) if kind=='vector' else ['value'],'unit':unit,'value_kind':value_kind}
        if sampling:value['sampling']=sampling
        return value
    params={'dynamic_viscosity':const(.01,'Pa.s')}
    if viscosity in ('cross','carreau','carreau_yasuda'):
        params={'zero_shear_viscosity':const(1.,'Pa.s'),'infinite_shear_viscosity':const(.01,'Pa.s'),'relaxation_time':const(2.,'s')}
        if viscosity=='cross':params['cross_exponent']=const(2.,'1')
        else:params['power_index']=const(.5,'1')
        if viscosity=='carreau_yasuda':params['transition_index']=const(2.,'1')
    if viscosity=='power_law':params={'reference_viscosity':const(1.,'Pa.s'),'reference_shear_rate':const(1.,'1/s'),'power_index':const(.5,'1'),'minimum_shear_rate':const(.01,'1/s'),'maximum_shear_rate':const(100.,'1/s')}
    if compressible:params['bulk_viscosity']=const(0.,'Pa.s')
    material={'region':'domain','density':{'kind':'isothermal_ideal_gas','parameters':{'specific_gas_constant':const(287.,'J/(kg.K)')}} if compressible else {'kind':'constant','parameters':{'density':const(1000.,'kg/m3')}},'viscosity':{'kind':viscosity,'parameters':params}}
    analysis={'type':'transient' if transient else 'steady','compressibility':'isothermal_compressible' if compressible else 'incompressible','flow_regime':'laminar','temperature':const(300.,'K'),'pressure':{'representation':'gauge','reference_pressure':const(101325.,'Pa')}}
    if transient:analysis['time_interval']={'start':0.,'end':1.}
    if not compressible:analysis['pressure_gauge']={'kind':'mean','location':'domain','value':const(0.,'Pa')}
    arrays={'cell_ids':cell_ids,'initial_times':np.array([0.]),'output_times':np.array([0.,.25,1.]) if transient else np.array([0.]),'aggregate_ids':np.array([1],dtype='int64')}
    locations={'domain':{'kind':'mesh','mesh':'main','entity':'element','dimension':dimension,'ids':'cell_ids','physical_group':{'dimension':dimension,'tag':1}}}
    for label,ids in boundaries.items():
        arrays[label+'_ids']=ids
        locations[label]={'kind':'mesh','mesh':'main','entity':'element','dimension':dimension-1,'ids':label+'_ids','physical_group':{'dimension':dimension-1,'tag':regions[label][0]}}
    locations['outlet_total']={'kind':'aggregate','source':'x_max','ids':'aggregate_ids','operation':'sum'}
    conditions=[{'role':'boundary','variable':'flow','location':label,'operator':'no_slip','data':{}} for label in boundaries]
    inputs={};sampling={'space':'uniform','time':'constant','extrapolation':'forbid'}
    density=float(material_density(material,101325.,300.))
    if compressible and not transient:analysis['mean_density']=const(density,'kg/m3')
    if transient:
        inputs['initial_velocity']=field('initial_velocity','velocity','domain','initial','vector','m/s',sampling)
        arrays['initial_velocity']=np.zeros((1,len(cell_ids),dimension))
        conditions.append({'role':'initial','variable':'velocity','location':'domain','operator':'assign','data':{'value':{'field':'initial_velocity'}}})
        if compressible:
            inputs['initial_density']=field('initial_density','density','domain','initial','scalar','kg/m3',sampling)
            arrays['initial_density']=np.full((1,len(cell_ids),1),density)
            conditions.append({'role':'initial','variable':'density','location':'domain','operator':'assign','data':{'value':{'field':'initial_density'}}})
    # An output-only time axis needs no initial axis for steady problems.
    if not transient:arrays.pop('initial_times')
    outputs={'velocity':field('velocity','velocity','domain','output','vector','m/s'), 'pressure':field('pressure','pressure','domain','output','scalar','Pa'), 'density':field('density','density','domain','output','scalar','kg/m3'), 'force':field('force','force','outlet_total','output','vector','N/m' if dimension==2 else 'N',value_kind='integral')}
    m={'task':f'cfd-contract-{dimension}d-'+analysis['type'],'contract_version':2,'profile':'cfd-2.1','spatial_dimension':dimension,'data_file':'input.h5','geometries':{},'meshes':{'main':{'file':'mesh.msh'}},'locations':locations,'time_axes':{'output':'output_times',**({'initial':'initial_times'} if transient else {})},'fields':inputs,'outputs':outputs,'conditions':conditions,'analysis':analysis,'materials':{'fluid':material}}
    write_json(destination/'problem.json',m);write_hdf5(destination/'input.h5',arrays)
    p=load_problem(destination/'problem.json');t=len(arrays['output_times'])
    write_result(destination/'reference.h5',p,{'velocity':np.zeros((t,len(cell_ids),dimension)), 'pressure':np.zeros((t,len(cell_ids),1)), 'density':np.full((t,len(cell_ids),1),density), 'force':np.zeros((t,1,dimension))})
    return destination/'problem.json'


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=Path('runs/cfd-contract-examples'));args=parser.parse_args()
    cases=[('steady-2d',2,False,'newtonian',False),('transient-3d',3,True,'newtonian',False),('non-newtonian-2d',2,True,'carreau_yasuda',False),('compressible-3d',3,True,'newtonian',True)]
    for name,d,t,v,c in cases:
        print(make_example(args.output/name,d,t,v,c))


if __name__=='__main__':main()
