"""Check public/private task separation and Harbor score aggregation."""
from caeoj.storage import write_hdf5
from caeoj.validation import read_hdf5
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch
import zipfile
from task_fixtures import project_fixture

ROOT = Path(__file__).resolve().parents[1]
TASK = 'heat-conduction-steady-2d'
TASK_PATH = Path('qbank/01-prescribed-pdes/1.1-elliptic') / TASK


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


sys.path.insert(0, str(ROOT / 'src/utils'))
try:
    import publish_dist as publisher
    prepare = module('prepare_harbor', ROOT / 'src/utils/prepare_harbor.py')
finally:
    sys.path.pop(0)
judge = module('harbor_judge', ROOT / 'src/utils/harbor/tests/judge.py')


class HarborTests(unittest.TestCase):
    def setUp(self):
        (ROOT / 'runs').mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=ROOT / 'runs')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        project_fixture(self.root, [TASK])
        task = self.root/TASK_PATH
        # These tests need two independent cases; sample fixtures remain complete.
        for case in sorted((task/'cases').iterdir())[2:]:
            shutil.rmtree(case)
            shutil.rmtree(task/'reference'/case.name)

    def set_policy(self, policy):
        from caeoj_tools.grading_policy import write_direct_grading
        task=self.root/TASK_PATH
        for reference in list((task/'reference').iterdir())+list((task/'samples').glob('*/reference')):
            write_direct_grading(reference,policy)

    def prepared(self):
        publisher.publish(TASK, root=self.root)
        return Path(prepare.prepare(TASK, self.root)['task_directory'])

    def test_explicit_public_assets_are_hashed_and_do_not_include_author_files(self):
        import hashlib
        task = self.root / TASK_PATH
        (task / 'public').mkdir()
        (task / 'public/source.txt').write_text('public source')
        (task / 'author/secret.txt').write_text('private reference')
        descriptor = {'version': 1, 'files': [{'path': 'public/source.txt',
                      'sha256': hashlib.sha256(b'public source').hexdigest()}]}
        (task / 'public-materials.json').write_text(json.dumps(descriptor))
        files, _ = publisher.collect_materials(TASK, self.root)
        self.assertEqual(files[f'{TASK_PATH.as_posix()}/public/source.txt'], b'public source')
        self.assertFalse(any(name.endswith('secret.txt') for name in files))
        descriptor['files'][0]['sha256'] = '0'*64
        (task / 'public-materials.json').write_text(json.dumps(descriptor))
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            publisher.collect_materials(TASK, self.root)
        descriptor['files'][0]['path'] = 'public/../author/secret.txt'
        (task / 'public-materials.json').write_text(json.dumps(descriptor))
        with self.assertRaisesRegex(ValueError, 'under public'):
            publisher.collect_materials(TASK, self.root)

    def test_source_repair_stages_a_trusted_backend_and_keeps_oracle_private(self):
        task = self.root / TASK_PATH
        config = {'version': 1, 'base_image': 'local-repair:test',
                  'replacements': [{'submission': 'Assembly.cpp', 'target': '/opt/source/Assembly.cpp'}],
                  'build_directory': '/opt/build', 'build_target': 'core',
                  'build_timeout_seconds': 123, 'baseline_timeout_seconds': 300, 'max_source_bytes': 1048576,
                  'rebuild_files': ['/opt/build/assembly.o'],
                  'runner': f'/app/{TASK_PATH.as_posix()}/public/run_case.py'}
        (task / 'harbor').mkdir(exist_ok=True)
        (task / 'harbor/source-repair.json').write_text(json.dumps(config))
        (task / 'author/generated').mkdir()
        (task / 'author/generated/Assembly.cpp').write_text('// private oracle\n')
        # The standard fixture must expose the new trusted backend template.
        shutil.copyfile(ROOT/'src/utils/harbor/tests/source_repair.py',
                        self.root/'src/utils/harbor/tests/source_repair.py')
        directory = self.prepared()
        self.assertEqual(json.loads((directory/'tests/source-repair.json').read_text()), config)
        self.assertTrue((directory/'tests/source_repair.py').is_file())
        self.assertIn('FROM --platform=linux/amd64 local-repair:test',
                      (directory/'environment/Dockerfile').read_text())
        self.assertIn('COPY . /tests', (directory/'tests/Dockerfile').read_text())
        self.assertEqual((directory/'solution/Assembly.cpp').read_text(), '// private oracle\n')
        self.assertNotIn('baseline.py', (directory/'solution/solve.sh').read_text())
        instruction = (directory/'instruction.md').read_text(encoding='utf-8')
        self.assertIn('不提交 solve.py', instruction)
        self.assertNotIn('python /app/submission/solve.py', instruction)
        with zipfile.ZipFile(directory/'environment/agent.zip') as archive:
            readme = archive.read('README.md').decode('utf-8')
            self.assertNotIn('python solve.py', readme)
            self.assertIn('源码修复材料', readme)
        with zipfile.ZipFile(directory/'environment/agent.zip') as archive:
            self.assertFalse(any('Assembly.cpp' in name or 'source_repair.py' in name for name in archive.namelist()))

    def test_source_repair_rejects_ambiguous_or_command_like_configuration(self):
        from caeoj_tools.source_repair import configuration
        task = self.root / TASK_PATH
        (task / 'harbor').mkdir(exist_ok=True)
        config = {'version': 1, 'base_image': 'bad\nRUN false', 'replacements': [],
                  'build_directory': '/opt/build', 'build_target': 'core',
                  'build_timeout_seconds': 300, 'max_source_bytes': 1024, 'runner': '/app/run.py',
                  'rebuild_files': ['/opt/build/assembly.o']}
        path = task / 'harbor/source-repair.json'
        path.write_text(json.dumps(config))
        with self.assertRaisesRegex(ValueError, 'base image'):
            configuration(task, self.root)
        config['base_image'] = 'repair:test'
        config['replacements'] = [{'submission': '../a.cpp', 'target': '/opt/a.cpp'}]
        path.write_text(json.dumps(config))
        with self.assertRaisesRegex(ValueError, 'plain supported'):
            configuration(task, self.root)
        for suffix in ('py', 'f90', 'hpp', 'inl'):
            config['replacements'] = [{'submission': 'material.' + suffix,
                                       'target': '/opt/source/material.' + suffix}]
            path.write_text(json.dumps(config))
            self.assertEqual(configuration(task, self.root)['replacements'], config['replacements'])
        for budget in (0, -1, True, 1.5, '300'):
            config['baseline_timeout_seconds'] = budget
            path.write_text(json.dumps(config))
            with self.assertRaisesRegex(ValueError, 'baseline_timeout_seconds'):
                configuration(task, self.root)
        config.pop('baseline_timeout_seconds')
        config['replacements'] = [{'submission': 'material.py.sh', 'target': '/opt/source/material.py.sh'}]
        path.write_text(json.dumps(config))
        with self.assertRaisesRegex(ValueError, 'plain supported'):
            configuration(task, self.root)

    def test_source_repair_baseline_budget_reaches_executor_without_changing_probe_or_candidate(self):
        backend = module('repair_budget_backend', ROOT/'src/utils/harbor/tests/source_repair.py')
        for baseline_budget, candidate_budget in ((300, 600), (None, 300), (None, 30)):
            with self.subTest(baseline_budget=baseline_budget, candidate_budget=candidate_budget):
                base = self.root/('budget-'+str(baseline_budget)+'-'+str(candidate_budget))
                submission, build, logs = base/'submission', base/'build', base/'logs'
                submission.mkdir(parents=True)
                build.mkdir()
                (submission/'Core.cpp').write_text('// candidate')
                source, artifact = base/'Core.cpp', build/'core.o'
                source.write_text('// original')
                artifact.write_bytes(b'original object')
                config = {'replacements': [{'submission': 'Core.cpp', 'target': str(source)}],
                          'build_directory': str(build), 'rebuild_files': [str(artifact)],
                          'max_source_bytes': 1024, 'build_timeout_seconds': candidate_budget,
                          'baseline_probe': ['/usr/bin/true']}
                if baseline_budget is not None:
                    config['baseline_timeout_seconds'] = baseline_budget
                config_file = base/'config.json'
                config_file.write_text(json.dumps(config))
                calls = []
                def compile_fixture(config, label, timeout, command_override=None):
                    calls.append((label, timeout))
                    if command_override:
                        return {'status': 'ready'}
                    self.assertFalse(artifact.exists())
                    artifact.write_bytes(source.read_bytes())
                    return {'status': 'built'}
                with patch.object(backend, 'CONFIG', config_file), patch.object(backend, 'SUBMISSION', submission), \
                     patch.object(backend, 'LOGS', logs), patch.object(backend, 'compile_source', compile_fixture), \
                     patch.object(backend.os, 'chown', create=True):
                    self.assertTrue(backend.prepare())
                self.assertEqual(calls, [('baseline', baseline_budget or min(60, candidate_budget)),
                                         ('baseline-probe', min(60, candidate_budget)),
                                         ('candidate', candidate_budget)])
                self.assertEqual(source.read_text(), '// candidate')
                # Windows cleanup needs write permission on the now frozen file.
                artifact.chmod(0o666)

    def test_instruction_lists_only_published_sample_assets(self):
        task = self.root / TASK_PATH
        for example in task.glob('samples/*/output/result.h5'):
            example.unlink()
        directory = self.prepared()
        instruction = (directory/'instruction.md').read_text(encoding='utf-8')
        self.assertNotIn('output/result.h5', instruction)
        self.assertNotIn('完整提交示例', instruction)
        with zipfile.ZipFile(directory/'environment/agent.zip') as bundle:
            for sample in ('01', '02'):
                for relative in ('input/problem.json', 'reference/grading.json', 'reference/reference.h5'):
                    name = f'{TASK_PATH.as_posix()}/samples/{sample}/{relative}'
                    self.assertIn(name, bundle.namelist())
                    self.assertIn(f'`/app/{name}`', instruction)
        self.assertIn('python -m caeoj grade', instruction)

    def test_instruction_handles_mixed_sample_examples(self):
        task = self.root / TASK_PATH
        (task/'samples/01/output/result.h5').unlink()
        directory = self.prepared()
        instruction = (directory/'instruction.md').read_text(encoding='utf-8')
        self.assertNotIn(f'{TASK_PATH.as_posix()}/samples/01/output/result.h5', instruction)
        self.assertIn(f'`/app/{TASK_PATH.as_posix()}/samples/02/output/result.h5`', instruction)
        self.assertEqual(instruction.count('完整提交示例：'), 1)

    def test_declared_nested_assets_survive_staging_and_can_be_graded(self):
        from caeoj.sdk import load_problem
        from caeoj.case_grading import grade_case
        task = self.root/TASK_PATH
        path = sorted((task/'cases').glob('*/problem.json'))[0]
        manifest = json.loads(path.read_text(encoding='utf-8'))
        names = [manifest['data_file']]
        names += [item['file'] for table in ('meshes','geometries') for item in manifest[table].values()]
        moved = {}
        for name in dict.fromkeys(names):
            target = path.parent/'assets/nested'/name
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.move(path.parent/name,target)
            moved[name] = 'assets/nested/'+name
        manifest['data_file'] = moved[manifest['data_file']]
        for table in ('meshes','geometries'):
            for item in manifest[table].values():item['file'] = moved[item['file']]
        path.write_text(json.dumps(manifest))
        (path.parent/'assets/private-notes.txt').write_text('not an input dependency')
        load_problem(path)
        directory = self.prepared()
        staged = directory/'tests/cases'/path.parent.name/'problem.json'
        load_problem(staged)
        for name in moved.values():
            self.assertEqual((path.parent/name).read_bytes(),(staged.parent/name).read_bytes())
        self.assertFalse((staged.parent/'assets/private-notes.txt').exists())
        reference = directory/'tests/reference'/path.parent.name
        self.assertEqual(grade_case(staged,reference/'reference.h5',reference/'grading.json')['score'],1)

    def test_public_sample_can_be_scored_and_is_identified_in_judge_report(self):
        from caeoj_tools import data_pool as pool
        task = self.root/TASK_PATH
        value = {'schema_version':4,'task_id':'caeoj-000123',
                 'repository':{'repo_id':'test/fixtures','repo_type':'dataset','path':TASK_PATH.as_posix()}}
        pool.pack(task,self.root/'bundle',value)
        selection = pool.manifest(self.root/'bundle/selection.json')
        pool.write_json(task/'data-manifest.json',selection)
        pool.assemble(task,selection,pool.LocalStore(self.root/'bundle/repository'))
        self.assertEqual(len(pool.verify(task,strict=True)['public_cases']),1)
        directory = self.prepared()
        private, logs = directory/'tests', self.root/'public-case-logs'
        public = json.loads((private/'selection.json').read_text(encoding='utf-8'))['public_cases']
        self.assertEqual(public[0]['case'],'01-constant-dirichlet')
        def execution(work, timeout, case_logs):
            write_hdf5(work/'result.h5',read_hdf5(private/'reference'/case_logs.name/'reference.h5'))
        with patch.object(judge,'TESTS',private),patch.object(judge,'LOGS',logs), \
                patch.object(judge,'freeze_submission',return_value=True), \
                patch.object(judge,'execute',side_effect=execution),patch.object(judge.os,'chown',create=True):
            judge.main()
        report = json.loads((logs/'report.json').read_text(encoding='utf-8'))
        self.assertEqual(report['score'],2)
        self.assertEqual(report['total_cases'],2)
        self.assertEqual(report['public_cases'],public)
        row = next(row for row in report['cases'] if row['case']==public[0]['case'])
        self.assertEqual(row['public_sample'],'01')

    def test_actual_case_count_drives_verifier_budget_and_keeps_larger_override(self):
        template = (ROOT / 'src/utils/harbor/task.toml').read_text(encoding='utf-8')
        config = {'timeout_seconds': 600,
                  'verifier_budget': {'base_seconds': 300, 'per_case_overhead_seconds': 60}}
        merged = tomllib.loads(prepare.task_config(template, {}, judge_config=config, case_count=3))
        self.assertEqual(merged['verifier']['timeout_sec'], 2460)
        self.assertEqual(merged['verifier']['network_mode'], 'no-network')
        self.assertEqual(merged['environment']['gpus'], 0)
        merged = tomllib.loads(prepare.task_config(template, {'verifier': {'timeout_sec': 5000}},
                                                   judge_config=config, case_count=3))
        self.assertEqual(merged['verifier']['timeout_sec'], 5000)

    def test_unknown_case_count_and_invalid_budget_are_not_silently_guessed(self):
        template = (ROOT / 'src/utils/harbor/task.toml').read_text(encoding='utf-8')
        config = {'timeout_seconds': 600,
                  'verifier_budget': {'base_seconds': 300, 'per_case_overhead_seconds': 60}}
        for count in (None, 0, True, 1.5):
            with self.subTest(count=count), self.assertRaises(ValueError):
                prepare.task_config(template, {}, judge_config=config, case_count=count)
        for budget in ({}, {'base_seconds': 300, 'per_case_overhead_seconds': -1},
                       {'base_seconds': float('nan'), 'per_case_overhead_seconds': 60}):
            with self.subTest(budget=budget), self.assertRaises(ValueError):
                prepare.task_config(template, {}, judge_config={**config, 'verifier_budget': budget}, case_count=3)

    def test_output_byte_cap_is_optional_but_regular_file_is_always_required(self):
        output = self.root / 'out.h5'
        output.write_bytes(b'12345')
        self.assertIsNone(judge.output_limit({'max_output_bytes': None}))
        self.assertEqual(judge.output_limit({}), 128 * 1024**2)
        self.assertTrue(judge.output_within_limit(output, None))
        self.assertFalse(judge.output_within_limit(output, 4))
        self.assertFalse(judge.output_within_limit(self.root, None))

    def test_quantity_policy_is_bound_per_case_in_real_private_grader(self):
        task = self.root / TASK_PATH
        policy = {'version': 2, 'quantities': {'temperature': {'unit': 'K', 'rule': {
            'metric': 'pointwise', 'time': 'per_time', 'components': 'per_component',
            'atol': .01, 'rtol': 0}}}}
        self.set_policy(policy)
        config_path = task / 'judge-config.json'
        config = json.loads(config_path.read_text(encoding='utf-8'))
        config_path.write_text(json.dumps(config))
        cases = sorted((task / 'cases').glob('*/problem.json'))
        manifest = json.loads(cases[1].read_text(encoding='utf-8'))
        manifest['outputs']['renamed_observation'] = manifest['outputs'].pop('temperature')
        cases[1].write_text(json.dumps(manifest))
        directory = self.prepared()
        private = directory / 'tests'; logs = self.root / 'quantity-logs'
        def execute(work, timeout, case_logs):
            arrays = read_hdf5(private / 'reference' / case_logs.name / 'reference.h5')
            if case_logs.name == cases[1].parent.name:
                arrays['temperature'] += .02
            write_hdf5(work / 'result.h5', arrays)
        with patch.object(judge, 'TESTS', private), patch.object(judge, 'LOGS', logs), \
             patch.object(judge, 'freeze_submission', return_value=True), \
             patch.object(judge, 'execute', side_effect=execute), patch.object(judge.os, 'chown', create=True):
            judge.main()
        report = json.loads((logs / 'report.json').read_text(encoding='utf-8'))
        self.assertEqual(report['score'], 1)
        self.assertEqual(report['reward'], .5)
        self.assertEqual(set(report['evaluation_manifest']), {row['case'] for row in report['cases']})
        self.assertEqual(set(report['cases'][1]['checks']['outputs']['fields']), {'renamed_observation'})
        self.assertIn('grading_sha256', report['cases'][1])

    def test_unknown_quantity_fails_preflight_before_submission_execution(self):
        task = self.root / TASK_PATH
        (task/'author').mkdir(parents=True,exist_ok=True)
        (task / 'author/grading-template.json').write_text(json.dumps({'version': 2, 'quantities': {
            'temperature': {'unit': 'K', 'rule': {'metric': 'pointwise', 'time': 'per_time',
            'components': 'per_component', 'atol': .01, 'rtol': 0}}}}))
        config_path = task / 'judge-config.json'
        config = json.loads(config_path.read_text(encoding='utf-8'))
        config_path.write_text(json.dumps(config))
        directory = self.prepared()
        path = next((directory / 'tests/cases').glob('*/problem.json'))
        manifest = json.loads(path.read_text(encoding='utf-8'))
        manifest['outputs']['temperature']['quantity'] = 'unknown'
        path.write_text(json.dumps(manifest))
        logs = self.root / 'bad-quantity-logs'
        with patch.object(judge, 'TESTS', directory / 'tests'), patch.object(judge, 'LOGS', logs), \
             patch.object(judge, 'freeze_submission') as freeze, patch.object(judge, 'execute') as execute:
            with self.assertRaisesRegex(ValueError, 'No grading rule'):
                judge.main()
            freeze.assert_not_called(); execute.assert_not_called()
        self.assertFalse((logs / 'reward.txt').exists())

    def test_prepare_requires_published_materials(self):
        with self.assertRaisesRegex(ValueError, 'publish_dist.py'):
            prepare.prepare(TASK, self.root)

    def test_changed_public_contract_requires_republishing(self):
        publisher.publish(TASK, root=self.root)
        contract = self.root / 'docs/CONTRACT.md'
        contract.write_bytes(contract.read_bytes() + b'\nUpdated storage convention.\n')
        with self.assertRaisesRegex(ValueError, 'stale.*publish_dist.py'):
            prepare.prepare(TASK, self.root)
        self.prepared()

    def test_changed_sdk_requires_republishing(self):
        publisher.publish(TASK, root=self.root)
        sdk = self.root / 'src/caeoj/sdk.py'
        sdk.write_bytes(sdk.read_bytes() + b'\n# Updated reader.\n')
        with self.assertRaisesRegex(ValueError, 'stale.*publish_dist.py'):
            prepare.prepare(TASK, self.root)

    def test_modified_archive_requires_republishing(self):
        publisher.publish(TASK, root=self.root)
        archive = self.root / 'dist' / f'{TASK}-agent.zip'
        with zipfile.ZipFile(archive, 'a') as bundle:
            bundle.writestr('obsolete-tool.py', 'old interface')
        with self.assertRaisesRegex(ValueError, 'stale.*publish_dist.py'):
            prepare.prepare(TASK, self.root)

    def test_build_context_contains_only_public_release(self):
        directory = self.prepared()
        self.assertEqual(directory, self.root / 'runs/harbor/tasks' / TASK)
        self.assertEqual({p.name for p in (directory / 'environment').iterdir()},
                         {'Dockerfile', 'agent.zip', 'requirements.txt'})
        with zipfile.ZipFile(directory / 'environment/agent.zip') as bundle:
            self.assertFalse(any('/author/' in p or '/cases/' in p or p.startswith(TASK_PATH.as_posix()+'/reference/') for p in bundle.namelist()))
        self.assertEqual(len(list((directory / 'tests/reference').glob('*/reference.h5'))), 2)
        self.assertTrue((directory / 'solution/baseline.py').is_file())
        self.assertEqual((directory / 'environment/requirements.txt').read_text(encoding='utf-8').strip(), 'scipy==1.18.1')
        instruction = (directory / 'instruction.md').read_text(encoding='utf-8')
        self.assertIn(f'/app/{TASK_PATH.as_posix()}/samples/01/input/problem.json', instruction)
        self.assertIn(f'/app/{TASK_PATH.as_posix()}/samples/02/', instruction)
        self.assertIn('read_constant', instruction)
        self.assertIn('read_field', instruction)
        for sample in ('01', '02'):
            self.assertIn(f'`/app/{TASK_PATH.as_posix()}/samples/{sample}/output/result.h5`', instruction)
        self.assertNotIn('${', instruction)
        config = tomllib.loads((directory / 'task.toml').read_text(encoding='utf-8'))
        self.assertEqual(config['verifier']['environment_mode'], 'separate')
        self.assertFalse((directory / 'tests/docker-compose.yaml').exists())
        self.assertEqual(config['artifacts'], ['/app/submission'])
        # Separate verification uses tests/ as its Docker build context.
        verifier_dockerfile = (directory / 'tests/Dockerfile').read_text(encoding='utf-8')
        self.assertTrue(verifier_dockerfile.endswith('COPY . /tests\n'))
        self.assertEqual((directory / 'tests/agent.zip').read_bytes(),
                         (directory / 'environment/agent.zip').read_bytes())
        self.assertEqual((directory / 'tests/requirements.txt').read_bytes(),
                         (directory / 'environment/requirements.txt').read_bytes())
        archive = self.root / 'dist' / f'{TASK}-agent.zip'
        self.assertEqual((directory / 'environment/agent.zip').read_bytes(), archive.read_bytes())
        published_mtime = archive.stat().st_mtime_ns
        for path in directory.rglob('*.sh'):
            self.assertNotIn(b'\r\n', path.read_bytes())
        jobs = self.root / 'runs/harbor/jobs'
        jobs.mkdir()
        (jobs / 'keep.log').write_text('keep')
        (directory / 'obsolete.txt').write_text('old')
        prepare.prepare(TASK, self.root)
        self.assertEqual(archive.stat().st_mtime_ns, published_mtime)
        self.assertFalse((directory / 'obsolete.txt').exists())
        self.assertEqual((jobs / 'keep.log').read_text(encoding='utf-8'), 'keep')

    def test_another_task_reuses_templates_and_overrides_resources(self):
        task = 'another-transport-task'
        source = self.root / TASK_PATH.parent / task
        shutil.copytree(self.root / TASK_PATH, source)
        for path in source.rglob('problem.json'):
            problem = json.loads(path.read_text(encoding='utf-8'))
            problem['task'] = task
            path.write_text(json.dumps(problem))
        (source / 'harbor/task.toml').write_text(
            '[agent]\ntimeout_sec = 240.0\n[environment]\ncpus = 1\nmemory_mb = 1024\n'
            '[verifier]\ntimeout_sec = 60.0\n')
        config_path = source / 'judge-config.json'
        judge_config = json.loads(config_path.read_text(encoding='utf-8'))
        judge_config['timeout_seconds'] = 15
        config_path.write_text(json.dumps(judge_config))
        binding_path = self.root/'qbank/extensions/caeoj_bundle/runtime.json'
        binding = json.loads(binding_path.read_text(encoding='utf-8'))
        binding['tasks'][task] = []
        binding_path.write_text(json.dumps(binding))
        publisher.publish(task, root=self.root)
        directory = Path(prepare.prepare(task, self.root)['task_directory'])
        config = tomllib.loads((directory / 'task.toml').read_text(encoding='utf-8'))
        self.assertEqual(config['agent']['timeout_sec'], 240)
        self.assertEqual(config['environment']['cpus'], 1)
        self.assertEqual(config['environment']['memory_mb'], 1024)
        self.assertEqual(config['verifier']['timeout_sec'], 570)  # 300 + 2 * (15 + 60 evaluation + 60 overhead)
        self.assertEqual(config['verifier']['environment_mode'], 'separate')
        instruction = (directory / 'instruction.md').read_text(encoding='utf-8')
        self.assertIn(f'/app/{(TASK_PATH.parent / task).as_posix()}/samples/01/', instruction)
        self.assertIn('15 秒', instruction)
        self.assertNotIn(TASK, instruction)

    def test_task_without_harbor_config_uses_shared_defaults(self):
        requirements = self.root / TASK_PATH / 'harbor/requirements.txt'
        requirements.unlink()
        resource_config = self.root / TASK_PATH / 'harbor/task.toml'
        if resource_config.exists():
            resource_config.unlink()
        directory = self.prepared()
        self.assertEqual((directory / 'environment/requirements.txt').read_bytes(), b'')
        config = tomllib.loads((directory / 'task.toml').read_text(encoding='utf-8'))
        self.assertEqual(config['agent']['timeout_sec'], 1800)
        self.assertNotIn('cpus', config['environment'])
        self.assertNotIn('memory_mb', config['environment'])

    def test_quantity_policy_allows_different_output_fields_per_case(self):
        source = self.root / TASK_PATH
        path = sorted((source / 'cases').glob('*/problem.json'))[-1]
        manifest = json.loads(path.read_text(encoding='utf-8'))
        manifest['outputs']['other_temperature'] = manifest['outputs'].pop('temperature')
        path.write_text(json.dumps(manifest))
        # The array key and reference stay identical; only the logical field
        # name varies. Quantity binding covers either field name.
        directory = self.prepared()
        self.assertTrue((directory / 'tests/cases' / path.parent.name / 'problem.json').is_file())

    def test_no_baseline_task_assembles_and_declares_provisional_limits(self):
        (self.root / TASK_PATH / 'author/baseline.py').unlink()
        config_path = self.root / TASK_PATH / 'judge-config.json'
        config = json.loads(config_path.read_text(encoding='utf-8'))
        config.update(stage='provisional', max_output_bytes=2*1024**3)
        policy_path = next((self.root/TASK_PATH/'reference').glob('*/grading.json'))
        policy = json.loads(policy_path.read_text(encoding='utf-8'))
        policy['checks'][0]['policy']['quantities']['temperature']['rule'].update(atol=0.1, rtol=0.2)
        policy_path.write_text(json.dumps(policy))
        config_path.write_text(json.dumps(config))
        publisher.publish(TASK, root=self.root)
        result = prepare.prepare(TASK, self.root)
        directory = Path(result['task_directory'])
        self.assertFalse(result['oracle_available'])
        self.assertFalse((directory / 'solution').exists())
        self.assertTrue((directory / 'tests/judge.py').is_file())
        instruction = (directory / 'instruction.md').read_text(encoding='utf-8')
        self.assertNotIn('宽松试运行', instruction)
        self.assertNotIn('校准', instruction)
        self.assertNotIn('Harbor', instruction)
        self.assertNotIn('独立内存限制', instruction)
        self.assertNotIn('0.1 + 0.2×', instruction)
        self.assertIn('1024 MB', instruction)
        self.assertIn(str(2*1024**3), instruction)

    def test_public_case_policy_and_private_grader_agree(self):
        task = self.root / TASK_PATH
        policy = {'version': 1, 'fields': {'temperature': {
            'all': [
                {'metric': 'rmse', 'time': 'per_time', 'components': 'per_component', 'limit': .01},
                {'metric': 'violation_fraction', 'time': 'per_time', 'components': 'joint',
                 'count': 'spatial_points', 'atol': .02, 'rtol': 0, 'limit': .01}]}}}
        self.set_policy(policy)
        config_path = task / 'judge-config.json'
        config = json.loads(config_path.read_text(encoding='utf-8'))
        config_path.write_text(json.dumps(config))
        directory = self.prepared()
        self.assertNotIn('空间点', (directory / 'instruction.md').read_text(encoding='utf-8'))
        self.assertNotIn(' 且 ', (directory / 'instruction.md').read_text(encoding='utf-8'))
        with zipfile.ZipFile(directory / 'environment/agent.zip') as archive:
            public = json.loads(archive.read(f'{TASK_PATH.as_posix()}/samples/01/reference/grading.json'))
            self.assertEqual(public['checks'][0]['policy'], policy)
            self.assertNotIn(f'{TASK_PATH.as_posix()}/grading.json', archive.namelist())
            self.assertIn('src/caeoj/grading.schema.json', archive.namelist())
        private = directory / 'tests'; logs = self.root / 'policy-logs'
        names = sorted(p.name for p in (private / 'cases').iterdir())
        def execution(work, timeout, case_logs):
            if case_logs.name == names[1]:
                snapshot = json.loads((logs / 'report.json').read_text(encoding='utf-8'))
                self.assertEqual(snapshot['completed_cases'], 1)
                self.assertFalse(snapshot['complete'])
                self.assertFalse((logs / 'reward.txt').exists())
            arrays = read_hdf5(private / 'reference' / case_logs.name / 'reference.h5')
            if case_logs.name == names[1]: arrays['temperature'] += .02
            write_hdf5(work / 'result.h5', arrays)
            return None
        with patch.object(judge, 'TESTS', private), patch.object(judge, 'LOGS', logs), \
                patch.object(judge, 'freeze_submission', return_value=True), \
                patch.object(judge, 'execute', side_effect=execution), \
                patch.object(judge.os, 'chown', create=True):
            judge.main()
        report = json.loads((logs / 'report.json').read_text(encoding='utf-8'))
        self.assertEqual(report['score'], 1)
        self.assertTrue(report['complete'])
        self.assertEqual(set(report['evaluation_manifest']), {row['case'] for row in report['cases']})
        self.assertIn('elapsed_seconds', report['cases'][0])
        self.assertEqual(report['cases'][1]['checks']['outputs']['fields']['temperature']['operator'], 'all')
        policy['fields']['temperature']['all'][0]['limit'] = .1
        self.set_policy(policy)
        with self.assertRaisesRegex(ValueError, 'stale'):
            prepare.prepare(TASK, self.root)

    def test_output_size_limit_is_configurable_with_explicit_default(self):
        self.assertEqual(judge.output_limit({}),128*1024**2)
        for bad in (0,-1,True,1.5,'100'):
            with self.assertRaises(ValueError):judge.output_limit({'max_output_bytes':bad})
        path=self.root/'large-result.h5'
        # Sparse file tests the actual size guard without allocating a large
        # array; subsequent HDF5/contract validation remains the grader's job.
        with path.open('wb') as stream:stream.truncate(129*1024**2)
        self.assertFalse(judge.output_within_limit(path,judge.output_limit({})))
        self.assertTrue(judge.output_within_limit(path,judge.output_limit({'max_output_bytes':2*1024**3})))

    def test_compilation_uses_writable_per_case_copy_without_changing_submission(self):
        submission = self.root / 'canonical-submission'
        submission.mkdir()
        (submission / 'solve.py').write_text('original source')
        executable = submission / 'core'
        executable.write_text('compiled helper')
        executable.chmod(0o755)
        with patch.object(judge, 'SUBMISSION', submission), patch.object(judge.os, 'chown', create=True):
            self.assertTrue(judge.freeze_submission())
            if sys.platform != 'win32':
                self.assertTrue(executable.stat().st_mode & 0o111)
            for index in range(2):
                work = self.root / f'work-{index}'
                logs = self.root / f'logs-{index}'
                work.mkdir(); logs.mkdir()
                def spawn(command, **kwargs):
                    self.assertEqual(command[6], str(work / 'submission/solve.py'))
                    self.assertEqual((work / 'submission/solve.py').read_text(encoding='utf-8'), 'original source')
                    (work / 'submission/solve.py').write_text('runtime change')
                    (work / 'submission/core.so').write_text('runtime compiled helper')
                    from unittest.mock import Mock
                    process = Mock(pid=12345)
                    process.wait.return_value = 0
                    return process
                with patch.object(judge.subprocess, 'Popen', side_effect=spawn), \
                        patch.object(judge.os, 'killpg', create=True), \
                        patch.object(judge.signal, 'SIGKILL', 9, create=True):
                    self.assertIsNone(judge.execute(work, 1, logs))
                self.assertEqual((submission / 'solve.py').read_text(encoding='utf-8'), 'original source')
                self.assertFalse((submission / 'core.so').exists())

    def test_resource_overrides_cannot_change_judging_interface(self):
        (self.root / TASK_PATH / 'harbor/task.toml').write_text(
            '[verifier]\nenvironment_mode = "same"\n')
        publisher.publish(TASK, root=self.root)
        with self.assertRaisesRegex(ValueError, 'Unsupported Harbor config field'):
            prepare.prepare(TASK, self.root)

    def test_actual_grader_aggregates_pass_and_fail(self):
        directory = self.prepared()
        private = directory / 'tests'
        config_path = private / 'judge-config.json'
        config = json.loads(config_path.read_text(encoding='utf-8'))
        config['stage'] = 'provisional'
        config_path.write_text(json.dumps(config))
        logs = self.root / 'judge-logs'
        names = sorted(p.name for p in (private / 'cases').iterdir())

        def execution(work, timeout, case_logs):
            arrays = read_hdf5(private / 'reference' / case_logs.name / 'reference.h5')
            if case_logs.name == names[1]:
                arrays['temperature'] += 0.02
            write_hdf5(work / 'result.h5', arrays)
            return None

        with patch.object(judge, 'TESTS', private), patch.object(judge, 'LOGS', logs), \
                patch.object(judge, 'freeze_submission', return_value=True), \
                patch.object(judge, 'execute', side_effect=execution), \
                patch.object(judge.os, 'chown', create=True):
            judge.main()
        report = json.loads((logs / 'report.json').read_text(encoding='utf-8'))
        self.assertEqual([row['score'] for row in report['cases']], [1, 0])
        self.assertEqual(report['score'], 1)
        self.assertEqual(report['total_cases'], 2)
        self.assertEqual(report['stage'], 'provisional')
        self.assertEqual(report['limits']['timeout_seconds'], config['timeout_seconds'])
        self.assertIsNone(report['limits']['max_output_bytes'])
        self.assertEqual(float((logs / 'reward.txt').read_text(encoding='utf-8')), 0.5)

    def test_evaluation_timeout_is_infrastructure_error_without_reward(self):
        directory = self.prepared()
        private = directory / 'tests'
        logs = self.root / 'evaluation-timeout'
        def execution(work, timeout, case_logs):
            write_hdf5(work / 'result.h5', read_hdf5(private / 'reference' / case_logs.name / 'reference.h5'))
        with patch.object(judge, 'TESTS', private), patch.object(judge, 'LOGS', logs), \
                patch.object(judge, 'freeze_submission', return_value=True), \
                patch.object(judge, 'execute', side_effect=execution), \
                patch.object(judge.os, 'chown', create=True), \
                patch.object(judge.subprocess, 'run', side_effect=subprocess.TimeoutExpired('evaluation', 60)):
            with self.assertRaisesRegex(RuntimeError, 'Evaluation infrastructure timeout'):
                judge.main()
        self.assertFalse((logs / 'reward.txt').exists())

    def test_bad_reference_is_infrastructure_error_without_reward(self):
        directory = self.prepared()
        private = directory / 'tests'
        reference = next((private / 'reference').glob('*/reference.h5'))
        reference.write_bytes(b'invalid HDF5')
        logs = self.root / 'judge-logs'
        with patch.object(judge, 'TESTS', private), patch.object(judge, 'LOGS', logs), \
                patch.object(judge, 'execute') as execute:
            with self.assertRaises(Exception):
                judge.main()
        execute.assert_not_called()
        self.assertFalse((logs / 'reward.txt').exists())

    def test_missing_or_duplicate_policy_source_fails_before_solver_execution(self):
        directory = self.prepared()
        private = directory / 'tests'
        original_policy=next((private/'reference').glob('*/grading.json'))
        for duplicate in (False, True):
            with self.subTest(duplicate=duplicate):
                config = json.loads((private/'judge-config.json').read_text(encoding='utf-8'))
                policy = original_policy
                if duplicate:
                    source=next((self.root/TASK_PATH/'reference').glob('*/grading.json'))
                    shutil.copyfile(source, policy)
                    config.update(atol=.01, rtol=0)
                    (private/'judge-config.json').write_text(json.dumps(config))
                else:
                    policy.unlink()
                logs = self.root/f'bad-policy-{duplicate}'
                with patch.object(judge, 'TESTS', private), patch.object(judge, 'LOGS', logs), \
                     patch.object(judge, 'freeze_submission') as freeze, patch.object(judge, 'execute') as execute:
                    with self.assertRaises((ValueError, FileNotFoundError)):
                        judge.main()
                    freeze.assert_not_called()
                    execute.assert_not_called()
                self.assertFalse((logs/'reward.txt').exists())


if __name__ == '__main__':
    unittest.main()
