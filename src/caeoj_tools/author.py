"""Maintainer helpers for author utilities and public declaration catalogs.

This is a maintainer API. No input manifest may select the module to load.
"""
from importlib.util import module_from_spec, spec_from_file_location
from copy import deepcopy
from pathlib import Path
import sys

from .task_paths import task_directory

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def public_model_catalog(models):
    """Copy declaration metadata without author-side execution/scoring settings."""
    public = deepcopy(models)
    for model in public.values():
        model.pop('timeout', None)
        for key in ('outputs', 'output_specs'):
            outputs = model.get(key)
            if isinstance(outputs, dict):
                for field in outputs.values():
                    field.pop('atol', None)
                    field.pop('rtol', None)
    return public


def load_author_module(task, name, root=PROJECT_ROOT):
    """Load an author filename from a trusted task directory."""
    if not name.isidentifier():
        raise ValueError('Author module must be a Python identifier')
    path = task_directory(task, root) / 'author' / f'{name}.py'
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError('Author module must not be a link')
    module_name = f'caeoj_task_author_{task.replace("-", "_")}_{name}'
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f'Cannot load author module: {path}')
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[module_name] = module
    return module
