"""Import the user-reviewed Solid26 snapshot through the existing pool APIs.

This is an author-side layout/import tool, not a numerical reference producer.
It never uploads data, changes formal selections, or starts a solver/agent.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import zipfile

ROSTER = ('elastic-solid-3d', 'elastic-beam', 'elastic-modes', 'elastic-transient',
          'hyperelastic-solid', 'elastic-buckling', 'j2-plasticity', 'linear-elastic-fracture')
FIXED = {'elastic-buckling', 'linear-elastic-fracture'}
COUNTS = dict(tasks=8, cases=26, public=8, held_out=18)
PROTOCOL = {'instruction.md', 'DATA.md', 'author/grading-template.json',
            'judge-config.json', 'harbor/task.toml'}
# Exact suffix of the frozen instructions, moved to the author review record.
LEGACY_INSTRUCTION_FOOTER = (
    '\n这些是待校准设计目标；契约工具验证不构成数值解、物理模型或参考精度的证据。正式数据、参考及评测发布另行完成。\n'
).encode('utf-8')
PROJECT = Path(__file__).resolve().parents[3]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def inside(root, relative):
    root, relative = Path(root).resolve(), Path(relative)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError(f'Unsafe relative source path: {relative}')
    path = root / relative
    if not path.resolve().is_relative_to(root):
        raise ValueError(f'Source escapes its root: {relative}')
    return path


def load_reviewed(source, project_root):
    source, project_root = Path(source), Path(project_root)
    manifest = read(source / 'task-manifest.json')
    accepted = read(source / 'reports/solid26/acceptance.json')
    if (accepted.get('schema_version') != 1 or accepted.get('status') != 'passed'
            or accepted.get('published') is not False or accepted.get('counts') != COUNTS):
        raise ValueError('Source is not the reviewed unpublished 8-task/26-case acceptance')
    tasks, rows = manifest['ordered_tasks'], accepted['cases']
    if len(tasks) != 8 or set(t['slug'] for t in tasks) != set(ROSTER):
        raise ValueError('Unexpected task roster')
    if len(rows) != 26 or len({(r['task'], r['case_id']) for r in rows}) != 26:
        raise ValueError('Missing or duplicate reviewed cases')
    if Counter(r['role'] for r in rows) != {'public': 8, 'held-out': 18}:
        raise ValueError('Unexpected public/held-out distribution')
    for task in tasks:
        selected = [r for r in rows if r['task'] == task['slug']]
        if len(selected) != (1 if task['slug'] in FIXED else 4) or sum(r['role'] == 'public' for r in selected) != 1:
            raise ValueError(f'Wrong case coverage: {task["slug"]}')
        if {f['path'] for f in task['copied_files']} != PROTOCOL:
            raise ValueError('Expected five original protocol/config files per task')
        for spec in task['copied_files']:
            path = inside(project_root, task['source_path']) / spec['path']
            if path.is_file():
                digest = hashlib.sha256(path.read_bytes())
                if digest.hexdigest() == spec['sha256']:
                    continue
                if spec['path'] == 'instruction.md':
                    digest.update(LEGACY_INSTRUCTION_FOOTER)
                    if digest.hexdigest() == spec['sha256']:
                        continue
            raise ValueError(f'Repository contract SHA mismatch: {path}')
    for row in rows:
        if (row['task'] not in ROSTER or row['case_dir'] != f'cases/{row["task"]}/{row["case_id"]}'
                or not all(row.get(k) is True for k in ('input_valid', 'reference_valid', 'baseline_valid'))
                or row.get('grader_score') != 1):
            raise ValueError('Invalid reviewed case identity or validation status')
        budget = row.get('reference_budget', {})
        if not budget or any(not isinstance(v, (int, float)) or isinstance(v, bool)
                             or not math.isfinite(v) or not 0 <= v < .2 for v in budget.values()):
            raise ValueError('Reference difference budget must remain below 0.2')
        artifacts = row.get('artifact_sha256', {})
        if not artifacts or row['baseline_result'] not in artifacts:
            raise ValueError('Baseline must be bound by the accepted artifact inventory')
        for relative, expected in artifacts.items():
            path = inside(source, relative)
            if not path.is_file() or sha(path) != expected:
                raise ValueError(f'Reviewed source artifact SHA mismatch: {relative}')
        prefix = row['case_dir'] + '/input/'
        expected_inputs = {p for p in artifacts if p.startswith(prefix)}
        actual_inputs = {p.relative_to(source).as_posix() for p in (source / row['case_dir'] / 'input').rglob('*') if p.is_file()}
        if actual_inputs != expected_inputs:
            raise ValueError('Unexpected or missing source input files')
    return {'task_manifest': manifest, 'acceptance': accepted}


def stage_task(source, task, rows, destination):
    source, destination = Path(source), Path(destination)
    if destination.exists():
        raise FileExistsError(f'Refusing to overwrite an import stage: {destination}')
    ordered = sorted(rows, key=lambda row: (row['role'] != 'public', row['case_id']))
    if not ordered or sum(r['role'] == 'public' for r in ordered) != 1:
        raise ValueError('One public case is required')
    destination.mkdir(parents=True)
    aliases = {}
    for number, row in enumerate(ordered, 1):
        alias = f'{number:03d}'
        aliases[row['case_id']] = alias
        origin = inside(source, row['case_dir'])
        for path in origin.rglob('*'):
            if path.is_symlink():
                raise ValueError(f'Imported case must not contain links: {path}')
        shutil.copytree(origin / 'input', destination / 'cases' / alias)
        reference = destination / 'reference' / alias
        reference.mkdir(parents=True)
        evidence = destination / 'author/data-evidence/source-cases' / alias
        for path in (origin / 'reference').iterdir():
            if path.name == 'reference-record.json':
                evidence.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, evidence / 'reference-record.original.json')
            elif path.is_file():
                shutil.copyfile(path, reference / path.name)
            else:
                shutil.copytree(path, reference / path.name)
        report = origin / 'reports/physics-verification.json'
        if report.is_file():
            evidence.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(report, evidence / report.name)
        if row['role'] == 'public':
            shutil.copytree(origin / 'input', destination / 'samples/001/input')
    return {'aliases': aliases, 'cases': len(ordered), 'public': 1}


def _copy_project(project, shadow, tasks):
    ignore = shutil.ignore_patterns('__pycache__', '*.pyc')
    for directory in ('src', 'docs', 'qbank/extensions'):
        shutil.copytree(project / directory, shadow / directory, ignore=ignore)
    for name in ('LICENSE', 'pyproject.toml'):
        target = shadow / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(project / name, target)
    for task in tasks:
        shutil.copytree(project / task['source_path'], shadow / task['source_path'],
                        ignore=shutil.ignore_patterns('__pycache__', 'cases', 'reference', 'samples',
                                                     'data-manifest.json', '.data-assembly.json'))


def build_import(source, output, project_root, task_ids, repo_id):
    # Match the upstream maintenance CLI's flat-module import environment.
    # prepare_harbor imports publish_dist from src/utils, not utils.publish_dist.
    sys.path.insert(0, str(Path(project_root).resolve() / 'src/utils'))
    from caeoj_tools import data_pool as pool
    from caeoj.case_grading import grade_case
    from publish_dist import publish
    from prepare_harbor import prepare

    source, output, project_root = Path(source).resolve(), Path(output).resolve(), Path(project_root).resolve()
    reviewed = load_reviewed(source, project_root)
    tasks, accepted = reviewed['task_manifest']['ordered_tasks'], reviewed['acceptance']
    if set(task_ids) != set(ROSTER) or len(set(task_ids.values())) != 8:
        raise ValueError('Supply eight distinct explicit task IDs')
    if output.exists():
        raise FileExistsError(f'Use a fresh output directory: {output}')
    if source == output or source in output.parents or output in source.parents:
        raise ValueError('Reviewed source and local output must be separate trees')
    old_selections = {}
    occupied = {}
    for path in (project_root / 'qbank').rglob('data-manifest.json'):
        occupied[read(path)['task_id']] = path.parent
    for task in tasks:
        path = project_root / task['source_path'] / 'data-manifest.json'
        old_selections[task['slug']] = sha(path) if path.is_file() else None
        identity = task_ids[task['slug']]
        if identity in occupied and occupied[identity] != path.parent:
            raise ValueError(f'Task ID already assigned: {identity}')
        if path.is_file() and read(path)['task_id'] != identity:
            raise ValueError('Cannot reassign an existing task identity')
    output.mkdir(parents=True)
    shadow = output / 'assembled-project'
    _copy_project(project_root, shadow, tasks)
    results = []
    for task in tasks:
        slug = task['slug']
        rows = [r for r in accepted['cases'] if r['task'] == slug]
        staged = output / 'prepared' / slug
        staged_info = stage_task(source, task, rows, staged)
        canonical = project_root / task['source_path'] / 'data-manifest.json'
        locator = pool.manifest(canonical) if canonical.exists() else {
            'schema_version': 4, 'task_id': task_ids[slug],
            'repository': {'repo_id': repo_id, 'repo_type': 'dataset', 'path': task['source_path']},
        }
        bundle = output / 'pools' / slug
        pool.pack(staged, bundle, locator)
        pool.validate_bundle(bundle)
        choice = pool.manifest(bundle / 'selection.json')
        target = shadow / task['source_path']
        pool.write_json(target / 'data-manifest.json', choice)
        assembled = pool.assemble(target, choice, pool.LocalStore(bundle / 'repository'))
        verified = pool.verify(target, strict=True)
        outcomes = []
        for row in rows:
            alias = staged_info['aliases'][row['case_id']]
            score = grade_case(target / 'cases' / alias / 'problem.json',
                               source / row['baseline_result'], target / 'reference' / alias / 'grading.json')
            grade_report = output / 'grading' / slug / f'{alias}.json'
            write(grade_report, score)
            if score['score'] != 1:
                raise ValueError(f'Imported baseline no longer passes: {slug}/{alias}')
            outcomes.append(dict(case_id=row['case_id'], alias=alias, role=row['role'], grader_score=1,
                                 pool_case_id=choice['cases'][alias]['case_id'],
                                 descriptor_sha256=choice['cases'][alias]['case']['sha256'],
                                 grade_report=grade_report.relative_to(output).as_posix(),
                                 grade_report_sha256=sha(grade_report)))
        publication = publish(slug, root=shadow)
        with zipfile.ZipFile(publication['archive']) as archive:
            prefix = task['source_path'] + '/'
            for name in archive.namelist():
                if name.startswith(prefix) and not (name in (prefix + 'instruction.md', prefix + 'DATA.md')
                                                    or name.startswith(prefix + 'samples/001/')):
                    raise ValueError(f'Non-public task material in candidate ZIP: {name}')
            public_row = next(r for r in rows if r['role'] == 'public')
            for path in (source / public_row['case_dir'] / 'input').rglob('*'):
                if path.is_file():
                    rel = path.relative_to(source / public_row['case_dir'] / 'input').as_posix()
                    if archive.read(prefix + 'samples/001/input/' + rel) != path.read_bytes():
                        raise ValueError('Public sample input bytes changed')
        harbor = prepare(slug, root=shadow)
        result = dict(task=slug, source_path=task['source_path'], requested_task_id=task_ids[slug],
                      cases=outcomes, public_cases=verified['public_cases'], local_pool_valid=verified['valid'],
                      pool_bundle=str(bundle.relative_to(output)), staged_selection=str((bundle/'selection.json').relative_to(output)),
                      pool_selection_sha256=sha(bundle/'selection.json'), publication=publication, harbor=harbor)
        results.append(result)
        print(f'{slug}: pool+strict assembly+public ZIP+Harbor prepared; {len(rows)} baseline regrades passed', flush=True)
    for task in tasks:
        path = project_root / task['source_path'] / 'data-manifest.json'
        if (sha(path) if path.is_file() else None) != old_selections[task['slug']]:
            raise ValueError('Formal selection changed unexpectedly')
    receipt = dict(schema_version=1, status='passed', published=False, remote_upload=False,
                   counts=COUNTS, source_acceptance_sha256=sha(source/'reports/solid26/acceptance.json'),
                   importer_sha256=sha(__file__),
                   source_contract_commit=reviewed['task_manifest'].get('source_commit'),
                   formal_selections_unchanged=True, local_store_revision='local', tasks=results,
                   numerical_references_recomputed=False, agent_benchmark_run=False,
                   source_policy='reviewed user-provided references; actual producers retained; not a new scientific source certification')
    write(output / 'IMPORT_RECEIPT.json', receipt)
    return receipt


def write_author_records(source, project_root, receipt):
    source, project_root = Path(source), Path(project_root)
    accepted = read(source / 'reports/solid26/acceptance.json')
    for task in receipt['tasks']:
        cases = []
        for item in task['cases']:
            row = next(r for r in accepted['cases'] if r['task'] == task['task'] and r['case_id'] == item['case_id'])
            physics = source / row['case_dir'] / 'reports/physics-verification.json'
            report = read(physics)
            cases.append({**item, 'reference_budget': row['reference_budget'],
                          'physics_status': report['status'], 'physics_report_sha256': sha(physics),
                          'source_artifacts_sha256': {p.removeprefix(row['case_dir']+'/'): h for p,h in row['artifact_sha256'].items()
                                                     if p.startswith(row['case_dir']+'/')},
                          'baseline_sha256': row['artifact_sha256'][row['baseline_result']],
                          'baseline_run_identity': row.get('run_identity'),
                          'method_as_recorded': report.get('reference_method', report.get('algorithm',
                                                 'See the hash-bound original physics report and author source snapshot'))})
        record = dict(schema_version=1, batch='solid8-reviewed-2026-11-17', task=task['task'],
                      status='reviewed-local-reference-import', published=False,
                      source_contract_commit=receipt['source_contract_commit'],
                      source_acceptance_sha256=receipt['source_acceptance_sha256'],
                      requested_task_id=task['requested_task_id'], cases=cases,
                      local_pool_valid=True, baseline_regrades_passed=len(cases),
                      staged_selection_sha256=task['pool_selection_sha256'],
                      candidate_zip_sha256=task['publication']['sha256'],
                      formal_selection_changed=False, hf_uploaded=False,
                      reference_origin='Existing user-reviewed local reference workspace; this importer only copies and validates bytes',
                      source_qualification='Preserve actual custom formulations/analytic evaluators and CalculiX attribution. Numerical user acceptance is not automatic compliance with the upstream external-reference provenance rule; maintainer source-policy review remains explicit before release.',
                      validation_scope='26 selected local cases; not complete task-family coverage or an agent/model score')
        write(project_root / task['source_path'] / 'author/data-evidence/solid8-2026-11-17.json', record)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True, help='Frozen user-reviewed Solid26 workspace')
    parser.add_argument('--output', type=Path, required=True, help='Fresh ignored local staging directory')
    parser.add_argument('--task-id-start', type=int, default=83, help='Explicit local staged identity allocation')
    parser.add_argument('--repo-id', default='jimzhouzzy2006/CAE-Bench-OJ', help='Configured future pool location; no upload is performed')
    parser.add_argument('--write-author-records', action='store_true', help='Write hash-bound evidence under the eight canonical author directories')
    args = parser.parse_args(argv)
    source_tasks = read(args.source / 'task-manifest.json')['ordered_tasks']
    task_ids = {task['slug']: f'caeoj-{args.task_id_start+i:06d}' for i,task in enumerate(source_tasks)}
    receipt = build_import(args.source, args.output, PROJECT, task_ids, args.repo_id)
    if args.write_author_records:
        write_author_records(args.source, PROJECT, receipt)
    print(json.dumps({'status': receipt['status'], 'counts': receipt['counts'],
                      'remote_upload': False, 'formal_selections_unchanged': True}, indent=2))


if __name__ == '__main__':
    main()
