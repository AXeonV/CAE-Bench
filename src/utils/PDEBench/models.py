"""Task contracts and frozen source-family routing (not solver algorithms)."""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Model:
    task: str
    model: str
    dimension: int
    bounds: tuple
    fields: tuple  # output name, initial name, unit, components
    prefix: str
    grouped: bool = False
    points: bool = False


MODELS = [
    Model("advection-1d", "advection_1d", 1, ((0, 1),),
          (("state", "initial_state", "1", 1),), "1D/Advection/"),
    Model("burgers-1d", "burgers_1d", 1, ((0, 1),),
          (("state", "initial_state", "m/s", 1),), "1D/Burgers/"),
    Model("reaction-diffusion-1d", "reaction_diffusion_1d", 1, ((0, 1),),
          (("state", "initial_state", "1", 1),), "1D/ReactionDiffusion/"),
    Model("diffusion-sorption-1d", "diffusion_sorption_1d", 1, ((0, 1),),
          (("concentration", "initial_concentration", "1", 1),),
          "1D/diffusion-sorption/", grouped=True),
    Model("reaction-diffusion-2d", "reaction_diffusion_2d", 2, ((-1, 1),)*2,
          (("activator", "initial_activator", "1", 1),
           ("inhibitor", "initial_inhibitor", "1", 1)),
          "2D/diffusion-reaction/", grouped=True),
    Model("darcy-flow-2d", "darcy_flow_2d", 2, ((0, 1),)*2,
          (("state", None, "1", 1),), "2D/DarcyFlow/"),
    Model("shallow-water-2d", "shallow_water_2d", 2, ((-2.5, 2.5),)*2,
          (("depth", "initial_depth", "m", 1),), "2D/shallow-water/", grouped=True),
    *[Model(f"compressible-navier-stokes-{d}d", f"compressible_navier_stokes_{d}d", d,
            ((-1, 1),) if d == 1 else ((0, 1),)*d,
            (("density", "initial_density", "kg/m3", 1),
             ("velocity", "initial_velocity", "m/s", d),
             ("pressure", "initial_pressure", "Pa", 1)),
            f"{d}D/CFD/" if d != 3 else "3D/Train/")
      for d in (1, 2, 3)],
    Model("incompressible-navier-stokes-2d",
          "inhomogeneous_incompressible_navier_stokes_2d", 2, ((0, 1),)*2,
          (("velocity", "initial_velocity", "m/s", 2),), "2D/NS_incom/", points=True),
]
BY_TASK = {m.task: m for m in MODELS}


def constant(value, unit):
    return {"value": value, "unit": unit}


def parameters(model, source):
    name = source["filename"]
    number = r"([-+0-9.eE]+)"
    def label(key):
        match = re.search(key + number, name)
        if not match: raise ValueError(f"Missing source parameter {key}: {name}")
        return float(match[1].rstrip('.'))
    if model.model == "advection_1d": return {"velocity": constant(label("beta"), "m/s")}
    if model.model == "burgers_1d":
        import math
        return {"diffusion_coefficient": constant(label("Nu") / math.pi, "m2/s")}
    if model.model == "reaction_diffusion_1d":
        return {"diffusivity": constant(label("Nu"), "m2/s"),
                "reaction_rate": constant(label("Rho"), "1/s")}
    if model.model == "darcy_flow_2d": return {"source_strength": constant(label("beta"), "1/s")}
    if model.model == "diffusion_sorption_1d":
        return {k: constant(v, u) for k, v, u in (
            ("diffusivity", .0005, "m2/s"), ("porosity", .29, "1"),
            ("solid_density", 2880, "kg/m3"), ("freundlich_coefficient", .00035, "m3/kg"),
            ("freundlich_exponent", .874, "1"), ("concentration_shift", 1e-6, "1"),
            ("inlet_concentration", 1, "1"), ("outlet_length", .0005, "m"))}
    if model.model == "reaction_diffusion_2d":
        return {k: constant(v, u) for k, v, u in (
            ("activator_diffusivity", .001, "m2/s"), ("inhibitor_diffusivity", .005, "m2/s"),
            ("reaction_offset", .005, "1"), ("activator_rate", 1, "1/s"),
            ("inhibitor_rate", 1, "1/s"))}
    if model.model == "shallow_water_2d": return {"gravity": constant(1, "m/s2")}
    if model.points: return {"kinematic_viscosity": constant(.01, "m2/s")}
    return {"gamma": constant(5/3, "1"),
            "shear_viscosity": constant(1e-8 if name.startswith("Sod") else label("Eta"), "m2/s"),
            "bulk_viscosity": constant(1e-8 if name.startswith("Sod") else label("Zeta"), "m2/s")}


def source_files(model, catalog):
    sources = [s for s in catalog["files"] if (s["directory"] + '/').startswith(model.prefix)]
    if model.points:
        # Eight four-trajectory shards form a bounded 32-candidate input pool.
        sources.sort(key=lambda s: int(s["filename"].rsplit('-', 1)[1].split('.')[0]))
        return sources
    def order(source):
        p = parameters(model, source)
        if model.model == 'advection_1d': return (p['velocity']['value'],)
        if model.model == 'burgers_1d': return (p['diffusion_coefficient']['value'],)
        if model.model == 'reaction_diffusion_1d': return (p['diffusivity']['value'],p['reaction_rate']['value'])
        if model.model == 'darcy_flow_2d': return (p['source_strength']['value'],)
        if model.model.startswith('compressible_'):
            name=source['filename']
            m=re.search(r'_M([-+0-9.eE]+)_',name)
            if model.dimension==1:
                kind=3 if name.startswith('Sod') else 2 if 'Shock' in name else 1 if 'trans' in name else 0
                return (kind,p['shear_viscosity']['value'])
            return (int('Turb' in name),float(m[1]) if m else 0,p['shear_viscosity']['value'])
        return (source['filename'],)
    return sorted(sources, key=order)
