"""Verify complete official trajectories and the public/private boundary."""
from caeoj.storage import write_hdf5
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
from caeoj.grading import grade_files
from caeoj.sdk import load_problem,load_result

ROOT=Path(__file__).resolve().parents[1]
TASK=ROOT/'tasks/1D_Advection_Sols_beta0.4'


class OfficialAdvectionTests(unittest.TestCase):
    def test_every_official_value_is_preserved(self):
        source=json.loads((TASK/'author/SOURCE.json').read_text())
        cases=sorted((TASK/'cases').glob('*/problem.json'))
        self.assertEqual(len(cases),12)
        for index,path in enumerate(cases):
            with self.subTest(sample=index):
                problem=load_problem(path)
                directory=TASK/'reference'/path.parent.name
                result=load_result(problem,directory/'reference.h5')
                certificate=json.loads((directory/'certificate.json').read_text())
                self.assertEqual(certificate['source_sample_index'],index)
                self.assertEqual(result['state'].shape,(201,1024,1))
                mapping=np.array(certificate['source_index_by_cell_row'])
                self.assertEqual(sorted(mapping.tolist()),list(range(1024)))
                original=result['state'][:,np.argsort(mapping),0].astype('float32')
                self.assertEqual(hashlib.sha256(original.tobytes()).hexdigest(),source['samples'][index]['sha256'])
                np.testing.assert_array_equal(result['state'],original.astype('float64')[:,mapping,None])
                np.testing.assert_array_equal(result['state'][0:1],problem.arrays['initial_values'])
                self.assertEqual(result['times'][0],0)
                self.assertEqual(result['times'][-1],2)

    def test_all_official_time_values_are_preserved(self):
        p=load_problem(TASK/'cases/01-official-0000/problem.json')
        # Restore the unused coordinate, never an additional solution frame.
        source_times=np.append(p.arrays['times'].astype('float32'),np.float32(2.01))
        source=json.loads((TASK/'author/SOURCE.json').read_text())
        self.assertEqual(hashlib.sha256(source_times.tobytes()).hexdigest(),source['coordinates']['t-coordinate'])

    def test_samples_are_correct_and_threshold_is_applied(self):
        config=json.loads((TASK/'judge-config.json').read_text())
        for index in (1,2):
            sample=TASK/'samples'/f'{index:02d}'
            path=sample/'input/problem.json';output=sample/'output/result.h5'
            self.assertEqual(grade_files(path,output,output,atol=config['atol'],rtol=0)['score'],1)
        p=load_problem(path);values=load_result(p,output)
        values['state']=values['state'].copy();values['state'][-1,-1,0]+=0.16
        with tempfile.TemporaryDirectory(dir=ROOT/'runs') as temporary:
            wrong=Path(temporary)/'wrong.h5';write_hdf5(wrong, values)
            self.assertEqual(grade_files(path,wrong,output,atol=config['atol'],rtol=0)['score'],0)

    def test_release_contains_no_private_trajectory_or_solver(self):
        import sys
        sys.path.insert(0,str(ROOT/'src/utils'))
        try:
            from publish_dist import collect_materials
            files,samples=collect_materials('1D_Advection_Sols_beta0.4')
        finally:sys.path.pop(0)
        self.assertEqual(samples,['01','02'])
        self.assertFalse(any('/reference/' in name or '/author/' in name or '/cases/' in name for name in files))
        self.assertNotIn('tasks/1D_Advection_Sols_beta0.4/DESIGN.md',files)
        for name in ('tasks/1D_Advection_Sols_beta0.4/instruction.md','tasks/1D_Advection_Sols_beta0.4/DATA.md'):
            text=files[name].decode('utf-8')
            for hint in ('PDEBench','数据来源','darus','有限体积','Fourier','通量修复'):
                self.assertNotIn(hint,text)
        self.assertFalse(any('pdebench' in name.lower() for name in files))


if __name__=='__main__':unittest.main()
