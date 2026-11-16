"""Compatibility API for the physical capabilities present in an assembly."""
from importlib import import_module
from importlib.util import find_spec
from caeoj.validation import issue
from . import reduced_parameters
from ._sampling import reduced_time_derivative
from ._rheology import viscosity_response

PREFIX = 'fluid-reduced-'
_MODULES = ('thin_film', 'depth_averaged', 'rarefied', 'complex_fluid')
_OWNERS = tuple(import_module(f'{__package__}.{name}') for name in _MODULES
                if find_spec(f'{__package__}.{name}') is not None)
MODELS = {model: config for owner in _OWNERS for model, config in owner.MODELS.items()}
UNITS = {q: unit for config in MODELS.values() for q, (unit, kind) in config['output_specs'].items()}
VECTORS = {q for config in MODELS.values() for q, (_, kind) in config['output_specs'].items() if kind == 'vector'}
TENSORS = {q for config in MODELS.values() for q, (_, kind) in config['output_specs'].items() if kind == 'tensor'}


def boundary_rules(cfg):
    return cfg['boundary_rules']



def reduced_viscosity(model, parameters, shear_rate, temperature=None, structure=None):
    return viscosity_response(MODELS[model], parameters, shear_rate, temperature, structure)


def _required(name):
    module = f'{__package__}.{name}'
    if find_spec(module) is None:
        raise RuntimeError(f'Installed materials do not include the {name} capability')
    return import_module(module)


def maxwellian(number_density, velocity, temperature, molecule_mass, molecular_velocity):
    return _required('rarefied').maxwellian(
        number_density, velocity, temperature, molecule_mass, molecular_velocity)


def layer_characteristic_speeds(lower_depth, upper_depth, lower_normal_velocity,
                                 upper_normal_velocity, gravity, density_ratio):
    return _required('depth_averaged').layer_characteristic_speeds(
        lower_depth, upper_depth, lower_normal_velocity, upper_normal_velocity, gravity, density_ratio)


def check_fluid_reduced(problem, errors):
    model = problem.manifest.get('physics', {}).get('model', '')
    if not model.startswith(PREFIX):
        return
    if model not in MODELS:
        errors.append(issue('E_FLUID', '$.physics.model', list(MODELS), model,
                            'Unknown reduced fluid model/version.'))
        return
    owner = next(owner for owner in _OWNERS if model in owner.MODELS)
    owner.check(problem, errors)


check = check_fluid_reduced
