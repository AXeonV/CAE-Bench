"""Declaration and tool evidence for solids; no numerical solver validation."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
import h5py
import numpy as np
from solid_fixture import fixture
from caeoj_ext.solid import elastic_constants, models
from caeoj.sdk import load_problem, load_result, write_result
from caeoj.validation import validate_input, validate_output


class SolidContractTests(unittest.TestCase):
    def report(self,slug,mutate):
        with tempfile.TemporaryDirectory() as tmp:
            path,m=fixture(tmp,slug);mutate(m,Path(tmp));path.write_text(json.dumps(m));return validate_input(path)

    def invalid(self,slug,mutate):
        r=self.report(slug,mutate);self.assertFalse(r['valid'],r);return r

    def test_all_models_real_files_roundtrip(self):
        for slug in models():
            with self.subTest(slug=slug),tempfile.TemporaryDirectory() as tmp:
                path,m=fixture(tmp,slug);r=validate_input(path);self.assertTrue(r['valid'],r)
                p=load_problem(path);values={s['array']:np.zeros((len(p.arrays[m['time_axes'][s['time_axis']]]),len(p.arrays[m['locations'][s['location']]['ids']]),*s['component_shape'])) for s in m['outputs'].values()}
                result=Path(tmp)/'result.h5';write_result(result,p,values);read=load_result(p,result)
                for key,x in values.items():np.testing.assert_array_equal(read[key],x)
                # A structure-valid numeric payload is not physical correctness.
                with h5py.File(result,'a') as data:
                    key=m['locations'][next(iter(m['outputs'].values()))['location']]['ids']
                    data[key][...]=data[key][...]+1
                self.assertFalse(validate_output(path,result)['valid'])

    def test_elastic_constants_independent_hand_values(self):
        # E=120 and nu=.2 => mu=50, lambda=100/3.
        lam,mu=elastic_constants(120.,.2);self.assertAlmostEqual(lam,100/3);self.assertEqual(mu,50)
        for e,nu in [(0,.2),(1,.5),(-1,.2),(1,-1)]:
            with self.assertRaises(ValueError):elastic_constants(e,nu)

    def test_physics_parameters_and_model_binding(self):
        slug='elastic-solid-3d'
        for mutate in [lambda m,b:m['physics']['parameters'].pop('young_modulus'),lambda m,b:m['physics']['parameters']['young_modulus'].update(unit='K'),lambda m,b:m['physics']['parameters']['poisson_ratio'].update(value=.5),lambda m,b:m.update(spatial_dimension=2),lambda m,b:m.update(task='plane-stress'),lambda m,b:m['physics'].update(model='solid-unknown-v1')]:
            with self.subTest(mutate=mutate):self.invalid(slug,mutate)
        self.invalid('elastic-modes',lambda m,b:m['physics']['parameters']['mode_count'].update(value=3.0))
        self.invalid('gradient-damage',lambda m,b:m['physics']['parameters']['residual_stiffness'].update(value=1.))

    def test_invalid_condition_reference_role_units_and_sampling(self):
        for mutate in [lambda m,b:m['conditions'][0].update(role='material'),lambda m,b:m['conditions'][0]['data']['value'].update(field='missing'),lambda m,b:m['conditions'][0]['data'].update(unknown={'value':1,'unit':'1'}),lambda m,b:next(iter(m['fields'].values())).update(unit='N'),lambda m,b:next(iter(m['fields'].values())).pop('sampling'),lambda m,b:m['conditions'].append(deepcopy(m['conditions'][0]))]:
            self.invalid('plane-stress',mutate)

    def test_boundary_complete_faces_and_region_coverage(self):
        def isolated(m,b):
            loc=m['locations']['fixed_nodes']
            with h5py.File(b/'input.h5','a') as h:
                h[loc['ids']][...]=np.array([11,23,35,95]) # not a full facet vertex union
        self.invalid('elastic-solid-3d',isolated)
        self.invalid('elastic-solid-3d',lambda m,b:m['conditions'][1].update(location='fixed_nodes'))

    def test_history_full_time_coverage_and_zero_start(self):
        self.invalid('j2-plasticity',lambda m,b:m['physics']['parameters']['end_time'].update(value=0.))
        def truncate(m,b):
            with h5py.File(b/'input.h5','a') as h:h['load_times'][...]=[0.,.5,.9]
        self.invalid('j2-plasticity',truncate)
        def initial_load(m,b):
            s=m['fields']['body_force_value']
            with h5py.File(b/'input.h5','a') as h:h[s['array']][0,...]=1.
        self.invalid('j2-plasticity',initial_load)
        def kink(m,b):
            with h5py.File(b/'input.h5','a') as h:h['payload_displacement_value'][1,...]=1.
        self.invalid('elastic-transient',kink)

    def test_contact_nonpenetration_overlap_and_normal(self):
        self.invalid('frictionless-contact',lambda m,b:m['physics']['parameters']['normal_z'].update(value=2.))
        self.invalid('frictionless-contact',lambda m,b:m['physics']['parameters']['plane_offset'].update(value=.5))
        self.invalid('frictional-contact',lambda m,b:m['physics']['parameters']['friction_coefficient'].update(value=-.1))
        self.invalid('frictionless-contact',lambda m,b:m['conditions'][-1].update(location='boundary'))

    def test_cohesive_pair_geometry_and_material(self):
        self.invalid('cohesive-interface',lambda m,b:m['physics']['parameters']['fracture_energy'].update(value=.01))
        self.invalid('cohesive-interface',lambda m,b:m['conditions'][-1]['data'].update(partner={'location':'minus'}))

    def test_cohesive_normal_direction_and_perpendicularity(self):
        # DATA defines n geometrically from the lower minus body to the upper plus body.
        for nx, ny in [(0., -1.), (1., 0.), (.6, .8)]:
            def change(m,b):
                m['physics']['parameters']['normal_x']['value']=nx
                m['physics']['parameters']['normal_y']['value']=ny
            with self.subTest(normal=(nx,ny)):
                r=self.invalid('cohesive-interface',change)
                self.assertTrue(any('outward from minus' in e['expected'] for e in r['errors']),r)

    def test_cohesive_normal_follows_rotated_geometry(self):
        def rotate(m,b):
            import gmsh
            # Rotate by an angle with sin=.6 and cos=.8; old +y normal becomes (-.6,.8).
            gmsh.initialize([],readConfigFiles=False)
            try:
                gmsh.option.setNumber('General.Terminal',0);gmsh.open(str(b/'mesh.msh'))
                tags,coords,_=gmsh.model.mesh.getNodes()
                for tag,(x,y,z) in zip(tags,coords.reshape(-1,3)):
                    gmsh.model.mesh.setNode(int(tag),[.8*x-.6*y,.6*x+.8*y,z],[])
                gmsh.write(str(b/'mesh.msh'))
            finally:gmsh.finalize()
            m['physics']['parameters']['normal_x']['value']=-.6
            m['physics']['parameters']['normal_y']['value']=.8
        r=self.report('cohesive-interface',rotate);self.assertTrue(r['valid'],r)

    def test_cohesive_traction_checks_both_sides_and_allows_outer_loading(self):
        # Literal traction definition comes from DATA, not the model catalog.
        def traction(m,b,where):
            with h5py.File(b/'input.h5','a') as h:
                count=len(h[m['locations'][where]['ids']])
                values=np.zeros((3,count,2));values[1:,:,1]=np.array([.25,.5])[:,None]
                h.create_dataset('applied_traction',data=values)
            m['fields']['applied']=dict(array='applied_traction',quantity='traction',unit='Pa',
                kind='vector',component_shape=[2],components=['x','y'],dtype='float64',
                location=where,time_axis='loads',value_kind='average',
                sampling=dict(space='piecewise_constant',time='linear',extrapolation='forbid'))
            m['conditions'].append(dict(role='boundary',variable='traction',operator='traction',
                location=where,data={'value':{'field':'applied'}}))
        for side in ('minus','plus'):
            with self.subTest(side=side):
                r=self.invalid('cohesive-interface',lambda m,b:traction(m,b,side))
                self.assertTrue(any('no external interface traction' in e['expected'] for e in r['errors']),r)
        def external(m,b):
            p=load_problem(b/'problem.json');mesh=p.meshes['main']
            tags=[tag for tag in mesh['elements'][1]
                  if all(mesh['node_coordinates'][n][0]==0 for n in mesh['connectivity'][tag][1])]
            with h5py.File(b/'input.h5','a') as h:h.create_dataset('outer_ids',data=np.array(sorted(tags),dtype='int64'))
            m['locations']['outer']=dict(kind='mesh',mesh='main',entity='element',dimension=1,ids='outer_ids')
            traction(m,b,'outer')
        r=self.report('cohesive-interface',external);self.assertTrue(r['valid'],r)

    def test_cohesive_whole_interface_displacement_is_forbidden(self):
        def change(m,b,side):
            p=load_problem(b/'problem.json')
            ids=p.arrays[m['locations'][side]['ids']]
            tags=sorted({n for tag in ids for n in p.meshes['main']['connectivity'][int(tag)][1]})
            with h5py.File(b/'input.h5','a') as h:
                h.create_dataset('interface_nodes',data=np.array(tags,dtype='int64'))
                h.create_dataset('interface_displacement',data=np.zeros((3,len(tags),2)))
            m['locations']['interface_nodes']=dict(kind='mesh',mesh='main',entity='node',ids='interface_nodes')
            spec=deepcopy(m['fields']['displacement_value'])
            spec.update(array='interface_displacement',location='interface_nodes')
            m['fields']['interface_displacement']=spec
            m['conditions'].append(dict(role='boundary',variable='displacement',operator='displacement',
                location='interface_nodes',data={'value':{'field':'interface_displacement'}}))
        for side in ('minus','plus'):
            with self.subTest(side=side):
                r=self.invalid('cohesive-interface',lambda m,b:change(m,b,side))
                self.assertTrue(any('interface/Dirichlet overlap' in e['expected'] for e in r['errors']),r)

    def test_aggregate_source_is_whole_cells_not_boundary_or_subset(self):
        def aggregate(m,b,source):
            m['locations']['extra']=dict(kind='aggregate',source=source,operation='sum',ids='whole_ids')
        r=self.report('elastic-solid-3d',lambda m,b:aggregate(m,b,'cells'))
        self.assertTrue(r['valid'],r)
        self.invalid('elastic-solid-3d',lambda m,b:aggregate(m,b,'boundary'))
        def subset(m,b):
            with h5py.File(b/'input.h5','a') as h:
                h.create_dataset('subset_ids',data=h['cells_ids'][:1])
            m['locations']['subset']=dict(kind='mesh',mesh='main',entity='element',dimension=3,ids='subset_ids')
            aggregate(m,b,'subset')
        self.invalid('elastic-solid-3d',subset)

    def test_fatigue_blocks_terminal_frame_ranges_and_axis(self):
        def mutate_field(name,value):
            def change(m,b):
                with h5py.File(b/'input.h5','a') as h:h['payload_'+name][...]=value
            return change
        self.invalid('stress-life-fatigue',mutate_field('cycle_blocks_amplitude',-1))
        self.invalid('stress-life-fatigue',mutate_field('cycle_blocks_mean',1e8))
        self.invalid('fatigue-crack-growth',mutate_field('initial_length_value',20))
        def last(m,b):
            with h5py.File(b/'input.h5','a') as h:h['payload_cycle_blocks_rate'][-1,...]=1.
        self.invalid('stress-life-fatigue',last)
        self.invalid('stress-life-fatigue',lambda m,b:m['fields']['cycle_blocks_rate']['sampling'].update(time='linear'))

    def test_fatigue_sources_require_block_fields_but_initial_length_allows_constant(self):
        def replace(m,b,operator,key):
            c=next(c for c in m['conditions'] if c['operator']==operator)
            spec=m['fields'].pop(c['data'][key]['field'])
            with h5py.File(b/'input.h5','a') as h:
                value=float(h[spec['array']][0,0,0]);del h[spec['array']]
            c['data'][key]=dict(value=value,unit=spec['unit'])
        # Other source fields still supply a cycle axis, so this catches an individual constant.
        r=self.invalid('stress-life-fatigue',lambda m,b:replace(m,b,'cycle_blocks','amplitude'))
        self.assertTrue(any('cycle-block field reference' in e['expected'] for e in r['errors']),r)
        r=self.report('fatigue-crack-growth',lambda m,b:replace(m,b,'initial_length','value'))
        self.assertTrue(r['valid'],r)

    def test_outputs_quantity_units_spectrum_and_component_limits(self):
        for mutate in [lambda m,b:m['outputs'].pop('observation_stress'),lambda m,b:m['outputs']['observation_stress'].update(unit='K'),lambda m,b:m['outputs']['observation_displacement'].update(value_kind='average'),lambda m,b:m['outputs']['observation_energy'].update(location='whole_mean')]:
            self.invalid('plane-stress',mutate)
        self.invalid('elastic-modes',lambda m,b:m['outputs']['observation_frequency'].update(components=['a','b','c']))
        self.invalid('elastic-modes',lambda m,b:m['physics']['parameters']['mode_count'].update(value=13))

    def test_single_frame_constant_is_explicit_full_interval(self):
        def mutate(m,b):
            # Noninitial constant uses a t0 frame and declares the entire interval.
            s=m['fields']['body_force_value'];s['time_axis']='initial';s['sampling']['time']='constant'
            with h5py.File(b/'input.h5','a') as h:
                values=h[s['array']][0:1].copy();del h[s['array']];h.create_dataset(s['array'],data=values)
        r=self.report('elastic-transient',mutate);self.assertTrue(r['valid'],r)

if __name__=='__main__':unittest.main()
