"""Exercise actual SDK dependencies and native material/assembly at a clamp control."""
import csv
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

import gmsh
import h5py
import jsonschema
import numpy
from caeoj.sdk import load_problem
from run_case import MOOSE, PETSC_OPTIONS

with tempfile.TemporaryDirectory(prefix='moose-health-') as temporary:
    directory=Path(temporary)
    shutil.copyfile(Path(__file__).with_name('health.i'),directory/'case.i')
    result=subprocess.run(['/bin/bash','-lc','source /environment && exec '+MOOSE+' -i case.i '+' '.join(PETSC_OPTIONS)],cwd=directory,capture_output=True,text=True,timeout=25)
    if result.returncode:
        print(result.stdout);print(result.stderr)
        raise SystemExit(result.returncode)
    with (directory/'result.csv').open() as stream:
        rows=list(csv.DictReader(stream))
    if not rows or not all(math.isfinite(float(v)) for v in rows[0].values()):
        raise RuntimeError('Native material observation is missing or nonfinite')
    print(json.dumps({'sdk_dependencies':'imported','native_application':MOOSE,'native_columns':len(rows[0]),'native_returncode':result.returncode}))
