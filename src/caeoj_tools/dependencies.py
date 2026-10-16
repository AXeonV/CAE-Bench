"""Resolve a reproducible public dependency closure from installed metadata.

This maintainer utility locks the environment used to verify an assembly. It does
not download packages or silently replace an incompatible installed distribution.
"""
from collections import deque
from importlib import metadata

from packaging.markers import default_environment
from packaging.requirements import InvalidRequirement, Requirement
from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, Version


def lock_dependencies(requirements):
    """Return sorted ``name==version`` pins for all active transitive requirements.

    Markers are evaluated for the build environment. Requested extras are merged
    before dependency expansion, including extras discovered through cycles.
    Direct URLs cannot be authenticated from version metadata and are rejected.
    Missing distributions, unknown extras and incompatible constraints fail the
    assembly instead of producing a lock that installation cannot satisfy.
    """
    environment = default_environment()
    pending = deque()

    def parse(text, origin):
        try:
            return Requirement(text)
        except (InvalidRequirement, TypeError) as exc:
            raise ValueError(f'Invalid dependency from {origin}: {text!r}') from exc

    def enabled(requirement, extras):
        return requirement.marker is None or any(
            requirement.marker.evaluate({**environment, 'extra': extra})
            for extra in {'', *extras})

    for text in requirements:
        requirement = parse(text, 'assembly')
        if enabled(requirement, ()):
            pending.append((requirement, 'assembly'))
    installed = {}
    while pending:
        requirement, origin = pending.popleft()
        if requirement.url:
            raise ValueError(f'Direct URL dependency cannot be verified from installed metadata: {requirement}')
        name = canonicalize_name(requirement.name)
        if name not in installed:
            try:
                distribution = metadata.distribution(name)
            except metadata.PackageNotFoundError as exc:
                raise ValueError(f'Missing installed dependency {name} required by {origin}') from exc
            try:
                version = Version(distribution.version)
            except InvalidVersion as exc:
                raise ValueError(f'Invalid installed version for {name}: {distribution.version!r}') from exc
            python_requirement = distribution.metadata.get('Requires-Python')
            if python_requirement:
                try:
                    compatible_python = SpecifierSet(python_requirement).contains(
                        environment['python_full_version'], prereleases=True)
                except InvalidSpecifier as exc:
                    raise ValueError(f'Invalid Requires-Python metadata for {name}: {python_requirement}') from exc
                if not compatible_python:
                    raise ValueError(f'Installed {name} requires Python {python_requirement}; '
                                     f'assembly uses {environment["python_full_version"]}')
            installed[name] = {'distribution': distribution, 'version': version,
                               'extras': set(), 'expanded': False}
        state = installed[name]
        if requirement.specifier and not requirement.specifier.contains(state['version'], prereleases=True):
            raise ValueError(f'Installed {name}=={state["version"]} does not satisfy {requirement} required by {origin}')
        requested = {canonicalize_name(extra) for extra in requirement.extras}
        distribution = state['distribution']
        provided = {canonicalize_name(extra) for extra in
                    (distribution.metadata.get_all('Provides-Extra') or [])}
        if requested - provided:
            raise ValueError(f'Installed {name} does not provide extras: {sorted(requested - provided)}')
        if state['expanded'] and requested <= state['extras']:
            continue
        state['extras'].update(requested)
        state['expanded'] = True
        for text in distribution.requires or []:
            dependency = parse(text, name)
            if enabled(dependency, state['extras']):
                pending.append((dependency, name))
    return [f'{name}=={state["version"]}' for name, state in sorted(installed.items())]
