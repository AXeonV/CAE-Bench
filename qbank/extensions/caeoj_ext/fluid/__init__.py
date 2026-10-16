"""Shared fluid declaration helpers; domain implementations live in subpackages."""


def reduced_parameters(problem):
    """Read declared SI constants without defaults or unit conversion."""
    return {name: item['value'] for name, item in problem.manifest['physics']['parameters'].items()}
