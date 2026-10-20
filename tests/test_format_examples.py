"""Format examples validate structure while numerical references remain private."""
import json
import shutil
import unittest
from pathlib import Path
import test_data_pool as pool_tests
import test_publish as publish_tests
publisher=publish_tests.publisher
import test_harbor as harbor_tests
prepare,TASK,TASK_PATH=harbor_tests.prepare,harbor_tests.TASK,harbor_tests.TASK_PATH
from caeoj_tools import data_pool as pool
from caeoj.storage import write_hdf5
from caeoj.validation import read_hdf5, output_support
from caeoj.sdk import load_problem


def randomize(sample):
    import numpy as np
    problem=load_problem(sample/'input/problem.json')
    arrays=read_hdf5(sample/'output/result.h5')
    rng=np.random.default_rng(20261020)
    support=output_support(problem)
    write_hdf5(sample/'output/result.h5',{k:v if k in support else rng.normal(size=v.shape) for k,v in arrays.items()})
    pool.write_json(sample/'example.json',{'kind':'format'})


class FormatExamples(unittest.TestCase):
    def fixture(self,cls):
        obj=cls();obj.setUp();self.addCleanup(obj.doCleanups);return obj

    def test_shared_test_format_sample_keeps_reference_private(self):
        f=self.fixture(pool_tests.PoolTests)
        randomize(f.source/'samples/01')
        bundle=f.root/'format';pool.pack(f.source,bundle,f.value)
        value=pool.manifest(bundle/'selection.json');store=pool.LocalStore(bundle/'repository')
        pool.validate_bundle(bundle)
        case_id=value['cases']['a']['case_id']
        with self.assertRaisesRegex(pool.PoolError,'--format-sample'):
            pool.select(value,store,[],[case_id])
        chosen=pool.select(value,store,['001='+case_id],[],format_samples=['01='+case_id])
        pool.write_json(f.task/'data-manifest.json',chosen)
        pool.assemble(f.task,chosen,store)
        self.assertTrue(pool.verify(f.task,strict=True)['valid'])
        self.assertFalse((f.task/'samples/01/reference').exists())
        self.assertTrue((f.task/'reference/001/reference.h5').is_file())
        self.assertEqual(pool.plan(chosen,store)['public_cases'][0]['sample_kind'],'format')
        from caeoj.case_grading import grade_case
        self.assertLess(grade_case(f.task/'samples/01/input/problem.json',f.task/'samples/01/output/result.h5',f.task/'reference/001/grading.json')['score'],1)

    def test_format_only_does_not_make_numerical_test_complete(self):
        f=self.fixture(pool_tests.PoolTests);randomize(f.source/'samples/01')
        shutil.rmtree(f.source/'cases');shutil.rmtree(f.source/'reference');shutil.rmtree(f.source/'samples/01/reference')
        bundle=f.root/'format';pool.pack(f.source,bundle,f.value)
        value=pool.manifest(bundle/'selection.json');store=pool.LocalStore(bundle/'repository')
        pool.validate_bundle(bundle)
        case_id=value['samples']['01']['case_id']
        with self.assertRaisesRegex(pool.PoolError,'[Ii]ncomplete'):
            pool.select(value,store,[case_id],[])
        pool.write_json(f.task/'data-manifest.json',value);pool.assemble(f.task,value,store)
        self.assertTrue(pool.verify(f.task,strict=True)['valid'])
        output=f.task/'samples/01/output/result.h5'
        write_hdf5(output,{'bad': __import__('numpy').array([1.])})
        with self.assertRaisesRegex(pool.PoolError,'SHA/size mismatch'):
            pool.verify(f.task,strict=True)
        source_output=f.source/'samples/01/output/result.h5'
        arrays=read_hdf5(source_output)
        support=output_support(load_problem(f.source/'samples/01/input/problem.json'))
        for key in support:
            arrays[key]=arrays[key][::-1].copy()
        write_hdf5(source_output,arrays)
        from caeoj.validation import ContractError
        with self.assertRaises(ContractError):
            pool.pack(f.source,f.root/'bad-format',f.value)

    def test_mixed_instruction_commands_use_graded_input(self):
        f=self.fixture(harbor_tests.HarborTests);task=f.root/TASK_PATH
        randomize(task/'samples/01')
        publisher.publish(TASK,root=f.root)
        out=Path(prepare.prepare(TASK,f.root)['task_directory'])
        instruction=(out/'instruction.md').read_text(encoding='utf-8')
        self.assertIn('samples/02/input/problem.json --output /app/sample-result.h5',instruction)
        self.assertIn('samples/02/reference/grading.json',instruction)
        self.assertNotIn('samples/01/reference/grading.json',instruction)
        self.assertIn('随机数值的格式示例',instruction)
        self.assertIn('完整提交示例',instruction)

    def test_public_bundle_mixed_examples_and_harbor_instructions(self):
        f=self.fixture(harbor_tests.HarborTests);task=f.root/TASK_PATH
        for sample in (task/'samples').iterdir():randomize(sample)
        files,_=publisher.collect_materials(TASK,f.root)
        self.assertEqual(set(json.loads(files['MANIFEST.json'])['sample_kinds'].values()),{'format'})
        self.assertFalse(any('/reference/' in k for k in files))
        self.assertIn('随机',files['README.md'].decode())
        self.assertNotIn('caeoj grade',files['README.md'].decode())
        publisher.publish(TASK,root=f.root)
        out=Path(prepare.prepare(TASK,f.root)['task_directory'])
        instruction=(out/'instruction.md').read_text(encoding='utf-8')
        self.assertIn('随机数值的格式示例',instruction)
        self.assertNotIn('完整提交示例',instruction)
        self.assertNotIn('samples/01/reference/grading.json',instruction)
        # Mixed task bundle still grades ordinary examples and validates format examples.
        p=self.fixture(publish_tests.PublishTests)
        target=p.project/TASK_PATH
        for sample in (target/'samples').iterdir():randomize(sample)
        report=publisher.publish([TASK,'heat-conduction-transient-2d'],p.root/'mixed',p.project)
        self.assertTrue(Path(report['archive']).is_file())

if __name__=='__main__':unittest.main()
