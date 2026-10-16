"""Minimal temporary protocol fixtures; these are not qbank cases or CFD evidence."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import tempfile
import unittest

import numpy as np

from caeoj.fluid_energy import (MODELS, check_fluid_energy, fluid_energy_condition_values,
                                fluid_energy_properties, fluid_energy_statistics, parameter_units)
from caeoj.sdk import load_problem, write_result, load_result
from caeoj.storage import write_hdf5
from caeoj.validation import read_hdf5, write_json, validate_input

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('energy_fixture_mesh', ROOT/'qbank/maintenance/cfd_examples.py')
meshgen = importlib.util.module_from_spec(spec); spec.loader.exec_module(meshgen)


def const(v, u): return {'value': v, 'unit': u}


def fixture(path, model, d=3):
    family, energy, method, mode = MODELS[model]
    meshgen.make_example(path, d, False)
    import json
    old = json.loads((path/'problem.json').read_text()); olda = read_hdf5(path/'input.h5')
    locations = {k:v for k,v in old['locations'].items() if v['kind'] == 'mesh'}
    arrays = {v['ids']: olda[v['ids']] for v in locations.values()}
    arrays.update(tzero=np.array([0.]), tout=np.array([0.]) if mode == 'steady' else np.array([1.]) if mode == 'statistics' else np.array([0., .5, 1.]))
    def field(name, q, loc, unit, kind, axis='zero'):
        return dict(array=name, quantity=q, location=loc, time_axis=axis, dtype='float64', kind=kind,
                    component_shape=[d] if kind=='vector' else [d,d] if kind=='tensor' else [1],
                    components=list('xyz'[:d]) if kind=='vector' else [x+y for x in 'xyz'[:d] for y in 'xyz'[:d]] if kind=='tensor' else ['value'],
                    unit=unit, value_kind='average')
    values=dict(reference_temperature=300.,minimum_temperature=200.,maximum_temperature=400.,density=1000.,reference_pressure=101325.,specific_gas_constant=287.,mean_density=1.,heat_capacity_ratio=1.4,isentropic_reference_density=1.,reference_viscosity=.01,viscosity_exponent=.5,bulk_viscosity=0.,reference_conductivity=.6,conductivity_exponent=.5,heat_capacity=4200.,thermal_expansion=.0005,time_start=0.,time_end=1.,statistics_start=.5,statistics_end=1.,statistics_step=.25)
    m=dict(task='fixture_not_a_qbank_case',spatial_dimension=d,data_file='input.h5',geometries={},meshes=old['meshes'],locations=locations,time_axes={'zero':'tzero','output':'tout'},fields={},outputs={},physics={'model':model,'parameters':{k:const(values[k],u) for k,u in parameter_units(model).items()}},conditions=[])
    def add_input(name,q,loc,unit,kind,value):
        m['fields'][name]=field(name,q,loc,unit,kind)
        m['fields'][name]['sampling']=dict(space='piecewise_constant',time='constant',extrapolation='forbid')
        shape=m['fields'][name]['component_shape'];arrays[name]=np.full((1,len(arrays[locations[loc]['ids']]),*shape),value,dtype='float64')
        return {'field':name}
    for loc in locations:
        if loc=='domain':continue
        if family=='inviscid':op='slip_wall';data={'impermeable':{'option':'yes'}}
        else:op='moving_wall';data={'value':add_input('wall_'+loc,'velocity',loc,'m/s','vector',0.)}
        m['conditions'].append(dict(role='boundary',variable='velocity',location=loc,operator=op,data=data))
        if energy and family!='inviscid':m['conditions'].append(dict(role='boundary',variable='temperature',location=loc,operator='temperature',data={'value':const(300.,'K')}))
    obs={'velocity':('m/s','vector'),'pressure':('Pa','scalar')}
    if energy:obs['temperature']=('K','scalar')
    if family in ('inviscid','compressible','isothermal'):obs['density']=('kg/m3','scalar')
    if mode!='steady':
        initial={k:v for k,v in obs.items() if k!='pressure'}
        if method=='urans':initial.update(turbulent_kinetic_energy=('m2/s2','scalar'),turbulence_length_scale=('m','scalar'))
        for q,(unit,kind) in initial.items():
            v=300. if q=='temperature' else 1. if q in ('density','turbulence_length_scale') else 0.
            val=add_input('initial_'+q,q,'domain',unit,kind,v) if kind=='vector' else const(v,unit)
            m['conditions'].append(dict(role='initial',variable=q,location='domain',operator='assign',data={'value':val}))
    if mode=='statistics':
        obs['velocity_covariance']=('m2/s2','tensor')
        if energy:obs.update(temperature_variance=('K2','scalar'),turbulent_heat_flux=('K.m/s','vector'))
    for q,(unit,kind) in obs.items():m['outputs'][q]=field('result_'+q,q,'domain',unit,kind,'output')
    write_json(path/'problem.json',m);write_hdf5(path/'input.h5',arrays)
    return m,arrays


class FluidEnergyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.temp.cleanup);cls.base=Path(cls.temp.name)
        cls.models={}
        for model in MODELS:
            path=cls.base/model;fixture(path,model);cls.models[model]=path

    def setUp(self):
        self.problem=deepcopy(load_problem(self.models['fluid-energy-lowmach-laminar-transient-v1']/'problem.json'))

    def errors(self,p=None):
        errors=[];check_fluid_energy(p or self.problem,errors);return errors

    def test_all_models_and_all_2d_variants_roundtrip(self):
        for model,path in self.models.items():
            with self.subTest(model=model):
                p=load_problem(path/'problem.json');self.assertEqual(self.errors(p),[])
                data={s['array']:np.zeros((len(p.arrays[p.manifest['time_axes'][s['time_axis']]]),len(p.arrays[p.manifest['locations'][s['location']]['ids']]),*s['component_shape'])) for s in p.manifest['outputs'].values()}
                write_result(path/'roundtrip.h5',p,data)
                read=load_result(p,path/'roundtrip.h5')
                for key in data:np.testing.assert_array_equal(read[key],data[key])
        for model,(family,energy,method,mode) in MODELS.items():
            if method=='laminar' or (family=='incompressible' and method=='rans'):
                path=self.base/('2d-'+model);fixture(path,model,2)
                self.assertTrue(validate_input(path/'problem.json')['valid'])

    def test_invalid_parameters_unknown_model_and_profile_mix(self):
        for mutate in [lambda m:m['physics']['parameters']['reference_viscosity'].update(value=0.),lambda m:m['physics']['parameters']['heat_capacity'].update(unit='1'),lambda m:m['physics']['parameters'].pop('density'),lambda m:m['physics'].update(model='fluid-energy-unknown-v1'),lambda m:m.update(profile='cfd-2.1')]:
            p=deepcopy(self.problem);mutate(p.manifest);self.assertTrue(self.errors(p))
        p=deepcopy(load_problem(self.models['fluid-energy-lowmach-resolved-statistics-v1']/'problem.json'))
        p.manifest['physics']['parameters']['statistics_step']['value']=0.
        self.assertTrue(self.errors(p))
        for name in ('reference_conductivity','reference_temperature','minimum_temperature'):
            p=deepcopy(self.problem);p.manifest['physics']['parameters'][name]['value']=0.
            self.assertTrue(self.errors(p))

    def test_boundary_coverage_conflicts_initial_and_units(self):
        original=deepcopy(self.problem)
        for mutation in ('missing','duplicate','initial','unit','sampling','normal','time','output','extra','temperature','option'):
            p=deepcopy(original);m=p.manifest
            if mutation=='missing':m['conditions'].pop(0)
            elif mutation=='duplicate':m['conditions'].append(deepcopy(m['conditions'][0]))
            elif mutation=='initial':m['conditions']=[c for c in m['conditions'] if c['role']!='initial']
            elif mutation=='unit':next(iter(m['fields'].values()))['unit']='cm/s'
            elif mutation=='sampling':next(iter(m['fields'].values())).pop('sampling')
            elif mutation=='normal':
                for f in m['fields'].values():
                    if f['quantity']=='velocity' and f['location']!='domain':p.arrays[f['array']][:]=1.
            elif mutation=='time':p.arrays['tout']=np.array([2.])
            elif mutation=='output':m['outputs']['pressure']['quantity']='kinematic_pressure'
            elif mutation=='extra':m['conditions'][0]['data']['extra']=const(1.,'1')
            elif mutation=='temperature':next(c for c in m['conditions'] if c['variable']=='temperature')['data']['value']=const(100.,'K')
            elif mutation=='option':m['conditions'][0]['data']['value']={'option':'yes'}
            with self.subTest(mutation=mutation):self.assertTrue(self.errors(p))

    def test_properties_independent_hand_calculations(self):
        # Power-law values independently chosen: sqrt(4)=2.
        p=self.problem
        props=fluid_energy_properties(p,300.)
        self.assertEqual(float(props['density']),1000.);self.assertEqual(float(props['dynamic_viscosity']),.01)
        p.manifest['physics']['parameters']['maximum_temperature']['value']=1500.
        props=fluid_energy_properties(p,1200.)
        self.assertAlmostEqual(float(props['dynamic_viscosity']),.02);self.assertAlmostEqual(float(props['conductivity']),1.2)
        gas=load_problem(self.models['fluid-energy-compressible-laminar-transient-v1']/'problem.json')
        props=fluid_energy_properties(gas,300.,86100.)
        self.assertAlmostEqual(float(props['density']),1.);self.assertAlmostEqual(float(props['heat_capacity']),1004.5)
        with self.assertRaises(ValueError):fluid_energy_properties(gas,300.,-1.)
        with self.assertRaises(ValueError):fluid_energy_properties(gas,10.,86100.)

    def test_linear_condition_and_statistics_independent_expected(self):
        p=self.problem;condition=next(c for c in p.manifest['conditions'] if c['variable']=='temperature')
        loc=condition['location'];n=len(p.arrays[p.manifest['locations'][loc]['ids']])
        p.manifest['fields']['signal']={'array':'signal','location':loc,'time_axis':'signal'}
        p.manifest['time_axes']['signal']='signal_times';p.arrays['signal_times']=np.array([0.,.2,1.]);p.arrays['signal']=np.array([np.full((n,1),v) for v in (10.,20.,60.)])
        condition['data']['value']={'field':'signal'}
        np.testing.assert_allclose(fluid_energy_condition_values(p,condition,'value',.6),40.)
        with self.assertRaises(ValueError):fluid_energy_condition_values(p,condition,'value',2.)
        u=np.array([[[1.,2.,0.]],[[3.,4.,0.]],[[5.,6.,0.]]]);t=np.array([[[10.]],[[20.]],[[30.]]])
        stats=fluid_energy_statistics([0.,1.,2.],u,t)
        np.testing.assert_allclose(stats['velocity'],[[3.,4.,0.]])
        np.testing.assert_allclose(stats['velocity_covariance'],[[[8/3,8/3,0],[8/3,8/3,0],[0,0,0]]])
        np.testing.assert_allclose(stats['temperature_variance'],[[200/3]])
        np.testing.assert_allclose(stats['turbulent_heat_flux'],[[40/3,40/3,0.]])
        with self.assertRaises(ValueError):fluid_energy_statistics([0.,1.,3.],u)


if __name__=='__main__':unittest.main()
