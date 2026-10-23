"""Exercise locked SDK dependencies and the genuine existing coupled NS/heat formulation."""
import csv,json,math,shutil,subprocess,tempfile
from pathlib import Path
import gmsh,h5py,jsonschema,numpy
from caeoj.sdk import load_problem
from run_case import APP,ENV
with tempfile.TemporaryDirectory(prefix='moose-energy-health-') as tmp:
 d=Path(tmp);shutil.copyfile(Path(__file__).with_name('health.i'),d/'case.i')
 r=subprocess.run(['/bin/bash','-lc',ENV+'exec '+APP+' -i case.i'],cwd=d,capture_output=True,text=True,timeout=45)
 if r.returncode:print(r.stdout);print(r.stderr);raise SystemExit(r.returncode)
 csvs=list(d.glob('*.csv'));assert csvs
 with csvs[0].open() as f:rows=list(csv.DictReader(f))
 assert rows and all(math.isfinite(float(v)) for row in rows for v in row.values())
 print(json.dumps({'sdk_dependencies':'imported','native_application':APP,'native_returncode':r.returncode,'native_columns':len(rows[-1]),'source_target_required':False}))
