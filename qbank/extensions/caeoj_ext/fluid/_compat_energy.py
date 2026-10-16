"""Compatibility API for the energy capabilities present in an assembly."""
from importlib import import_module
from importlib.util import find_spec

_MODULES = ('thermal_flow', 'turbulence')
_OWNERS = tuple(import_module(f'{__package__}.{name}') for name in _MODULES
                if find_spec(f'{__package__}.{name}') is not None)
MODELS = {model: config for owner in _OWNERS for model, config in owner.MODELS.items()}


def _required(name):
    module = f'{__package__}.{name}'
    if find_spec(module) is None:
        raise RuntimeError(f'Installed materials do not include the {name} capability')
    return import_module(module)


def parameter_units(model):
    return _required('thermal_flow').parameter_units(model, MODELS)


def fluid_energy_properties(problem, temperature, pressure=None):
    model = problem.manifest['physics']['model']
    return _required('thermal_flow').fluid_energy_properties(
        problem, temperature, pressure, model_config=MODELS[model])


def fluid_energy_condition_values(problem, condition, parameter, time):
    return _required('thermal_flow').fluid_energy_condition_values(problem, condition, parameter, time)


def fluid_energy_statistics(times, velocity, temperature=None):
    return _required('turbulence').fluid_energy_statistics(times, velocity, temperature)


def check_fluid_energy(problem, errors):
    _required('thermal_flow').check_declaration(problem, errors, MODELS)


check = check_fluid_energy
