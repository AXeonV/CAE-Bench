"""Maintainer-side assembly for source-repair submissions, separate from data IO."""
import json
from pathlib import Path, PurePosixPath
import re
from .assembly import read_public_file


def configuration(source, root):
    path = source / 'harbor/source-repair.json'
    if not path.is_file():
        return None
    config = json.loads(read_public_file(root, path))
    required = {'version', 'base_image', 'replacements', 'build_directory', 'build_target',
                'build_timeout_seconds', 'max_source_bytes', 'runner', 'rebuild_files'}
    if set(config) - required - {'baseline_probe'} or required - set(config) or config['version'] != 1:
        raise ValueError('Invalid source-repair configuration keys')
    if 'baseline_probe' in config:
        probe = config['baseline_probe']
        if (not isinstance(probe, list) or not probe or len(probe) > 16
                or any(not isinstance(arg, str) or '\0' in arg for arg in probe)
                or not PurePosixPath(probe[0]).is_absolute()):
            raise ValueError('Invalid trusted baseline probe command')
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._:/@-]*', config['base_image']):
        raise ValueError('Invalid source-repair base image')
    if not re.fullmatch(r'[A-Za-z0-9_-]+', config['build_target']):
        raise ValueError('Invalid source-repair build target')
    for name in ('build_directory', 'runner'):
        path = PurePosixPath(config[name])
        if not path.is_absolute() or '..' in path.parts or '\\' in config[name]:
            raise ValueError('Invalid trusted source-repair path: ' + name)
    for name in ('build_timeout_seconds', 'max_source_bytes'):
        if type(config[name]) is not int or config[name] <= 0:
            raise ValueError('Invalid source-repair budget: ' + name)
    if not isinstance(config['rebuild_files'], list) or not config['rebuild_files']:
        raise ValueError('Missing source-repair rebuild files')
    build = PurePosixPath(config['build_directory'])
    for name in config['rebuild_files']:
        path = PurePosixPath(name)
        if (not path.is_relative_to(build) or path == build or '..' in path.parts or '\\' in name):
            raise ValueError('Rebuild files must remain within the trusted build directory')
    replacements = config['replacements']
    if not isinstance(replacements, list) or not replacements:
        raise ValueError('Source replacement list is empty')
    names, targets = set(), set()
    for row in replacements:
        if not isinstance(row, dict) or set(row) != {'submission', 'target'}:
            raise ValueError('Invalid source replacement')
        if not re.fullmatch(r'[A-Za-z0-9_]+\.(cpp|c|h|hpp|py|f|f90|F|F90)', row['submission']):
            raise ValueError('Submission must be a plain supported source/header filename')
        target = PurePosixPath(row['target'])
        if not target.is_absolute() or '..' in target.parts or '\\' in row['target']:
            raise ValueError('Invalid source replacement target')
        if row['submission'] in names or row['target'] in targets:
            raise ValueError('Duplicate source replacement')
        names.add(row['submission'])
        targets.add(row['target'])
    return config


def dockerfile(config):
    return f'''FROM --platform=linux/amd64 {config['base_image']}
WORKDIR /app
COPY agent.zip /tmp/agent.zip
COPY requirements.txt /tmp/requirements.txt
RUN python -m zipfile -e /tmp/agent.zip /app \\
    && python -m pip install --no-cache-dir /app -r /tmp/requirements.txt \\
    && mkdir -p /app/submission
'''


def oracle_sources(source, config):
    paths = [source / 'author/generated' / row['submission'] for row in config['replacements']]
    return paths if all(p.is_file() for p in paths) else []
