"""Bounded isolated staging of an existing native solver, never a PDE producer.

Thetis is not in the installed Firedrake image. Retain downloaded distributions,
hashes and import evidence without changing the shared host Python or base image.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import traceback
from native_closed_cavity import SOCKET,save,digest
from titan_resources import reservation
IMAGE='sha256:f58f5bd13e5290a1c1ddec7cfa1a04e9cad5ec27dfc0bd2f01e6febc31c35175'
COMMIT='162c605079611dfce69b4d1182181a421116b141'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int,default=1);a=ap.parse_args()
    j=a.root/'maintenance/thetis-native-stage';assert not j.exists(),'Inspect previous stage; never automatically repeat';j.mkdir();name='ch02-thetis-stage-'+str(time.time_ns())[-9:]
    source='https://github.com/thetisproject/thetis/archive/'+COMMIT+'.tar.gz'
    code='python3 -m pip download --retries 2 --timeout 30 --no-deps --dest /work/wheels '+source+' netCDF4 pyproj pytz uptide cftime certifi && python3 -m pip install --no-deps --target /work/vendor /work/wheels/* && PYTHONPATH=/work/vendor python3 -c "import thetis; import thetis.shallowwater_eq as s; import inspect; print(thetis.__file__); print(inspect.getsource(s.LinearDragTerm))"'
    cmd=['docker','--host',SOCKET,'run','--name',name,'--network','bridge','--cpus','1','--memory','2g','--user',f'{os.getuid()}:{os.getgid()}','-e','HOME=/tmp','-e','OMP_NUM_THREADS=1','-e','OPENBLAS_NUM_THREADS=1','-e','XDG_CACHE_HOME=/work/cache','-v',f'{j}:/work',IMAGE,'bash','-c',code]
    record={'scope':'Native Thetis dependency staging and import only; no PDE solve or numerical validation.','source':source,'commit':COMMIT,'image':IMAGE,'command':cmd,'script_sha256':digest(Path(__file__)),'start_unix':time.time(),'status':'queued','next_case':'ch02-2-9-2-08-friction_decay','next_adapter':'Match frozen P1 inputs, native nonlinear shallow water plus LinearDragTerm, no rotation/viscosity, closed native slip walls; then finite runtime and output assembly.'};save(j/'stage.json',record)
    try:
        with reservation(a.root,name):
            record.update(status='running',container=name);save(j/'stage.json',record)
            with (j/'stage.log').open('w') as log:
                try:cp=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
                except subprocess.TimeoutExpired:
                    # This exact container only downloads/imports dependencies;
                    # it never runs a solver or another task's work.
                    subprocess.run(['docker','--host',SOCKET,'stop','--time','10',name],stdout=log,stderr=subprocess.STDOUT,timeout=30)
                    raise
            assert cp.returncode==0,f'stage exit{cp.returncode}'
            record.update(status='native_solver_imported_pending_case_adapter',distribution_sha256={p.name:digest(p) for p in (j/'wheels').iterdir() if p.is_file()})
    except Exception as ex:record.update(status='stage_needs_attention',error=repr(ex),traceback=traceback.format_exc())
    record['ended_unix']=time.time();save(j/'stage.json',record)
if __name__=='__main__':main()
