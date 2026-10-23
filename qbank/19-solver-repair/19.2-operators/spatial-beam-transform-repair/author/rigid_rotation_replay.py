"""Measure actual element stiffness energy under a physical rigid rotation."""
import json,subprocess
from pathlib import Path
import numpy as np
TASK=Path(__file__).resolve().parents[1];DOCKER='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
if __name__=='__main__':
    out=TASK.parents[3]/'runs/authoring/repair-22/kratos-replay/rigid-rotation';out.mkdir(parents=True,exist_ok=True)
    values=[0,0,0,1,2,3,0,1,0,210e9,.3,.01,1e-5,2e-5,1.5e-5,.008,.007,7800,0,0,0];(out/'input.txt').write_text('1\n'+' '.join(map(str,values))+'\n')
    omega=np.array([0.,0.,.01]);d=np.r_[np.zeros(3),omega,np.cross(omega,[1,2,3]),omega];record={}
    for mode,image in [('baseline','caeoj-kratos14657-runtime:base'),('upstream','caeoj-kratos14657-upstream:fixed'),('author_supplemented','caeoj-kratos14657-reference:fixed')]:
        command=[DOCKER,'run','--rm','--network','none','--mount',f'type=bind,source={out.resolve()},target=/job',image,'/opt/beam-build/beam_driver','/job/input.txt','/job/'+mode+'.txt'];subprocess.run(command,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        K=np.fromstring((out/(mode+'.txt')).read_text().splitlines()[0],sep=' ').reshape(12,12)
        record[mode]={'rigid_rotation_strain_energy_J':float(d@K@d/2),'matrix_times_rigid_rotation_max_N':float(np.max(np.abs(K@d))),'image_id':json.loads(subprocess.check_output([DOCKER,'image','inspect',image]))[0]['Id']}
    assert abs(record['author_supplemented']['rigid_rotation_strain_energy_J'])<1e-9
    (TASK/'author/data-evidence/rigid-rotation-replay.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
