"""Runtime boundary and trusted assembly failure cases, using temporary metadata."""
from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from caeoj import runtime
from caeoj.cli import main
from caeoj.grading_policy import load_policy
from caeoj.sdk import load_problem
from caeoj_tools.grading_policy import author_policy
from caeoj.validation import schema_errors
from caeoj_tools.assembly import runtime_materials
from caeoj_tools.task_paths import task_directory

ROOT = Path(__file__).resolve().parents[1]
TASK = 'heat-conduction-steady-2d'


class RuntimeAssemblyTests(unittest.TestCase):
    def test_grade_bad_input_is_infrastructure_error_not_a_wrong_answer(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/'problem.json'
            path.write_text('{}')
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(['grade', '--input', str(path), '--output', 'unused.h5',
                             '--grading', 'unused-grading.json'])
            self.assertEqual(code, 2)
            result = json.loads(output.getvalue())
            self.assertEqual(result['status'], 'input_error')
            self.assertIsNone(result['score'])

    def test_every_task_declares_a_single_scoring_source(self):
        for path in ROOT.glob('qbank/*/*/*/instruction.md'):
            with self.subTest(task=path.parent.name):
                load_policy(path.parent/'author/grading-template.json')
                config = json.loads((path.parent/'judge-config.json').read_text(encoding='utf-8'))
                self.assertFalse({'atol', 'rtol'} & set(config))

    def test_author_template_requires_explicit_source_and_no_execution_tolerances(self):
        with tempfile.TemporaryDirectory() as temporary:
            task = Path(temporary)
            with self.assertRaises(FileNotFoundError):
                author_policy(task)
            (task/'author').mkdir()
            (task/'author/grading-template.json').write_text(json.dumps(load_policy(task_directory(TASK, ROOT)/'author/grading-template.json')))
            (task/'judge-config.json').write_text('{"atol": 0.01, "rtol": 0}')
            with self.assertRaisesRegex(ValueError, 'Scoring belongs in case grading.json'):
                author_policy(task)

    def test_malformed_metadata_has_schema_diagnostics_and_no_traceback(self):
        for value in (None, [], {'task': []}, {'task': {}}):
            with self.subTest(value=value):
                self.assertTrue(schema_errors(value))
                with tempfile.TemporaryDirectory() as temporary:
                    path = Path(temporary)/'problem.json'; path.write_text(json.dumps(value))
                    for args in (['info','--input',str(path)], ['validate-input',str(path)]):
                        output = io.StringIO()
                        with redirect_stdout(output):
                            code = main(args)
                        self.assertEqual(code, 1)
                        self.assertFalse(json.loads(output.getvalue())['valid'])

    def test_core_only_scope_and_missing_required_extension(self):
        core = {'version':1, 'id':'core-only', 'extensions':{}, 'tasks':{}, 'strict_tasks':False}
        with patch.object(runtime, 'descriptor', return_value=core):
            self.assertEqual(runtime.describe({'task':'standalone'})['scope'], 'generic-structure')
        broken = {**core, 'strict_tasks':True, 'tasks':{'x':['missing']}}
        with patch.object(runtime, 'descriptor', return_value=broken):
            with self.assertRaisesRegex(runtime.RuntimeSupportError, 'missing extension'):
                runtime.selected({'task':'x'})
            with self.assertRaisesRegex(runtime.RuntimeSupportError, 'not included'):
                runtime.selected({'task':'other'})

    def test_schema_conflicts_and_explicit_extension_point_ownership(self):
        base = {'properties': {'a': {'type':'integer'}}, 'limit':1}
        with self.assertRaisesRegex(runtime.RuntimeSupportError, 'Conflicting'):
            runtime.compose_schema(base, [('one', {'properties':{'a':{'type':'string'}}}, [])])
        duplicate = runtime.compose_schema(base, [('one',deepcopy(base),[])])
        self.assertEqual(duplicate,base)
        self.assertEqual(runtime.compose_schema(base,[('one',{'limit':0},['limit'])],['limit'])['limit'],0)
        with self.assertRaisesRegex(runtime.RuntimeSupportError, 'owners'):
            runtime.compose_schema(base,[('one',{'limit':0},['limit']),('two',{'limit':2},['limit'])],['limit'])
        with self.assertRaisesRegex(runtime.RuntimeSupportError, 'Unsupported'):
            runtime.compose_schema(base,[('one',{'limit':0},['limit'])])

    def copied_runtime(self, directory):
        shutil.copytree(ROOT/'src/caeoj', directory/'src/caeoj', ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copytree(ROOT/'qbank/extensions', directory/'qbank/extensions', ignore=shutil.ignore_patterns('__pycache__','*.egg-info'))
        shutil.copy2(ROOT/'pyproject.toml', directory/'pyproject.toml')
        task = directory/'qbank/test/section'/TASK; task.mkdir(parents=True)
        return task

    def test_task_extension_closure_and_prepublication_failures(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); task = self.copied_runtime(root)
            extension = task/'extension'; code=extension/'caeoj_task_ext/probe'
            code.mkdir(parents=True)
            (code/'__init__.py').write_text('def check(problem, errors):\n    return None\n')
            spec = {'id':'task.probe', 'version':1, 'requires':['fluid.thin_film'],
                    'files':['caeoj_task_ext/probe/__init__.py'], 'check':'caeoj_task_ext.probe:check'}
            (extension/'runtime.json').write_text(json.dumps(spec))
            files, data = runtime_materials({TASK:task},root)
            self.assertEqual(set(data['extensions']),{'task.probe','fluid.thin_film','fluid.common'})
            self.assertIn('src/caeoj_task_ext/probe/__init__.py',files)
            self.assertFalse(any('caeoj_tools' in path for path in files))
            spec['requires']=['task.probe']; (extension/'runtime.json').write_text(json.dumps(spec))
            with self.assertRaisesRegex(ValueError,'Cyclic'):
                runtime_materials({TASK:task},root)
            spec['requires']=['absent']; (extension/'runtime.json').write_text(json.dumps(spec))
            with self.assertRaisesRegex(ValueError,'Missing'):
                runtime_materials({TASK:task},root)
            spec['requires']=[];spec['files']=['../private.py'];(extension/'runtime.json').write_text(json.dumps(spec))
            with self.assertRaisesRegex(ValueError,'Invalid runtime'):
                runtime_materials({TASK:task},root)

    def test_all_authored_tasks_have_explicit_bindings_and_minimal_public_core(self):
        data=json.loads((ROOT/'qbank/extensions/caeoj_bundle/runtime.json').read_text(encoding='utf-8'))
        names={p.parent.name for p in ROOT.glob('qbank/*/*/*/instruction.md')}
        self.assertEqual(names,set(data['tasks']))
        files,runtime_data=runtime_materials({TASK:task_directory(TASK,ROOT)},ROOT)
        self.assertEqual(runtime_data['extensions'],{})
        self.assertFalse(any('caeoj_ext/' in path for path in files))
        self.assertIn('src/caeoj_bundle/runtime.json',files)
        self.assertNotIn('caeoj-maint',files['pyproject.toml'].decode())
