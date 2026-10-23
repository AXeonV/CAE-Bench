"""Build private probes against the exact final prepared verifier/exam bundle."""
import argparse,shutil,subprocess
from pathlib import Path
TASK=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--tests',required=True,type=Path);p.add_argument('--context',required=True,type=Path);p.add_argument('--docker',default='docker');a=p.parse_args();a.context.mkdir(parents=True,exist_ok=True);shutil.copytree(a.tests,a.context/'tests',dirs_exist_ok=True);shutil.copyfile(TASK/'author/generated/step_db.cpp',a.context/'step_db.cpp');shutil.copyfile(TASK/'author/backend_probe.py',a.context/'backend_probe.py');a.context.joinpath('Dockerfile').write_text('FROM caeoj-meep2338-runtime:base\nCOPY tests/agent.zip /tmp/agent.zip\nRUN python -m zipfile -e /tmp/agent.zip /app && python -m pip install --no-cache-dir /app && mkdir -p /app/submission\nCOPY tests /tests\nCOPY step_db.cpp /probe/step_db.cpp\nCOPY backend_probe.py /opt/backend_probe.py\n');subprocess.run([a.docker,'build','-t','caeoj-meep2338-probes:preflight',str(a.context)],check=True)
