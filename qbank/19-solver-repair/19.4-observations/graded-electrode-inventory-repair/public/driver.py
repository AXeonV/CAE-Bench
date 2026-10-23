"""Evaluate real PyBaMM total-concentration submodels on supplied FV states."""
import os
os.environ['PYBAMM_DISABLE_TELEMETRY']='true'
import json
import sys
import numpy as np
import pybamm


def evaluate(request):
    options=pybamm.BatteryModelOptions({})
    parameters=pybamm.LithiumIonParameters(options)
    geometry={}; types={}; points={}; variables=[]; expressions={}
    for domain,suffix in [('negative','n'),('positive','p')]:
        x=pybamm.SpatialVariable('x_'+suffix,domain=domain+' electrode')
        r=pybamm.SpatialVariable('r_'+suffix,domain=domain+' particle',coord_sys='spherical polar')
        geometry[domain+' electrode']={x:{'min':0,'max':1}}
        geometry[domain+' particle']={r:{'min':0,'max':1}}
        points[x]=request['x_count_'+suffix]; points[r]=request['r_count_'+suffix]
        types[domain+' electrode']=pybamm.Uniform1DSubMesh
        types[domain+' particle']=pybamm.Uniform1DSubMesh
        concentration=pybamm.Variable('c_'+suffix,domain=domain+' particle',auxiliary_domains={'secondary':domain+' electrode'})
        epsilon=pybamm.Variable('epsilon_'+suffix,domain=domain+' electrode')
        variables.extend([concentration,epsilon])
        radial=pybamm.r_average(concentration)
        model=pybamm.particle.TotalConcentration(parameters,domain,options)
        observations=model.get_coupled_variables({
            'R-averaged '+domain+' particle concentration [mol.m-3]':radial,
            domain.title()+' electrode active material volume fraction':epsilon})
        expressions['radial_'+suffix]=radial
        expressions['volume_'+suffix]=observations[domain.title()+' electrode volume-averaged concentration [mol.m-3]']
        expressions['stoichiometry_'+suffix]=observations[domain.title()+' electrode stoichiometry']
        expressions['inventory_'+suffix]=observations['Total lithium in primary phase in '+domain+' electrode [mol]']
    expressions['total_inventory']=expressions['inventory_n']+expressions['inventory_p']
    mesh=pybamm.Mesh(geometry,types,points)
    discretisation=pybamm.Discretisation(mesh,{domain:pybamm.FiniteVolume() for domain in geometry})
    discretisation.set_variable_slices(variables)
    result={name:[] for name in expressions}
    for state in request['states']:
        values=pybamm.ParameterValues('Chen2020')
        values.update({'Negative electrode thickness [m]':state['thickness_n'],
                       'Positive electrode thickness [m]':state['thickness_p'],
                       'Electrode width [m]':state['area'],'Electrode height [m]':1.,
                       'Maximum concentration in negative electrode [mol.m-3]':state['cmax_n'],
                       'Maximum concentration in positive electrode [mol.m-3]':state['cmax_p']})
        y=np.concatenate([np.asarray(state[name],dtype=float).reshape(-1) for name in
                          ['concentration_n','epsilon_n','concentration_p','epsilon_p']])
        for name,symbol in expressions.items():
            output=discretisation.process_symbol(values.process_symbol(symbol)).evaluate(y=y)
            result[name].append(np.asarray(output,dtype=float).reshape(-1).tolist())
    return result


if __name__=='__main__':
    json.dump(evaluate(json.load(sys.stdin)),sys.stdout,allow_nan=False)
