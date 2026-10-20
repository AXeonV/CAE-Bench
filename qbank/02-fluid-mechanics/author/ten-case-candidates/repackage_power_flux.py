"""One finite conversion repair: use prescribed impermeable wall flux.

Archive previous payloads; do not rerun or interrupt any native solver.
"""
import argparse
import json
import shutil
import subprocess
import time
from pathlib import Path
import h5py
import numpy as np
from native_closed_cavity import SOCKET, digest, save
from native_power_periodic import convert
from titan_resources import reservation


def perform(args):
    records=[]
    for job in sorted((args.root/'cases').iterdir()):
        status=job/'status.json';execution=job/'execution.json'
        if not status.exists() or not execution.exists():continue
        state=json.loads(status.read_text());meta=json.loads(execution.read_text())
        if state['status']!='unvalidated_candidate' or 'stock bounded powerLaw/fvOptions' not in meta.get('producer',''):continue
        if (job/'conversion-wall-flux.json').exists():continue
        obj=json.loads(subprocess.check_output(['docker','--host',SOCKET,'inspect',state['container']]))[0];assert not obj['State']['Running'] and any(m['Source']==str(job.resolve()) for m in obj['Mounts'])
        archive=args.root/'maintenance/adapter-attempts'/(job.name+'-pre-wall-flux-conversion-'+str(time.time_ns()));archive.mkdir()
        for name in ('input','reference'):shutil.copytree(job/name,archive/name)
        shutil.copy2(status,archive/'status.json');e=json.loads((job/'design.json').read_text());m=dict(np.load(job/'adapter-data.npz'));updated=convert(job,e,m)
        with h5py.File(archive/'reference/reference.h5') as old,h5py.File(job/'reference/reference.h5') as new:
            assert set(old)==set(new)
            changed=[key for key in old if not np.array_equal(old[key][...],new[key][...])];assert set(changed)<=set(('volume_flow','mass_flow')),changed
        record={'reason':'Use prescribed impermeable-wall normal velocity, not adjacent interior-cell normal velocity, for boundary flow observables.','archive':str(archive),'changed_datasets':changed,'old_reference_sha256':state['reference_sha256'],'new_reference_sha256':updated['reference_sha256'],'conversion_script_sha256':digest(Path(__file__).with_name('native_power_periodic.py')),'at_unix':time.time(),'native_recomputed':False,'numerical_validation':False};save(job/'conversion-wall-flux.json',record);save(job/'producer.json',{**meta,'conversion_script_sha256':record['conversion_script_sha256'],'conversion_record':'conversion-wall-flux.json'});state.update(updated);save(status,state);records.append({'design_id':job.name,**record})
    save(args.root/'maintenance/power-wall-flux-conversion-summary.json',records);print(json.dumps({'repackaged':len(records),'native_recomputed':False}))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);args=ap.parse_args()
    with reservation(args.root,'ch02power-flux-conversion-'+str(time.time_ns())):perform(args)


if __name__=='__main__':main()
