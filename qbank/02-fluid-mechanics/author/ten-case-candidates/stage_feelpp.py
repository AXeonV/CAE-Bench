"""Bounded staging of an existing CFD toolbox, without authoring a PDE solver."""
import argparse
import json
import subprocess
import time
from pathlib import Path
from native_closed_cavity import SOCKET,save,digest

TAG='ghcr.io/feelpp/feelpp:noble-v0.111.0'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path);ap.add_argument('--workers',type=int);a=ap.parse_args()
    root=a.root/'maintenance/feelpp-native-stage';root.mkdir(exist_ok=True);status=root/'status.json';start=time.time()
    state={'stage':'pulling_official_toolbox','tag':TAG,'started_unix':start,'maximum_stage_seconds':6900,'script_sha256':digest(Path(__file__)),'solver_rerun':False,'reference_produced':False,'numerical_validation':False,'source_docs':['https://github.com/feelpp/feelpp/releases/tag/v0.111.0','https://docs.feelpp.org/toolboxes/latest/cfd/manual.html'],'scope':'Existing CFD toolbox: two-sided power-law viscosity bounds plus full stress Neumann interfaces. Matching actual version and case adapter still required.'};save(status,state)
    try:
        with (root/'pull.log').open('w') as log:subprocess.run(['docker','--host',SOCKET,'pull',TAG],stdout=log,stderr=subprocess.STDOUT,timeout=6600,check=True)
        info=json.loads(subprocess.check_output(['docker','--host',SOCKET,'image','inspect',TAG],text=True))[0]
        save(root/'image.json',{'image_id':info['Id'],'repo_digests':info.get('RepoDigests',[]),'created':info['Created'],'labels':info['Config'].get('Labels',{}),'size':info['Size']})
        command=['docker','--host',SOCKET,'run','--rm','--network','none','--cpus','1','--memory','2g','--entrypoint','/bin/bash',info['Id'],'-c','command -v mpirun; command -v feelpp_toolbox_fluid; find /usr/bin /usr/local/bin -maxdepth 1 -name "*toolbox*fluid*" 2>/dev/null; cat /etc/os-release']
        p=subprocess.run(command,capture_output=True,text=True,timeout=120,check=True);(root/'runtime-inventory.txt').write_text(p.stdout+p.stderr)
        assert 'mpirun' in p.stdout and 'fluid' in p.stdout,'Native fluid executable/MPI not found; inspect inventory'
        state.update(stage='official_toolbox_available_pending_case_adapter',image=info['Id'],repo_digests=info.get('RepoDigests',[]),ended_unix=time.time())
    except Exception as ex:state.update(stage='needs_attention',error=repr(ex),ended_unix=time.time())
    save(status,state);print(json.dumps(state))

if __name__=='__main__':main()
