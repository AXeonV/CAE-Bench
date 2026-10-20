"""Numerical experiment specifications, not a reference solver.

Expressions specify input data construction. They are never inserted into
problem.json as a new interface or used to synthesize reference answers.
"""
from __future__ import annotations
import math
import re
from copy import deepcopy

VALUES = {
    "reference_temperature":300., "minimum_temperature":250., "maximum_temperature":450.,
    "specific_gas_constant":287., "mean_density":1., "heat_capacity_ratio":1.4,
    "isentropic_reference_density":0.98,"density":1.,"reference_pressure":100000.,
    "reference_viscosity":0.01,"viscosity_exponent":0.,"bulk_viscosity":0.,
    "reference_conductivity":0.02,"conductivity_exponent":0.,"heat_capacity":1.,
    "thermal_expansion":0.,"time_start":0.,"time_end":1.,"start_time":0.,"end_time":1.,
    "statistics_start":0.5,"statistics_end":1.,"statistics_step":0.025,
    "density_a":1000.,"density_b":500.,"viscosity_a":1.,"viscosity_b":0.5,
    "pressure_reference":100000.,"surface_tension":0.05,"contact_angle":math.pi/2,
    "slip_length":2e-7,"relaxation_time":0.1,"diameter":1e-4,
    "packing_fraction":0.6,"particle_modulus":1.,
    "heat_capacity_a":1000.,"heat_capacity_b":1500.,"conductivity_a":1.,"conductivity_b":0.1,
    "latent_heat":10000.,"saturation_temperature":300.,"evaporation_frequency":0.1,
    "condensation_frequency":1.,"saturation_pressure":100000.,"pressure_rate":0.001,
    "nuclei_fraction":0.001,"interface_mass_coefficient":0.01,
    "heat_exchange":1000.,"mass_exchange":1.,"diffusivity_a":1e-4,"diffusivity_b":5e-5,
    "solidus_temperature":299.,"liquidus_temperature":301.,"mushy_resistance":1e6,
    "mushy_epsilon":0.001,"viscosity":0.01,"cavitation_pressure":100000.,
    "zero_viscosity":0.1,"infinite_viscosity":0.001,"time_constant":0.1,"power_index":0.6,
    "conductivity":0.02,"temperature_coefficient":0.02,"heat_transfer":100.,
    "gravity":9.81,"drag_rate":0.,"lower_density":1000.,"upper_density":900.,
    "bottom_drag":0.,"interface_drag":0.,"molecule_mass":6.63e-26,
    "molecule_diameter":3.4e-10,"temperature_jump_length":1e-7,"heat_conductivity":0.018,
    "solvent_viscosity":0.05,"polymer_viscosity":0.05,"base_viscosity":0.01,
    "structure_viscosity":0.09,"build_time":0.2,"breakdown":0.1,
}


def required_parameters(data):
    m=re.search(r"## (?:参数与材料响应|全局参数)(.*?)(?=\n## |\Z)",data,re.S)
    pairs=[]
    if m:
        for line in m[1].splitlines():
            x=line.strip().split("|")
            if len(x)>3 and re.fullmatch("[a-z_, `]+",x[1].strip()) and x[1].strip() not in ("name",""):
                pairs += [(k.strip(" `"),x[2].strip()) for k in x[1].split(",")]
    else:
        line=next((line for line in data.splitlines() if line.startswith("参数：")),"")
        pairs=re.findall(r"`(\w+)` \((.*?)\)(?:；|。)",line)
    return pairs


def parameters(data,family,slug,i):
    result={k:{"value":VALUES[k],"unit":u} for k,u in required_parameters(data)}
    def setv(k,v):
        if k in result:result[k]["value"]=v
    if family in ("lowmach_energy","compressible_energy"):
        if i in (1,3,4):setv("thermal_expansion",0.002)
        if i==7:setv("viscosity_exponent",1.5)
        if i in (7,8):setv("conductivity_exponent",0.75)
        if i==8:setv("bulk_viscosity",0.02)
    if family=='lowmach_energy' or 'rans' in slug.split('-') or 'urans' in slug.split('-') or 'statistics' in slug:
        setv('minimum_temperature',280.);setv('maximum_temperature',320.)
    if family in ('euler_transient','euler_equilibrium','compressible_energy'):
        setv('minimum_temperature',100.);setv('maximum_temperature',1000.)
    if "rans" in slug.split('-') or "urans" in slug.split('-') or "statistics" in slug:
        setv("reference_viscosity",1e-4)
    if family in ("free_surface","immiscible"):
        setv("viscosity_a",10. if i==8 else 1.)
        if family=='immiscible' and i==3:setv('density_a',500.);setv('density_b',1000.)
    if family=="capillary":
        setv("density_b",10.);setv("viscosity_a",0.01);setv("viscosity_b",0.001)
        setv("slip_length",2e-5)
        angles=[90,60,120,50 if slug.endswith('3d') else 30,90,90,90,120,60,90]
        setv("contact_angle",math.radians(angles[i]))
        if i==5:setv("viscosity_a",0.1)
        if i==6:setv("density_b",100.)
    if family=="dispersed":
        setv("density_b",10. if slug=="bubbles-droplets-3d" else 2500.)
        setv("viscosity_b",0.01);setv("relaxation_time",0.1 if i==4 else 0.001 if i==5 else 0.01)
    if family in ("evaporation","boiling","cavitation"):
        setv("density_b",10.);setv("viscosity_a",0.01);setv("viscosity_b",0.001)
        if family=="cavitation" and i in (0,1):setv("saturation_pressure",100100. if i==0 else 99900.)
    if family=="exchange":
        setv("heat_capacity_a",10.);setv("heat_capacity_b",20.)
        if i==0:setv("mass_exchange",0.)
        if i==1:setv("heat_exchange",0.)
    if family=="melting":setv("latent_heat",5000.)
    if family in ("gas_film","slip_gas"):
        setv("viscosity",1.8e-5);setv("specific_gas_constant",208.23295625942683)
    if family=="thermal_film":
        setv("density",1000.);setv("heat_capacity",1000.);setv("conductivity",0.1)
        setv("heat_transfer",1. if i in (1,2,5) else 1000. if i==6 else 100.)
    if family in ("liquid_film","nonnewtonian_film"):setv("density",1000.)
    if family in ("shallow_steady","shallow_transient","wetdry"):
        setv("density",1000.);setv("drag_rate",0.1 if i in (7,8) else 0.)
    if family=="two_layer":
        setv("bottom_drag",0.1 if i==6 else 0.)
        setv("interface_drag",10. if i in (2,7) else 0.)
    return result


def geometry(family,i,d,title):
    L=[1.,1.,0.8][:d]
    if i in (1,):L[1]=2.
    if i in (2,):L[0]=3.
    if family in ("free_surface","immiscible","exchange","dispersed"):L=[0.1,0.1,0.08][:d]
    if family in ("capillary","boiling","cavitation","evaporation","melting"):L=[0.01,0.01,0.008][:d]
    if "film" in family:L=[0.001,0.0005] if family=="gas_film" else [0.01,0.005]
    if family.startswith("shallow") or family in ("two_layer","wetdry"):L=[10.,5.]
    if family=="slip_gas":L=[1e-4,2e-5]
    if family=="kinetic_gas":L=[1e-3,2e-4,2e-4]
    if any(k in title for k in ("长","宽")):L[0]*=2.
    if any(k in title for k in ("高","深")):L[1]*=2.
    if "短宽" in title:L[1]=2*L[0]
    recipe={"length_unit":"m","dimension":d,"origin":[0.]*d,"bounding_lengths":L,
            "operation":"box","holes":[],"ports":{"inlet":"x=0","outlet":"x=Lx"},"boundary_partition":"coordinate faces; split moving/thermal faces at their midpoint when specified"}
    if any(k in title for k in ("方柱","方孔","障碍物","内孔","有岛")):
        hole=[[0.4*L[0],0.3*L[1]],[0.6*L[0],0.5*L[1]]]
        recipe["holes"]=[{"operation":"box","xy_corners":hole,"span_z":[0,L[2]] if d==3 else None}]
    if "收缩" in title or "扩张" in title:
        poly=[[0,0],[L[0],0],[L[0],0.5*L[1]],[0.6*L[0],0.5*L[1]],[0.4*L[0],L[1]],[0,L[1]]]
        if "扩张" in title:poly=[[L[0]-x,y] for x,y in poly][::-1]
        recipe.update(operation="polygon_extrusion" if d==3 else "polygon",xy_vertices=poly)
    if "弯" in title:
        recipe.update(operation="polygon_extrusion" if d==3 else "polygon",xy_vertices=[[0,0],[L[0],0],[L[0],L[1]],[0.7*L[0],L[1]],[0.7*L[0],0.3*L[1]],[0,0.3*L[1]]],ports={"inlet":"x=0,y<0.3*Ly","outlet":"y=Ly,x>0.7*Lx"})
    if "分支" in title or "分叉" in title or "多入口" in title:
        recipe.update(operation="union_extrusion" if d==3 else "union",xy_rectangles=[[[0,0.375*L[1]],[L[0],0.625*L[1]]],[[0.375*L[0],0],[0.625*L[0],L[1]]]],ports={"inlet":"x=0","outlet":"x=Lx","left":"x=0","right":"x=Lx","bottom":"y=0","top":"y=Ly"})
    if "两池" in title:
        recipe.update(operation="union_extrusion" if d==3 else "union",xy_rectangles=[[[0,0],[L[0]/3,L[1]]],[[L[0]/3,0.4*L[1]],[2*L[0]/3,0.6*L[1]]],[[2*L[0]/3,0],[L[0],L[1]]]])
    if "台阶" in title:
        recipe["holes"].append({"operation":"box","xy_corners":[[0.5*L[0],0],[L[0],0.25*L[1]]],"span_z":[0,L[2]] if d==3 else None})
    if "非对称多边形" in title:
        recipe.update(operation="polygon",xy_vertices=[[0,0],[L[0],0],[L[0],0.7*L[1]],[0.6*L[0],L[1]],[0,L[1]]])
    return recipe


def field(expr,unit,space="piecewise_constant",history=None):
    return {"expression":expr,"unit":unit,"space_reconstruction":space,"time_history":history or "constant"}


def base_spec(rec,entry,i,data):
    fam=rec["family"];d=entry["spatial_dimension"];kind=rec["analysis_kind"]
    geo=geometry(fam,i,d,entry["title"]);L=geo["bounding_lengths"]
    end={"free_surface":0.3,"immiscible":0.3,"capillary":0.003,"dispersed":0.2,"exchange":2.,"evaporation":20.,"boiling":2.,"cavitation":0.2,"melting":10.031,"liquid_film":0.,"nonnewtonian_film":0.,"gas_film":0.01,"thermal_film":1.,"shallow_steady":0.,"shallow_transient":0.5,"wetdry":0.5,"two_layer":0.5,"slip_gas":0.,"kinetic_gas":0.}.get(fam,1.)
    if kind=="steady":end=0.
    if fam=="euler_transient":end=0.001
    params=parameters(data,fam,rec["task"],i)
    for key in ("time_end","end_time"):
        if key in params:params[key]["value"]=end
    if kind=="discrete_statistics":
        for k,v in (("statistics_start",end/2),("statistics_end",end),("statistics_step",end/40)):params[k]["value"]=v
    times=[0.] if kind=="steady" else [end] if kind=="discrete_statistics" else [round(end*v,12) for v in (.173,.397,.719,1.)]
    spec={"version":1,"status":"numerical_experiment_specified_not_input_package_not_reference",
          "geometry":geo,"analysis_kind":kind,"parameters":params,
          "time_interval_s":None if kind=="steady" else [0.,end],"output_times_s":times,
          "mesh_recipe":{"generator":"Gmsh","format":"4.1 ASCII","order":1,"coordinate_unit":"m","algorithm_2d":6,"algorithm_3d":1,"random_seed":112358,"base_divisions":[24,24] if d==2 else [12,12,10],"top_dimensional_element_cap":25000,"phase_boundary_conforming":fam in ("free_surface","immiscible","capillary","evaporation"),"corner_refinement_size_m":min(L)/40,"bulk_size_m":min(L)/12},
          "definitions":{"X":"x/Lx","Y":"y/Ly","Z":"z/Lz (3D only)","n":"true outward unit normal of each supplied boundary entity","R":"linear table (0,0),(0.1*end,1),(end,1); in steady analysis R=1","P":"linear table (0,0),(.1*end,1),(.4*end,1),(.6*end,0),(end,0)","V":"linear table (0,0),(.1*end,1),(.4*end,1),(.6*end,-1),(end,-1)","bump":"max(1-r2,0)^4; r2=sum(((x_j-centre_j)/radius_j)^2)","C":"cellwise curl of the continuous nodal P1 potential; zero potential on all boundary-adjacent elements; scale the resulting field to specified max speed. In 2D use rotated gradient of scalar potential; in 3D curl of vector potential (0,0,psi). No projection of an inconsistent initial velocity is permitted."},
          "field_time_semantics":"R/P/V in an expression are evaluated once at each history node; a string time_history names interpolation only, not an extra multiplier. A dictionary of samples is an explicit scalar multiplier on the spatial expression. A constant expression with linear history has equal endpoints. Initial fields only have the start frame.",
          "field_evaluation":"Expressions construct INPUT samples only. Nodal expressions are evaluated on actual nodes then interpreted as P1, entity data are actual averages of the indicated input reconstruction. Actual phase is the specified phase-cell union. Do not reinterpret sampling as an unprovided analytic field.",
          "initial":{},"sources":{},"boundaries":[],
          "pressure_convention":"exactly the task DATA; no output re-zeroing unless the declared gauge requires it",
          "observations":{"primary":"all quantities required by DATA; stored on the required support","optional_quantities_from_grading_template":"add only applicable quantities at unique finite traces","interior_node_rule":"for reduced node outputs select all nodes at least two local edge layers from boundary intersections and phase/bed derivative singularities; retain the full domain-node input location separately","derivative_at_initial_time":False},
          "numerical_validation_requested":False,"acceptance_claim":"none; no accuracy/resource certification",
          "manufacturing_rules":["All boundary entities belong to exactly one mechanical partition; independent thermal partition only when permitted by DATA.","Every numeric parameter and field uses the stated SI unit; no hidden Earth gravity or solver-specific physical input.","Output physical times are independent of native integration steps. Do not substitute a final frame for a steady state or for discrete statistics."]}
    return spec


def wall(spec,selection="all",operator="wall",**data):
    spec["boundaries"].append({"selection":selection,"operator":operator,"data":data})


def cfd_flow(spec,rec,i):
    d=spec["geometry"]["dimension"];f=rec["family"];steady=rec["analysis_kind"]=="steady"
    gas=f=="isothermal_compressible";gn=f=="generalized_flow";rho=1.;mu=0.1 if gas else .01
    spec["materials"]={"density":{"kind":"isothermal_ideal_gas" if gas else "constant","parameters":{"specific_gas_constant":{"value":287.,"unit":"J/(kg.K)"}} if gas else {"density":{"value":rho,"unit":"kg/m3"}}},"viscosity":{"kind":"newtonian","parameters":{"dynamic_viscosity":{"value":mu,"unit":"Pa.s"}}}}
    if gas:
        spec["materials"]["viscosity"]["parameters"]["bulk_viscosity"]={"value":.2 if i in (3,8) else 0.,"unit":"Pa.s"}
        if i in (1,3,6,9):spec["materials"]["density"]={"kind":"linear_barotropic","parameters":{"reference_density":{"value":1.,"unit":"kg/m3"},"reference_pressure":{"value":86100.,"unit":"Pa"},"sound_speed":{"value":300.,"unit":"m/s"}}}
    if gn:
        law=["power_law","power_law","cross","carreau","carreau_yasuda","power_law","cross","carreau","carreau_yasuda","power_law"][i]
        lawparams={'reference_viscosity':(.05,'Pa.s'),'reference_shear_rate':(1.,'1/s'),'minimum_shear_rate':(.1,'1/s'),'maximum_shear_rate':(10.,'1/s'),'power_index':(1.3 if i==1 else .6,'1')} if law=='power_law' else {'zero_shear_viscosity':(.1,'Pa.s'),'infinite_shear_viscosity':(.01,'Pa.s'),'relaxation_time':(.5,'s'),**({'cross_exponent':(1.5,'1')} if law=='cross' else {'power_index':(.6,'1')})}
        if law=='carreau_yasuda':lawparams['transition_index']=(1.5,'1')
        spec['materials']['viscosity']={'kind':law,'parameters':{k:{'value':v,'unit':u} for k,(v,u) in lawparams.items()}}
    spec["analysis"]={"temperature_K":300.,"pressure_representation":"absolute" if gas else "gauge","reference_pressure_Pa":None if gas else 101325.,"pressure_gauge":None,"mean_density_kg_m3":1. if gas and steady else None}
    spec["initial"]={} if steady else {"velocity":field([0.]*d,"m/s")}
    if gas and not steady:spec["initial"]["density"]=field("1+0.0001*bump(centre=.5*L,radius=.2*L)" if i==8 else 1.,"kg/m3")
    # all unlisted boundary faces are no_slip; each subsequent partition is removed from that set
    wall(spec,"complement_of_explicit_partitions","no_slip")
    ramp="constant" if steady else "R"
    closed=not gas
    if not gn and not gas:
        if i in (0,8,9):wall(spec,"y=Ly","moving_wall",velocity=field(["1*"+("P" if i==8 else "V" if i==9 else "R"),0]+([0] if d==3 else []),"m/s",history="constant" if steady else "linear"))
        if i in (1,4,7):
            wall(spec,"x=0","flow_rate" if i==7 else "velocity",**({"rate_m_dimension_per_s":.1,"shape":field("1+0.5*Y","1","piecewise_linear"),"history":ramp} if i==7 else {"velocity":field(["R*0.1*4*Y*(1-Y)"+('*4*Z*(1-Z)' if d==3 else ''),0]+([0] if d==3 else []),"m/s","piecewise_linear",ramp)}))
            wall(spec,"x=Lx","pressure_outlet",pressure_Pa=0.,backflow="forbid",meaning="full sigma*n=-p_ext*n")
        if i==2:
            wall(spec,"x=0","traction",traction=field("-R*0.1*n","Pa",history=ramp))
            wall(spec,"x=Lx","traction",traction=field([0.]*d,"Pa"))
        if i==3:
            wall(spec,"x=0 and x=Lx","periodic",translation_m="(+Lx,0[,0]) left-to-right; opposite on partner",pressure_jump_Pa=0.)
            spec["sources"]["acceleration"]=field(["R*0.1",0]+([0] if d==3 else []),"m/s2",history=ramp)
        if i==4:wall(spec,"y=Ly","symmetry")
        if i==5:
            spec["boundaries"]=[];wall(spec,"all","slip")
            spec["initial"]["velocity"]=field("C from nodal psi=sin(pi*X)*sin(pi*Y)"+('*cos(pi*Z)' if d==3 else '')+"; max speed 0.1 m/s; boundary potential chosen for zero tangential traction", "m/s")
            spec["definitions"]["slip_vortex_construction"]="Use the defined compact boundary-adjacent-zero C construction, so velocity and gradient vanish in the initial boundary band. Curl of continuous P1 potential has matching normal traces. The nodal potential is the stated sine/cosine pattern before applying that band."
        if i==6:
            spec["sources"]["acceleration"]=field("(0.1*sin(2*pi*Y),0[,0])","m/s2","piecewise_linear",{"mode":"previous","samples":[[0,1],[.5*spec['time_interval_s'][1],-1],[spec['time_interval_s'][1],-1]]})
        closed=i in (0,3,5,6,8,9)
    elif gn:
        if i in (0,2,4,8):
            wall(spec,"x=0","flow_rate" if i==2 else "velocity",velocity=field(["0.1*R*4*Y*(1-Y)"+('*4*Z*(1-Z)' if d==3 else ''),0]+([0] if d==3 else []),"m/s","piecewise_linear",ramp),**({"rate_m_dimension_per_s":.1,"shape":field("1+0.5*Y","1","piecewise_linear")} if i==2 else {}))
            if i==2:spec["boundaries"][-1]["data"].pop("velocity")
            wall(spec,"x=Lx","pressure_outlet",pressure_Pa=0.,backflow="forbid",meaning="full sigma*n=-p_ext*n")
        if i==1:
            wall(spec,"x=0 and x=Lx","periodic",translation_m="(+Lx,0[,0]) left-to-right; opposite on partner",pressure_jump_Pa=0.)
            spec["sources"]["acceleration"]=field(["0.1*R",0]+([0] if d==3 else []),"m/s2",history=ramp)
        if i==4:wall(spec,"y=Ly","symmetry")
        if i==8:wall(spec,"y=Ly","slip")
        if i==5:
            wall(spec,"x=0","traction",traction=field("-0.1*R*n","Pa",history=ramp));wall(spec,"x=Lx","traction",traction=field([0.]*d,"Pa"))
        if i in (3,7,9):
            wall(spec,"y=Ly","moving_wall",velocity=field(["R" if i!=7 or steady else "P",0]+([0] if d==3 else []),"m/s",history=ramp))
            wall(spec,"y=0","moving_wall",velocity=field(["-0.5*R",0]+([0] if d==3 else []),"m/s",history=ramp))
        if i==6:spec["sources"]["acceleration"]=field("(.1*sin(2*pi*Y),0[,0])","m/s2","piecewise_linear",ramp)
        if i==9 and not steady:spec["initial"]["velocity"]=field("C from compact P1 potential; centre=.5*L, radius=.2*L; max speed .1 m/s","m/s")
        closed=i in (1,3,6,7,9)
    else:
        if i in (0,1,2):wall(spec,"y=Ly","moving_wall",velocity=field(["R",0]+([0] if d==3 else []),"m/s",history=ramp))
        if i==3:
            wall(spec,"x=0 and x=Lx","periodic",translation_m="(+Lx,0[,0]) left-to-right; opposite on partner",pressure_jump_Pa=0.)
            spec["sources"]["acceleration"]=field(["R*.1",0]+([0] if d==3 else []),"m/s2",history=ramp)
        if i in (4,7,8,9):
            wall(spec,"x=0","flow_rate" if i==4 else "velocity",density=field("1+.0001*Y" if i in (8,9) else 1.,"kg/m3","piecewise_linear"),**({"rate_m_dimension_per_s":.1,"shape":field("1+.5*Y","1","piecewise_linear"),"history":ramp} if i==4 else {"velocity":field([".1*R*4*Y*(1-Y)"+('*4*Z*(1-Z)' if d==3 else ''),0]+([0] if d==3 else []),"m/s","piecewise_linear",ramp)}))
            wall(spec,"x=Lx","pressure_outlet",pressure_Pa=86100.,backflow="forbid",meaning="full sigma*n=-p_ext*n")
            if i==9:wall(spec,"y=0 port","velocity",velocity=field([0,".05*R"]+([0] if d==3 else []),"m/s",history=ramp),density_kg_m3=1.00005)
        if i==5:
            spec["boundaries"]=[];wall(spec,"all","slip");spec["sources"]["acceleration"]=field([0,"-.1*R"]+([0] if d==3 else []),"m/s2",history=ramp)
        if i==6:spec["sources"]["acceleration"]=field("(.05*R,-.1*R[,0])","m/s2",history=ramp)
        if i==7:wall(spec,"y=Ly","symmetry")
        closed=i in (0,1,2,3,5,6)
        if not closed:spec["analysis"]["mean_density_kg_m3"]=None
    if closed and not gas:spec["analysis"]["pressure_gauge"]={"kind":"point" if i==6 else "mean","point_m":[.25*x for x in spec['geometry']['bounding_lengths']] if i==6 else None,"value_Pa":0.}
    spec["observations"]["extra"]=["cell mean velocity/pressure/density/dynamic_viscosity/shear_rate","point velocity and pressure at (.25,.35[, .45])*L in fluid","region-volume mean velocity","boundary traction and summed opposite fluid force","signed volume/mass flow on every open port"]
    spec["observations"]["extra_applicability"]="Use no duplicate compulsory field; boundary flow integrals only on actual open boundaries; point pressure gauge is not a second outlet constraint."


def energy(spec,rec,i):
    fam=rec["family"];slug=rec["task"];d=spec["geometry"]["dimension"];steady=rec["analysis_kind"]=="steady";R="1" if steady else "R"
    spec["initial"]={} if steady else {"velocity":field([0.]*d,"m/s"),"temperature":field(300.,"K")}
    compress=fam in ("compressible_energy","euler_transient","euler_equilibrium") or slug=="isothermal-rans-3d"
    if compress and not steady:spec["initial"]["density"]=field(1.,"kg/m3")
    wall(spec,"all","slip_adiabatic" if fam.startswith("euler") else "moving_wall",velocity=field([0.]*d,"m/s"))
    if fam=="euler_equilibrium":
        potentials=["3000*y","2000*x","1500*x+3000*y"+("+1000*z" if d==3 else ""),"5000*y","2500*sum((x-.5*L)^2)",".5*sum(a*(x-.5*L)^2), a=(3000,6000[,9000])","3000*sum((x-.4*L)^2)","3000*abs(x-.5*Lx)","200000*(X-.25)^2*(X-.75)^2",".5*6000*delta^T*M*delta, delta=x-.5*L, M=[[2,.3],[.3,1]] or [[2,.3,.1],[.3,1,.2],[.1,.2,1.5]]"]
        spec["definitions"]["Phi_nodes"]={"expression":potentials[i],"unit":"J/kg"}
        spec["sources"]["acceleration"]=field("-grad(P1 Phi_nodes)","m/s2","piecewise_constant")
        spec["mesh_recipe"].update(base_divisions=[20,20] if d==2 else [20,20,8],simplex_split="2 triangles/rectangle; 6 Kuhn tetrahedra/brick",force_construction="continuous P1 potential on actual supplied simplices")
        spec["input_conservative_force_construction"]="Evaluate potential at supplied nodes, reconstruct continuously P1, set acceleration to its exact negative gradient in each simplex. Equilibrium uses the supplied P1 potential, not the smooth expression before sampling."
        spec["analytic_producer_candidate"]={"source":"Chandrashekar and Zenk, arXiv:1511.08739v2 section 2.1.2 and section 3.1","url":"https://arxiv.org/abs/1511.08739","relation":"K*gamma/(gamma-1)*rho^(gamma-1)+Phi=C; p=K*rho^gamma; T=p/(rho*R); u=0","normalization":"K=R*Tref/rho_s^(gamma-1); choose C from volume-mean density. Same hydrostatic relation extends to 3D conservative potentials.","evaluation":"8-point Gauss-Legendre product/Duffy quadrature per simplex for cell averages; scalar mass-normalization root, no PDE discretization; not accuracy certified"}
        if i in (3,9):spec["parameters"]["mean_density"]["value"]=1.03;spec["parameters"]["isentropic_reference_density"]["value"]=.97
        return
    if fam=="euler_transient":
        rho=["1+.001*cos(pi*X)","1+.1*bump(centre=.4*L,radius=.15*L)","1-.1*bump(centre=.5*L,radius=.15*L)","1 if X<.5 else .125","1 if X<.5 else .5","1+.001*cos(pi*X)*cos(pi*Y)","1","1","1","1+.01*bump(centre=.25*L,radius=.1*L)"][i]
        p=["86100*(rho)^1.4","86100*(rho)^1.4","86100*(rho)^1.4","86100 if X<.5 else 8610","86100","86100*rho^1.4","86100*(1+.3*bump(centre=.5*L,radius=.15*L))","86100*(1+.3*bump(centre=.3*L,radius=.1*L))","86100","86100*rho^1.4"][i]
        spec["initial"].update(density=field(rho,"kg/m3"),temperature=field(f"({p})/(287*({rho}))","K"))
        if i==8:spec["sources"]["acceleration"]=field([0,"-10*P"]+([0] if d==3 else []),"m/s2",history="linear")
        return
    if fam=="turbulent_flow" or slug=="isothermal-rans-3d":
        thermal=False
    else:thermal=True
    spec["boundaries"]=[];wall(spec,"complement_of_explicit_mechanical_parts","moving_wall",velocity=field([0.]*d,"m/s"))
    if fam=="turbulent_flow":
        if i!=7:wall(spec,"y=Ly","moving_wall",velocity=field([R,0]+([0] if d==3 else []),"m/s",history=R))
        if i in (3,4,8):wall(spec,"y=0","moving_wall",velocity=field([f"{-.5 if i!=4 else .5}*{R}",0]+([0] if d==3 else []),"m/s",history=R))
        if i==5:wall(spec,"x=Lx","moving_wall",velocity=field([0,0,R] if d==3 else [0,R],"m/s",history=R))
        if i==7:spec["sources"]["acceleration"]=field(f"(.1*{R}*sin(2*pi*Y),0[,0])","m/s2","piecewise_constant",R)
        if i==9 and not steady:spec["initial"]["velocity"]=field("C from compact nodal potential, centre=.5*L,radius=.2*L,max speed .1 m/s","m/s")
        if i==9 and steady:
            spec['boundaries']=[b for b in spec['boundaries'] if b['selection']!='y=Ly']
            wall(spec,'y=Ly,X<.5','moving_wall',velocity=field([1,0]+([0] if d==3 else []),'m/s'))
            wall(spec,'y=Ly,X>.5','moving_wall',velocity=field([-.5,0]+([0] if d==3 else []),'m/s'))
    elif i in (2,3,4,7,9):
        wall(spec,"y=Ly","moving_wall",velocity=field([R,0]+([0] if d==3 else []),"m/s",history=R))
        if i in (3,4):wall(spec,"x=Lx","moving_wall",velocity=field([0,f"{1 if i==3 else -1}*{R}"]+([0] if d==3 else []),"m/s",history=R))
        if i==2 and d==3:wall(spec,"x=Lx","moving_wall",velocity=field([0,0,f".5*{R}"],"m/s",history=R))
    if i in (1,3,4):spec["sources"]["acceleration"]=field([0,f"-9.81*{R}"]+([0] if d==3 else []),"m/s2",history=R)
    if i==5:
        if thermal:spec["sources"]["heat_source"]=field(f"1*{R}*bump(centre=.5*L,radius=.2*L)","W/m3","piecewise_constant",R)
        else:
            # User-approved correction: isothermal 2.3 forbids a heat source.
            spec["sources"]["acceleration"]=field([f".1*{R}*bump(centre=.5*L,radius=.2*L)"]+[0]*(d-1),"m/s2","piecewise_constant",R)
    if thermal:
        spec["thermal_partition"]=[]
        def temp(selection,expr):spec["thermal_partition"].append({"selection":selection,"operator":"temperature","value":field(expr,"K","piecewise_constant",R)})
        temp("x=0",f"300+5*{R}");temp("x=Lx",f"300-5*{R}")
        if i==6:
            spec["thermal_partition"].append({"selection":"y=0","operator":"outward_heat_flux","value":field(f"-0.1*{R}","W/m2",history=R)})
            temp("y=Ly",300.)
        if i==8 and spec["geometry"]["holes"]:temp("all inner obstacle surfaces",f"300+10*{R}")
        spec["thermal_partition"].append({"selection":"complement_of_explicit_thermal_parts","operator":"outward_heat_flux","value":field(0.,"W/m2")})
        if i==9:
            for part in spec["thermal_partition"]:
                if part["operator"]=="temperature" and not steady:part["value"]["expression"]=str(part["value"]["expression"]).replace("*R","*P")
    if "urans" in slug:
        spec["initial"].update(turbulent_kinetic_energy=field(".001*(1+.2*bump(centre=.5*L,radius=.2*L))" if i==9 else .001,"m2/s2"),turbulence_length_scale=field(.05,"m"))
        spec["producer_private_initialization"]="For a selected documented closure initialize private states from public k/l and DATA second-order states; save mapping in producer record. No private closure state enters problem.json."
    if rec["analysis_kind"]=="discrete_statistics":
        spec["statistics"]={"sample_times":"a+j*delta, j=0..20, both endpoints", "space_then_time":True,"weight":"equal 1/21","covariance_denominator":21,"favre_weighting":False}


def memory(spec,rec,i):
    d=spec['geometry']['dimension'];slug=rec['task'];fam=rec['family'];steady=rec['analysis_kind']=='steady';R='1' if steady else 'R'
    thermal=slug.startswith('thermal-');thix=fam=='thixotropic';open_case=(i==6 and fam=='viscoelastic') or (i in (8,9) and thix) or (i==3 and fam=='thermal_generalized')
    wall(spec,'complement_of_explicit_mechanical_parts','velocity_wall',value=field([0.]*d,'m/s'))
    if open_case:
        extra={'structure':field('.2+.6*Y' if i==9 else .8,'1','piecewise_constant')} if thix else {'conformation':field('identity_'+str(d),'1')} if fam=='viscoelastic' else {}
        wall(spec,'x=0','velocity_inlet',value=field([f'.1*{R}*4*Y*(1-Y)'+('*4*Z*(1-Z)' if d==3 else ''),0]+([0] if d==3 else []),'m/s','piecewise_constant',R),**extra)
        wall(spec,'x=Lx','traction_outlet',value=field('-100000*n','Pa'))
    else:
        wall(spec,'y=Ly','velocity_wall',value=field([R if steady or i not in (8,9) else ('P' if i==8 else 'V'),0]+([0] if d==3 else []),'m/s',history=R))
        if i in (2,7):wall(spec,'y=0','velocity_wall',value=field([f'-.5*{R}',0]+([0] if d==3 else []),'m/s',history=R))
        if i==4 and d==3:wall(spec,'x=Lx','velocity_wall',value=field([0,0,f'.5*{R}'],'m/s',history=R))
        if i==3 and fam=='viscoelastic':
            spec['boundaries'][-1]['selection']='y=Ly,x<Lx/2';wall(spec,'y=Ly,x>Lx/2','velocity_wall',value=field([f'-{R}',0],'m/s',history=R))
    if not steady:
        spec['initial']['velocity']=field([0.]*d,'m/s')
        if fam=='viscoelastic':spec['initial']['conformation']=field([[1.1,.02],[.02,.95]] if i==7 else [[1.,0.],[0.,1.]],'1','piecewise_linear')
        if thix:spec['initial']['structure']=field('.2+.6*bump(centre=.5*L,radius=.2*L)' if i==6 else .2 if i==1 else 1.,'1','piecewise_linear')
        if thermal:spec['initial']['temperature']=field(300.,'K','piecewise_linear')
    if thermal:
        spec['thermal_partition']=[{'selection':'x=0','operator':'temperature_wall','value':field('300+5*R','K',history='linear')},{'selection':'x=Lx','operator':'temperature_wall','value':field('300-5*R','K',history='linear')},{'selection':'complement','operator':'temperature_wall','value':field(300.,'K')}]
        if open_case:spec['thermal_partition'][0]['operator']='temperature_inlet';spec['thermal_partition'][1]={'selection':'x=Lx','operator':'natural_advective_outflow','diffusive_heat_flux_W_m2':0.}
    if fam=='viscoelastic':
        if i==5:wall(spec,'x=Lx','velocity_wall',value=field([0,f'.5*{R}'],'m/s',history=R))
        if i==8 and steady:
            spec['boundaries'][-1]['selection']='y=Ly,X<1/3'
            wall(spec,'y=Ly,1/3<X<2/3','velocity_wall',value=field([-.5,0],'m/s'))
            wall(spec,'y=Ly,X>2/3','velocity_wall',value=field([.25,0],'m/s'))
        if i==9 and steady:
            L=spec['geometry']['bounding_lengths'];spec['geometry']['holes']=[{'operation':'box','xy_corners':[[.25*L[0],.55*L[1]],[.45*L[0],.7*L[1]]],'span_z':None}]
            wall(spec,'y=0','velocity_wall',value=field([-.25,0],'m/s'))
        if i==8 and not steady:
            spec['initial']['conformation']=field([[1.1,.02],[.02,.95]],'1','piecewise_linear')
    if thix:
        if i==1:
            spec['boundaries'][-1]['data']['value']=field([0.,0.],'m/s')
        if i==2:
            spec['boundaries']=[spec['boundaries'][0]]
            wall(spec,'y=Ly','velocity_wall',value=field(['V',0],'m/s',history='linear'))
        if i==3:wall(spec,'y=0','velocity_wall',value=field(['-.5*R',0],'m/s',history='linear'))
        if i==4:
            spec['boundaries'][-1]['selection']='y=Ly,X<.5'
            wall(spec,'y=Ly,X>.5','velocity_wall',value=field(['-R',0],'m/s',history='linear'))
        if i==6:
            spec['mesh_recipe'].update(base_divisions=[6,6],simplex_split='Each rectangle split into four triangles through its exact centre; uniform rational Cartesian coordinates')
            spec['initial']['velocity']=field('C_nodal, max Euclidean nodal speed .01 m/s','m/s','piecewise_linear')
            spec['definitions']['C_nodal']='On the prescribed 6x6 crisscross triangular mesh, form exact rational rows for the constant divergence of continuous P1 velocity on every triangle and zero velocity at every boundary node. Compute canonical RREF with x/y components ordered by increasing node ID; take the first nonzero nullspace basis vector (first free component=1, other free components=0), then scale its largest Euclidean nodal speed to .01 m/s. The physical initial input IS this constructed P1 vector; no solver projection or unsupplied seed velocity is used.'
        if i==7:
            spec['boundaries']=[spec['boundaries'][0]]
            wall(spec,'y=Ly','velocity_wall',value=field(['P',0],'m/s',history='linear'))
    spec['pressure_convention']='absolute Pa; closed case volume mean=100000 Pa; open case fixed by full outlet traction, no extra mean constraint'
    spec['memory_closure_constraints']=['Do not add conformation/stress/structure diffusion.','Supply true inflow memory; natural transport outflow; no backflow branch is included.','Conformation is SPD, 2D block with Azz=1; polymer stress is reconstructed with the DATA constitutive law.' if fam=='viscoelastic' else 'Use the exact DATA Carreau or structural rheology, without yield stress.']


def interfaces(spec,rec,i):
    fam=rec['family'];d=spec['geometry']['dimension'];L=spec['geometry']['bounding_lengths'];zero=[0.]*d
    wall(spec,'all','wall',mechanical='navier_wetting' if fam=='capillary' else 'no_slip')
    spec['sources']['acceleration']=field(zero,'m/s2')
    spec['initial']['velocity']=field(zero,'m/s')
    masks=["X<.35 and Y<.8","Y<(.8 if X<.35 else .15)","Y<.5+.1*(X-.5)","Y<.3+.15*exp(-40*((X-.5)^2"+('+(Z-.5)^2' if d==3 else '')+'))',"Y<.3+.15*exp(-40*((X-.3)^2"+('+(Z-.4)^2' if d==3 else '')+'))',"X<.35 and Y<.8","(X<.2 or X>.8) and Y<.7","X<.35 and Y<.8","X<.35 and Y<.8","Y<(.8 if X<.5 else .3)"]
    if fam=='immiscible':masks=["Y<.5","X<.5","Y>.5+.02*cos(2*pi*X)"+("*cos(2*pi*Z)" if d==3 else ''),"sum(((x-.5*L)/(.15*L))^2)<1","sum(((x-.5*L)/(.15*L))^2)<1","sum(((x-.35*L)/(.12*L))^2)<1 or sum(((x-.7*L)/(.08*L))^2)<1","Y<.4+.2*X","X<.4","Y<.5","X<.2 or X>.8"]
    if fam=='capillary':
        theta=spec['parameters']['contact_angle']['value'];spec['initial_phase_geometry']={"kind":"contact_conforming_polyhedral_cap","centre_m":[.5*L[0],0]+([.5*L[2]] if d==3 else []),"base_apothem_m":.1*min(L),"height_m":.03*min(L),"contact_angle_rad":theta,"azimuth_sides":8 if d==3 else 2,"side_apothem_at_height":"base_apothem-y*cot(contact_angle)","definition":"a is inside the frustum, 0<=y<=height; side facets meet the wall at exactly the specified contact angle; the complete a/b interface must be mesh-conforming. No artificial mixed initial alpha."}
        if i==0:spec['initial_phase_geometry']={'kind':'flat_layer','interface_y_m':.4*L[1],'phase_a':'y<interface_y','contact_angle_rad':math.pi/2};spec['parameters']['contact_angle']['value']=math.pi/2
        if i in (1,2):spec['initial_phase_geometry']['height_m']*=1.3 if i==1 else .7
        if i==3:
            spec['initial_phase_geometry']={'kind':'corner_component_outside_ball','corner_m':[0.]*d,'radius_m':.15*min(L),'ball_centre_each_axis_m':.15*min(L)*math.cos(theta),'component':'connected component containing the origin; other outside-ball components are phase b','first_interface_band':'mesh facets match the static contact angle exactly; contact vertices with nonunique traces are never point observations'}
        if i==4:
            spec['initial_phase_geometry']={'kind':'liquid_bridge','axis':'y','radius_m':.12*L[0],'radial_profile':'r(y)=radius*(1+.1*sin(pi*Y)^2)','wall_contact_angle_rad':math.pi/2,'mesh_rule':'first and last interface bands normal to the horizontal walls'}
        if i==5:spec['initial_phase_geometry']={'kind':'detached_polyhedral_ellipsoid','centre_m':[.5*x for x in L],'radii_m':[.15*L[0],.1*L[1]]+([.12*L[2]] if d==3 else []),'phase_a':'inside','wall_contacts':False}
        if i==6:spec['sources']['acceleration']=field([0,'-9.81*R']+([0] if d==3 else []),'m/s2',history='linear')
        if i==7:
            spec['initial_phase_geometry']['wall']='left planar face of internal obstacle; cap axis is that face outward normal; centre is its midpoint and cap avoids all obstacle edges'
        if i==8:spec['initial_phase_geometry']['copies_centres_m']=[[.3*L[0],0]+([.5*L[2]] if d==3 else []),[.7*L[0],0]+([.5*L[2]] if d==3 else [])]
        if i==9:spec['initial_phase_geometry']['base_apothems_m']=[.15*L[0]]+([.1*L[2]] if d==3 else []);spec['initial_phase_geometry']['contact_angle_rad']=math.pi/2
        mask='mesh-conforming initial_phase_geometry; a-cell=1, b-cell=0'
    else:
        mask=masks[i];spec['sources']['acceleration']=field([0,'-.1*R']+([0] if d==3 else []),'m/s2',history='linear')
        if fam=='free_surface' and i==8:spec['initial']['velocity']=field('C with compact support strictly inside a, away from interface and walls; centre=(.15*Lx,.3*Ly[, .5*Lz]), radius=.05*min(L), max speed .01 m/s','m/s')
        if fam=='immiscible' and i==8:spec['initial']['velocity']=field('C from compact P1 potential entirely inside a; centre=(.5*Lx,.25*Ly[, .5*Lz]),radius=.05*min(L),max speed .01 m/s','m/s')
    spec['initial']['alpha']=field(mask,'1')
    spec['initial_alpha_semantics']='Pure 0/1 per supplied initial phase cell; actual interface is the union of these cell faces. An analytic mask is a geometry-construction recipe, not an extra subcell interface. Phase-cell conforming meshing must retain the listed contact/interface construction.'


def dispersed_exchange(spec,rec,i):
    fam=rec['family'];slug=rec['task'];d=spec['geometry']['dimension'];wall(spec,'all','wall',mechanical='no_slip',**({'thermal':'adiabatic'} if fam=='exchange' else {}))
    spec['sources']['acceleration']=field([0,'-.01*R',0] if i in (1,8) else [0.,0.,0.],'m/s2',history='linear' if i in (1,8) else 'constant')
    if fam=='dispersed':
        beta='.02*bump(centre=.5*L,radius=.2*L)'
        if i==2:beta='.01*bump(centre=.3*L,radius=.15*L)+.02*bump(centre=.7*L,radius=.1*L)'
        if i==6:beta='.02+.01*tanh(8*(X-.5))'
        if slug=='dense-dispersed-3d':beta=beta.replace('.02','.2').replace('.01','.1')
        spec['initial']['alpha']=field(f'1-({beta})','1')
        slip='(0,0,0)' if i in (1,2,8) else '(.001*bump(centre=.5*L,radius=.15*L),0,0)'
        if i==9:slip='(.001*(1+.5*Y)*bump(centre=.5*L,radius=.15*L),.0005*bump(centre=.5*L,radius=.1*L),0)'
        carrier='C from compact P1 potential, centre=.5*L,radius=.2*L,max speed .001 m/s' if i in (3,7) else '(0,0,0)'
        spec['initial']['flux_b']=field(f'beta*({slip})','m/s')
        spec['initial']['flux_a']=field(f'(1-beta)*({carrier})' if slug=='passive-particles-3d' else f'-beta*({slip})','m/s')
        spec['initial_volume_constraint']='For coupled/bubble/dense branches flux_a+flux_b=0 exactly per initial entity; for passive branch construct the carrier velocity by curl(P1 potential), independent of beta. No projection is allowed.'
    else:
        spec['initial'].update(alpha=field('.5+.1*X' if i==6 else .6,'1'),velocity=field([0.]*d,'m/s'),temperature_a=field(305. if i in (0,2,6) else '300+5*bump(centre=.3*L,radius=.15*L)' if i==8 else 300.,'K'),temperature_b=field(295. if i in (0,2,6) else 300.,'K'),concentration_a=field('1+bump(centre=.5*L,radius=.15*L)' if i in (4,5) else 2. if i in (1,2) else 1.,'kg/m3'),concentration_b=field('1+bump(centre=.7*L,radius=.15*L)' if i==8 else 0. if i in (1,2,4,5) else 1.,'kg/m3'))
        if i==5:spec['initial']['velocity']=field('C, centre=.5*L,radius=.2*L,max speed .01 m/s','m/s')
        if i in (3,7,9):
            spec['boundaries']=[];wall(spec,'complement','wall',mechanical='no_slip',thermal='adiabatic')
            wall(spec,'inner obstacle faces' if i==7 else 'x=0','wall',mechanical='no_slip',temperature=field('300+5*P' if i==9 else '300+5*R','K',history='linear'))


def phase_change(spec,rec,i):
    fam=rec['family'];d=spec['geometry']['dimension'];zero=[0.]*d
    spec['sources']['acceleration']=field([0,'-.01*R']+([0] if d==3 else []),'m/s2',history='linear') if i in (3,7,8) else field(zero,'m/s2')
    spec['initial']['velocity']=field(zero,'m/s')
    if fam=='melting':
        T0=302. if i==1 else 300. if i in (6,8) else 298.
        spec['initial']['temperature']=field(T0,'K')
        wall(spec,'complement','wall',mechanical='no_slip',thermal='adiabatic')
        selection='x=0 or x=Lx' if i==2 else 'y=0, .3<X<.7' if i==4 else 'all inner obstacle surfaces' if i==5 else 'x=0 or y=0' if i==9 else 'y=0' if i==3 else 'x=0'
        wall(spec,selection,'wall',mechanical='no_slip',temperature=field(f'{T0}+({297.-T0 if i==1 else 303.-T0})*'+('P' if i==7 else 'R'),'K',history='linear'))
        if i==3:spec['sources']['acceleration']=field('(0.1*R*sin(2*pi*Y),0)','m/s2',history='linear')
        if i==8:spec['initial']['velocity']=field('C, centre=.5*L,radius=.2*L,max speed .001 m/s','m/s')
        spec['phase_rate_rule']='No independent alpha initial state. Derive alpha=f(T); output m=-rho*D_t alpha, only at positive requested times with a finite unique cell-average derivative.'
        return
    sharp=fam=='evaporation';cav=fam=='cavitation'
    alpha=('X<.5' if i not in (3,4,5,6,9) else ['','','','sum(((x-.5*L)/(.2*L))^2)<1','sum(((x-.35*L)/(.15*L))^2)<1','not(sum(((x-.5*L)/(.15*L))^2)<1)','.3<X<.7','','','X<.4'][i]) if sharp else '.8'
    if cav and i in (4,5,7):alpha='1-(.001+.05*bump(centre=.5*L,radius=.2*L))'
    spec['initial']['alpha']=field(alpha,'1')
    T0=300.
    if fam=='boiling' and i in (0,1):
        T0=301. if i==0 else 299.;alpha='1' if i==0 else '.8';spec['initial']['alpha']=field(alpha,'1')
    if not cav:spec['initial']['temperature']=field(T0,'K')
    all_open=(fam=='boiling' or cav) and i in (0,1)
    if all_open:
        if cav:
            alpha0=.8;spec['initial']['alpha']=field(alpha0,'1');m=.001*(alpha0*100. if i==0 else -(.2-.001)*100.)
        else:m=.1*1000./300. if i==0 else -1.*10.*.2/300.
        div=m*(1/10.-1/1000.)
        spec['initial']['velocity']=field(f'{div/3:.17g}*(x-.5*L)','m/s')
        spec['initial_divergence_s_inverse']=div
        wall(spec,'all','pressure_reservoir',alpha=float(alpha),**({} if cav else {'temperature_K':T0}))
    else:
        wall(spec,'complement','wall',mechanical='no_slip',**({} if cav else {'thermal':'adiabatic'}))
        wall(spec,'x=Lx','pressure_reservoir',alpha=0. if sharp else field('.8-.2*R' if i==9 else .8,'1',history='linear' if i==9 else 'constant'),**({} if cav else {'temperature_K':300.}))
        if not cav:wall(spec,'inner obstacle surfaces' if i==9 else 'y=0' if i in (2,3) else 'x=0','wall',mechanical='no_slip',temperature=field('300-2*R' if i in (1,5) else '300+2*P' if i==8 else '300+2*R','K',history='linear'))
    if sharp:spec['sharp_phase_initialization']='alpha=0 or 1 on conforming phase cells; initial T=Tsat, u=0, so initial j=0 and there is no missing initial expansion. Reservoir inflow alpha is pure phase, constant in time.'


def films(spec,rec,i):
    fam=rec['family'];h0=1e-5 if fam=='gas_film' else 5e-5
    gaps=[f'{h0}*(2-X)',f'{h0}*(1+X)',f'{h0}*(1.5+.5*abs(2*X-1))',f'{h0}*(2-X)',f'{h0}*(2-.5*X-.5*Y)',f'{h0}*(2-X)',f'{h0}*(1+.3*bump(centre=.5*L,radius=.2*L))',f'{h0}',f'{h0}*(2-X)',f'{h0}']
    gap=gaps[i]
    if fam=='gas_film':gap=[str(h0),str(h0),f'{h0}*(2-X)',str(h0),f'{h0}*(2-.5*X-.5*Y)',f'{h0}*(1+.3*bump(centre=.5*L,radius=.2*L))',f'{h0}*(2-.5*X-.5*Y)',str(h0),f'{h0}*(2-X)',str(h0)][i]
    if fam=='nonnewtonian_film' and i==4:gap=f'{h0}*(1+X)'
    if fam=='nonnewtonian_film' and i==6:gap=f'{h0}*(2-.5*X-.5*Y)'
    if fam=='nonnewtonian_film' and i==7:gap=f'{h0}*(1+.3*bump(centre=.5*L,radius=.2*L))'
    if fam=='thermal_film' and i==7:gap=f'{h0}*(2-.5*X-.5*Y)'
    if (fam=='nonnewtonian_film' and i in (0,1,2)) or (fam=='thermal_film' and i in (1,2)):gap=str(h0)
    if fam=='gas_film':gap=f'{h0}*(1+{.1 if i==1 else -.1}*R)' if i in (0,1) else f'({gap})*(1-.05*P)' if i==9 else f'({gap})*(1-.05*R)' if i==4 else gap
    if fam=='thermal_film' and i==3:gap=f'{h0}*(1-.05*R)'
    U0=[0.,0.];U1=[.1,0.]
    if fam=='nonnewtonian_film':U1=[.0001 if i==0 else .01,0.]
    if i in (1,2) and fam in ('thermal_film','nonnewtonian_film'):U0=[-.1,0.] if i==1 and fam=='thermal_film' else [0.,0.];U1=[.1,0.] if i==1 and fam=='thermal_film' else [0.,0.] if i==1 else [.01,0.]
    if fam=='thermal_film' and i==2:U1=[0.,0.]
    if i in (4,6):U1=[.05,.05]
    if i in (5,8):U0=[-.05,0.]
    spec['domain_conditions']={'gap':field(gap,'m','piecewise_linear','linear' if 'R' in gap or 'P' in gap else 'constant'),'lower_velocity':field(U0,'m/s','piecewise_linear'),'upper_velocity':field([str(v)+'*R' for v in U1] if fam=='gas_film' and i in (2,7) else U1,'m/s','piecewise_linear','linear' if fam=='gas_film' and i in (2,7) else 'constant')}
    if fam=='gas_film' and i==7:spec['domain_conditions']['lower_velocity']=field(['.05*P',0.],'m/s','piecewise_linear','linear')
    p='100000'
    if fam=='nonnewtonian_film' and i in (1,2):p='100000+20000*(1-X)' if i==1 else '100000+500*(1-X)'
    if i==7 and fam!='gas_film':p='100000+5000*(1-X)'
    if fam=='thermal_film' and i==2:p='100000+20000*(1-X)'
    if fam=='gas_film' and i==3:p='100000+1000*P*(1-X)'
    args={'value':field(p,'Pa','piecewise_constant','linear' if 'P' in p else 'constant')}
    if fam=='liquid_film':args['inlet_fraction']=field(.4 if i==8 else 1.,'1')
    if fam=='thermal_film':args['temperature']=field(300.,'K')
    wall(spec,'all side boundaries except inner supply','film_pressure',**args)
    if spec['geometry']['holes']:
        args=deepcopy(args);args['value']=field('100000+5000*R','Pa',history='linear') if fam=='gas_film' else field(105000.,'Pa');wall(spec,'all inner hole sides','film_pressure',**args)
    if fam=='gas_film':spec['initial']['pressure']=field(100000.,'Pa','piecewise_linear')
    if fam=='thermal_film':
        spec['initial']['temperature']=field(300.,'K','piecewise_linear')
        spec['domain_conditions']['wall_temperature']=field('300+10*'+('P' if i==8 else 'R')+('*bump(centre=.5*L,radius=.25*L)' if i==4 else ''),'K','piecewise_linear','linear')
        if i in (1,2):spec['domain_conditions']['wall_temperature']=field(300.,'K','piecewise_linear')
    spec['observations']['extra']=['interior-node pressure/film flux and fraction or temperature when permitted','load=sum((p-reference_pressure)*actual horizontal area), N']


def shallow(spec,rec,i):
    fam=rec['family'];two=fam=='two_layer';steady=rec['analysis_kind']=='steady'
    bed='0'
    if i in (1,4,9):bed='.2*bump(centre=.5*L,radius=.2*L)'
    if i==9:bed='.05*X+.1*bump(centre=.5*L,radius=.2*L)'
    if i==2:bed='-.2*bump(centre=.5*L,radius=.2*L)'
    if i==3:bed='.05*Y'
    if i==7 and steady:bed='-.01*X'
    if fam=='wetdry' and i in (2,3,7,9):bed='.5*X' if i==2 else '.3*bump(centre=.5*L,radius=.2*L)'
    spec['domain_conditions']={'bed':field(bed,'m','piecewise_linear')}
    wall(spec,'complement_of_explicit_partitions','layer_wall' if two else 'water_wall',mode='impermeable')
    if steady:
        for face,u in [('x=0',6. if i==5 else .5),('x=Lx',6. if i==5 else .5)]:wall(spec,face,'water_reservoir',depth_m=1.,velocity=field([u,0.],'m/s'))
    elif two:
        spec['initial'].update(lower_depth=field('1+.01*cos(pi*X)' if i in (1,5,9) else '1','m','piecewise_linear'),upper_depth=field('.5-.01*cos(pi*X)' if i==1 else '.5+.01*cos(pi*X)' if i in (0,9) else '.5','m','piecewise_linear'),lower_velocity=field([('.05*sin(pi*X)*sin(pi*Y)^2' if i in (2,3,6,7) else '0'),0],'m/s','piecewise_linear'),upper_velocity=field([('-.05*sin(pi*X)*sin(pi*Y)^2' if i==2 else '.025*sin(pi*X)*sin(pi*Y)^2' if i in (3,6,7) else '0'),0],'m/s','piecewise_linear'))
        if i==9:
            spec['initial']['lower_velocity']=field([6.,0.],'m/s','piecewise_linear');spec['initial']['upper_velocity']=field([6.,0.],'m/s','piecewise_linear')
            wall(spec,'x=0','layer_inlet',lower_depth_m=1.01,upper_depth_m=.51,lower_velocity=field([6.,0.],'m/s'),upper_velocity=field([6.,0.],'m/s'))
            wall(spec,'x=Lx','layer_outflow',mode='supercritical_outflow')
            # use a boundary-compatible travelling perturbation rather than cos(pi X) at the inflow
            spec['initial']['lower_depth']=field('1+.01*exp(-100*(X-.5)^2)','m','piecewise_linear');spec['initial']['upper_depth']=field('.5+.01*exp(-100*(X-.5)^2)','m','piecewise_linear')
            spec['boundaries'][-2]['data']['lower_depth_m']=1.+.01*math.exp(-25);spec['boundaries'][-2]['data']['upper_depth_m']=.5+.01*math.exp(-25)
    else:
        h='1+.05*bump(centre=.5*L,radius=.2*L)'
        if fam=='wetdry':h='max(1-5*X,0)' if i not in (1,5,7) else 'max(1-5*sqrt((X-.5)^2+(Y-.5)^2),0)' if i==1 else 'max(1-5*X,0)+max(1-5*(1-X),0)' if i==5 else 'max(1-('+bed+'),0)'
        elif i==1:h='.5+max(0,min(1,25*(.52-X)))'
        elif i==3:h='1+.05*(X-.5)'
        elif i==6:h='1+.025*cos(pi*X)+.025*cos(pi*Y)'
        spec['initial'].update(depth=field(h,'m','piecewise_linear'),velocity=field(['.1*sin(pi*X)*sin(pi*Y)^2' if i==7 and fam!='wetdry' else '0',0],'m/s','piecewise_linear'))
        if i in (6,8) and fam!='two_layer':
            depth='1+.05*P' if fam!='wetdry' else '.1+.4*R'
            wall(spec,'x=0','water_reservoir',depth=field(depth,'m',history='linear'),velocity=field([0.,0.],'m/s'))
    spec['observations']['extra']=['depth and velocity at interior real nodes; lower/upper fields separately in two-layer model','water_volume=sum of exact P1 layer-depth integral over horizontal cells)']


def rarefied(spec,rec,i):
    kinetic=rec['family']=='kinetic_gas';thermal=rec['task']=='thermal-slip';d=spec['geometry']['dimension']
    spec['initial']={};spec['sources']={}
    wall(spec,'complement_of_all_explicit_partitions','gas_wall' if kinetic else 'slip_wall',velocity=field([0.]*d,'m/s'),temperature_K=300.,**({'accommodation':1.} if kinetic else {}))
    if kinetic:
        rho=1.3e-5 if rec['task']=='free-molecular' else .0013
        for port,r,T in [('inlet',1.1*rho,310. if i==1 else 300.),('outlet',.9*rho,290. if i==1 else 300.)]:wall(spec,port,'gas_reservoir',density_kg_m3=r,temperature_K=T,velocity=field([0.]*3,'m/s'))
        if i==1:
            for b in spec['boundaries'][1:]:b['data']['density_kg_m3']=rho*300/b['data']['temperature_K']
        if i==3:spec['boundaries'][0]['data']['accommodation']=.3
        if i in (2,9):wall(spec,'y=Ly','gas_wall',velocity=field([5.,0.,0.],'m/s'),temperature_K=300.,accommodation=0. if i==9 else 1.)
        if i==9:wall(spec,'y=0','gas_wall',velocity=field([0.,0.,0.],'m/s'),temperature_K=300.,accommodation=1.)
        if i==7:
            wall(spec,'y=Ly','gas_wall',velocity=field([0.,0.,0.],'m/s'),temperature_K=310.,accommodation=1.)
            wall(spec,'y=0','gas_wall',velocity=field([0.,0.,0.],'m/s'),temperature_K=290.,accommodation=1.)
        if i==4:
            L=spec['geometry']['bounding_lengths'];spec['geometry']['holes']=[{'operation':'box','xy_corners':[[.45*L[0],a*L[1]],[.55*L[0],b*L[1]]],'span_z':[0,L[2]]} for a,b in [(0,.4),(.6,1)]]
        if i==8:
            wall(spec,'bottom port','gas_reservoir',density_kg_m3=rho,temperature_K=305.,velocity=field([0.,0.,0.],'m/s'))
            wall(spec,'top port','gas_reservoir',density_kg_m3=.95*rho,temperature_K=295.,velocity=field([0.,0.,0.],'m/s'))
        spec['producer_internal_plan']={'burn_in_crossing_times':20,'sampling_crossing_times':200,'particles_per_cell':100,'collision_model':'off' if rec['task']=='free-molecular' else 'hard sphere total cross-section pi*d^2, isotropic scattering','random_seed':20261020+i,'status':'private numerical controls; not physical problem input; no precision certification'}
    else:
        inlet=[5. if i in (2,3) else 1.,0.]
        wall(spec,'inlet','slip_inlet',velocity=field(inlet,'m/s'),**({'temperature_K':300.} if thermal else {}))
        wall(spec,'outlet','slip_outlet',pressure_Pa=99900.)
        if i in (1,2,3,8):wall(spec,'y=Ly','slip_wall',velocity=field([5. if i!=3 else -5.,0.],'m/s'),**({'temperature_K':310. if i==8 else 300.} if thermal else {}))
        if i==8:wall(spec,'y=0','slip_wall',velocity=field([-2.5,0.],'m/s'),**({'temperature_K':295.} if thermal else {}))
        if thermal and i==7:spec['boundaries'][0]['data']['temperature_K']=310.
        if not thermal:
            for p in spec['boundaries']:p['data'].pop('temperature_K',None)


def make_detailed(rec,entry,i,data):
    spec=base_spec(rec,entry,i,data);f=rec['family']
    if f in ('closed_flow','generalized_flow','isothermal_compressible'):cfd_flow(spec,rec,i)
    elif f in ('lowmach_energy','compressible_energy','euler_equilibrium','euler_transient','turbulent_flow'):energy(spec,rec,i)
    elif f in ('viscoelastic','thixotropic','thermal_generalized'):memory(spec,rec,i)
    elif f in ('free_surface','immiscible','capillary'):interfaces(spec,rec,i)
    elif f in ('dispersed','exchange'):dispersed_exchange(spec,rec,i)
    elif f in ('evaporation','boiling','cavitation','melting'):phase_change(spec,rec,i)
    elif f in ('liquid_film','gas_film','thermal_film','nonnewtonian_film'):films(spec,rec,i)
    elif f in ('shallow_steady','shallow_transient','wetdry','two_layer'):shallow(spec,rec,i)
    elif f in ('slip_gas','kinetic_gas'):rarefied(spec,rec,i)
    else:raise ValueError(f)
    # A flow-rate inlet must be strictly positive even at t=0. Starting Q=0
    # would violate DATA. Use an exactly compatible plug-through initial state;
    # introduce nonuniform shape only after the initial instant.
    flow_case=(f=='closed_flow' and i==7) or (f=='generalized_flow' and i==2) or (f=='isothermal_compressible' and i==4)
    transient=rec['analysis_kind']!='steady'
    if flow_case and transient:
        L=spec['geometry']['bounding_lengths'];d=entry['spatial_dimension'];area=L[1]*(L[2] if d==3 else 1.)
        spec['geometry'].update(operation='box',holes=[])
        for k in ('xy_vertices','xy_rectangles'):spec['geometry'].pop(k,None)
        spec['boundaries']=[];wall(spec,'complement','slip')
        inlet={'rate':field(.1*area,'m2/s' if d==2 else 'm3/s',history={'mode':'linear','samples':[[0,1],[.1*spec['time_interval_s'][1],1.5],[spec['time_interval_s'][1],1.5]]}),'shape':field('1+.5*R*Y','1','piecewise_constant','linear')}
        if f=='isothermal_compressible':inlet['density']=field(1.,'kg/m3')
        wall(spec,'x=0','flow_rate',**inlet)
        wall(spec,'x=Lx','pressure_outlet',pressure_Pa=86100. if f=='isothermal_compressible' else 0.,backflow='forbid',meaning='full Cauchy traction')
        spec['initial']['velocity']=field([.1,0.]+([0.] if d==3 else []),'m/s')
        if f=='isothermal_compressible':spec['initial']['density']=field(1.,'kg/m3')
        spec['positive_rate_initialization']='Q(0)=.1*port area >0, shape(0)=1; initial velocity uniform .1 e_x; slip side walls, zero initial shear, outlet traction matches initial pressure. Later nonuniform positive shape is normalized over actual inlet entities.'
    if f=='closed_flow' and i==1:
        L=spec['geometry']['bounding_lengths'];spec['geometry']['holes']=[{'operation':'box','xy_corners':[[.4*L[0],.3*L[1]],[.6*L[0],.5*L[1]]],'span_z':[0,L[2]] if entry['spatial_dimension']==3 else None}]
    if f=='generalized_flow' and i==3:
        L=spec['geometry']['bounding_lengths'];spec['geometry']['holes']=[{'operation':'box','xy_corners':[[.4*L[0],.3*L[1]],[.6*L[0],.5*L[1]]],'span_z':[0,L[2]] if entry['spatial_dimension']==3 else None}]
    if f=='dispersed':
        spec['initial']['flux_b']['expression']='('+spec['initial']['flux_b']['expression']+') * boundary_band_mask'
        if rec['task']!='passive-particles-3d':spec['initial']['flux_a']['expression']='-flux_b'
        if rec['task']!='passive-particles-3d' and i in (3,7):
            spec['definitions']['carrier_C']='curl of continuous nodal P1 potential psi=bump(centre=.5*L,radius=.2*L), vector potential (0,0,psi); zero every potential node belonging to a boundary-adjacent simplex before taking the curl, then scale max cell speed to .001 m/s'
            spec['initial']['flux_b']['expression']='beta*carrier_C + '+spec['initial']['flux_b']['expression']
            spec['initial']['flux_a']['expression']='carrier_C-flux_b'
            spec['initial_volume_constraint']='flux_a+flux_b=carrier_C exactly; carrier_C has continuous normal traces and zero distributional divergence. Both phase fluxes vanish on external/obstacle walls.'
        spec['definitions']['boundary_band_mask']='0 on every cell touching any external or obstacle boundary, 1 elsewhere; a supplied entity field, not a hidden force. This ensures zero initial phase flux at all solid walls.'
    if f=='evaporation' and i==5:
        for b in spec['boundaries']:
            if b['operator']=='pressure_reservoir':b['data']['alpha']=1.
    if 'prescription' in entry:
        spec['native_closed_cavity_prescription']=deepcopy(entry['prescription'])
        spec['precedence']='The complete native closed-cavity prescription fixes geometry/material/time/history/output support for this entry; the generic extra-observation coverage targets remain unimplemented and must not be claimed as present.'
        spec['geometry']['bounding_lengths']=entry['prescription']['length_m'][:entry['spatial_dimension']]
        spec['time_interval_s']=entry['prescription']['time_interval_s'];spec['output_times_s']=entry['prescription']['output_times_s']
        for name in ('R','P','V'):spec['definitions'][name]=entry['prescription']['wall_speed_multiplier_linear_table']
    if rec['family']=='thixotropic':
        for b in spec['boundaries']:
            if b['operator']=='velocity_inlet':b['data']['structure']=field('1+R*(-.8+.6*Y)' if i==9 else '1-.2*R','1','piecewise_constant','linear')
    if any(isinstance(v,dict) and isinstance(v.get('expression'),str) and re.search(r'\bC\b',v['expression']) for v in spec['initial'].values()):
        spec['definitions']['C_seed']='Unless the field expression explicitly supplies a sine/cosine psi, evaluate the defined bump at nodes with the centre/radius stated in that expression. Zero all potential nodes on boundary-adjacent simplices, take the defined cell curl, and normalize by its largest cell Euclidean speed. Use actual simplicial cells so the curl has matching normal traces; do not average it onto a different cell partition.'
        spec['mesh_recipe']['top_dimensional_elements']='simplices'
    spec['producer_status']='matching_required_before_execution'
    spec['physical_scope_status']='specified; not numerically checked; no claim of solved-state admissibility'
    return spec


def observation_requests(rec,entry,grading):
    """Exact requested quantities/supports; no unprovided answer arrays."""
    d=entry['spatial_dimension'];f=rec['family'];i=int(entry['design_id'].split('-')[-2])-1
    allq=grading['quantities'];keys=list(allq)
    if f in ('closed_flow','generalized_flow','isothermal_compressible'):
        keys=['velocity','pressure']
        if i in (1,5,6):keys += [q for q in ('density','dynamic_viscosity','shear_rate') if q in allq]
        if i in (1,2,7):keys += [q for q in ('traction','force','volume_flow','mass_flow') if q in allq]
    requests=[]
    for q in keys:
        aggregate=q in ('force','volume_flow','mass_flow','water_volume','load','heat_flow')
        boundary=q in ('traction','force','volume_flow','mass_flow','heat_flow') or (f=='kinetic_gas' and q=='heat_flux')
        support=('sum over actual outlet port, or a central wall subset excluding both corner quarters' if boundary else 'sum over all top-dimensional domain cells') if aggregate else 'real external boundary entities excluding corner-adjacent faces' if boundary else 'all fluid cells' if rec['question_path'].split('/')[2].startswith(('2.1-','2.2-','2.3-','2.4-','2.5-','2.6-','2.7-')) else 'real interior node subset selected by the stated rule'
        if f=='kinetic_gas' and q in ('traction','heat_flux'):support='real gas_wall boundary entities excluding corner-adjacent faces; wall-frame exchange as defined by DATA'
        requests.append({'quantity':q,'unit':allq[q]['unit'],'support':support,'value_kind':'integral' if aggregate else 'average' if boundary or support=='all fluid cells' else 'point','time_axis':'output_times_s','grading_rule':deepcopy(allq[q]['rule'])})
    if 'prescription' in entry:requests=[r for r in requests if r['quantity'] in ('velocity','pressure')]
    return requests
