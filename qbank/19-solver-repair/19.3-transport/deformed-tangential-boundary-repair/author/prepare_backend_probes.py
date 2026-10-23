"""Package probes with the exact prepared shared verifier and public archive."""
import argparse,shutil,subprocess
from pathlib import Path
Q=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--tests',type=Path,required=True);p.add_argument('--context',type=Path,required=True);a=p.parse_args();a.context.mkdir(parents=True,exist_ok=True)
 shutil.copytree(a.tests,a.context/'tests',dirs_exist_ok=True)
 shutil.copyfile(Q/'author/generated/core.cc',a.context/'core.cc');shutil.copyfile(Q/'author/backend_probe.py',a.context/'backend_probe.py')
 (a.context/'Dockerfile').write_text('FROM caeoj-aspect6818-runtime:offline-v4\nCOPY tests/agent.zip /tmp/agent.zip\nRUN python -m zipfile -e /tmp/agent.zip /app && python -m pip install --no-cache-dir /app && mkdir -p /app/submission\nCOPY tests /tests\nCOPY core.cc /probe/core.cc\nCOPY backend_probe.py /opt/backend_probe.py\n')
 subprocess.run(['docker','build','--network','none','-t','caeoj-aspect6818-probes:final',str(a.context)],check=True)
