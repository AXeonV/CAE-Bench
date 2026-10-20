"""Read selected HDF5 frames without loading the source tensor in full."""
from contextlib import contextmanager
import json
from pathlib import Path

import h5py
import numpy as np
import yaml

from .storage import PreparationError, RangeReader, atomic_json, digest


@contextmanager
def open_source(source, cache, budget, local=None, timeout=45, network=None, block_size=1024*1024):
    if local is not None:
        root = Path(local)
        candidates = [root/source["filename"], root/source["directory"]/source["filename"]]
        path = next((p for p in candidates if p.is_file()), None)
        if path is None: raise PreparationError(f"Local source missing: {source['filename']}")
        stat=path.stat()
        identity={'path':str(path.resolve()),'bytes':stat.st_size,'mtime_ns':stat.st_mtime_ns,
                  'ctime_ns':stat.st_ctime_ns,'md5':source['md5']}
        ledger=Path(cache)/'full-file-checks'/f"{source['id']}.json"
        verified=False
        if ledger.exists():
            try:verified=json.loads(ledger.read_text())==identity
            except (OSError,ValueError):pass
        if stat.st_size != source["bytes"] or (not verified and digest(path, "md5") != source["md5"]):
            raise PreparationError(f"Local full-file size/MD5 mismatch: {path}")
        after=path.stat()
        if (after.st_mtime_ns,after.st_ctime_ns,after.st_size)!=(stat.st_mtime_ns,stat.st_ctime_ns,stat.st_size):
            raise PreparationError('Local source changed during checksum verification')
        if not verified:
            budget.check(4096)
            atomic_json(ledger,identity)
        with h5py.File(path, "r") as handle: yield handle
    else:
        with RangeReader(source, Path(cache)/"ranges", budget, timeout=timeout, network=network, block_size=block_size) as raw:
            with h5py.File(raw, "r") as handle: yield handle


class Reader:
    def __init__(self, handle, model):
        self.h, self.model = handle, model
        self.grouped = model.grouped
        self.scalar_cfd = False
        if self.grouped:
            # Known zero-padded group naming; do not enumerate 10,000 groups remotely.
            # Legacy HDF5 symbol tables may enumerate every remote group for
            # len(handle). Published family counts bound the candidate prefix;
            # each selected group is still checked before use.
            self.count = None  # each explicit group is validated; no invented count
        elif model.points:
            self.count = handle['velocity'].shape[0]
        elif 'tensor' in handle:
            self.count = handle['tensor'].shape[0]
        elif 'density' in handle:
            ds = handle['density']
            self.scalar_cfd = ds.ndim == model.dimension + 1
            self.count = 1 if self.scalar_cfd else ds.shape[0]
        else:
            raise PreparationError("Unsupported source HDF5 layout")

    def check_index(self, index):
        if type(index) is not int or index < 0 or (self.count is not None and index >= self.count):
            raise PreparationError("Source trajectory index outside actual layout")
        if self.grouped:
            self._group(index)

    def _group(self, index):
        key = f"{index:04d}"
        if key not in self.h: raise PreparationError(f"Missing sample group {key}")
        return self.h[key]

    def metadata(self, index=0, frames=None):
        model = self.model
        if self.grouped:
            group = self._group(index)
            coords = [np.asarray(group['grid'][axis], dtype=np.float64)
                      for axis in 'xyz'[:model.dimension]]
            times = np.asarray(group['grid/t'], dtype=np.float64)
            length = group['data'].shape[0]
            config = yaml.safe_load(group.attrs.get('config', '{}')) or {}
        elif model.points:
            config = yaml.safe_load(self.h.attrs.get('config', '{}')) or {}
            shape = self.h['velocity'].shape[2:-1]
            if len(shape) != 2: raise PreparationError("Expected centered 2D velocity field")
            declared = config.get('domain_size')
            if declared is None or list(declared) != [1, 1]:
                raise PreparationError("Cannot establish unit-square source configuration")
            if list(config.get('grid_size',[]))!=list(shape):
                raise PreparationError('Source grid_size does not match the published velocity grid')
            expected = {'NU': .01, 'velocity_extrapolation': 'ZERO',
                        'particle_extrapolation': 'BOUNDARY', 'force_extrapolation': 'ZERO'}
            if any(config.get(key) != value for key, value in expected.items()):
                raise PreparationError('Incompressible source viscosity or boundary configuration differs from task')
            if config.get('enable_gravity', False) or config.get('enable_obstacles', False):
                raise PreparationError('Incompressible gravity/obstacle configuration outside task')
            n, nt, nx, ny, components = self.h['velocity'].shape
            if components != 2 or self.h['particles'].shape != (n, nt, nx, ny, 1) or self.h['force'].shape != (n, nx, ny, 2) or self.h['t'].shape != (n, nt):
                raise PreparationError('Incompressible scalar/vector axes differ from declared source layout')
            # Released domain_size is checked independently against short-time
            # tracer transport; the current generator's grid_size Box differs.
            coords = [lo+(np.arange(n)+.5)*(hi-lo)/n
                      for n,(lo,hi) in zip(shape,model.bounds)]
            length = self.h['velocity'].shape[1]
            if frames is None:
                times = np.asarray(self.h['t'][index], dtype=np.float64)
            else:
                frames = np.asarray(frames, dtype=np.int64)
                if (frames.ndim != 1 or not len(frames) or frames[0] != 0
                    or np.any(np.diff(frames) <= 0) or frames[-1] >= length):
                    raise PreparationError('Invalid selected source time indices')
                # Each published timestamp is its own compressed HDF5 chunk.
                # Read actual requested entries, never synthesize timestamps
                # or fetch all unrelated chunks distributed across the file.
                times = np.asarray(self.h['t'][index, frames], dtype=np.float64)
                length = len(frames)
        else:
            coords = [np.asarray(self.h[axis+'-coordinate'], dtype=np.float64)
                      for axis in 'xyz'[:model.dimension]]
            config = {}
            if model.model == 'darcy_flow_2d':
                if 'beta' not in self.h.attrs:
                    raise PreparationError('Darcy source beta attribute missing')
                beta = np.asarray(self.h.attrs['beta'])
                if beta.ndim != 0 or not np.isfinite(beta) or float(beta) not in (.01,.1,1.,10.,100.):
                    raise PreparationError('Darcy source beta outside declared values')
                config = {'beta': float(beta)}
                times, length = np.array([0.]), 1
            else:
                times = np.asarray(self.h['t-coordinate'], dtype=np.float64)
                ds = self.h['tensor'] if 'tensor' in self.h else self.h['density']
                length = ds.shape[0 if self.scalar_cfd else 1]
        if len(times) != length:
            # NLE historical allocation adds one unused trailing coordinate.
            if len(times) == length+1 and (model.model in ('advection_1d','burgers_1d','reaction_diffusion_1d') or model.model.startswith('compressible_')):
                times = times[:length]
            else:
                raise PreparationError("Source time-coordinate/frame count mismatch")
        if not np.isfinite(times).all() or times[0] != 0 or np.any(np.diff(times) <= 0):
            raise PreparationError("Invalid actual source times")
        for coord, (low, high) in zip(coords, model.bounds):
            expected = low + (np.arange(len(coord))+.5)*(high-low)/len(coord)
            spacing=(high-low)/len(coord)
            # Published FHN is strided from a finer grid. The task explicitly
            # assigns these ordered values to coarse cells as initial averages.
            tolerance=.5*spacing if model.model=='reaction_diffusion_2d' else 2e-6*(high-low)
            if (len(coord)<2 or np.any(np.diff(coord)<=0) or
                not np.allclose(np.diff(coord),spacing,rtol=0,atol=2e-6*(high-low)) or
                not np.allclose(coord,expected,rtol=0,atol=tolerance)):
                raise PreparationError("Source coordinates do not match task's equidistant cell centers")
        return coords, times, config

    def values(self, index, frames):
        model = self.model
        if self.grouped:
            data = np.asarray(self._group(index)['data'][frames], dtype=np.float64)
            # FHN source explicitly stores [time,y,x,channel].
            if model.model == 'reaction_diffusion_2d': data = data.transpose(0, 2, 1, 3)
            if data.ndim != model.dimension+2:
                raise PreparationError("Grouped state shape differs from declared spatial axes")
            return {name: data[..., i:i+1] for i, (name, _, _, _) in enumerate(model.fields)}
        if model.points:
            return {'velocity': np.asarray(self.h['velocity'][index, frames], dtype=np.float64),
                    # Tracer is input only: never fetch unrequested hidden transport outputs.
                    'tracer': np.asarray(self.h['particles'][index, 0:1], dtype=np.float64),
                    'forcing': np.asarray(self.h['force'][index], dtype=np.float64)[None]}
        if model.model == 'darcy_flow_2d':
            # Published Darcy uses a separate nu coefficient and scalar tensor.
            if 'nu' not in self.h:
                raise PreparationError("Darcy coefficient dataset 'nu' missing; refusing channel guesses")
            state = np.asarray(self.h['tensor'][index], dtype=np.float64)
            coefficient = np.asarray(self.h['nu'][index], dtype=np.float64)
            shape = tuple(len(c) for c in self.metadata(index)[0])
            if state.size != np.prod(shape) or coefficient.size != np.prod(shape):
                raise PreparationError("Darcy source shape mismatch")
            if not np.all(np.isclose(coefficient,.1,rtol=0,atol=1e-7)|np.isclose(coefficient,1,rtol=0,atol=1e-7)):
                raise PreparationError("Darcy source coefficient is not a 0.1/1 field")
            coefficient=np.where(np.isclose(coefficient,.1,rtol=0,atol=1e-7),.1,1.)
            return {'state': state.reshape((1,)+shape+(1,)),
                    'diffusivity': coefficient.reshape((1,)+shape+(1,))}
        if 'tensor' in self.h:
            state = np.asarray(self.h['tensor'][index, frames], dtype=np.float64)
            if state.ndim == model.dimension+1: state = state[..., None]
            return {'state': state}
        names = {'density': 'density', 'pressure': 'pressure'}
        result = {}
        for name, key in names.items():
            dataset = self.h[key]
            value = dataset[frames] if self.scalar_cfd else dataset[index, frames]
            result[name] = np.asarray(value, dtype=np.float64)[..., None]
        velocity = []
        for axis in 'xyz'[:model.dimension]:
            dataset = self.h['V'+axis]
            value = dataset[frames] if self.scalar_cfd else dataset[index, frames]
            velocity.append(np.asarray(value, dtype=np.float64))
        result['velocity'] = np.stack(velocity, axis=-1)
        return result


def check_initial(model, values):
    if any(not np.isfinite(v).all() for v in values.values()):
        raise PreparationError("Nonfinite source fields")
    if 'density' in values and (np.min(values['density']) <= 0 or np.min(values['pressure']) <= 0):
        raise PreparationError("Nonpositive compressible state")
    if model.model == 'reaction_diffusion_1d' and (values['state'].min() < 0 or values['state'].max() > 1):
        raise PreparationError("Logistic initial state is outside [0,1]")
    if model.model == 'diffusion_sorption_1d':
        field = values['concentration']
        if field.min() < 0 or field.max() > .2 or not np.all(field == field.flat[0]):
            raise PreparationError("Sorption initial field must be a single constant in [0,0.2]")
    if model.model == 'darcy_flow_2d' and not np.isin(values['diffusivity'], [.1, 1]).all():
        # float32 0.1 needs a numeric comparison, not exact float64 identity.
        if not np.all(np.isclose(values['diffusivity'], .1) | np.isclose(values['diffusivity'], 1)):
            raise PreparationError("Darcy coefficient must be 0.1 or 1")
    if model.model == 'shallow_water_2d' and not np.isin(values['depth'], [1, 2]).all():
        raise PreparationError("Unsupported shallow-water initial heights")


def fhn_initial(coords,values,config):
    sim=config.get('sim',{})
    nx=int(sim['xdim']);ny=int(sim['ydim']);seed=int(sim['seed'])
    if nx<2 or ny<2:raise PreparationError('Invalid original FHN initial grid')
    axes=[]
    for c,n,lo,hi in zip(coords,(nx,ny),(-1.,-1.),(1.,1.)):
        index=np.rint((c-lo)*n/(hi-lo)-.5).astype(int)
        if np.any(index<0) or np.any(index>=n):raise PreparationError('FHN sample outside original grid')
        centers=lo+(index+.5)*(hi-lo)/n
        if not np.allclose(c,centers,rtol=0,atol=2e-7):raise PreparationError('FHN sample is not an original cell center')
        axes.append(index)
    # The released data uses legacy MT19937, unlike current default_rng source.
    # Never guess: all released t=0 samples must match the reconstruction.
    rng=np.random.RandomState(seed)
    fields={}
    for name in ('activator','inhibitor'):
        original=rng.standard_normal(nx*ny).reshape(ny,nx).T.astype(np.float32).astype(np.float64)
        sampled=original[np.ix_(*axes)]
        if not np.array_equal(sampled,values[name][0,...,0]):
            raise PreparationError('FHN legacy initial reconstruction does not reproduce every released t=0 value')
        fields[name]=original[None,...,None]
    return (nx,ny),axes,fields
