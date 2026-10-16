"""Exercise real quantity policies, resource consumers and public closure."""
from copy import deepcopy
import importlib.util
import json
import sys
from pathlib import Path
import tempfile
import tomllib
import unittest
import numpy as np
from solid_fixture import fixture
from caeoj_ext.solid import models
from caeoj.grading import grade_arrays
from caeoj.grading_policy import resolve_policy
from caeoj.sdk import load_problem
from caeoj.validation import output_support
from caeoj_tools.assembly import runtime_materials
from caeoj_tools.grading_policy import task_policy
from caeoj_tools.task_paths import task_directory
ROOT=Path(__file__).resolve().parents[1]


def load_file(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);module=importlib.util.module_from_spec(spec)
    sys.path.insert(0,str(ROOT/'src/utils'))
    try:spec.loader.exec_module(module)
    finally:sys.path.pop(0)
    return module


class SolidJudgeTests(unittest.TestCase):
    def test_every_quantity_pass_equal_boundary_and_fail_above(self):
        for slug in models():
            with self.subTest(task=slug),tempfile.TemporaryDirectory() as tmp:
                path,m=fixture(tmp,slug);problem=load_problem(path);task=task_directory(slug,ROOT)
                policy=task_policy(task,problem);bound=resolve_policy(policy,problem)
                support=output_support(problem)
                reference={key:problem.arrays[key].copy() for key in support}
                for name,s in m['outputs'].items():
                    reference[s['array']]=np.zeros((len(problem.arrays[m['time_axes'][s['time_axis']]]),len(problem.arrays[m['locations'][s['location']]['ids']]),*s['component_shape']))
                self.assertEqual(grade_arrays(problem,deepcopy(reference),reference,policy=policy)['score'],1)
                for name,s in m['outputs'].items():
                    actual=deepcopy(reference);tol=bound['fields'][name]['atol'];actual[s['array']][:]=tol
                    self.assertEqual(grade_arrays(problem,actual,reference,policy=policy)['score'],1)
                    actual[s['array']].flat[0]=np.nextafter(tol,np.inf)
                    self.assertEqual(grade_arrays(problem,actual,reference,policy=policy)['score'],0)
                # Relative part at a nonzero hand-chosen reference.
                actual=deepcopy(reference);name,s=next(iter(m['outputs'].items()));ref=1.;atol=bound['fields'][name]['atol']
                reference[s['array']][:]=ref;actual[s['array']][:]=ref+atol+.01*ref+1e-5
                self.assertEqual(grade_arrays(problem,actual,reference,policy=policy)['score'],0)

    def test_harbor_resource_merge_budget_and_output_consumer(self):
        prepare=load_file('solid_prepare','src/utils/prepare_harbor.py');judge=load_file('solid_judge','src/utils/harbor/tests/judge.py')
        template=(ROOT/'src/utils/harbor/task.toml').read_text()
        for slug,cfg in models().items():
            task=task_directory(slug,ROOT);config=json.loads((task/'judge-config.json').read_text());overrides=tomllib.loads((task/'harbor/task.toml').read_text())
            merged=tomllib.loads(prepare.task_config(template,overrides,judge_config=config,case_count=2))
            self.assertEqual(merged['environment']['cpus'],4);self.assertEqual(merged['environment']['memory_mb'],8192)
            self.assertEqual(merged['verifier']['environment_mode'],'separate');self.assertEqual(merged['verifier']['network_mode'],'no-network')
            self.assertEqual(merged['verifier']['timeout_sec'],300+2*(cfg['timeout']+60))
            self.assertEqual(config['timeout_seconds'],cfg['timeout']);self.assertIsNone(judge.output_limit(config))
        # Unknown resource keys must not silently disappear.
        with self.assertRaises(ValueError):prepare.task_config(template,{'environment':{'cores':4}})
        with self.assertRaises(ValueError):prepare.task_config(template,{},judge_config=config,case_count=0)

    def test_solid_multitask_closure_is_public_and_explicit(self):
        tasks={slug:task_directory(slug,ROOT) for slug in models()}
        files,runtime=runtime_materials(tasks,ROOT)
        self.assertEqual(set(runtime['tasks']),set(tasks));self.assertEqual(set(runtime['extensions']),{'solid.mechanics'})
        self.assertIn('src/caeoj_ext/solid/models.json',files)
        self.assertFalse(any(any(part in path for part in ['caeoj_tools','/author/','maintenance','/cases/','/reference/']) for path in files))
        self.assertFalse(any('fluid/' in path for path in files))

if __name__=='__main__':unittest.main()
