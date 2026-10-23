"""Trusted installation health probe using the actual native ASPECT solver."""
from pathlib import Path
import tempfile
import numpy as np
from run_case import native

p=dict(width=1.,height=1.,rate_x=0.,velocity_x=.8,
       end_time=.25,time_step=.25,temperature=300.,density=1.,viscosity=1.,refinement=1)
m={'spatial_dimension':2,'physics':{'model':'deformed-tangential-parallel-v1','parameters':{k:{'value':v} for k,v in p.items()}}}
a={'probe_coordinates':np.array([[.5,.5]]),'probe_ids':np.array([3]),'times':np.array([0.,.25])}
with tempfile.TemporaryDirectory(prefix='aspect-health-') as directory:
    out=native(m,a,'/opt/aspect-build/aspect-release',Path(directory))
    if out['velocity'].shape!=(2,1,2) or out['pressure'].shape!=(2,1,1):
        raise RuntimeError('Native health probe shape failure')
    if not all(np.isfinite(v).all() for v in out.values()):
        raise RuntimeError('Native health probe nonfinite output')
