"""Install one public package offline, then probe the installed task environment."""
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile
from check_environment import check


def main():
    slug = sys.argv[1]
    with tempfile.TemporaryDirectory(prefix='caeoj-public-install-') as directory:
        with zipfile.ZipFile('/material/agent.zip') as archive:
            archive.extractall(directory)
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-index', '--no-deps',
                        '--no-build-isolation', directory, '-r', '/material/requirements.txt'], check=True)
    subprocess.run([sys.executable, '-m', 'pip', 'check'], check=True)
    os.chdir('/tmp')
    from caeoj import runtime
    import caeoj_bundle
    descriptor = runtime.descriptor()
    info = runtime.bundle_info()
    if not descriptor.get('strict_tasks') or info['tasks'] != [slug]:
        raise RuntimeError('Installed provider does not match the required task: ' + str(info))
    for extension in descriptor['extensions'].values():
        for key in ('check', 'condition_compatibility'):
            if key in extension:
                importlib.import_module(extension[key].split(':')[0])
        for evaluator in extension.get('evaluators', {}).values():
            importlib.import_module(evaluator.split(':')[0])
    if not str(Path(caeoj_bundle.__file__).resolve()).startswith('/usr/local/lib/'):
        raise RuntimeError('Task provider was not loaded from the independent installation')
    print(json.dumps({'task': slug, 'task_runtime': info, 'environment': check(),
                      'offline_install': True, 'pip_check': True, 'provider': str(Path(caeoj_bundle.__file__).resolve())}))


if __name__ == '__main__':
    main()
