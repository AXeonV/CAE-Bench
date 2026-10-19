"""Direct-source case preparation and consumption; no solver or reference repair."""
from contextlib import contextmanager
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

import numpy as np

from caeoj.sdk import load_problem, load_result, write_result
from caeoj.case_grading import prepare_case, grade_case
from caeoj_tools.assembly import runtime_materials, read_public_file
from caeoj_tools.grading_policy import author_policy, write_direct_grading
from caeoj_tools.task_paths import task_directory
from caeoj_tools.public_examples import BINDING, example_snapshot, verify_public_examples
from .selection import ROOT, CATALOG, identity, validate_selection
from .models import BY_TASK, source_files
from .sources import Reader, open_source, check_initial
from .conversion import build_input
from .checks import source_reference, source_geometry
from .storage import Budget, NetworkBudget, PreparationError, atomic_json, digest


@contextmanager
def cache_lock(cache):
    cache.mkdir(parents=True, exist_ok=True)
    with (cache/'operation.lock').open('a') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise PreparationError('Cache/workspace operation already active; do not duplicate it') from exc
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def check_files(root, files):
    for name, sha in files.items():
        p = root/name
        if not p.resolve().is_relative_to(root.resolve()) or p.is_symlink() or not p.is_file() or digest(p) != sha:
            raise PreparationError(f'Prepared material missing or changed: {p}')


def workspace_init(workspace, selection, disk):
    if workspace == ROOT or ROOT.is_relative_to(workspace) or workspace.is_relative_to(ROOT/'qbank'):
        raise PreparationError('Use an isolated workspace outside the canonical qbank')
    marker = workspace/'workspace.json'
    if marker.exists():
        state = json.loads(marker.read_text())
        if state['selection_sha256'] != selection['sha256']:
            raise PreparationError('Workspace belongs to another selection; use a new directory')
        check_files(workspace, state['materials'])
        return
    init = workspace/'initializing.json'
    resuming = init.exists()
    if resuming:
        if json.loads(init.read_text()) != {'selection_sha256': selection['sha256']}:
            raise PreparationError('Interrupted initialization identity mismatch')
    elif workspace.exists() and any(p.name != 'operation.lock' for p in workspace.iterdir()):
        raise PreparationError('New workspace must be empty')
    workspace.mkdir(parents=True, exist_ok=True)
    tasks = {e['task']: task_directory(e['task'], ROOT) for e in selection['entries']}
    # Obtain the normal runtime closure rather than copying all source history.
    materials, _ = runtime_materials(tasks, ROOT)
    for name in ('LICENSE', 'docs/CONTRACT.md', 'docs/GRADING.md'):
        materials[name] = read_public_file(ROOT, ROOT/name)
    for source in (ROOT/'src/utils/harbor').rglob('*'):
        if source.is_file() and '__pycache__' not in source.parts:
            materials[source.relative_to(ROOT).as_posix()] = read_public_file(ROOT, source)
    for task in tasks.values():
        for name in ('instruction.md', 'DATA.md', 'judge-config.json', 'author/grading-template.json',
                     'harbor/task.toml', 'harbor/requirements.txt'):
            p = task/name
            if p.is_file():
                materials[p.relative_to(ROOT).as_posix()] = read_public_file(ROOT, p)
    disk.check(sum(len(v) for v in materials.values())+65536)
    if resuming:
        allowed = set(materials) | {'operation.lock', 'initializing.json'}
        if any(p.relative_to(workspace).as_posix() not in allowed for p in workspace.rglob('*') if p.is_file()):
            raise PreparationError('Unknown files in interrupted workspace; inspect before recovery')
    atomic_json(init, {'selection_sha256': selection['sha256']})
    for name, data in materials.items():
        target = workspace/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    public_examples = {}
    for slug, aliases in selection['examples'].items():
        public_examples[slug] = {
            'public_cases': [{'case': link['case'], 'sample': sample,
                              'case_id': identity(_case_entry(selection, slug, link['case']))}
                             for sample, link in aliases.items()],
            'samples': sorted([e['id'] for e in selection['entries'] if e['task'] == slug and e['role'] == 'sample'] + list(aliases)),
            'cases': sorted(e['id'] for e in selection['entries'] if e['task'] == slug and e['role'] == 'case')}
    atomic_json(marker, {'selection_sha256': selection['sha256'], 'public_examples': public_examples,
                         'materials': {name: hashlib.sha256(data).hexdigest() for name, data in materials.items()}})
    init.unlink(missing_ok=True)


def read_entry(entry, cache, disk, local, timeout, network):
    model, source = BY_TASK[entry['task']], entry['source']
    frames = np.asarray(entry['frames'], dtype=np.int64)
    with open_source(source, cache, disk, local, timeout, network) as h:
        reader = Reader(h, model); reader.check_index(entry['index'])
        coords, times, config = reader.metadata(entry['index'], frames=frames if model.points else None)
        if not model.points:
            if frames[-1] >= len(times):
                raise PreparationError('Requested frame outside actual source time axis')
            times = times[frames]
        source_geometry(model, source, coords, times, config)
        # Reserve enough for original values, mesh, input, reference, example and staging.
        cells = int(np.prod([len(c) for c in coords]))
        estimate = cells*(len(frames)*(sum(f[3] for f in model.fields)+4)*8*5+1000)
        if model.model == 'reaction_diffusion_2d':
            sim = config.get('sim', {})
            estimate += int(sim.get('xdim', 0))*int(sim.get('ydim', 0))*1500
        disk.check(estimate)
        values = reader.values(entry['index'], frames)
        if any(not np.isfinite(v).all() for v in values.values()):
            raise PreparationError('Nonfinite source trajectory')
        check_initial(model, {k: v[0:1] for k, v in values.items()})
    return coords, times, config, values


def prepare_entry(workspace, entry, cache, disk, local, timeout, network):
    tag = f"{entry['task']}-{entry['role']}-{entry['id']}"
    receipt_path = workspace/'evidence'/f'{tag}.json'
    if receipt_path.is_file():
        receipt = json.loads(receipt_path.read_text())
        if receipt['entry_sha256'] == identity(entry):
            check_files(workspace, receipt['files'])
            return {**receipt, 'reused': True}
        raise PreparationError('Entry receipt belongs to another source or selection')
    journal = workspace/'transactions'/f'{tag}.json'
    task = task_directory(entry['task'], workspace)
    destinations = ([task/'samples'/entry['id']] if entry['role'] == 'sample' else
                    [task/'cases'/entry['id'], task/'reference'/entry['id']])
    if journal.exists():
        if json.loads(journal.read_text()) != {'entry_sha256': identity(entry)}:
            raise PreparationError('Interrupted transaction identity mismatch')
        for target in destinations:
            if target.exists(): shutil.rmtree(target)
        journal.unlink()
    coords, times, config, values = read_entry(entry, cache, disk, local, timeout, network)
    model = BY_TASK[entry['task']]
    task = task_directory(entry['task'], workspace)
    initial_hash = hashlib.sha256()
    for key in sorted(values):
        # Ignore forcing time extent; initial identity includes all required source input fields.
        initial_hash.update(key.encode()); initial_hash.update(values[key][0:1].tobytes())
    initial_sha = initial_hash.hexdigest()
    for path in (workspace/'evidence').glob('*.json'):
        other = json.loads(path.read_text())
        if other.get('task') == entry['task'] and other.get('initial_sha256') == initial_sha:
            raise PreparationError('Duplicate source initial state, including sample/case leakage')
    with tempfile.TemporaryDirectory(prefix='.case-', dir=workspace) as tmp:
        staged = Path(tmp)
        problem = build_input(model, entry['source'], coords, times, values, staged/'input', config=config)
        arrays, evidence = source_reference(model, problem, values, config)
        private = staged/'reference'; private.mkdir()
        candidate = private/('candidate.h5' if evidence['blocked'] else 'reference.h5')
        write_result(candidate, problem, arrays); load_result(problem, candidate)
        if not evidence['blocked']:
            write_direct_grading(private, author_policy(task, problem))
            prepare_case(problem, private/'grading.json')
        if entry['role'] == 'sample':
            target = task/'samples'/entry['id']
            targets = [(staged/'input', target/'input'), (private, target/'reference')]
            if not evidence['blocked']:
                (staged/'output').mkdir(); shutil.copyfile(candidate, staged/'output/result.h5')
                targets.append((staged/'output', target/'output'))
        else:
            targets = [(staged/'input', task/'cases'/entry['id']), (private, task/'reference'/entry['id'])]
        if any(p.exists() for p in destinations):
            raise PreparationError('Unreceipted destination exists; refusing overwrite')
        atomic_json(journal, {'entry_sha256': identity(entry)})
        for source, target in targets:
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                raise PreparationError('Unreceipted output already exists; inspect it instead of overwriting')
            shutil.copytree(source, target)
            # Generated JSON uses private atomic temporaries; candidate inputs must be readable by solver UID.
            for p in target.rglob('*'):
                p.chmod(0o755 if p.is_dir() else 0o644)
        files = {p.relative_to(workspace).as_posix(): digest(p)
                 for _, target in targets for p in target.rglob('*') if p.is_file()}
    record = {'task': entry['task'], 'role': entry['role'], 'id': entry['id'],
              'entry_sha256': identity(entry), 'source': entry['source'], 'source_index': entry['index'],
              'original_frames': entry['frames'], 'actual_times': times.tolist(),
              'initial_sha256': initial_sha, 'files': files, 'source_evidence': evidence,
              'input_ready': True, 'reference_ready': not evidence['blocked'],
              'example_ready': entry['role'] == 'sample' and not evidence['blocked'],
              'integrity_scope': 'range block and converted payload SHA256; full-source MD5 only in local source mode'}
    disk.check(32768); atomic_json(receipt_path, record)
    journal.unlink(missing_ok=True)
    return record


def _case_entry(selection, task, case):
    return next(e for e in selection['entries'] if e['task'] == task and e['role'] == 'case' and e['id'] == case)


def prepare_examples(workspace, selection, disk):
    """Copy explicit aliases from prepared cases without opening a source again."""
    for slug, aliases in selection['examples'].items():
        task = task_directory(slug, workspace)
        bindings = []
        for sample, link in aliases.items():
            case = link['case']; entry = _case_entry(selection, slug, case)
            case_id = identity(entry)
            original = json.loads((workspace/'evidence'/f'{slug}-case-{case}.json').read_text())
            if original['entry_sha256'] != case_id:
                raise PreparationError('Referenced case receipt identity mismatch')
            check_files(workspace, original['files'])
            if not original['reference_ready']:
                continue
            receipt_path = workspace/'evidence'/f'{slug}-example-{sample}.json'
            target = task/'samples'/sample
            journal = workspace/'transactions'/f'{slug}-example-{sample}.json'
            if journal.exists():
                pending = json.loads(journal.read_text())
                if {k: pending[k] for k in ('case', 'sample', 'case_id')} != {'case': case, 'sample': sample, 'case_id': case_id}:
                    raise PreparationError('Interrupted example identity mismatch')
                if target.exists():
                    check_files(workspace, pending['files'])
                    if not receipt_path.exists(): atomic_json(receipt_path, pending)
                journal.unlink()
            if receipt_path.exists():
                receipt = json.loads(receipt_path.read_text())
                if {k: receipt[k] for k in ('case', 'sample', 'case_id')} != {'case': case, 'sample': sample, 'case_id': case_id}:
                    raise PreparationError('Example receipt belongs to a different case')
                check_files(workspace, receipt['files'])
            else:
                if target.exists():
                    raise PreparationError('Unreceipted example destination exists; inspect before replacing')
                source = task/'cases'/case; ref = task/'reference'/case
                problem = load_problem(source/'problem.json')
                files = prepare_case(problem, ref/'grading.json').evidence['assets']
                inputs = {'problem.json', problem.manifest['data_file']}
                inputs.update(v['file'] for table in ('meshes', 'geometries') for v in problem.manifest[table].values())
                size = sum((source/n).stat().st_size for n in inputs)
                size += sum((ref/n).stat().st_size for n in files)+(ref/'reference.h5').stat().st_size
                disk.check(size+65536)
                with tempfile.TemporaryDirectory(dir=workspace, prefix='.example-') as temporary:
                    stage = Path(temporary)/'sample'
                    for name in inputs:
                        path = stage/'input'/name
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_bytes(read_public_file(task, source/name))
                    for name in files:
                        path = stage/'reference'/name
                        path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(ref/name, path)
                    (stage/'output').mkdir()
                    shutil.copyfile(ref/'reference.h5', stage/'output/result.h5')
                    target.parent.mkdir(parents=True, exist_ok=True)
                    # Commit the whole sample at once; interruptions before this leave no public partial tree.
                    receipt = {'case': case, 'sample': sample, 'case_id': case_id,
                               'files': {(target/p.relative_to(stage)).relative_to(workspace).as_posix(): digest(p)
                                         for p in stage.rglob('*') if p.is_file()}}
                    atomic_json(journal, receipt)
                    stage.rename(target)
                atomic_json(receipt_path, receipt)
                journal.unlink()
            bindings.append({'case': case, 'sample': sample, 'case_id': case_id,
                             'snapshot': example_snapshot(task, case, sample)})
        if len(bindings) != len(aliases):
            continue  # source applicability is still blocked; never produce a partial public binding
        document = {'schema_version': 1, 'public_cases': bindings}
        marker = task/BINDING
        if marker.exists():
            if json.loads(marker.read_text()) != document:
                raise PreparationError('Local example binding differs; refusing to overwrite')
        else:
            atomic_json(marker, document)
        verify_public_examples(task)


def verify(workspace, selection):
    state = json.loads((workspace/'workspace.json').read_text())
    if state['selection_sha256'] != selection['sha256']:
        raise PreparationError('Workspace selection mismatch')
    check_files(workspace, state['materials'])
    records = []; blocked = False
    expected_paths = set()
    for entry in selection['entries']:
        task = task_directory(entry['task'], workspace)
        receipt = json.loads((workspace/'evidence'/f"{entry['task']}-{entry['role']}-{entry['id']}.json").read_text())
        if receipt['entry_sha256'] != identity(entry):
            raise PreparationError('Receipt/selection mismatch')
        check_files(workspace, receipt['files'])
        public = entry['role'] == 'sample'
        input_dir = task/'samples'/entry['id']/'input' if public else task/'cases'/entry['id']
        expected_paths.add(input_dir/'problem.json')
        problem = load_problem(input_dir/'problem.json')
        reference = task/'samples'/entry['id']/'reference' if public else task/'reference'/entry['id']
        if not receipt['reference_ready']:
            blocked = True
            records.append({'task': entry['task'], 'id': entry['id'], 'role': entry['role'], 'status': 'blocked',
                            'reasons': receipt['source_evidence']['blocked']})
            continue
        prepare_case(problem, reference/'grading.json')
        candidate = task/'samples'/entry['id']/'output/result.h5' if public else reference/'reference.h5'
        positive = grade_case(problem.path, candidate, reference/'grading.json')
        if positive['score'] != 1:
            raise PreparationError('Source reference/example fails its own grading configuration')
        arrays = load_result(problem, candidate)
        wrong = {k: arrays[k]+1e9 for k in problem.manifest['outputs']}
        with tempfile.TemporaryDirectory(dir=workspace) as tmp:
            output = Path(tmp)/'wrong.h5'; write_result(output, problem, wrong)
            negative = grade_case(problem.path, output, reference/'grading.json')
            if negative['score'] != 0:
                raise PreparationError('Wrong-value control unexpectedly passes')
        records.append({'task': entry['task'], 'id': entry['id'], 'role': entry['role'],
                        'positive_score': positive['score'], 'negative_score': negative['score'], 'status': 'verified'})
    public_by_task = {}
    example_records = []
    for slug in {e['task'] for e in selection['entries']}:
        task = task_directory(slug, workspace)
        expected_public = []
        for sample, link in selection['examples'].get(slug, {}).items():
            case = link['case']; entry = _case_entry(selection, slug, case)
            source = json.loads((workspace/'evidence'/f'{slug}-case-{case}.json').read_text())
            if not source['reference_ready']:
                blocked = True
                example_records.append({'task': slug, 'sample': sample, 'case': case, 'status': 'blocked'})
                continue
            expected_public.append({'case': case, 'sample': sample, 'case_id': identity(entry)})
            receipt = json.loads((workspace/'evidence'/f'{slug}-example-{sample}.json').read_text())
            if {k: receipt[k] for k in ('case', 'sample', 'case_id')} != expected_public[-1]:
                raise PreparationError('Example receipt/selection mismatch')
            check_files(workspace, receipt['files'])
            expected_paths.add(task/'samples'/sample/'input/problem.json')
            example_records.append({'task': slug, 'sample': sample, 'case': case, 'status': 'verified'})
        pending_examples = len(expected_public) != len(selection['examples'].get(slug, {}))
        actual_public = expected_public if pending_examples else verify_public_examples(task)
        if actual_public != expected_public:
            raise PreparationError('Public example mapping differs from frozen selection')
        public_by_task[slug] = actual_public
    actual = {p for task_name in {e['task'] for e in selection['entries']}
              for pattern in ('cases/*/problem.json', 'samples/*/input/problem.json')
              for p in task_directory(task_name, workspace).glob(pattern)}
    if actual != expected_paths:
        raise PreparationError('Workspace contains unselected or missing inputs')
    report = {'status': 'blocked' if blocked else 'verified', 'records': records,
              'selection_sha256': selection['sha256'], 'assembly_ready': not blocked,
              'public_cases': public_by_task, 'examples': example_records,
              'case_count': sum(e['role'] == 'case' for e in selection['entries']),
              'scope': 'source conversion and judge checks; not independent PDE accuracy certification'}
    atomic_json(workspace/'verification.json', report)
    return report


def execute(args):
    if args.command in ('install', 'verify-installed'):
        from .installation import install, verify_installed
        selection = validate_selection(json.loads(args.selection.read_text()))
        if args.command == 'verify-installed':
            return verify_installed(selection, args.target_root)
        with cache_lock(args.workspace.resolve()):
            return install(args.workspace, selection, args.target_root, replace=args.replace)
    if args.command in ('verify', 'assemble'):
        selection = validate_selection(json.loads(args.selection.read_text()))
        workspace = args.workspace.resolve()
        with cache_lock(workspace):
            report = verify(workspace, selection)
            if args.command == 'assemble' and report['assembly_ready']:
                # Existing production assemblers, using their ordinary isolated-root API.
                from utils.publish_dist import publish
                from utils.prepare_harbor import prepare
                tasks = sorted({e['task'] for e in selection['entries']})
                report['artifacts'] = []
                for task in tasks:
                    publish([task], output=workspace/'dist', root=workspace)
                    report['artifacts'].append(prepare(task, root=workspace))
                report['status'] = 'assembled'
                atomic_json(workspace/'assembly.json', report)
            return report
    if not all(np.isfinite(v) and v >= 0 for v in (args.network_mb, args.disk_mb)) or args.disk_mb == 0 or not np.isfinite(args.timeout) or args.timeout <= 0:
        raise ValueError('Budgets must be finite nonnegative, disk and timeout positive')
    cache = args.cache_root.resolve()
    network = NetworkBudget(int(args.network_mb*1e6))
    roots = [cache] + ([args.workspace.resolve()] if args.command == 'prepare' else [])
    disk = Budget(roots, int(args.disk_mb*1e6)); disk.check()
    with cache_lock(cache):
        try:
            if args.command == 'inspect':
                catalog = json.loads(CATALOG.read_text()); model = BY_TASK[args.task]
                source = next((s for s in source_files(model, catalog) if s['id'] == args.source_id), None)
                if source is None: raise ValueError('Source does not belong to task')
                with open_source(source, cache, disk, args.source_dir, args.timeout, network) as h:
                    reader = Reader(h, model); reader.check_index(args.index)
                    frames = np.array([0], dtype=np.int64) if model.points else None
                    coords, times, config = reader.metadata(args.index, frames=frames)
                    result = {'task': args.task, 'source': source, 'index': args.index, 'trajectory_count': reader.count,
                              'shape': [len(c) for c in coords], 'actual_times': times.tolist(),
                              'group_count_note': 'unknown; selected group exists' if model.grouped else None,
                              'time_scope': 'selected initial timestamp only' if model.points else 'full time coordinate metadata'}
            else:
                selection = validate_selection(json.loads(args.selection.read_text()))
                workspace = args.workspace.resolve()
                with cache_lock(workspace):
                    workspace_init(workspace, selection, disk)
                    records = []
                    for entry in selection['entries']:
                        records.append(prepare_entry(workspace, entry, cache, disk, args.source_dir, args.timeout, network))
                        atomic_json(workspace/'preparation.json', {'status': 'preparing', 'records': records,
                                                                  'network': network.report()})
                    prepare_examples(workspace, selection, disk)
                    result = verify(workspace, selection)
                    result['prepared'] = len(records)
            result['network'] = network.report(); result['disk_accounted_peak_bytes'] = disk.peak
            return result
        finally:
            atomic_json(cache/'last-transfer.json', network.report())
