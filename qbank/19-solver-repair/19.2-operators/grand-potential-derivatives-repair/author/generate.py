"""Generate distinct material/FE API programs, with explicit strict/non-strict controls."""
import sys
from pathlib import Path
import numpy as np
from caeoj.storage import write_hdf5
from caeoj.validation import write_json
TASK=Path(__file__).resolve().parents[1];sys.path.insert(0,str(TASK/'extension'))
from caeoj_task_ext.grand_potential import inputs,outputs,parameter_units

def parameters(count=2,strict=1,names=0,va=4e-29,ks=3.2e8,kv=4.8e8,length=1.,constant=.2,linear=None,hessian=None):
    p=dict(grain_count=count,strict_mass_conservation=strict,variable_name_set=names,atomic_volume=va,solid_energy_coefficient=ks,void_energy_coefficient=kv,surface_energy=.16,grainboundary_energy=.112,interface_width=1e-9,surface_switch_value=.3,probe_length=length,equilibrium_constant=constant)
    linear=np.array(linear if linear is not None else [.1,.03,0,0]);b=np.zeros((4,4)) if hessian is None else np.array(hessian)
    for i in range(4):p[f'equilibrium_linear_{i}']=float(linear[i])
    for i in range(4):
        for j in range(i,4):p[f'equilibrium_hessian_{i}{j}']=float(b[i,j])
    return p
BASE_B=[[.1,.04,0,0],[.04,.02,0,0],[0,0,0,0],[0,0,0,0]]
MIX_B=[[.04,-.03,.02,.01],[-.03,-.02,.015,-.025],[.02,.015,.03,.035],[.01,-.025,.035,.02]]
TRI_B=[[.03,.025,-.015,0],[.025,.02,.035,0],[-.015,.035,-.02,0],[0,0,0,0]]
ETA4=[[.2,.4,.6,.8],[.8,.1,.5,.2],[.3,.7,.1,.9],[.6,.5,.8,.3]]
CASES=[
 ('01-coupled-polynomial-public',parameters(hessian=BASE_B),[.2,.4,.7,.9],[[.3,.6,0,0],[.4,.5,0,0],[.7,.1,0,0],[.2,.8,0,0]]),
 ('02-renamed-three-grains-public',parameters(count=3,names=1,constant=.3,linear=[-.08,.1,.04,0],hessian=TRI_B),[.15,.5,.85,.35],[[.3,.6,.4,0],[.4,.5,.2,0],[.7,.1,.8,0],[.2,.8,.6,0]]),
 ('03-clamped-constant-control',parameters(count=1,names=1,constant=.4,linear=[0,0,0,0]),[-.1,0,1,1.1],[[.0,0,0,0],[.2,0,0,0],[.8,0,0,0],[1.,0,0,0]]),
 ('04-pure-void-control',parameters(count=4,strict=0,constant=.35,linear=[.05,-.03,.02,.01],hessian=MIX_B),[1,1.1,1,1.1],ETA4),
 ('05-solid-endpoint-grain-derivatives',parameters(count=4,names=1,constant=.35,linear=[.05,-.03,.02,.01],hessian=MIX_B),[0,-.1,0,-.05],ETA4),
 ('06-near-interface-endpoints',parameters(count=4,names=1,constant=.35,linear=[.05,-.03,.02,.01],hessian=MIX_B),[1e-5,.001,.999,1-1e-5],ETA4),
 ('07-one-grain-sign-change',parameters(count=1,constant=.4,linear=[-.03,0,0,0],hessian=[[.07,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]]),[.25,.45,.65,.8],[[.1,0,0,0],[.4,0,0,0],[.7,0,0,0],[1,0,0,0]]),
 ('08-four-grain-mixed-hessian',parameters(count=4,names=1,constant=.35,linear=[.05,-.03,.02,.01],hessian=MIX_B),[.18,.37,.62,.82],ETA4),
 ('09-nonstrict-parabolic-regression',parameters(strict=0,hessian=BASE_B),[.2,.4,.7,.9],[[.3,.6,0,0],[.4,.5,0,0],[.7,.1,0,0],[.2,.8,0,0]]),
 ('10-stiffness-contrast',parameters(va=1e-30,ks=1e8,kv=1e11,length=.25,hessian=BASE_B),[.12,.39,.61,.88],[[.3,.6,0,0],[.4,.5,0,0],[.7,.1,0,0],[.2,.8,0,0]]),
 ('11-volume-and-reverse-contrast',parameters(count=4,names=1,va=1e-28,ks=1e11,kv=2e8,length=4.,constant=.35,linear=[.05,-.03,.02,.01],hessian=MIX_B),[.22,.43,.64,.86],ETA4),
 ('12-eight-program-sparse-identities',parameters(count=4,length=2.,ks=4e9,kv=8e9,constant=.35,linear=[.05,-.03,.02,.01],hessian=MIX_B),[0,.1,.25,.4,.5,.7,.9,1],ETA4+list(reversed(ETA4)))]
def main():
    records=[]
    for index,(name,p,phi,eta) in enumerate(CASES):
        d=TASK/'cases'/name;d.mkdir(parents=True,exist_ok=True);n=len(phi);eta=np.array(eta,dtype=float)
        linear=np.array([p[f'equilibrium_linear_{i}'] for i in range(4)]);b=np.zeros((4,4))
        for i in range(4):
            for j in range(i,4):b[i,j]=b[j,i]=p[f'equilibrium_hessian_{i}{j}']
        ceq=p['equilibrium_constant']+eta@linear+.5*np.einsum('ni,ij,nj->n',eta,b,eta)
        fractions=np.resize(np.array([.03,-.02,0,.05]),n)
        if index in [2,3]:fractions[:]=0
        potential=fractions*p['atomic_volume']*np.minimum(p['solid_energy_coefficient']*ceq,p['void_energy_coefficient'])
        arrays={'program_ids':np.array([17+19*i for i in range(n)],dtype='int64'),'times':np.array([0.]),'phi':np.array(phi)[None,:,None],'eta':eta[None],'potential':potential[None,:,None],'temperature':np.linspace(250,2000,n)[None,:,None],'concentration':np.resize(np.array([.2,.8,0.,1.]),n)[None,:,None]}
        if index==11:arrays['program_ids']=np.array([2**40+101+1009*i for i in range(n)],dtype='int64')
        manifest={'task':'grand-potential-derivatives-repair','spatial_dimension':1,'data_file':'input.h5','geometries':{},'meshes':{},'locations':{'programs':{'kind':'entities','ids':'program_ids'}},'time_axes':{'instant':'times'},'fields':inputs(),'outputs':outputs(),'physics':{'model':'grand-potential-material-programs-v1','parameters':{k:{'value':v,'unit':parameter_units()[k]} for k,v in p.items()}},'conditions':[]}
        write_json(d/'problem.json',manifest);write_hdf5(d/'input.h5',arrays)
        records.append({'case':name,'programs':n,'grain_count':p['grain_count'],'strict':p['strict_mass_conservation'],'variable_name_set':p['variable_name_set'],'origin':'Author material/FE operator programs adapted to the real issue30236 capability; not original upstream sintering trajectories.','non_strict_pair_with':'01-coupled-polynomial-public' if index==8 else None})
    write_json(TASK/'author/data-evidence/cases.json',records)
if __name__=='__main__':main()
