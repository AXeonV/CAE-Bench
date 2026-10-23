"""Fetch pinned upstream trees; prepare public assets and real solver builds."""
import argparse
import hashlib
import json
import posixpath
from pathlib import Path
import shutil
import subprocess
import tarfile
import urllib.request

TASK = Path(__file__).resolve().parents[1]
COMMITS = {'base': '371b41d7db6246bddcd9fba4d1c6a20deeabf8b6',
           'fixed': 'd76aed8f0152b790d088f298ebb25755f0d33485'}
HASHES = {'base': '9e4011d605f7ea64bfab5904df2d832ce09e47b254a5876cf487acd1a9897a4e',
          'fixed': '1e92cc3c567cc2dbc8bba9cae142eff8106f8df4f4259693920901fbeeafd417'}
SUBDIR = Path('packages/pybamm/src/pybamm/models/submodels/equivalent_circuit_elements')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_tree(archive, target, reviewed_links=None):
    expected = {}
    documentation_links = {}
    with tarfile.open(archive) as source:
        prefix = source.getmembers()[0].name + '/'
        regular = {m.name: m for m in source.getmembers() if m.isfile()}
        for member in source.getmembers():
            if member.isfile() and member.name.startswith(prefix):
                relative = member.name[len(prefix):]
                expected[relative] = hashlib.sha256(source.extractfile(member).read()).hexdigest()
            elif member.issym() and member.name.startswith(prefix):
                relative = member.name[len(prefix):]
                allowed = ({'.cursorrules', '.github/copilot-instructions.md', 'CLAUDE.md', 'GEMINI.md', 'QWEN.md'}
                           if reviewed_links is None else reviewed_links)
                if relative not in allowed:
                    raise ValueError('Unreviewed upstream symlink: ' + relative)
                if reviewed_links is not None and member.linkname != reviewed_links[relative]:
                    raise ValueError('Changed reviewed upstream link: ' + relative)
                resolved = posixpath.normpath(posixpath.join(posixpath.dirname(member.name), member.linkname))
                if resolved not in regular or not resolved.startswith(prefix):
                    raise ValueError('Invalid upstream documentation link')
                documentation_links[relative] = hashlib.sha256(source.extractfile(regular[resolved]).read()).hexdigest()
    actual = {p.relative_to(target).as_posix(): sha(p) for p in target.rglob('*') if p.is_file()}
    # Windows tar extraction can skip or copy these five documentation links.
    # All regular archive files must match; copied links must match their source.
    for name, digest in documentation_links.items():
        if name in actual:
            if actual[name] != digest:
                raise ValueError('Changed copied documentation link: ' + name)
            expected[name] = digest
    if actual != expected or any(p.is_symlink() for p in target.rglob('*')):
        raise ValueError('Existing source tree differs from the pinned archive: ' + str(target))
    return hashlib.sha256(json.dumps(expected, sort_keys=True).encode()).hexdigest()


def prepare(work):
    work.mkdir(parents=True, exist_ok=True)
    evidence = {'repository': 'https://github.com/pybamm-team/PyBaMM',
                'issue': 'https://github.com/pybamm-team/PyBaMM/issues/5859',
                'pull': 'https://github.com/pybamm-team/PyBaMM/pull/5869', 'archives': {}}
    for kind, commit in COMMITS.items():
        archive = work / (kind + '.tar.gz')
        url = f'https://codeload.github.com/pybamm-team/PyBaMM/tar.gz/{commit}'
        if not archive.exists():
            urllib.request.urlretrieve(url, archive)
        if sha(archive) != HASHES[kind]:
            raise ValueError('Upstream archive content changed: ' + kind)
        target = work / kind
        if not target.exists():
            target.mkdir()
            with tarfile.open(archive) as source:
                prefix = source.getmembers()[0].name + '/'
                for member in source.getmembers():
                    if member.name.startswith(prefix):
                        member.name = member.name[len(prefix):]
                        if member.name:
                            source.extract(member, target, filter='data')
        evidence['archives'][kind] = {'commit': commit, 'url': url, 'sha256': sha(archive),
                                     'tree_manifest_sha256': verify_tree(archive, target)}
    context = work / 'context'
    context.mkdir(exist_ok=True)
    if not (context / 'source').exists():
        shutil.copytree(work / 'base', context / 'source')
    verify_tree(work / 'base.tar.gz', context / 'source')
    for origin, name in [(TASK/'author/runtime.Dockerfile', 'Dockerfile'),
                         (TASK/'public/CMakeLists.txt', 'CMakeLists.txt'),
                         (TASK/'public/driver.py', 'driver.py')]:
        shutil.copyfile(origin, context / name)
    shutil.copyfile(work/'base.tar.gz', TASK/'public/pybamm-source.tar.gz')
    oracle = TASK/'author/generated'
    oracle.mkdir(exist_ok=True)
    for name in ('diffusion_element.py', 'thermal.py'):
        shutil.copyfile(work/'fixed'/SUBDIR/name, oracle/name)
    reference = work/'reference-context'
    reference.mkdir(exist_ok=True)
    for name in ('diffusion_element.py', 'thermal.py'):
        shutil.copyfile(oracle/name, reference/name)
    # Applied runtime changes are precisely these two source files, not the full PR tree.
    commands = ['FROM caeoj-pybamm5859-core:base']
    for name in ('diffusion_element.py', 'thermal.py'):
        commands.append(f'COPY {name} /opt/pybamm-build/source/{SUBDIR.as_posix()}/{name}')
    commands.append('RUN rm -f /opt/pybamm-build/source/'+SUBDIR.as_posix()+'/__pycache__/diffusion_element.cpython-314.pyc /opt/pybamm-build/source/'+SUBDIR.as_posix()+'/__pycache__/thermal.cpython-314.pyc && cmake --build /opt/pybamm-build --target repair_sources')
    (reference/'Dockerfile').write_text('\n'.join(commands)+'\n', encoding='utf-8')
    files = sorted((TASK/'public').iterdir())
    (TASK/'public-materials.json').write_text(json.dumps({'version': 1, 'files': [
        {'path': 'public/'+p.name, 'sha256': sha(p)} for p in files if p.is_file()]}, indent=2)+'\n', encoding='utf-8')
    evidence['applied_fix'] = ['diffusion_element.py', 'thermal.py']
    evidence['version_metadata_note'] = 'Source archive has no Git metadata; installed package reports 0.0.0. Source identity is the pinned commit and archive digest.'
    (TASK/'author/data-evidence').mkdir(exist_ok=True)
    (TASK/'author/data-evidence/source.json').write_text(json.dumps(evidence, indent=2)+'\n', encoding='utf-8')
    return context, reference


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--docker', default='docker')
    parser.add_argument('--build', action='store_true')
    args = parser.parse_args()
    context, reference = prepare(args.work)
    if args.build:
        image = 'python:3.14-slim@sha256:a2b82f3c48559aa0a8446d9af49826b6e2b2016f4cd2afabfe6013ec53729170'
        probe = subprocess.run([args.docker, 'image', 'inspect', image], capture_output=True)
        if probe.returncode:
            subprocess.run([args.docker, 'pull', image], check=True)
        # Local alias prevents redundant registry resolution during each build.
        subprocess.run([args.docker, 'tag', image, 'caeoj-python314-pinned:repair22'], check=True)
        for directory, tag in [(context, 'caeoj-pybamm5859-core:base'), (reference, 'caeoj-pybamm5859-reference:fixed')]:
            subprocess.run([args.docker, 'build', '--pull=false', '--progress', 'plain', '-t', tag, str(directory)], check=True)
        # Deployment alias works online as-is; prepare_offline_sdk may replace
        # it with the same solver plus a verified local SDK dependency cache.
        subprocess.run([args.docker,'tag','caeoj-pybamm5859-core:base','caeoj-pybamm5859-core:offline-sdk'],check=True)
