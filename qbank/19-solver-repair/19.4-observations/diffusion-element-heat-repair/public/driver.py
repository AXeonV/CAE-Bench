"""Trusted caller of PyBaMM submodel APIs; no reference corrections."""
import json
import os
import sys
import numpy as np
os.environ['PYBAMM_DISABLE_TELEMETRY'] = 'true'
import pybamm


def run(data):
    count = data['grid_count']
    x = pybamm.SpatialVariable('x ECMD', domain=['ECMD particle'], coord_sys='Cartesian')
    geometry = {'ECMD particle': {x: {'min': 0, 'max': 1}}}
    mesh = pybamm.Mesh(geometry, {'ECMD particle': pybamm.Uniform1DSubMesh}, {x: count})
    discretisation = pybamm.Discretisation(mesh, {'ECMD particle': pybamm.FiniteVolume()})
    param = pybamm.EcmParameters()
    options = {'number of rc elements': data['rc_count']}
    result = {name: [] for name in ('surface_soc', 'diffusion_overpotential', 'irreversible_heat', 'total_heat')}
    for state in data['states']:
        coeff = state['ocv_coefficients']

        def ocv(s):
            return coeff[0] + coeff[1] * s + coeff[2] * s**2 + coeff[3] * s**3

        values = pybamm.ParameterValues({'Open-circuit voltage [V]': ocv})
        variables = {'SoC': pybamm.Scalar(state['average_soc']),
                     'Distributed SoC': pybamm.Vector(np.asarray(state['soc_profile']), domain='ECMD particle'),
                     'Current [A]': pybamm.Scalar(state['current']),
                     'Reversible heat generation [W]': pybamm.Scalar(state['reversible_heat'])}
        variables.update({f'Element-{i} irreversible heat generation [W]': pybamm.Scalar(q)
                          for i, q in enumerate(state['element_heat'])})
        cls = pybamm.equivalent_circuit_elements.DiffusionElement if state['diffusion_enabled'] else pybamm.equivalent_circuit_elements.NoDiffusion
        variables = cls(param, options).get_coupled_variables(variables)
        variables = pybamm.equivalent_circuit_elements.ThermalSubModel(param, options).get_coupled_variables(variables)
        for output, variable in [('surface_soc', 'Surface SoC'),
                                 ('diffusion_overpotential', 'Diffusion overpotential [V]'),
                                 ('irreversible_heat', 'Irreversible heat generation [W]'),
                                 ('total_heat', 'Total heat generation [W]')]:
            expression = values.process_symbol(variables[variable])
            scalar = discretisation.process_symbol(expression).evaluate()
            result[output].append([float(np.asarray(scalar).item())])
    return result


if __name__ == '__main__':
    try:
        print(json.dumps(run(json.load(sys.stdin)), allow_nan=False))
    except Exception:
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
