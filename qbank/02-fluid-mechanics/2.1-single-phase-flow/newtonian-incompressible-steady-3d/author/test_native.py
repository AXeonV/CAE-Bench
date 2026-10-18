"""Regression checks for this supplement's native adapters; no physical solver."""
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

import numpy as np

import supplement as s
import native


class NativeAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.root=Path(cls.temp.name)
        cls.cases=s.catalog()
        cls.problems={c['name']:s.input_case(c,cls.root/'inputs'/c['name']) for c in cls.cases}

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_every_candidate_native_configuration(self):
        for c in self.cases:
            with self.subTest(case=c['name']):
                n=8 if c['geometry']=='two-obstacles' else 4
                p=self.problems[c['name']]
                e=self.root/'elmer'/c['name'];f=self.root/'foam'/c['name']
                native.elmer(c,p,e,n);native.foam(c,p,f,n)
                points,cells,faces,_,_=s.box_grid(c,n)
                bcs,*_=s.settings(c)
                natural=any(op in ('traction','pressure_outlet') for op in bcs.values())
                rows=[line.split() for line in (e/'mesh/mesh.boundary').read_text().splitlines()]
                pins=[r for r in rows if r[1]=='99']
                self.assertEqual(len(pins),int(not natural))
                if pins:
                    node=int(pins[0][-1])-1
                    boundary={i for group in faces.values() for _,q in group for i in q}
                    self.assertNotIn(node,boundary)
                    self.assertIn(node,cells[int(pins[0][2])-1])
                self.assertIn('endTime 12000',(f/'system/controlDict').read_text())
                self.assertNotIn('nan',(f/'0/p').read_text().lower())
                self.assertNotIn('nan',(f/'0/U').read_text().lower())
                # Native oriented facets must point out of their owner cells,
                # including mixed-normal obstacle patches.
                for group in faces.values():
                    for owner,q in group:
                        vertices=points[list(q)]
                        normal=np.cross(vertices[1]-vertices[0],vertices[2]-vertices[0])
                        self.assertGreater(float(normal@(vertices.mean(axis=0)-points[cells[owner]].mean(axis=0))),0)

    def test_rotated_gradient_retains_global_components(self):
        c=self.cases[7]
        field=object.__new__(native.NativeField)
        field.R=np.asarray(c['rotation']);field.origin=np.asarray(c['origin']);field.lengths=np.asarray(c['lengths'])
        expected=np.array([[.1,-.3,.2],[.4,.1,-.5],[-.2,.6,.3]])
        field.interpolator=lambda local:np.column_stack([local@field.R.T@expected.T,np.zeros(len(local))])
        xyz=s.transform(c,np.array([[.2,.3,.4],[.6,.5,.7]])*field.lengths)
        np.testing.assert_allclose(field.gradient(xyz),np.broadcast_to(expected,(2,3,3)),atol=1e-10)

    def test_obstacle_field_conversion_and_mean_pressure(self):
        for c in self.cases:
            if c['geometry']=='box':continue
            with self.subTest(case=c['name']):
                folder=self.root/'foam'/c['name'];latest=folder/'1';latest.mkdir(exist_ok=True)
                _,_,faces,_,_=s.box_grid(c,8)
                patches=''.join(f'b{b} {{type fixedValue;value uniform (0 0 0);}}\n' for b,g in faces.items() if g)
                (latest/'U').write_text('internalField uniform (0 0 0);\nboundaryField {\n'+patches+'}\n')
                (latest/'p').write_text('internalField uniform 0;\n')
                p=self.problems[c['name']]
                field=native.NativeField(c,folder,8,'openfoam')
                result=native.outputs(c,p,field)
                self.assertTrue(np.isfinite(field.shift))
                self.assertTrue(all(np.all(np.isfinite(v)) for v in result.values()))
                pressure=next(spec['array'] for spec in p.manifest['outputs'].values() if spec['quantity']=='pressure')
                np.testing.assert_allclose(result[pressure],c['pressure_value'])

    def test_small_update_does_not_hide_unfixed_pressure(self):
        c=self.cases[38];folder=self.root/'false-convergence'
        native.elmer(c,self.problems[c['name']],folder,4)
        points,*_=s.box_grid(c,4)
        tree=ET.Element('VTKFile');piece=ET.SubElement(tree,'Piece')
        pt=ET.SubElement(piece,'Points');a=ET.SubElement(pt,'DataArray');a.text=' '.join(map(str,points.ravel()))
        pd=ET.SubElement(piece,'PointData');pressure=ET.SubElement(pd,'DataArray',Name='pressure')
        pressure.text=' '.join(['1']*len(points))
        path=folder/'mesh/solution_t0001.vtu';ET.ElementTree(tree).write(path)
        (folder/'flow.log').write_text('Result Norm : 1\nRelative Change : 1e-12\n')
        with self.assertRaisesRegex(RuntimeError,'pressure pin'):
            native.convergence('elmer',folder)
        pressure.text=' '.join(['0']*len(points));ET.ElementTree(tree).write(path)
        self.assertEqual(native.convergence('elmer',folder)['stationarity']['numerical_pressure_pin'],0)


if __name__=='__main__':
    unittest.main(verbosity=2)
