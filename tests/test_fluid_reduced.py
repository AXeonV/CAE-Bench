"""Temporary real protocol fixtures; never task examples or references."""
import copy
import json
import math
from pathlib import Path
import tempfile
import unittest

import gmsh
import h5py
import numpy as np

from caeoj.fluid_reduced import (MODELS, UNITS, VECTORS, TENSORS, boundary_rules,
                                reduced_viscosity, maxwellian, reduced_time_derivative, layer_characteristic_speeds)
from caeoj.validation import validate_input
from caeoj.sdk import load_problem, write_result, load_result


def make_fixture(base, model):
    """One triangle/tetrahedron; all physical data explicitly declared."""
    cfg=MODELS[model]; d=cfg['dimension'];base=Path(base)
    gmsh.initialize([],readConfigFiles=False)
    try:
        gmsh.option.setNumber('General.Terminal',0);gmsh.model.add('fixture')
        node_tags=[11,23,37]+([51] if d==3 else [])
        coordinates=[[0,0,0],[1,0,0],[0,1,0]]+([[0,0,1]] if d==3 else [])
        cell=gmsh.model.addDiscreteEntity(d)
        gmsh.model.mesh.addNodes(d,cell,node_tags,np.asarray(coordinates).ravel())
        gmsh.model.mesh.addElementsByType(cell,2 if d==2 else 4,[101],node_tags)
        faces=[[11,23],[23,37],[37,11]] if d==2 else [[11,23,37],[11,51,23],[23,51,37],[37,51,11]]
        for tag,face in enumerate(faces,201):
            entity=gmsh.model.addDiscreteEntity(d-1)
            gmsh.model.mesh.addElementsByType(entity,1 if d==2 else 2,[tag],face)
        gmsh.option.setNumber('Mesh.MshFileVersion',4.1);gmsh.option.setNumber('Mesh.Binary',0)
        gmsh.write(str(base/'mesh.msh'))
    finally:gmsh.finalize()
    arrays={'nodes':np.array(node_tags,dtype=np.int64),'boundaries':np.arange(201,201+len(faces),dtype=np.int64),
            'cells':np.array([101],dtype=np.int64),'observations':np.array([0],dtype=np.int64),
            'steady':np.array([0.]),'initial':np.array([0.]),'times':np.array([0.,0.5,1.])}
    locs={'domain':dict(kind='mesh',mesh='main',entity='node',ids='nodes'),
          'boundary':dict(kind='mesh',mesh='main',entity='element',dimension=d-1,ids='boundaries'),
          'cells':dict(kind='mesh',mesh='main',entity='element',dimension=d,ids='cells'),
          'integral':dict(kind='aggregate',source='cells',ids='observations',operation='sum')}
    if cfg['family'].startswith('kinetic'):
        arrays['boundaries']=np.array([201],dtype=np.int64)
        arrays['wall_ids']=np.arange(202,201+len(faces),dtype=np.int64)
        locs['wall']=dict(kind='mesh',mesh='main',entity='element',dimension=d-1,ids='wall_ids')
    params={k:dict(value=1.,unit=u) for k,u in cfg['parameters'].items()}
    for key,value in {'start_time':0.,'end_time':1.,'reference_pressure':100000.,'cavitation_pressure':100.,
                      'temperature_jump_length':0.,'reference_temperature':300.,'lower_density':1000.,
                      'upper_density':900.,'molecule_mass':6.6e-26,'molecule_diameter':3.4e-10}.items():
        if key in params:params[key]['value']=value
    m=dict(task='protocol_fixture',spatial_dimension=d,data_file='input.h5',geometries={},
           meshes={'main':{'file':'mesh.msh'}},locations=locs,
           time_axes={'steady':'steady','initial':'initial','times':'times'},fields={},outputs={},
           physics={'model':model,'parameters':params},conditions=[])
    def field(name,unit,kind,bound,location,initial=False,quantity=None):
        axis='initial' if initial else 'times' if cfg['transient'] else 'steady'
        n=len(arrays[locs[location]['ids']])
        shape=[d,d] if kind=='tensor' else [d] if kind=='vector' else [1]
        labels=[a+b for a in 'xyz'[:d] for b in 'xyz'[:d]] if kind=='tensor' else list('xyz'[:d]) if kind=='vector' else ['value']
        values=np.ones((len(arrays[axis]),n,*shape))
        if kind=='vector':values[:]=0
        if kind=='tensor':values[:]=np.eye(d)
        if unit=='K':values[:]=300.
        if unit=='Pa':values[:]=100000.
        m['fields'][name]=dict(array=name,quantity=quantity or name,location=location,time_axis=axis,
            dtype='float64',kind=kind,component_shape=shape,components=labels,unit=unit,
            value_kind='point' if location=='domain' else 'average',
            sampling=dict(space='piecewise_linear' if location=='domain' else 'piecewise_constant',
                          time='linear' if cfg['transient'] and not initial else 'constant',extrapolation='forbid'))
        arrays[name]=values
        return {'field':name}
    for var,(role,op,u,kind,bound) in cfg['domain'].items():
        ref=field('domain_'+var,u,kind,bound,'domain',role=='initial',var)
        m['conditions'].append(dict(role=role,variable=var,operator=op,location='domain',data={'value':ref}))
    rules=boundary_rules(cfg)
    # Open reservoir/outlet fixes gas mass/pressure and steady water amount.
    op=next((x for x in ('film_pressure','water_reservoir','layer_wall','gas_reservoir','slip_outlet','velocity_wall') if x in rules))
    var,reqs=rules[op];data={}
    for key,req in reqs.items():
        if req[0]=='option':data[key]={'option':req[1]}
        else:data[key]=field('boundary_'+key,req[1],req[0],req[2],'boundary',quantity=var if key=='value' else key)
    m['conditions'].append(dict(role='boundary',variable=var,operator=op,location='boundary',data=data))
    if cfg['family'].startswith('kinetic'):
        data={'velocity':field('wall_velocity','m/s','vector','finite','wall',quantity='velocity'),
              'temperature':{'value':300.,'unit':'K'},'accommodation':{'value':1.,'unit':'1'}}
        m['conditions'].append(dict(role='boundary',variable='gas',operator='gas_wall',location='wall',data=data))
    if cfg['family'] in ('thermal_carreau','thermal_oldroyd'):
        data={'value':field('boundary_temperature','K','scalar','positive','boundary',quantity='temperature')}
        m['conditions'].append(dict(role='boundary',variable='temperature',operator='temperature_wall',location='boundary',data=data))
    for q in cfg['outputs']:
        kind='vector' if q in VECTORS else 'tensor' if q in TENSORS else 'scalar'
        shape=[d,d] if kind=='tensor' else [d] if kind=='vector' else [1]
        labels=[a+b for a in 'xyz'[:d] for b in 'xyz'[:d]] if kind=='tensor' else list('xyz'[:d]) if kind=='vector' else ['value']
        aggregate=q in ('load','water_volume');boundary=q in ('traction','heat_flux')
        m['outputs']['result_'+q]=dict(array='result_'+q,quantity=q,location='integral' if aggregate else ('wall' if cfg['family'].startswith('kinetic') else 'boundary') if boundary else 'domain',
            time_axis='times' if cfg['transient'] else 'steady',dtype='float64',kind=kind,
            component_shape=shape,components=labels,unit=UNITS[q],value_kind='integral' if aggregate else 'average' if boundary else 'point')
    # HDF5 only contains actually referenced support/time/field arrays.
    used=set(m['time_axes'].values())|{l['ids'] for l in locs.values()}|{f['array'] for f in m['fields'].values()}
    with h5py.File(base/'input.h5','w') as f:
        for key in used:f.create_dataset(key,data=arrays[key])
    path=base/'problem.json';path.write_text(json.dumps(m));return path,m


class ReducedContractTests(unittest.TestCase):
    def valid(self, model, mutate=None):
        with tempfile.TemporaryDirectory() as temp:
            path,m=make_fixture(temp,model)
            if mutate:mutate(m);path.write_text(json.dumps(m))
            report=validate_input(path)
            return report

    def test_each_model_real_protocol(self):
        for model in MODELS:
            with self.subTest(model=model):
                report=self.valid(model)
                self.assertTrue(report['valid'],report)

    def test_output_roundtrip_each_model(self):
        for model in MODELS:
            with self.subTest(model=model),tempfile.TemporaryDirectory() as temp:
                path,m=make_fixture(temp,model);problem=load_problem(path);out={}
                for spec in m['outputs'].values():
                    nt=len(problem.arrays[m['time_axes'][spec['time_axis']]])
                    n=len(problem.arrays[m['locations'][spec['location']]['ids']])
                    out[spec['array']]=np.zeros((nt,n,*spec['component_shape']),dtype=np.float64)
                dest=Path(temp)/'result.h5';write_result(dest,problem,out);loaded=load_result(problem,dest)
                for key,a in out.items():np.testing.assert_array_equal(loaded[key],a)

    def test_invalid_cavitation_wall_and_kinetic_support(self):
        with tempfile.TemporaryDirectory() as temp:
            path,m=make_fixture(temp,'fluid-reduced-liquid-lubrication-v1')
            with h5py.File(Path(temp)/'input.h5','a') as data:data['boundary_fraction'][...]=0.5
            self.assertFalse(validate_input(path)['valid'])
        with tempfile.TemporaryDirectory() as temp:
            path,m=make_fixture(temp,'fluid-reduced-transition-gas-v1')
            with h5py.File(Path(temp)/'input.h5','a') as data:data['wall_velocity'][...]=1
            self.assertFalse(validate_input(path)['valid'])
        self.assertFalse(self.valid('fluid-reduced-transition-gas-v1',lambda m:m['outputs']['result_traction'].update(location='boundary'))['valid'])

    def test_time_derivative_one_sided_contract(self):
        # Slopes are hand-computed 2 and 3 on [0,1] and [1,3].
        t=[0.,1.,3.];v=np.array([0.,2.,8.])
        for time,expected in [(0.,2.),(.5,2.),(1.,3.),(2.,3.),(3.,3.)]:
            self.assertEqual(float(reduced_time_derivative(t,v,time)),expected)
        np.testing.assert_array_equal(reduced_time_derivative([4.],np.array([[2.,7.]]),10.),[0.,0.])
        with self.assertRaises(ValueError):reduced_time_derivative(t,v,4.)

    def test_two_layer_explicit_supercritical_inlet(self):
        from caeoj.mesh_geometry import boundary_geometry
        model='fluid-reduced-two-layer-v1'
        with tempfile.TemporaryDirectory() as temp:
            path,m=make_fixture(temp,model);p=load_problem(path)
            _,normals,_=boundary_geometry(p,'boundary')
            data={};n=len(normals)
            for layer in ('lower','upper'):
                data[layer+'_depth']={'value':1.,'unit':'m'}
                name=layer+'_inflow'
                m['fields'][name]=dict(array=name,quantity=layer+'_velocity',location='boundary',
                    time_axis='times',dtype='float64',kind='vector',component_shape=[2],components=['x','y'],
                    unit='m/s',value_kind='average',sampling=dict(space='piecewise_constant',time='linear',extrapolation='forbid'))
                data[layer+'_velocity']={'field':name}
                with h5py.File(Path(temp)/'input.h5','a') as h:h.create_dataset(name,data=np.broadcast_to(-20*normals,(3,n,2)))
            m['conditions'][-1].update(operator='layer_inlet',data=data)
            path.write_text(json.dumps(m));self.assertTrue(validate_input(path)['valid'],validate_input(path))
            with h5py.File(Path(temp)/'input.h5','a') as h:
                h['lower_inflow'][...]=0;h['upper_inflow'][...]=0
            report=validate_input(path);self.assertFalse(report['valid'])
            self.assertIn('E_FLUID',{e['code'] for e in report['errors']})
        self.assertTrue(self.valid(model,lambda m:m['conditions'][-1].update(operator='layer_outflow',data={'mode':{'option':'supercritical_outflow'}}))['valid'])
        self.assertFalse(self.valid(model,lambda m:m['conditions'][-1].update(operator='layer_reservoir'))['valid'])
        # Equal velocities: analytic wave speeds U +/- sqrt(g*(1 +/- sqrt(r))) for h=1.
        wave=layer_characteristic_speeds(1,1,-20,-20,1,.81)
        expected=[-20-math.sqrt(1+.9),-20+math.sqrt(1+.9),-20-math.sqrt(1-.9),-20+math.sqrt(1-.9),-20,-20]
        np.testing.assert_allclose(np.sort(wave),np.sort(expected),rtol=1e-12)

    def test_invalid_model_units_parameters_and_dimensions(self):
        model='fluid-reduced-viscoelastic-transient-v1'
        mutations=[lambda m:m['physics'].update(model='fluid-reduced-unknown-v1'),
                   lambda m:m['physics']['parameters'].pop('start_time'),
                   lambda m:m['physics']['parameters']['density'].update(unit='Pa'),
                   lambda m:m['physics']['parameters']['density'].update(value=-1),
                   lambda m:m['physics']['parameters'].update(unowned={'value':1,'unit':'1'}),
                   lambda m:m.update(spatial_dimension=3)]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                self.assertFalse(self.valid(model,mutate)['valid'])

    def test_bad_initial_quantity_sampling_and_coverage(self):
        model='fluid-reduced-viscoelastic-transient-v1'
        mutations=[lambda m:m['fields']['domain_conformation'].update(quantity='banana'),
                   lambda m:m['fields']['domain_conformation']['sampling'].update(space='uniform'),
                   lambda m:m['conditions'].pop(),
                   lambda m:m['conditions'].append(copy.deepcopy(m['conditions'][-1])),
                   lambda m:m['outputs']['result_conformation'].update(unit='Pa')]
        for mutate in mutations:
            self.assertFalse(self.valid(model,mutate)['valid'])

    def test_wrong_kind_cannot_crash_spd(self):
        # A generic-valid scalar array cannot be interpreted as a matrix by the domain checker.
        model='fluid-reduced-viscoelastic-transient-v1'
        with tempfile.TemporaryDirectory() as temp:
            path,m=make_fixture(temp,model);f=m['fields']['domain_conformation']
            f.update(kind='scalar',component_shape=[1],components=['value'])
            with h5py.File(Path(temp)/'input.h5','a') as data:
                del data[f['array']];data.create_dataset(f['array'],data=np.ones((1,3,1)))
            path.write_text(json.dumps(m));result=validate_input(path)
            self.assertFalse(result['valid']);self.assertIn('E_FLUID',{e['code'] for e in result['errors']})

    def test_negative_conformation_and_structure(self):
        for model,name,value in [('fluid-reduced-viscoelastic-transient-v1','domain_conformation',-1),
                                 ('fluid-reduced-thixotropic-transient-v1','domain_structure',2)]:
            with tempfile.TemporaryDirectory() as temp:
                path,m=make_fixture(temp,model)
                with h5py.File(Path(temp)/'input.h5','a') as data:data[name][...]=value
                self.assertFalse(validate_input(path)['valid'])

    def test_material_independent_expected(self):
        # n=1 gives constant zero-shear viscosity for every rate; hand-computed exp shift.
        p={'zero_viscosity':10.,'infinite_viscosity':2.,'time_constant':3.,'power_index':1.,
           'temperature_coefficient':math.log(2)/10,'reference_temperature':300.}
        np.testing.assert_allclose(reduced_viscosity('fluid-reduced-thermal-generalized-newtonian-v1',p,[0,5],310),[5,5])
        self.assertEqual(float(reduced_viscosity('fluid-reduced-thixotropic-transient-v1',
                         {'base_viscosity':2.,'structure_viscosity':8.},0,structure=.25)),4.)
        with self.assertRaises(ValueError):reduced_viscosity('fluid-reduced-thixotropic-transient-v1',
                         {'base_viscosity':2.,'structure_viscosity':8.},0,structure=2)

    def test_maxwellian_independent_ratio(self):
        m=6.6e-26;T=300.;speed=math.sqrt(2*1.380649e-23*T/m)
        f=maxwellian(1e20,[0,0,0],T,m,np.array([[0,0,0],[speed,0,0]]))
        self.assertAlmostEqual(f[1]/f[0],math.exp(-1),places=14)
        expected=1e20*(m/(2*math.pi*1.380649e-23*T))**1.5
        self.assertAlmostEqual(f[0]/expected,1,places=14)

if __name__=='__main__':unittest.main()
