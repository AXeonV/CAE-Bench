"""Offline, disposable task data and project trees; never write into qbank."""
import atexit
from functools import lru_cache
from pathlib import Path
import shutil
import tempfile
import subprocess
import sys

from caeoj_tools.author import load_author_module
from caeoj_tools.task_paths import task_directory

ROOT = Path(__file__).resolve().parents[1]
_temporary = tempfile.TemporaryDirectory(prefix='caeoj-test-fixtures-')
atexit.register(_temporary.cleanup)
BASE = Path(_temporary.name)


@lru_cache(None)
def task_fixture(task):
    """Generate one session template, independent of installed HF assemblies."""
    canonical = task_directory(task, ROOT)
    target = BASE/canonical.relative_to(ROOT)
    # Keep author evidence; only task-root data directories are excluded.
    target.mkdir(parents=True)
    for path in canonical.iterdir():
        if path.name in {'cases','reference','samples','data-manifest.json',
                         '.data-assembly.json','.data-pool.lock'}:
            continue
        if path.is_dir():
            shutil.copytree(path,target/path.name,ignore=shutil.ignore_patterns('__pycache__','*.pyc','prepared','preparation.json','data-evidence','direct-source.json','public-examples.json'))
        else:
            shutil.copyfile(path,target/path.name)
    data = BASE/'generated'/task
    if task == 'smoke-test':
        load_author_module(task,'examples').make_cases(data/'cases')
    else:
        result = subprocess.run([sys.executable,'-X','utf8',str(canonical/'author/generate.py'),
                                 '--output',str(data)],capture_output=True,text=True,encoding='utf-8')
        if result.returncode:
            raise RuntimeError(result.stdout+result.stderr)
    shutil.copytree(data,target,dirs_exist_ok=True)
    return target


def project_fixture(destination, tasks):
    """Copy source-only runtime/configuration and freshly generated data."""
    destination = Path(destination)
    for name in ('LICENSE','pyproject.toml','docs','src/caeoj','src/utils/harbor','qbank/extensions'):
        source, target = ROOT/name, destination/name
        target.parent.mkdir(parents=True,exist_ok=True)
        if source.is_dir():
            shutil.copytree(source,target,dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.egg-info'))
        else:
            shutil.copyfile(source,target)
    for task in tasks:
        canonical = task_directory(task,ROOT)
        shutil.copytree(task_fixture(task),destination/canonical.relative_to(ROOT),dirs_exist_ok=True)
    return destination
