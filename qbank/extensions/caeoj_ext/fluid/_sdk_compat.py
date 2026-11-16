"""Preserve historical SDK keyword names independently of module helper APIs."""


def reduced_viscosity(model, params, shear_rate, temperature=None, structure=None):
    from ._compat_reduced import reduced_viscosity as evaluate
    return evaluate(model, params, shear_rate, temperature, structure)


def maxwellian(number_density, velocity, temperature, mass, molecular_velocity):
    from ._compat_reduced import maxwellian as evaluate
    return evaluate(number_density, velocity, temperature, mass, molecular_velocity)
