"""Package private probes using the final shared Harbor test bundle."""
import argparse,shutil,subprocess
from pathlib import Path
TASK=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--tests',type=Path,required=True);p.add_argument('--context',type=Path,required=True);a=p.parse_args();a.context.mkdir(parents=True,exist_ok=True)
    shutil.copytree(a.tests,a.context/'tests',dirs_exist_ok=True);shutil.copyfile(TASK/'author/generated/get_MPI.F90',a.context/'get_MPI.F90');shutil.copyfile(TASK/'author/backend_probe.py',a.context/'backend_probe.py')
    (a.context/'Dockerfile').write_bytes(b'FROM caeoj-specfem661-runtime:base\nCOPY tests/agent.zip /tmp/agent.zip\nRUN python -m zipfile -e /tmp/agent.zip /app && python -m pip install --no-cache-dir /app && mkdir -p /app/submission\nCOPY tests /tests\nCOPY get_MPI.F90 /probe/get_MPI.F90\nCOPY backend_probe.py /opt/backend_probe.py\n')
    subprocess.run(['docker','build','-t','caeoj-specfem661-probes:preflight',str(a.context)],check=True)
