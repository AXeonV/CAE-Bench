"""Build an explicit public runtime closure, independently of physics names."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path, PurePosixPath
import tomllib
from jsonschema import Draft202012Validator, SchemaError
from caeoj.runtime import compose_schema, read_metadata
from .dependencies import lock_dependencies


def read_public_file(root, path):
    root, path = Path(root).resolve(), Path(path)
    relative = path.relative_to(root)
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink() or getattr(current, 'is_junction', lambda: False)():
            raise ValueError(f'Public material must not be a link: {relative}')
    if not path.resolve().is_relative_to(root):
        raise ValueError(f'Public material escapes project: {relative}')
    return path.read_bytes()


def _relative(name):
    path = PurePosixPath(name)
    if path.is_absolute() or not path.parts or any(p in ('..', '.', '') for p in path.parts) or '\\' in name:
        raise ValueError(f'Invalid runtime resource path: {name}')
    return path


def _json(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode()


def runtime_materials(tasks, root):
    """Return public files and a fully resolved single- or multi-task binding.

    The source catalog and optional task extension/runtime.json are trusted
    maintainer metadata, never supplied by a solver or selected by input paths.
    """
    root = Path(root).resolve()
    normalized = {}
    for name, path in tasks.items():
        path = Path(path).absolute()
        current = path
        while current.resolve() != root:
            if current.is_symlink() or getattr(current, 'is_junction', lambda: False)():
                raise ValueError(f'Task directory must not be a link: {current}')
            if current == current.parent:
                raise ValueError('Task directory escapes project')
            current = current.parent
        normalized[name] = path.resolve()
    tasks = normalized
    catalog_path = root / 'qbank/extensions/caeoj_bundle/runtime.json'
    development = catalog_path.is_file()
    if not development:
        catalog_path = root / 'src/caeoj_bundle/runtime.json'
    catalog = read_metadata(read_public_file(root, catalog_path))
    if catalog.get('version') != 1:
        raise ValueError('Unsupported runtime catalog version')
    catalog = deepcopy(catalog)
    source_base = root / ('qbank/extensions' if development else 'src')
    sources = {name: source_base for name in catalog['extensions']}
    bindings = {}
    for task, directory in tasks.items():
        task_config = directory / 'extension/runtime.json'
        if task_config.is_file():
            spec = read_metadata(read_public_file(root, task_config))
            name = spec.pop('id')
            if name in catalog['extensions']:
                raise ValueError(f'Duplicate extension identity: {name}')
            if not name.startswith('task.'):
                raise ValueError('Task-specific extension identity must start with task.')
            catalog['extensions'][name] = spec
            sources[name] = directory / 'extension'
            bindings[task] = [name]
        else:
            if task not in catalog['tasks']:
                raise ValueError(f'Task {task!r} has no explicit runtime binding')
            bindings[task] = list(catalog['tasks'][task])
    selected, active = [], set()
    def visit(name):
        if name in active:
            raise ValueError(f'Cyclic extension dependency: {name}')
        if name in selected:
            return
        if name not in catalog['extensions']:
            raise ValueError(f'Missing extension dependency: {name}')
        spec = catalog['extensions'][name]
        if type(spec.get('version')) is not int or spec['version'] <= 0:
            raise ValueError(f'Invalid extension version: {name}')
        active.add(name)
        for item in spec.get('requires', []):
            visit(item)
        for dependency, required_version in spec.get('requires_versions', {}).items():
            if dependency not in spec.get('requires', []) or catalog['extensions'][dependency]['version'] != required_version:
                raise ValueError(f'Incompatible extension version: {name} requires {dependency}=={required_version}')
        active.remove(name)
        selected.append(name)
    for names in bindings.values():
        for name in names:
            visit(name)
    files = {}
    def add(target, path):
        target = str(_relative(target))
        data = read_public_file(root, path)
        if target in files and files[target] != data:
            raise ValueError(f'Conflicting public runtime resource: {target}')
        files[target] = data
    core = json.loads(read_public_file(root, root/'src/caeoj/public-runtime.json'))
    for name in core['files']:
        name = str(_relative(name))
        add('src/caeoj/'+name, root/'src/caeoj'/name)
    owners = {}
    fragments = []
    for name in selected:
        spec = catalog['extensions'][name]
        for resource in spec['files']:
            resource = str(_relative(resource))
            if not resource.startswith(('caeoj_ext/', 'caeoj_task_ext/')):
                raise ValueError(f'Extension cannot overwrite core or metadata: {resource}')
            add('src/'+resource, sources[name]/resource)
        for resource in spec.get('schemas', []):
            package, relative = resource.split(':', 1)
            target = 'src/'+package.replace('.','/')+'/'+str(_relative(relative))
            if target not in files:
                raise ValueError(f'Undeclared contract resource: {resource}')
            fragments.append((name, json.loads(files[target]), spec.get('schema_overrides', [])))
        for selector in spec.get('selectors', []):
            identity = json.dumps(selector, sort_keys=True)
            if identity in owners:
                raise ValueError(f'Duplicate model registration: {name} and {owners[identity]}')
            owners[identity] = name
    try:
        Draft202012Validator.check_schema(compose_schema(json.loads(files['src/caeoj/problem.schema.json']), fragments, core.get('schema_overrides', [])))
    except SchemaError as exc:
        raise ValueError(f'Invalid extension Schema: {exc.message}') from exc
    def available(target):
        module = target.split(':', 1)[0]
        return ('src/'+module.replace('.','/')+'.py' in files or
                'src/'+module.replace('.','/')+'/__init__.py' in files)
    for name in selected:
        for key in ('check','condition_compatibility'):
            if catalog['extensions'][name].get(key) and not available(catalog['extensions'][name][key]):
                raise ValueError(f'Missing declared extension implementation: {name}.{key}')
    runtime = {'version':1, 'strict_tasks':True, 'tasks':bindings,
               'extensions':{n:catalog['extensions'][n] for n in selected},
               'aliases':{n:t for n,t in catalog.get('aliases',{}).items() if available(t)},
               'modules':{n:t for n,t in catalog.get('modules',{}).items() if available(t)},
               'model_namespaces':catalog.get('model_namespaces',[]),
               'model_namespace_diagnostics':catalog.get('model_namespace_diagnostics',{})}
    metadata = tomllib.loads(read_public_file(root, root/'pyproject.toml').decode())
    project = metadata['project']
    requested_dependencies = list(project['dependencies'])
    for name in selected:
        requested_dependencies.extend(catalog['extensions'][name].get('dependencies', []))
    locked = lock_dependencies(requested_dependencies)
    runtime['core_version'] = project['version'].split('+')[0]
    runtime['dependencies'] = locked
    # Files and descriptors both contribute; hidden material never contributes.
    digest = hashlib.sha256(_json(runtime))
    for path, data in sorted(files.items()):
        digest.update(path.encode()+b'\0'+hashlib.sha256(data).digest())
    runtime['id'] = digest.hexdigest()
    files['src/caeoj_bundle/__init__.py'] = b'"""Installed public contract assembly."""\n'
    files['src/caeoj_bundle/runtime.json'] = _json(runtime)
    # One distribution owns the complete public namespace; no overlay installs.
    base_version = project['version'].split('+')[0]
    lines = ['[build-system]', 'requires = ["setuptools>=68"]', 'build-backend = "setuptools.build_meta"',
             '', '[project]', 'name = "cae-bench-oj"',
             'version = '+json.dumps(base_version+'+bundle.'+runtime['id'][:16]),
             'requires-python = '+json.dumps(project['requires-python']),
             'dependencies = '+json.dumps(locked),
             '', '[project.scripts]', 'caeoj = "caeoj.cli:main"',
             '', '[tool.setuptools.packages.find]', 'where = ["src"]',
             'include = ["caeoj", "caeoj_bundle", "caeoj_ext*", "caeoj_task_ext*"]',
             '', '[tool.setuptools.package-data]', '"*" = ["*.json"]', '']
    files['pyproject.toml'] = '\n'.join(lines).encode()
    return files, runtime


def validate_public_runtime(files):
    """Check the exact staged public closure, not the developer's provider.

    No task code is chosen by an input: only the trusted closure is executed.
    Installation itself is covered separately by normal-wheel platform checks.
    """
    import subprocess
    import sys
    import tempfile
    with tempfile.TemporaryDirectory(prefix='caeoj-public-preflight-') as temporary:
        root = Path(temporary)
        for name, data in files.items():
            target = root/str(_relative(name))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        script = '''import sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1])/'src'))
from caeoj.sdk import load_problem, load_result
from caeoj.grading_policy import load_policy, validate_policy
root=Path(sys.argv[1])
for path in root.glob('qbank/*/*/*/samples/*/input/problem.json'):
    problem=load_problem(path)
    load_result(problem, path.parent.parent/'output/result.h5')
    validate_policy(load_policy(path.parents[3]/'grading.json'), problem)
'''
        result = subprocess.run([sys.executable, '-I', '-c', script, str(root)],
                                cwd=root, capture_output=True, text=True, timeout=120)
        if result.returncode:
            raise ValueError('Assembled public runtime preflight failed:\n'+result.stderr+result.stdout)
