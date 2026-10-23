"""Actual nontriggering native health run, separate from scored trajectories."""
import importlib.util,re,subprocess,tempfile
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem
TASK=Path('/app/qbank/19-solver-repair/19.6-waves/parallel-pml-reduction-repair')
spec=importlib.util.spec_from_file_location('wave_adapter',TASK/'public/run_case.py');adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
problem=load_problem(TASK/'samples/01/input/problem.json')
with tempfile.TemporaryDirectory(prefix='specfem-health-') as tmp:
    adapter.prepare(problem,tmp);par=Path(tmp)/'DATA/Par_file';text=par.read_text()
    text=re.sub(r'^NPROC\s*=.*$','NPROC = 1',text,flags=re.M);text=re.sub(r'^NSTEP\s*=.*$','NSTEP = 400',text,flags=re.M);par.write_text(text)
    for exe in ['xmeshfem2D','xspecfem2D']:
        r=subprocess.run([str(adapter.BUILD/'bin'/exe)],cwd=tmp,text=True,capture_output=True)
        if r.returncode:raise RuntimeError(exe+': '+r.stdout+'\n'+r.stderr)
    trace=np.loadtxt(Path(tmp)/'OUTPUT_FILES/AA.R0000.BXY.semd')
    assert trace.shape==(400,2) and np.all(np.isfinite(trace)) and np.any(trace[:,1]!=0)
    print('Genuine original SPECFEM SH health: serial 400-step nonzero propagation passed')
