"""Replay the dimensions and directions stated in original issue #14657.

This evidence uses raw trusted-driver input, outside the formal data pool bounds;
formal cases are smaller-section author adaptations with separately declared scope.
"""
import argparse,json,subprocess
from pathlib import Path
import numpy as np
from independent import independent,closed_tip
TASK=Path(__file__).resolve().parents[1]
DOCKER='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--image',required=True);p.add_argument('--mode',required=True);args=p.parse_args()
    A=.3*.7;Iy=.3*.7**3/12;Iz=.7*.3**3/12;mat=[200e9,.3,A,Iy,Iz,Iy+Iz,5*A/6,5*A/6,7800]
    states=[]
    for direction,axis in [([4,0,0],[0,1,0]),([0,4,0],[0,0,1]),([0,0,4],[0,1,0])]:states.append(([0,0,0,*direction],axis))
    directory=TASK.parents[3]/'runs/authoring/repair-22/kratos-replay'/args.mode/'original-issue';directory.mkdir(parents=True,exist_ok=True)
    lines=['3']+[' '.join(str(v) for v in [*x,*axis,*mat,0,0,0]) for x,axis in states];(directory/'input.txt').write_text('\n'.join(lines)+'\n')
    command=[DOCKER,'run','--rm','--network','none','--cpus','2','--memory','4g','--user','1000:1000','--mount',f'type=bind,source={directory.resolve()},target=/job',args.image,'/opt/beam-build/beam_driver','/job/input.txt','/job/output.txt']
    process=subprocess.run(command,capture_output=True,text=True,timeout=45);(directory/'stderr.log').write_text(process.stderr)
    if process.returncode:raise RuntimeError(process.stderr)
    rows=(directory/'output.txt').read_text().splitlines();results=[]
    for i,(x,axis) in enumerate(states):
        K=np.fromstring(rows[4*i],sep=' ').reshape(12,12);exact,_=independent(x,axis,mat,np.zeros(3));observed=[];expected=[]
        for j in range(3):
            force=np.zeros(6);force[j]=1;observed.append(np.linalg.solve(K[6:,6:],force).tolist());expected.append(closed_tip(x,axis,mat,force).tolist())
        # closed_tip returns L*theta whereas raw driver uses theta.
        expected=np.asarray(expected);expected[:,3:]/=4
        results.append({'direction':x[3:],'actual_unit_force_tip_responses':observed,'closed_tip_responses':expected.tolist(),'max_stiffness_absolute_error':float(np.max(np.abs(K-exact)))})
    report={'origin':'Original issue text: L=4m, 0.3x0.7m rectangular section, E=200GPa, nu=.3, unit tip forces; J and rho supplied for complete 3D record but not affecting tested transverse/axial displacement comparisons','mode':args.mode,'states':results,'command':command}
    (TASK/'author/data-evidence'/('original-issue-'+args.mode+'.json')).write_text(json.dumps(report,indent=2)+'\n')
