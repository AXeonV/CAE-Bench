"""Real PyBaMM thermal submodel evaluation for supplied local states."""
import os
os.environ['PYBAMM_DISABLE_TELEMETRY']='true'
import json
import sys
import numpy as np
import pybamm


def run(request):
    def choice(suffix):
        count=request['phases_'+suffix];mask=request['mask_'+suffix]
        names=['current sigmoid' if (mask>>k)&1 else 'single' for k in range(count)]
        return names[0] if count==1 else tuple(names)
    options=pybamm.BatteryModelOptions({'particle phases':(str(request['phases_n']),str(request['phases_p'])),
                                       'open-circuit potential':(choice('n'),choice('p'))})
    param=pybamm.LithiumIonParameters(options)
    thermal=pybamm.thermal.BaseThermal(param,options)
    model=pybamm.lithium_ion.DFN()
    out={name:[] for name in ['heat_negative','heat_positive','area_heat','cell_heat','volume_heat']}
    for state in request['states']:
        def broad(value,domain):return pybamm.FullBroadcast(float(value),domain,'current collector')
        v={'Current collector current density [A.m-2]':pybamm.Scalar(0),
           'Volume-averaged cell temperature [K]':pybamm.Scalar(state['temperature'])}
        for Domain,domain,suffix in [('Negative','negative','n'),('Positive','positive','p')]:
            region=domain+' electrode'
            v[Domain+' electrode current density [A.m-2]']=broad(0,region)
            v[Domain+' electrode potential [V]']=broad(0,region)
            v[Domain+' electrode temperature [K]']=broad(state['temperature'],region)
            phases=[''] if request['phases_'+suffix]==1 else ['primary ','secondary ']
            for index,phase in enumerate(phases):
                for field,key in [('current','volumetric interfacial current density [A.m-3]'),
                                  ('eta','reaction overpotential [V]'),('entropy','entropic change [V.K-1]'),
                                  ('ocp','open-circuit potential [V]'),('equilibrium','equilibrium open-circuit potential [V]')]:
                    v[Domain+' electrode '+phase+key]=broad(state[field+'_'+suffix][index],region)
        v['Electrolyte current density [A.m-2]']=pybamm.concatenation(*[broad(0,d) for d in ['negative electrode','separator','positive electrode']])
        for title,domain in [('Negative','negative electrode'),('Separator','separator'),('Positive','positive electrode')]:
            v[title+' electrolyte potential [V]']=broad(0,domain)
        v['Electrolyte potential [V]']=pybamm.concatenation(*[v[d+' electrolyte potential [V]'] for d in ['Negative','Separator','Positive']])
        variables=thermal._get_standard_coupled_variables(v)
        q=variables['Total heating [W.m-3]']
        expressions={'heat_negative':pybamm.boundary_value(q,'left'),'heat_positive':pybamm.boundary_value(q,'right'),
                     'area_heat':variables['Total heating per unit electrode-pair area [W.m-2]'],
                     'cell_heat':variables['Total heating [W]'],'volume_heat':variables['Volume-averaged total heating [W.m-3]']}
        values=pybamm.ParameterValues('Chen2020')
        values.update({'Negative electrode thickness [m]':state['length_n'],'Positive electrode thickness [m]':state['length_p'],
                       'Separator thickness [m]':state['length_s'],'Negative current collector thickness [m]':state['length_cn'],
                       'Positive current collector thickness [m]':state['length_cp'],'Electrode width [m]':state['area'],
                       'Electrode height [m]':1.,'Number of electrodes connected in parallel to make a cell':request['pairs'],
                       'Cell volume [m3]':state['volume']})
        geometry=model.default_geometry;values.process_geometry(geometry)
        mesh=pybamm.Mesh(geometry,model.default_submesh_types,{k:3 for k in model.default_var_pts})
        disc=pybamm.Discretisation(mesh,model.default_spatial_methods)
        for name,symbol in expressions.items():
            value=disc.process_symbol(values.process_symbol(symbol)).evaluate()
            out[name].append(np.asarray(value,dtype=float).reshape(-1).tolist())
    return out


if __name__=='__main__':json.dump(run(json.load(sys.stdin)),sys.stdout,allow_nan=False)
