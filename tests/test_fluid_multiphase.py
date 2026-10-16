"""Temporary protocol fixtures; no benchmark examples or references are authored."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from caeoj.fluid_multiphase import (BASE_PARAMETERS, PARAMETERS, MODELS,
    DISPERSED, THERMAL, OPEN_REQUIRED, QUANTITIES, required_initial, required_outputs,
    multiphase_parameters, multiphase_phase_mass, check_fluid_multiphase)
from caeoj.storage import write_hdf5
from caeoj.validation import check_problem, read_hdf5, write_json

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('multiphase_mesh_fixture',ROOT/'qbank/maintenance/cfd_examples.py')
generator=importlib.util.module_from_spec(spec);spec.loader.exec_module(generator)


def constant(x,unit):return {'value':x,'unit':unit}


def make_fixture(destination, kind='immiscible', dimension=None):
    dimension=dimension or MODELS[kind][0]
    generator.make_example(destination,dimension,True,'newtonian',False)
    path=destination/'problem.json'; m=json.loads(path.read_text()); old=read_hdf5(destination/'input.h5')
    locations={name:loc for name,loc in m['locations'].items() if loc['kind']=='mesh'}
    arrays={loc['ids']:old[loc['ids']] for loc in locations.values()}
    arrays.update(initial_times=np.array([0.]), output_times=np.array([.25,.5,1.]) if kind in OPEN_REQUIRED or kind=='melting-solidification' else np.array([0.,.5,1.]))
    m={k:m[k] for k in ('spatial_dimension','data_file','geometries','meshes')}
    m.update(locations=locations,time_axes={'initial':'initial_times','output':'output_times'},fields={},outputs={},conditions=[])
    values={'time_start':0.,'time_end':1.,'density_a':1000.,'density_b':2.,'viscosity_a':.01,'viscosity_b':.001,'pressure_reference':101325.,
        'contact_angle':1.,'surface_tension':.07,'slip_length':.01,'relaxation_time':.1,'diameter':.001,'packing_fraction':.6,
        'particle_modulus':1.,'heat_capacity_a':1000.,'heat_capacity_b':1000.,'conductivity_a':1.,'conductivity_b':1.,
        'heat_exchange':1.,'mass_exchange':1.,'diffusivity_a':.001,'diffusivity_b':.002,'latent_heat':1000.,'saturation_temperature':350.,
        'interface_mass_coefficient':.1,'evaporation_frequency':1.,'condensation_frequency':1.,'saturation_pressure':100000.,
        'pressure_rate':.001,'nuclei_fraction':.001,'solidus_temperature':300.,'liquidus_temperature':310.,
        'mushy_resistance':100.,'mushy_epsilon':.001}
    m['physics']={'model':'fluid-multiphase-'+kind+'-v1','parameters':{k:constant(values[k],desc[0]) for k,desc in (BASE_PARAMETERS|PARAMETERS[kind]).items()}}
    def field(name,q,axis='initial'):
        unit,knd=QUANTITIES[q]
        return {'array':name,'quantity':q,'location':'domain','time_axis':axis,'dtype':'float64','kind':knd,
            'component_shape':[dimension] if knd=='vector' else [1],
            'components':list('xyz'[:dimension]) if knd=='vector' else ['value'],'unit':unit,'value_kind':'average'}
    n=len(arrays['cell_ids'])
    for q in sorted(required_initial(kind)|{'acceleration'}):
        name='in_'+q; f=field(name,q);f['sampling']={'space':'piecewise_constant','time':'constant','extrapolation':'forbid'}
        m['fields'][name]=f
        v=np.zeros((1,n,dimension if f['kind']=='vector' else 1))
        if q=='alpha':
            if kind in DISPERSED:v[:]=.98
            elif kind=='interphase-exchange':v[:]=.5
            elif kind in {'boiling','cavitation'}:v[:]=.9
            else:v[:,n//2:]=1.
        if q.startswith('temperature'):v[:]=305.
        if q.startswith('concentration'):v[:]=1.
        arrays[name]=v
        m['conditions'].append({'role':'source' if q=='acceleration' else 'initial','variable':q,'location':'domain','operator':'assign','data':{'value':{'field':name}}})
    for location in locations:
        if location=='domain':continue
        if kind in OPEN_REQUIRED and location=='x_max':
            data={'alpha':constant(1.,'1')}
            if kind in THERMAL:data['temperature']=constant(350.,'K')
            op='pressure_reservoir'
        else:
            op='wall';data={'mechanical':{'option':'navier_wetting' if kind=='wetting' else 'no_slip'}}
            if kind in THERMAL:data['thermal']={'option':'adiabatic'}
        m['conditions'].append({'role':'boundary','variable':'flow','location':location,'operator':op,'data':data})
    for q in sorted(required_outputs(kind)):m['outputs'][q]=field(q,q,'output')
    write_json(path,m);write_hdf5(destination/'input.h5',arrays)
    return path,m,arrays


class MultiphaseTests(unittest.TestCase):
    def setUp(self):
        self.pool=tempfile.TemporaryDirectory();self.addCleanup(self.pool.cleanup);self.root=Path(self.pool.name)
    def fixture(self,kind='immiscible',dimension=None):
        self.path,self.m,self.arrays=make_fixture(self.root/('case'+str(len(list(self.root.iterdir())))),kind,dimension)
        return self.path
    def save(self):
        write_json(self.path,self.m);write_hdf5(self.path.parent/'input.h5',self.arrays)
    def bad(self):
        self.save();_,r=check_problem(self.path);self.assertFalse(r['valid'],r)
        self.assertIn('E_FLUID',{e['code'] for e in r['errors']},r)
        return r
    def test_all_models_real_input(self):
        for kind,dimensions in MODELS.items():
            for dimension in dimensions:
                with self.subTest(kind=kind,d=dimension):
                    self.fixture(kind,dimension);p,r=check_problem(self.path);self.assertTrue(r['valid'],r)
                    self.assertEqual(multiphase_parameters(p)['density_a'],1000.)
    def test_independent_mass_expected(self):
        self.fixture('immiscible');p,r=check_problem(self.path);self.assertTrue(r['valid'],r)
        # Independent arithmetic: a volume=.25*2+.75*6=5; rho_a=1000.
        a=np.array([[.25,.75],[1.,0.]])
        np.testing.assert_array_equal(multiphase_phase_mass(p,a,np.array([2.,6.])),[5000.,2000.])
        np.testing.assert_array_equal(multiphase_phase_mass(p,a,np.array([2.,6.]),'b'),[6.,12.])
        with self.assertRaises(ValueError):multiphase_phase_mass(p,a,np.array([-2.,6.]))
        with self.assertRaises(ValueError):multiphase_phase_mass(p,a,np.array([2.,6.,1.]))
    def test_unknown_version_and_profile(self):
        self.fixture();self.m['physics']['model']='fluid-multiphase-unannounced-v1';self.bad()
        self.m['physics']['model']='fluid-multiphase-immiscible-v2';self.bad()
    def test_wrong_units_parameter_set(self):
        self.fixture();self.m['physics']['parameters']['density_a']['unit']='g/cm3';self.bad()
        self.fixture();self.m['physics']['parameters']['secret']=constant(1.,'1');self.bad()
        self.fixture();self.m['physics']['parameters']['density_a']['value']=0.;self.bad()
    def test_missing_or_duplicate_initial(self):
        self.fixture();self.m['conditions'].pop(0);self.bad()
        self.fixture();self.m['conditions'].append(deepcopy(self.m['conditions'][1]));self.bad()
    def test_invalid_alpha_and_absent_flux(self):
        self.fixture();self.arrays['in_alpha'][:]=.5;self.bad()
        self.fixture('coupled-particles');self.arrays['in_alpha'][:]=.5;self.bad()
    def test_missing_boundary_and_overlap(self):
        self.fixture();self.m['conditions'].pop();self.bad()
        self.fixture();self.m['conditions'].append(deepcopy(self.m['conditions'][-1]));self.bad()
    def test_forbid_unknown_condition(self):
        self.fixture();self.m['conditions'][-1]['operator']='do_something';self.bad()
        self.fixture();self.m['conditions'][-1]['data']['unknown']={'option':'yes'};self.bad()
    def test_phase_change_requires_reservoir(self):
        self.fixture('boiling')
        for c in self.m['conditions']:
            if c['operator']=='pressure_reservoir':c.update(operator='wall',data={'mechanical':{'option':'no_slip'},'thermal':{'option':'adiabatic'}})
        self.bad()
    def test_sharp_reservoir_pure_constant_phases(self):
        self.fixture('evaporation-condensation')
        reservoir=next(c for c in self.m['conditions'] if c['operator']=='pressure_reservoir')
        reservoir['data']['alpha']=constant(.5,'1');self.bad()
        reservoir['data']['alpha']=constant(0.,'1');self.save()
        _,r=check_problem(self.path);self.assertTrue(r['valid'],r)
        # Field values may differ by boundary facet, but each is a fixed pure phase.
        location=reservoir['location'];n=len(self.arrays[self.m['locations'][location]['ids']])
        f=deepcopy(self.m['fields']['in_alpha'])
        f.update(array='reservoir_phase',location=location)
        self.m['fields']['reservoir_phase']=f
        self.arrays['reservoir_phase']=np.zeros((1,n,1));self.arrays['reservoir_phase'][:,::2]=1.
        reservoir['data']['alpha']={'field':'reservoir_phase'};self.save()
        _,r=check_problem(self.path);self.assertTrue(r['valid'],r)
        self.arrays['reservoir_phase'][:]=.5;self.bad()
        # Pure endpoints still cannot be interpolated as a sharp boundary label.
        self.arrays['reservoir_times']=np.array([0.,1.]);self.m['time_axes']['reservoir']='reservoir_times'
        f['time_axis']='reservoir';f['sampling']['time']='linear'
        self.arrays['reservoir_phase']=np.stack([np.zeros((n,1)),np.ones((n,1))]);self.bad()
    def test_mixed_reservoir_fraction_remains_supported(self):
        for kind in ('boiling','cavitation'):
            self.fixture(kind)
            reservoir=next(c for c in self.m['conditions'] if c['operator']=='pressure_reservoir')
            reservoir['data']['alpha']=constant(.5,'1');self.save()
            _,r=check_problem(self.path);self.assertTrue(r['valid'],r)
    def test_melting_temperature_order(self):
        self.fixture('melting-solidification');self.m['physics']['parameters']['liquidus_temperature']['value']=290.;self.bad()
    def test_source_coverage_and_sampling(self):
        self.fixture();f=self.m['fields']['in_acceleration'];f['sampling']['time']='linear';self.bad()
        self.fixture();self.m['fields']['in_acceleration']['sampling']['extrapolation']='hold';self.bad()
        self.fixture();self.m['fields']['in_acceleration'].pop('sampling');self.bad()
    def test_output_units_and_interval(self):
        self.fixture();self.m['outputs']['pressure']['unit']='1';self.bad()
        self.fixture();self.arrays['output_times'][-1]=2.;self.bad()
    def test_legacy_not_reinterpreted(self):
        self.fixture();p,r=check_problem(self.path);self.assertTrue(r['valid'],r)
        p.manifest['physics']['model']='legacy_model';p.manifest['physics']['parameters']={}
        e=[];check_fluid_multiphase(p,e);self.assertEqual(e,[])
    def test_heat_exchange_solute_negative(self):
        self.fixture('interphase-exchange');self.arrays['in_concentration_a'][:]=-1.;self.bad()
    def test_wetting_angle_and_packing(self):
        self.fixture('wetting');self.m['physics']['parameters']['contact_angle']['value']=np.pi;self.bad()
        self.fixture('dense-dispersed');self.m['physics']['parameters']['packing_fraction']['value']=1.;self.bad()

if __name__=='__main__':unittest.main()
