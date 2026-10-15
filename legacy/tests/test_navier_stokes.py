"""NS reference physics, periodic topology, observation scope and public packaging."""
from copy import deepcopy
from dataclasses import replace
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from legacy.tests.materials import collect_archived_materials

import gmsh
import numpy as np
from caeoj.grading import grade_arrays, grade_files
from caeoj.sdk import load_problem, load_result
from caeoj.validation import check_result, output_support, validate_input, Checker

ROOT=Path(__file__).resolve().parents[2]
AUTHOR=ROOT/'legacy/navier-stokes-steady/author'


def module(name,file):
    spec=importlib.util.spec_from_file_location(name,file)
    value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value)
    return value


catalog=module('ns_catalog',AUTHOR/'catalog.py')
ghia=module('ns_ghia',AUTHOR/'ghia.py')
previous=sys.modules.get('ghia');sys.modules['ghia']=ghia
try:oracle=module('ns_oracle',AUTHOR/'oracle.py')
finally:
    if previous is None:sys.modules.pop('ghia',None)
    else:sys.modules['ghia']=previous
baseline=module('ns_baseline',AUTHOR/'baseline.py')
publisher=module('ns_publisher',ROOT/'src/utils/publish_dist.py')


class NSTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs={}
        for task in ('navier-stokes-steady','navier-stokes-transient'):
            for path in sorted((ROOT/'legacy'/task/'cases').glob('*/problem.json')):
                p=load_problem(path)
                reference=load_result(p,ROOT/'legacy'/task/'reference'/path.parent.name/'reference.h5')
                cls.inputs[task,path.parent.name]=(p,reference)

    def case(self,task,name):return self.inputs[task,name]

    def test_bank_structure_and_ranges(self):
        self.assertEqual(sum(t=='navier-stokes-steady' for t,_ in self.inputs),32)
        self.assertEqual(sum(t=='navier-stokes-transient' for t,_ in self.inputs),32)
        for (task,name),(p,ref) in self.inputs.items():
            self.assertLessEqual(len(p.arrays['node_ids']),4225)
            self.assertTrue(check_result(p,ref)['valid'])
            parameters=p.manifest['physics']['parameters']
            self.assertGreater(parameters['dynamic_viscosity']['value'],0)
            self.assertEqual(parameters['density']['unit'],'kg/m3')
            if task.endswith('transient'):
                np.testing.assert_array_equal(ref['velocity'][0],p.arrays['initial_velocity'][0])
                self.assertLessEqual(p.arrays['times'][-1],100)
                self.assertGreaterEqual(len(p.arrays['times']),6)
                self.assertLessEqual(len(p.arrays['times']),8)
                self.assertLessEqual(np.max(abs(p.arrays['initial_velocity'])),2)
                par=p.manifest['physics']['parameters']
                periodic_count=sum(c['operator']=='periodic' for c in p.manifest['conditions'])
                lengths=[par['length_x']['value'],par['length_y']['value']]
                if periodic_count==1:
                    axis=next(c['location']=='top' for c in p.manifest['conditions'] if c['operator']=='periodic')
                    nu=par['dynamic_viscosity']['value']/par['density']['value']
                    self.assertGreaterEqual(nu*p.arrays['times'][1]/lengths[1-int(axis)]**2,.001-1e-12)
                else:self.assertGreaterEqual(p.arrays['times'][1]/lengths[0],.005-1e-12)

    def test_native_periodic_links_survive_sparse_numbering(self):
        for (task,name),(p,_) in self.inputs.items():
            if not any(c['operator']=='periodic' for c in p.manifest['conditions']):continue
            gmsh.initialize([],readConfigFiles=False)
            try:
                gmsh.option.setNumber('General.Terminal',0);gmsh.open(str(p.path.parent/'mesh.msh'))
                for condition in p.manifest['conditions']:
                    if condition['operator']!='periodic':continue
                    loc=p.manifest['locations'][condition['location']]
                    slave_tag=loc['physical_group']['tag']
                    self.assertIs(type(condition['data']['master_physical_tag']['value']),int)
                    master_tag=int(condition['data']['master_physical_tag']['value'])
                    masters=set(map(int,gmsh.model.getEntitiesForPhysicalGroup(1,master_tag)))
                    mapped=[]
                    for entity in gmsh.model.getEntitiesForPhysicalGroup(1,slave_tag):
                        master,slaves,targets,affine=gmsh.model.mesh.getPeriodicNodes(1,int(entity))
                        self.assertIn(master,masters);self.assertEqual(len(affine),16)
                        self.assertEqual(len(slaves),len(targets));mapped.extend(slaves)
                        for slave,target in zip(slaves,targets):
                            s=gmsh.model.mesh.getNode(int(slave))[0]
                            t=gmsh.model.mesh.getNode(int(target))[0]
                            np.testing.assert_allclose(s,(np.array(affine).reshape(4,4)@np.r_[t,1])[:3],atol=1e-12)
                    self.assertEqual(set(map(int,mapped)),set(map(int,p.arrays[loc['ids']])))
            finally:gmsh.finalize()

    def test_frozen_data_matches_recipes_boundary_equations_and_grid(self):
        for transient,items in [(False,catalog.STEADY),(True,catalog.TRANSIENT)]:
            task='navier-stokes-transient' if transient else 'navier-stokes-steady'
            self.assertEqual({name for t,name in self.inputs if t==task},{c.name for c in items})
            for c in items:
                p,ref=self.case(task,c.name);xy,xs,ys,_,_=baseline.grid(p)
                self.assertEqual(len(xs),c.n+1);self.assertEqual(len(ys),c.n+1)
                np.testing.assert_allclose([xs[0],ys[0]],c.origin,atol=1e-8)
                np.testing.assert_allclose([xs[-1]-xs[0],ys[-1]-ys[0]],c.size,atol=1e-8)
                par=p.manifest['physics']['parameters']
                self.assertEqual(par['density']['value'],c.rho)
                self.assertAlmostEqual(par['dynamic_viscosity']['value'],c.rho*c.nu)
                self.assertLessEqual(abs(c.acceleration),.2)
                force=np.zeros(2);force[c.axis]=c.acceleration
                np.testing.assert_allclose(p.arrays['acceleration'],np.broadcast_to(force,(1,len(xy),2)))
                for condition in p.manifest['conditions']:
                    if condition['operator']!='dirichlet':continue
                    side=baseline.side_name(p,condition['location'],xy)
                    loc=p.manifest['locations'][condition['location']]
                    points=xy[np.searchsorted(p.arrays['node_ids'],p.arrays[loc['ids']])]
                    actual=p.arrays[p.manifest['fields'][condition['data']['value']['field']]['array']][0]
                    expected=np.zeros_like(actual)
                    if c.family=='cavity' and side==c.lid:
                        tangent=0 if side in ('bottom','top') else 1
                        interior=(points[:,tangent]>c.origin[tangent]+1e-10)&(points[:,tangent]<c.origin[tangent]+c.size[tangent]-1e-10)
                        expected[interior,tangent]=c.upper*c.lid_sign
                    elif c.family=='channel':expected[:,c.axis]=c.lower if side in ('bottom','left') else c.upper
                    np.testing.assert_array_equal(actual,expected)
                if transient:
                    np.testing.assert_allclose(p.arrays['times'],np.array(c.epochs)*catalog.time_scale(c))
                    if c.family=='periodic':self.assertGreaterEqual(c.n,16)
                elif c.family=='channel':
                    s=xy[:,1-c.axis]-c.origin[1-c.axis];h=c.size[1-c.axis]
                    q=c.lower+(c.upper-c.lower)*s/h+c.acceleration*s*(h-s)/(2*c.nu)
                    expected=np.zeros_like(ref['velocity']);expected[0,:,c.axis]=q
                    np.testing.assert_allclose(ref['velocity'],expected,atol=1e-13)
                    np.testing.assert_array_equal(ref['pressure'],0)

    def test_ghia_scope_and_reynolds_number(self):
        for case in catalog.STEADY:
            if case.family!='cavity':continue
            self.assertAlmostEqual(case.upper*case.size[0]/case.nu,100)
            p,ref=self.case('navier-stokes-steady',case.name)
            self.assertEqual(set(p.manifest['outputs']),{'u_centerline','v_centerline'})
            self.assertNotIn('pressure',ref)
        self.assertEqual(len(ghia.U),17);self.assertEqual(len(ghia.V),17)
        self.assertEqual(ghia.U[8],-0.20581);self.assertEqual(ghia.V[8],0.05454)

    def test_channel_steady_momentum_and_walls(self):
        for c in catalog.STEADY:
            if c.family!='channel':continue
            h=c.size[1-c.axis]
            s=np.linspace(0,h,101)
            q=c.lower+(c.upper-c.lower)*s/h+c.acceleration*s*(h-s)/(2*c.nu)
            self.assertAlmostEqual(q[0],c.lower);self.assertAlmostEqual(q[-1],c.upper)
            residual=c.nu*np.diff(q,n=2)/(h/100)**2+c.acceleration
            self.assertLess(np.max(abs(residual)),1e-10)

    def test_startup_couette_against_independent_closed_series(self):
        p,ref=self.case('navier-stokes-transient','02-start-couette')
        xy,*_=baseline.grid(p);y=xy[:,1]
        n=np.arange(1,512,dtype=float)
        for i,t in enumerate(p.arrays['times'][1:],1):
            expected=y+np.sin(np.pi*y[:,None]*n)@(2*(-1)**n/(np.pi*n)*np.exp(-0.01*(np.pi*n)**2*t))
            np.testing.assert_allclose(ref['velocity'][i,:,0],expected,atol=1e-12)

    def test_all_channel_series_against_independent_gauss_integrals(self):
        # Numerical quadrature integrates q0-q_inf directly, independent of the
        # reference's antiderivative and closed-form steady Fourier coefficients.
        z,w=np.polynomial.legendre.leggauss(24)
        for c in catalog.TRANSIENT:
            if c.family!='channel':continue
            p,ref=self.case('navier-stokes-transient',c.name);xy,*_=baseline.grid(p)
            s=xy[:,1-c.axis]-c.origin[1-c.axis];h=c.size[1-c.axis];layers=np.unique(s)
            q0=np.array([p.arrays['initial_velocity'][0,np.argmin(abs(s-y)),c.axis] for y in layers])
            width=np.diff(layers)
            points=layers[:-1,None]+width[:,None]*(z+1)/2
            initial=q0[:-1,None]+np.diff(q0)[:,None]*(z+1)/2
            steady=c.lower+(c.upper-c.lower)*points/h+c.acceleration*points*(h-points)/(2*c.nu)
            k=np.arange(1,129,dtype=float)*np.pi/h
            coeff=2/h*np.einsum('ij,ijn,ij->n',initial-steady,np.sin(points[:,:,None]*k),width[:,None]*w/2)
            base=c.lower+(c.upper-c.lower)*s/h+c.acceleration*s*(h-s)/(2*c.nu)
            for i,t in enumerate(p.arrays['times'][1:],1):
                expected=base+np.sin(s[:,None]*k)@(coeff*np.exp(-c.nu*k*k*t))
                np.testing.assert_allclose(ref['velocity'][i,:,c.axis],expected,atol=2e-12,err_msg=c.name)

    def test_baseline_follows_renamed_references_and_condition_order(self):
        for task,name in [('navier-stokes-steady','07-vertical-channel'),
                          ('navier-stokes-steady','13-cavity-32'),
                          ('navier-stokes-transient','14-advected-vortex')]:
            original,reference=self.case(task,name);p=deepcopy(original)
            maps={section:{key:'alias_'+key for key in p.manifest[section]}
                  for section in ('locations','fields','time_axes','meshes')}
            arrays={key:'data_'+key for key in p.arrays}
            for section in maps:p.manifest[section]={maps[section][k]:v for k,v in p.manifest[section].items()}
            p.meshes={maps['meshes'][k]:v for k,v in p.meshes.items()}
            p.arrays={arrays[k]:v for k,v in p.arrays.items()}
            for loc in p.manifest['locations'].values():
                loc['ids']=arrays[loc['ids']]
                if 'coordinates' in loc:loc['coordinates']=arrays[loc['coordinates']]
                if 'mesh' in loc:loc['mesh']=maps['meshes'][loc['mesh']]
            for field in p.manifest['fields'].values():
                field['array']=arrays[field['array']]
                field['location']=maps['locations'][field['location']]
                field['time_axis']=maps['time_axes'][field['time_axis']]
            for key,array in p.manifest['time_axes'].items():p.manifest['time_axes'][key]=arrays[array]
            renamed_ref={arrays[k]:v for k,v in reference.items() if k in arrays}
            for field in p.manifest['outputs'].values():
                old=field['array'];field['array']='requested_'+old
                renamed_ref[field['array']]=reference[old]
                field['location']=maps['locations'][field['location']]
                field['time_axis']=maps['time_axes'][field['time_axis']]
            for condition in p.manifest['conditions']:
                condition['location']=maps['locations'][condition['location']]
                for value in condition['data'].values():
                    if 'field' in value:value['field']=maps['fields'][value['field']]
            p.manifest['conditions'].reverse()
            errors=[];checker=Checker(p,errors)
            checker.locations();checker.times();checker.fields();checker.conditions()
            self.assertEqual(errors,[])
            result={k:p.arrays[k] for k in output_support(p)}|baseline.solve_values(p)
            self.assertEqual(grade_arrays(p,result,renamed_ref,atol=.02,rtol=0)['score'],1,name)

    def test_periodic_formula_satisfies_full_navier_stokes(self):
        for c in catalog.TRANSIENT:
            if c.family=='periodic':
                with self.subTest(case=c.name):self.check_periodic_pde(c)

    def check_periodic_pde(self,c):
        xy=np.array([[.17,.29],[.38,.71],[.79,.53]])
        t=.23;h=2e-5
        def evaluate(points,time):
            u,p=oracle.vortex(c,points,[time]);return u[0],p[0,:,0]
        u,p=evaluate(xy,t)
        ut=(evaluate(xy,t+h)[0]-evaluate(xy,t-h)[0])/(2*h)
        derivatives=[];lap=np.zeros_like(u);gradp=[]
        for axis in (0,1):
            shift=np.zeros_like(xy);shift[:,axis]=h
            up,pp=evaluate(xy+shift,t);um,pm=evaluate(xy-shift,t)
            derivatives.append((up-um)/(2*h));lap+=(up-2*u+um)/h**2
            gradp.append((pp-pm)/(2*h))
        div=derivatives[0][:,0]+derivatives[1][:,1]
        conv=u[:,0,None]*derivatives[0]+u[:,1,None]*derivatives[1]
        residual=c.rho*(ut+conv)+np.column_stack(gradp)-c.rho*c.nu*lap
        self.assertLess(np.max(abs(div)),1e-7)
        self.assertLess(np.max(abs(residual)),2e-5)
        if c.name=='15-oblique-advection':self.assertGreater(np.max(abs(conv)),0.1)

    def test_periodic_pressure_area_mean(self):
        z,w=np.polynomial.legendre.leggauss(24)
        for c in catalog.TRANSIENT:
            if c.family!='periodic':continue
            xx,yy=np.meshgrid(c.origin[0]+c.size[0]*(z+1)/2,c.origin[1]+c.size[1]*(z+1)/2)
            _,p=oracle.vortex(c,np.column_stack((xx.ravel(),yy.ravel())),[.1])
            self.assertLess(abs(np.sum(p[0,:,0].reshape(24,24)*w[:,None]*w[None,:])/4),1e-12)

    def test_cavity_rotation_transforms_coordinates_and_components(self):
        p,ref=self.case('navier-stokes-steady','28-cavity-left-positive')
        np.testing.assert_array_equal(ref['u_centerline'][0,:,0],-ghia.V)
        np.testing.assert_array_equal(ref['v_centerline'][0,:,0],ghia.U)
        np.testing.assert_allclose(p.arrays['vertical_coordinates'],np.column_stack((np.full(17,.5),ghia.X)))
        np.testing.assert_allclose(p.arrays['horizontal_coordinates'],np.column_stack((1-ghia.Y,np.full(17,.5))))
        p,ref=self.case('navier-stokes-steady','27-cavity-bottom-negative')
        np.testing.assert_array_equal(ref['u_centerline'][0,:,0],-ghia.U)
        np.testing.assert_array_equal(ref['v_centerline'][0,:,0],-ghia.V)
        np.testing.assert_allclose(p.arrays['vertical_coordinates'][:,1],1-ghia.Y)

    def test_rich_cases_preserve_reynolds_and_initial_ranges(self):
        for transient,items in [(False,catalog.STEADY),(True,catalog.TRANSIENT)]:
            for c in items:
                if c.family=='channel':
                    h=c.size[1-c.axis];z=np.linspace(0,1,10001)
                    q=c.lower+(c.upper-c.lower)*z+c.acceleration*h*h*z*(1-z)/(2*c.nu)
                    speed=max(float(np.max(abs(q))),abs(c.lower),abs(c.upper))
                    if transient:
                        u0=oracle.initial_channel(c,np.linspace(0,1,c.n+1))
                        speed=max(speed,float(np.max(abs(u0))))
                    re=speed*h/c.nu
                elif c.family=='cavity':re=c.upper*c.size[0]/c.nu
                else:
                    bound=(sum(abs(a) for a in c.coefficients) if c.coefficients else abs(c.amplitude))+np.linalg.norm(c.drift)
                    re=bound*c.size[0]/c.nu
                self.assertLessEqual(re,100+1e-9,c.name)
        for c in catalog.TRANSIENT:
            if c.coefficients:self.assertGreater(abs(np.linalg.det(np.array(c.coefficients).reshape(2,2))),.01)
        c=next(c for c in catalog.STEADY if c.name=='17-zero-net-flux')
        self.assertAlmostEqual((c.lower+c.upper)/2+c.acceleration/(12*c.nu),0)

    def test_missing_advection_fails_even_with_valid_io(self):
        c=next(c for c in catalog.TRANSIENT if c.name=='14-advected-vortex')
        p,reference=self.case('navier-stokes-transient',c.name)
        xy,*_=baseline.grid(p)
        wrong,_=oracle.vortex(replace(c,drift=(0,0)),xy,p.arrays['times'])
        wrong+=np.array(c.drift)
        arrays={k:p.arrays[k] for k in output_support(p)}|{'velocity':wrong,'pressure':reference['pressure']}
        self.assertTrue(check_result(p,arrays)['valid'])
        self.assertEqual(grade_arrays(p,arrays,reference,atol=.02,rtol=0)['score'],0)

    def test_zero_pressure_and_wrong_gauge_fail_numeric_grade_only(self):
        p,ref=self.case('navier-stokes-transient','13-periodic-vortex')
        for pressure in [np.zeros_like(ref['pressure']),ref['pressure']+0.03]:
            arrays={k:v.copy() for k,v in ref.items()};arrays['pressure']=pressure
            self.assertTrue(check_result(p,arrays)['valid'])
            self.assertEqual(grade_arrays(p,arrays,ref,atol=.02,rtol=0)['score'],0)

    def test_validator_does_not_repair_physics_or_conflate_axes(self):
        p,ref=self.case('navier-stokes-transient','04-start-combined')
        altered=deepcopy(p);altered.arrays['initial_velocity']+=100
        from caeoj.validation import Checker
        errors=[];checker=Checker(altered,errors);checker.locations();checker.times();checker.fields();checker.conditions()
        self.assertEqual(errors,[])
        bad={k:v.copy() for k,v in ref.items()};bad['initial_times']=p.arrays['initial_times']
        self.assertFalse(check_result(p,bad)['valid'])

    def test_samples_grade_and_public_archive_has_no_reference_material(self):
        for task in ('navier-stokes-steady','navier-stokes-transient'):
            files,samples=collect_archived_materials(publisher.collect_materials,task)
            self.assertGreaterEqual(len(samples),2)
            self.assertFalse(any('/author/' in n or '/reference/' in n or '/cases/' in n or
                                 n.endswith(('DESIGN.md','TEST-CASES.md','baseline.py','ghia.py')) for n in files))
            for sample in samples:
                root=ROOT/'legacy'/task/'samples'/sample
                case=json.loads((root/'verification.json').read_text(encoding='utf-8'))['case']
                result=grade_files(root/'input/problem.json',root/'output/result.h5',
                    ROOT/'legacy'/task/'reference'/case/'reference.h5',atol=.02,rtol=0)
                self.assertEqual(result['score'],1)


if __name__=='__main__':unittest.main()
