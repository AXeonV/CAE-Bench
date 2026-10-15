"""CFD 2.1 declaration, geometry, material and public-release contract checks."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import numpy as np

from caeoj.cfd import check_cfd, material_viscosity
from caeoj.grading import grade_files
from caeoj.sdk import (absolute_pressure, boundary_geometry, boundary_integral,
                       condition_values, density_at_pressure, dynamic_viscosity, load_problem,
                       load_result, periodic_face_pairs, sample_field, write_result)
from caeoj.storage import write_hdf5
from caeoj.validation import Problem, read_hdf5, validate_input, write_json

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('cfd_example_generator',ROOT/'src/utils/make_cfd_examples.py')
examples=importlib.util.module_from_spec(spec);spec.loader.exec_module(examples)


def c(value,unit):return {'value':value,'unit':unit}


class CFDContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pool=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.pool.cleanup)
        cls.templates=Path(cls.pool.name)
        for dimension in (2,3):
            for transient in (False,True):
                for family,viscosity,compressible in [('newtonian','newtonian',False),('non_newtonian','carreau_yasuda',False),('compressible','newtonian',True)]:
                    name=f'{dimension}-{transient}-{family}'
                    examples.make_example(cls.templates/name,dimension,transient,viscosity,compressible)

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.copy()

    def copy(self,dimension=2,transient=True,family='newtonian'):
        self.case=self.root/f'{dimension}-{transient}-{family}'
        shutil.copytree(self.templates/self.case.name,self.case,dirs_exist_ok=True)
        self.path=self.case/'problem.json';self.m=json.loads(self.path.read_text());self.arrays=read_hdf5(self.case/'input.h5')

    def save(self):
        write_json(self.path,self.m);write_hdf5(self.case/'input.h5',self.arrays)

    def bad(self):
        self.save();report=validate_input(self.path)
        self.assertFalse(report['valid'],report)
        return {e['code'] for e in report['errors']}

    def boundary(self,name):return next(c for c in self.m['conditions'] if c['role']=='boundary' and c['location']==name)

    def outlet(self):
        self.m['analysis'].pop('pressure_gauge',None)
        self.boundary('x_max').update(operator='pressure_outlet',data={'pressure':c(0.,'Pa'),'backflow':{'option':'forbid'}})

    def input_field(self,name,quantity,location,unit,kind,values,axis='initial',time='constant',space='uniform',extrapolation='forbid'):
        d=self.m['spatial_dimension']
        self.m['fields'][name]={'array':name,'quantity':quantity,'location':location,'time_axis':axis,'dtype':'float64','kind':kind,'component_shape':[d] if kind=='vector' else [1],'components':list('xyz'[:d]) if kind=='vector' else ['value'],'unit':unit,'value_kind':'average','sampling':{'space':space,'time':time,'extrapolation':extrapolation}}
        self.arrays[name]=np.asarray(values,dtype='float64')

    def test_all_twelve_profiles_roundtrip_and_analytic_rest_references(self):
        for path in sorted(self.templates.glob('*/problem.json')):
            with self.subTest(case=path.parent.name):
                p=load_problem(path);ref=load_result(p,path.parent/'reference.h5')
                np.testing.assert_array_equal(ref['velocity'],0.)
                np.testing.assert_array_equal(ref['pressure'],0.)
                np.testing.assert_array_equal(ref['force'],0.)
                np.testing.assert_allclose(ref['density'],density_at_pressure(p,0.))
                self.assertEqual(grade_files(path,path.parent/'reference.h5',path.parent/'reference.h5',atol=0,rtol=0)['score'],1)
                wrong={s['array']:ref[s['array']].copy() for s in p.manifest['outputs'].values()}
                wrong['force'][:]=1.
                write_result(self.root/'wrong.h5',p,wrong)
                self.assertEqual(grade_files(path,self.root/'wrong.h5',path.parent/'reference.h5',atol=0,rtol=0)['score'],0)

    def test_opt_in_is_explicit_and_old_declarations_cannot_conflict(self):
        original=deepcopy(self.m)
        for key in ('contract_version','profile','analysis','materials'):
            self.m=deepcopy(original);self.m.pop(key)
            self.assertIn('E_SCHEMA',self.bad())
        self.m=deepcopy(original);self.m['physics']={'model':'different','parameters':{}}
        self.assertIn('E_CFD',self.bad())

    def test_material_units_missing_extra_parameters_and_positive_ranges(self):
        original=deepcopy(self.m)
        changes=[lambda m:m['materials']['fluid']['density']['parameters']['density'].update(unit='g/cm3'),
                 lambda m:m['materials']['fluid']['viscosity']['parameters'].clear(),
                 lambda m:m['materials']['fluid']['viscosity']['parameters'].update(extra=c(1.,'1')),
                 lambda m:m['materials']['fluid']['density']['parameters']['density'].update(value=-1.)]
        for change in changes:
            self.m=deepcopy(original);change(self.m);self.assertIn('E_CFD',self.bad())

    def test_material_response_values_are_independent_of_case_ids(self):
        self.copy(family='non_newtonian');p=load_problem(self.path)
        g=np.array([0.,.5,2.])
        expected=.01+.99*(1+(2*g)**2)**(-.25)
        np.testing.assert_allclose(dynamic_viscosity(p,g),expected)
        for kind,params,expected in [
            ('newtonian',{'dynamic_viscosity':c(.2,'Pa.s')},[.2,.2,.2]),
            ('cross',{'zero_shear_viscosity':c(2.,'Pa.s'),'infinite_shear_viscosity':c(1.,'Pa.s'),'relaxation_time':c(2.,'s'),'cross_exponent':c(2.,'1')},[2.,1.5,1+1/17]),
            ('power_law',{'reference_viscosity':c(2.,'Pa.s'),'reference_shear_rate':c(1.,'1/s'),'power_index':c(.5,'1'),'minimum_shear_rate':c(.25,'1/s'),'maximum_shear_rate':c(4.,'1/s')},[4.,2/np.sqrt(.5),2/np.sqrt(2.)])]:
            material={'viscosity':{'kind':kind,'parameters':params}}
            np.testing.assert_allclose(material_viscosity(material,g),expected)
        with self.assertRaises(ValueError):dynamic_viscosity(p,[-1.])
        with self.assertRaises(ValueError):dynamic_viscosity(p,[np.nan])

    def test_eos_pressure_reference_and_initial_density(self):
        self.copy(dimension=3,family='compressible');p=load_problem(self.path)
        np.testing.assert_allclose(absolute_pressure(p,[0.,100.]),[101325.,101425.])
        np.testing.assert_allclose(density_at_pressure(p,[0.,100.]),np.array([101325.,101425.])/(287*300))
        self.m['materials']['fluid']['density']={'kind':'linear_barotropic','parameters':{'reference_density':c(1000.,'kg/m3'),'reference_pressure':c(101325.,'Pa'),'sound_speed':c(100.,'m/s')}}
        self.arrays['initial_density'][:]=1000.;self.save();p=load_problem(self.path)
        np.testing.assert_allclose(density_at_pressure(p,100.),1000.01)
        self.arrays['initial_density'][:]=1.
        self.assertIn('E_CFD',self.bad())

    def test_missing_or_conflicting_pressure_constraint(self):
        original=deepcopy(self.m)
        self.m['analysis'].pop('pressure_gauge');self.assertIn('E_CFD',self.bad())
        self.m=deepcopy(original);self.outlet();self.save();load_problem(self.path)
        self.m['analysis']['pressure_gauge']=original['analysis']['pressure_gauge']
        self.assertIn('E_CFD',self.bad())
        self.m=deepcopy(original);self.m['analysis']['pressure'].pop('reference_pressure')
        self.assertIn('E_CFD',self.bad())

    def test_initial_state_required_and_steady_is_not_one_transient_frame(self):
        original=deepcopy(self.m)
        self.m['conditions']=[x for x in self.m['conditions'] if x['role']!='initial']
        self.assertIn('E_CFD',self.bad())
        self.m=deepcopy(original);self.m['analysis']['type']='steady'
        self.assertIn('E_CFD',self.bad())
        self.copy(transient=False);self.arrays['output_times'][0]=1.
        self.assertIn('E_CFD',self.bad())

    def test_boundary_coverage_overlap_and_unknown_physics(self):
        original=deepcopy(self.m)
        self.m['conditions'].pop(0);self.assertIn('E_CFD',self.bad())
        self.m=deepcopy(original);self.m['conditions'].append(deepcopy(self.m['conditions'][0]))
        self.assertIn('E_CFD',self.bad())
        self.m=deepcopy(original);self.boundary('x_min')['operator']='some_solver_specific_patch'
        self.assertIn('E_CFD',self.bad())

    def test_normals_measures_and_integrals_in_2d_and_3d(self):
        for d in (2,3):
            self.copy(dimension=d);p=load_problem(self.path)
            for axis,x in enumerate('xyz'[:d]):
                for side,sign in [('min',-1),('max',1)]:
                    name=x+'_'+side;center,n,measure=boundary_geometry(p,name)
                    expected=np.zeros(d);expected[axis]=sign
                    np.testing.assert_allclose(n,np.broadcast_to(expected,n.shape),atol=1e-14)
                    np.testing.assert_allclose(center[:,axis],0 if side=='min' else 1,atol=1e-14)
                    self.assertAlmostEqual(measure.sum(),1.)
                    values=np.full((2,len(measure),d),3.)
                    np.testing.assert_allclose(boundary_integral(p,name,values),3.)
                    # Reversing every boundary element must not reverse fluid-domain normals.
                    for tag in p.arrays[p.manifest['locations'][name]['ids']]:
                        typ,conn=p.meshes['main']['connectivity'][int(tag)]
                        p.meshes['main']['connectivity'][int(tag)]=(typ,tuple(reversed(conn)))
                    np.testing.assert_allclose(boundary_geometry(p,name)[1],n,atol=1e-14)

    def test_first_order_cell_topologies_have_correct_closed_surface_geometry(self):
        # Independent analytic perimeter/surface targets, including non-simplex cells.
        cases=[
            (2,2,[(0,0),(1,0),(0,1)],[(0,1),(1,2),(2,0)],2+np.sqrt(2)),
            (2,3,[(0,0),(1,0),(1,1),(0,1)],[(0,1),(1,2),(2,3),(3,0)],4.),
            (3,4,[(0,0,0),(1,0,0),(0,1,0),(0,0,1)],[(0,1,2),(0,3,1),(1,3,2),(2,3,0)],(3+np.sqrt(3))/2),
            (3,5,[(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1)],[(0,1,2,3),(4,5,6,7),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],6.),
            (3,6,[(0,0,0),(1,0,0),(0,1,0),(0,0,1),(1,0,1),(0,1,1)],[(0,1,2),(3,4,5),(0,3,4,1),(1,4,5,2),(2,5,3,0)],3+np.sqrt(2)),
            (3,7,[(0,0,0),(1,0,0),(1,1,0),(0,1,0),(.5,.5,1)],[(0,1,2,3),(0,4,1),(1,4,2),(2,4,3),(3,4,0)],1+np.sqrt(5)),
        ]
        for d,typ,coordinates,faces,area in cases:
            with self.subTest(gmsh_type=typ):
                nodes={i+10:np.pad(np.array(x,dtype=float),(0,3-d)) for i,x in enumerate(coordinates)}
                connectivity={1000:(typ,tuple(nodes))};ids=[]
                for i,face in enumerate(faces):
                    tag=2000+i;ids.append(tag)
                    connectivity[tag]=(1 if d==2 else (2 if len(face)==3 else 3),tuple(j+10 for j in face))
                mesh={'elements':{d:{1000}},'connectivity':connectivity,'node_coordinates':nodes,'coordinates':np.array(list(nodes.values()))}
                manifest={'spatial_dimension':d,'locations':{'surface':{'kind':'mesh','mesh':'main','entity':'element','dimension':d-1,'ids':'surface_ids'}}}
                p=Problem(Path('unused'),manifest,{'surface_ids':np.array(ids,dtype='int64')},{'main':mesh})
                centers,normals,measure=boundary_geometry(p,'surface')
                self.assertAlmostEqual(measure.sum(),area)
                np.testing.assert_allclose(np.sum(normals*measure[:,None],axis=0),0.,atol=1e-14)
                np.testing.assert_allclose(boundary_integral(p,'surface',np.ones((1,len(ids),1))),area)
                if typ==7:
                    # A skew planar quad needs its area centroid, not mean(vertices).
                    mesh['node_coordinates'][11]=np.array([2.,0.,0.])
                    center,normal,measure=boundary_geometry(p,'surface')
                    np.testing.assert_allclose(center[0],[7/9,4/9,0.])
                    self.assertAlmostEqual(measure[0],1.5)

    def test_disconnected_fluid_domains_need_a_separate_profile_extension(self):
        from caeoj.mesh_geometry import exterior_facets
        mesh={'elements':{2:{1,2}},'connectivity':{1:(2,(10,11,12)),2:(2,(20,21,22))}}
        with self.assertRaisesRegex(ValueError,'facet-connected'):
            exterior_facets(mesh,2)

    def test_periodic_regions_match_geometry_not_row_numbers(self):
        for side,partner,delta in [('x_min','x_max',1.),('x_max','x_min',-1.)]:
            self.boundary(side).update(operator='periodic',data={'partner':{'location':partner},'translation_x':c(delta,'m'),'translation_y':c(0.,'m')})
        self.save();p=load_problem(self.path)
        pairs=periodic_face_pairs(p,self.boundary('x_min'))
        self.assertEqual({a for a,b in pairs},set(self.arrays['x_min_ids']))
        self.assertEqual({b for a,b in pairs},set(self.arrays['x_max_ids']))
        self.boundary('x_min')['data']['translation_y']['value']=.1
        self.assertIn('E_CFD',self.bad())

    def test_input_sampling_covers_interval_and_helper_honors_declared_interpolation(self):
        count=len(self.arrays['x_min_ids']);self.arrays['drive_times']=np.array([0.,.5,1.]);self.m['time_axes']['drive']='drive_times'
        values=np.zeros((3,count,2));values[1,:,1]=2.;values[2,:,1]=4.
        self.input_field('drive','velocity','x_min','m/s','vector',values,'drive','linear')
        self.boundary('x_min').update(operator='moving_wall',data={'velocity':{'field':'drive'}})
        self.save();p=load_problem(self.path)
        np.testing.assert_allclose(sample_field(p,'drive',.25)[:,1],1.)
        with self.assertRaises(ValueError):sample_field(p,'drive',1.1)
        self.m['fields']['drive']['sampling']['time']='previous';self.save();p=load_problem(self.path)
        np.testing.assert_allclose(sample_field(p,'drive',.5)[:,1],2.)
        np.testing.assert_allclose(sample_field(p,'drive',.49)[:,1],0.)
        self.arrays['drive_times'][-1]=.8;self.assertIn('E_CFD',self.bad())
        self.m['fields']['drive']['sampling']['extrapolation']='hold';self.save();p=load_problem(self.path)
        np.testing.assert_allclose(sample_field(p,'drive',1.)[:,1],4.)
        self.arrays['drive'][:,:,0]=1.;self.assertIn('E_CFD',self.bad())

    def test_flow_rate_units_and_compressible_inlet_state(self):
        self.outlet();self.boundary('x_min').update(operator='flow_rate',data={'rate':c(1.,'m2/s'),'shape':c(1.,'1')})
        self.save();load_problem(self.path)
        self.boundary('x_min')['data']['rate']['unit']='m3/s';self.assertIn('E_CFD',self.bad())
        self.copy(dimension=3,family='compressible');self.outlet()
        n=len(self.arrays['x_min_ids']);v=np.zeros((1,n,3));v[:,:,0]=1.
        self.input_field('inlet_velocity','velocity','x_min','m/s','vector',v)
        self.boundary('x_min').update(operator='velocity',data={'velocity':{'field':'inlet_velocity'}})
        self.assertIn('E_CFD',self.bad())
        self.boundary('x_min')['data']['density']=c(1.,'kg/m3');self.save();load_problem(self.path)

    def test_aggregate_output_does_not_use_fake_probe_or_allow_wrong_units(self):
        self.m['locations']['outlet_total']['source']='not_a_region'
        self.assertIn('E_REFERENCE',self.bad())
        self.m['locations']['outlet_total']['source']='x_max'
        self.m['outputs']['force']['unit']='N'
        self.assertIn('E_CFD',self.bad())

    def test_nodal_boundary_data_reconstructs_exact_entity_averages(self):
        for d in (2,3):
            self.copy(dimension=d);p=load_problem(self.path);mesh=p.meshes['main']
            nodes=sorted({node for tag in self.arrays['x_min_ids'] for node in mesh['connectivity'][int(tag)][1]})
            self.arrays['wall_nodes']=np.array(nodes,dtype='int64')
            self.m['locations']['wall_nodes']={'kind':'mesh','mesh':'main','entity':'node','ids':'wall_nodes'}
            values=np.zeros((1,len(nodes),d));values[0,:,1]=[2*mesh['node_coordinates'][node][1] for node in nodes]
            self.input_field('wall_drive','velocity','wall_nodes','m/s','vector',values,space='piecewise_linear')
            self.m['fields']['wall_drive']['value_kind']='point'
            self.boundary('x_min').update(operator='moving_wall',data={'velocity':{'field':'wall_drive'}})
            self.save();p=load_problem(self.path)
            averaged=condition_values(p,self.boundary('x_min'),'velocity',0.)
            centers,_,_=boundary_geometry(p,'x_min')
            np.testing.assert_allclose(averaged[:,1],2*centers[:,1])
            self.arrays['wall_nodes']=self.arrays['wall_nodes'][:-1]
            self.arrays['wall_drive']=self.arrays['wall_drive'][:,:-1]
            self.assertIn('E_REFERENCE',self.bad())

    def test_time_varying_total_flow_rate_has_one_uniform_value(self):
        self.outlet();n=len(self.arrays['x_min_ids'])
        self.arrays['rate_times']=np.array([0.,1.]);self.m['time_axes']['rate']='rate_times'
        self.input_field('rate','volume_flow','x_min','m2/s','scalar',np.array([np.full((n,1),1.),np.full((n,1),3.)]),axis='rate',time='linear')
        self.boundary('x_min').update(operator='flow_rate',data={'rate':{'field':'rate'},'shape':c(1.,'1')})
        self.save();p=load_problem(self.path)
        np.testing.assert_allclose(condition_values(p,self.boundary('x_min'),'rate',.5),2.)
        self.m['fields']['rate']['sampling']['space']='piecewise_constant'
        self.assertIn('E_CFD',self.bad())

    def test_intensive_fields_cannot_be_disguised_as_integrals(self):
        self.m['outputs']['pressure']['value_kind']='integral'
        self.assertIn('E_CFD',self.bad())
        self.m['outputs']['pressure']['value_kind']='average'
        self.m['fields']['initial_velocity']['value_kind']='integral'
        self.assertIn('E_CFD',self.bad())

    def test_malformed_field_location_reports_errors_instead_of_crashing(self):
        self.m['fields']['initial_velocity']['location']='missing'
        self.assertIn('E_REFERENCE',self.bad())

    def test_missing_sampling_in_boundary_fields_is_a_diagnostic(self):
        n=len(self.arrays['x_min_ids'])
        self.input_field('drive','velocity','x_min','m/s','vector',np.zeros((1,n,2)))
        self.boundary('x_min').update(operator='moving_wall',data={'velocity':{'field':'drive'}})
        self.m['fields']['drive'].pop('sampling')
        self.assertIn('E_CFD',self.bad())
        self.m['fields'].pop('drive');self.arrays.pop('drive')
        self.outlet()
        self.input_field('rate','volume_flow','x_min','m2/s','scalar',np.ones((1,n,1)))
        self.boundary('x_min').update(operator='flow_rate',data={'rate':{'field':'rate'},'shape':c(1.,'1')})
        self.m['fields']['rate'].pop('sampling')
        self.assertIn('E_CFD',self.bad())

    def test_carreau_and_cross_input_profiles_and_parameter_bounds(self):
        self.copy(family='non_newtonian');base=deepcopy(self.m)
        law=self.m['materials']['fluid']['viscosity'];law['kind']='carreau';law['parameters'].pop('transition_index')
        self.save();p=load_problem(self.path)
        np.testing.assert_allclose(dynamic_viscosity(p,0.),1.)
        law['parameters']['power_index']['value']=1.1
        self.assertIn('E_CFD',self.bad())
        self.m=deepcopy(base);law=self.m['materials']['fluid']['viscosity']
        law['kind']='cross';law['parameters'].pop('transition_index');law['parameters'].pop('power_index');law['parameters']['cross_exponent']=c(2.,'1')
        self.save();p=load_problem(self.path)
        np.testing.assert_allclose(dynamic_viscosity(p,.5),.505)
        law['parameters']['infinite_shear_viscosity']['value']=2.
        self.assertIn('E_CFD',self.bad())

    def test_generator_refuses_to_overwrite_existing_input(self):
        before=self.path.read_bytes()
        with self.assertRaises(FileExistsError):examples.make_example(self.case)
        self.assertEqual(self.path.read_bytes(),before)

    def test_public_release_includes_profile_runtime_and_documentation(self):
        root=self.root/'public_project';root.mkdir()
        for name in ('pyproject.toml','LICENSE'):shutil.copy2(ROOT/name,root/name)
        shutil.copytree(ROOT/'docs',root/'docs');shutil.copytree(ROOT/'src/caeoj',root/'src/caeoj')
        task=root/'tasks/cfd-fixture';task.mkdir(parents=True)
        for name,text in [('instruction.md','Uniform rest contract fixture.'),('DATA.md','See docs/CFD-2.1.md.'),('judge-config.json',json.dumps({'atol':0.,'rtol':0.,'timeout_seconds':1}))]:
            (task/name).write_text(text)
        sample=task/'samples/01';shutil.copytree(self.case,sample/'input')
        (sample/'input/reference.h5').unlink();(sample/'output').mkdir();shutil.copyfile(self.case/'reference.h5',sample/'output/result.h5')
        spec=importlib.util.spec_from_file_location('cfd_public_packager',ROOT/'src/utils/publish_dist.py')
        publisher=importlib.util.module_from_spec(spec);spec.loader.exec_module(publisher)
        files,_=publisher.collect_materials('cfd-fixture',root)
        for name,data in files.items():
            destination=self.root/'release'/name;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(data)
        for name in ('cfd.py','mesh_geometry.py'):self.assertIn('src/caeoj/'+name,files)
        self.assertIn('docs/CFD-2.1.md',files)
        code='from pathlib import Path; import caeoj; assert Path(caeoj.__file__).resolve()==Path("src/caeoj/__init__.py").resolve(); from caeoj.sdk import load_problem, dynamic_viscosity; p=load_problem("tasks/cfd-fixture/samples/01/input/problem.json"); assert float(dynamic_viscosity(p,0)) == .01'
        import os
        env={**os.environ,'PYTHONPATH':str(self.root/'release/src')}
        result=subprocess.run([sys.executable,'-c',code],cwd=self.root/'release',env=env,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)


    def test_closed_compressible_steady_requires_physical_mass_inventory(self):
        self.copy(transient=False,family='compressible')
        self.assertTrue(validate_input(self.path)['valid'])
        self.assertGreater(load_problem(self.path).manifest['analysis']['mean_density']['value'],0.)
        original=deepcopy(self.m)
        for mutation in ('missing','unit','negative'):
            self.m=deepcopy(original)
            if mutation=='missing':self.m['analysis'].pop('mean_density')
            elif mutation=='unit':self.m['analysis']['mean_density']['unit']='kg'
            else:self.m['analysis']['mean_density']['value']=-1.
            with self.subTest(mutation=mutation):self.assertIn('E_CFD',self.bad())

    def test_mass_inventory_is_not_an_extra_open_boundary_or_transient_constraint(self):
        self.copy(transient=False,family='compressible')
        self.outlet()
        self.assertIn('E_CFD',self.bad())
        self.m['analysis'].pop('mean_density');self.save()
        self.assertTrue(validate_input(self.path)['valid'])
        self.copy(transient=True,family='compressible')
        self.m['analysis']['mean_density']=c(1.,'kg/m3')
        self.assertIn('E_CFD',self.bad())
        self.copy(transient=False,family='newtonian')
        self.m['analysis']['mean_density']=c(1.,'kg/m3')
        self.assertIn('E_CFD',self.bad())

    def test_linear_response_mass_inventory_positive_pressure_domain(self):
        self.copy(transient=False,family='compressible')
        self.m['materials']['fluid']['density']={'kind':'linear_barotropic','parameters':{
            'reference_density':c(2.,'kg/m3'),'reference_pressure':c(100.,'Pa'),
            'sound_speed':c(10.,'m/s')}}
        self.m['analysis']['mean_density']=c(2.,'kg/m3');self.save()
        self.assertTrue(validate_input(self.path)['valid'])
        # Independent EOS inversion: rho=1 gives p=100+(1-2)*100=0.
        self.m['analysis']['mean_density']['value']=1.
        self.assertIn('E_CFD',self.bad())


if __name__=='__main__':unittest.main()
