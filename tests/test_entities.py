"""Core-only nonspatial identity tables; no mechanical-model dependency."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import h5py
import numpy as np
from caeoj.sdk import load_problem,write_result,target_ids
from caeoj.validation import check_problem,validate_output


class EntityLocationTests(unittest.TestCase):
    def test_identity_table_roundtrip_and_rejections_without_provider(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=root/'problem.json'
            spec=dict(array='state',quantity='generalized_state',location='objects',time_axis='snapshot',dtype='float64',kind='components',component_shape=[2],components=['a','b'],unit='1',value_kind='point')
            m=dict(spatial_dimension=2,data_file='input.h5',meshes={},geometries={},locations=dict(objects=dict(kind='entities',ids='entity_ids')),time_axes=dict(snapshot='times'),fields=dict(initial=spec),outputs=dict(response=dict(spec,array='result')),conditions=[])
            with h5py.File(root/'input.h5','w') as h:
                h['entity_ids']=np.array([0,19],dtype='int64');h['times']=np.array([0.]);h['state']=np.array([[[1.,2.],[3.,4.]]])
            core=dict(version=1,id='core-only',extensions={},tasks={},strict_tasks=False)
            with patch('caeoj.runtime.descriptor',return_value=core):
                path.write_text(json.dumps(m));problem=load_problem(path)
                np.testing.assert_array_equal(target_ids(problem,'objects'),[0,19])
                write_result(root/'output.h5',problem,{'result':problem.arrays['state']})
                self.assertTrue(validate_output(path,root/'output.h5')['valid'])
                with h5py.File(root/'output.h5') as h:self.assertEqual(set(h),{'entity_ids','times','result'})
                for change in [lambda x:x['locations']['objects'].update(coordinates='fake'),lambda x:x['outputs']['response'].update(value_kind='average'),lambda x:x['locations']['objects'].update(kind='entity')]:
                    bad=deepcopy(m);change(bad);path.write_text(json.dumps(bad));self.assertFalse(check_problem(path)[1]['valid'])
                path.write_text(json.dumps(m))
                with h5py.File(root/'input.h5','r+') as h:h['entity_ids'][:]=[19,0]
                self.assertFalse(check_problem(path)[1]['valid'])

if __name__=='__main__':unittest.main()
