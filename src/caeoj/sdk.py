"""Optional helpers; array values, shapes and numbering are never repaired."""
import numpy as np
from .storage import write_hdf5
from .validation import ContractError, check_problem, check_result, output_support, read_hdf5

def load_problem(path):
    problem, diagnostics = check_problem(path)
    if not diagnostics["valid"]:
        raise ContractError(diagnostics)
    return problem



def load_result(problem, path):
    arrays = read_hdf5(path)
    diagnostics = check_result(problem, arrays)
    if not diagnostics["valid"]:
        raise ContractError(diagnostics)
    return arrays



def read_constant(data):
    """Read a validated {value, unit} constant; never convert its unit."""
    if not isinstance(data, dict) or set(data) != {"value", "unit"}:
        raise TypeError('Expected a {"value": number, "unit": string} constant; '
                        'use read_field(problem, reference) for a field reference.')
    return data["value"]



def read_field(problem, reference):
    """Resolve {field: name} to its HDF5 array; preserve dtype, shape and order."""
    if not isinstance(reference, dict) or set(reference) != {"field"}:
        raise TypeError('Expected a {"field": name} reference; '
                        'use read_constant(data) for a constant.')
    name = reference["field"]
    if name not in problem.manifest["fields"]:
        raise KeyError(f'Unknown input field: {name!r}; use the field name, not the HDF5 key.')
    return problem.arrays[problem.manifest["fields"][name]["array"]]



def write_result(path, problem, fields):
    """fields maps required HDF5 array keys to actual ndarrays; no dtype conversion."""
    if any(not isinstance(a, np.ndarray) for a in fields.values()):
        raise TypeError("Pass ndarrays with the declared dtype and shape.")
    support = output_support(problem)
    if set(fields) & support:
        raise ValueError("Field keys cannot overwrite support arrays.")
    arrays = {key: problem.arrays[key] for key in support} | fields
    diagnostics = check_result(problem, arrays)
    if not diagnostics["valid"]:
        raise ContractError(diagnostics)
    write_hdf5(path, arrays)
    return arrays



def target_ids(problem, location):
    return problem.arrays[problem.manifest["locations"][location]["ids"]].copy()



def id_to_row(ids):
    if len(set(map(int, ids))) != len(ids):
        raise ValueError("Entity IDs must be unique.")
    return {int(tag): row for row, tag in enumerate(ids)}



def read_option(data):
    """Read a declared categorical option, without interpreting its meaning."""
    if not isinstance(data, dict) or set(data) != {'option'}:
        raise TypeError('Expected an {"option": string} value.')
    return data['option']



def sample_field(problem, name, time):
    """Sample an input field in time; returns [N,*components] without spatial remapping.

    Explicitly applies its sampling declaration. Does not infer continuity from
    output times; previous means right-continuous zero-order hold.
    """
    if not np.isfinite(time):raise ValueError('Sample time must be finite')
    spec=problem.manifest['fields'][name];sampling=spec['sampling']
    times=problem.arrays[problem.manifest['time_axes'][spec['time_axis']]]
    values=problem.arrays[spec['array']]
    if sampling['time']=='constant':return values[0].copy()
    if time<times[0] or time>times[-1]:
        if sampling['extrapolation']=='forbid':raise ValueError('Time extrapolation forbidden')
        return values[0 if time<times[0] else -1].copy()
    i=int(np.searchsorted(times,time,side='right')-1)
    if sampling['time']=='previous' or i==len(times)-1:return values[i].copy()
    w=(time-times[i])/(times[i+1]-times[i])
    return (1-w)*values[i]+w*values[i+1]



def boundary_geometry(problem, location):
    """Facet centroids, outward unit normals and measures in prescribed ID order."""
    from .mesh_geometry import boundary_geometry as geometry
    return geometry(problem,location)



def boundary_integral(problem, location, values):
    """Integrate facet-average [T,N,*components] values; output [T,1,*components]."""
    values=np.asarray(values)
    _,_,measure=boundary_geometry(problem,location)
    if values.ndim<3 or values.shape[1]!=len(measure):raise ValueError('Expected [T,N,*components] facet averages')
    return np.sum(values*measure.reshape((1,len(measure))+((1,)*(values.ndim-2))),axis=1,keepdims=True)



def __getattr__(name):
    """Resolve optional SDK compatibility names from the installed assembly."""
    if name.startswith('__'):
        raise AttributeError(name)
    from . import runtime
    return runtime.resolve_alias(name)
