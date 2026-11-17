"""Actual penalty sensitivity, boundary flux and natural-stress checks."""
from pathlib import Path
import argparse,json,re
import numpy as np
from convert_supplement import vtu,sample,probes
from supplement80 import specifications


def values(d,xy):
    raw=vtu(sorted(d.glob('solution.*.00000.vtu'))[-1]);out=sample(raw,xy,relative_pressure=False)
    return raw,out


def flux(raw,x):
    hit=np.abs(raw['xyz'][:,0]-x)<1e-8;ys=raw['xyz'][hit,1];uu=raw['velocity'][hit,0]
    unique=np.unique(np.round(ys,12));velocity=np.array([uu[np.abs(ys-y)<1e-8].mean() for y in unique]);h=np.diff(unique)
    assert len(unique)%2==1 and np.max(h)-np.min(h)<1e-9
    return float(h[0]/3*(velocity[0]+velocity[-1]+4*velocity[1:-1:2].sum()+2*velocity[2:-1:2].sum()))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--level',type=int,default=64);a=p.parse_args();root=a.root
    s=next(s for s in specifications() if s.get('open_shaped'));xy=probes(s)
    _,base=values(root/'runs'/s['name']/'n16',xy);_,high=values(root/'penalty-sensitivity/runs'/s['name']/'n16',xy)
    ratios={q:float(np.max(np.abs(base[q]-high[q])/(atol+.01*np.abs(high[q])))) for q,atol in [('velocity',.001),('pressure',.1),('shear_rate',.01)]}
    assert max(ratios.values())<.05,ratios
    log=(root/'penalty-sensitivity/runs'/s['name']/'n16/solver.log').read_text();residual=float(re.findall(r'alpha\s*=.*?res\s*=\s*([\deE.+-]+)',log)[-1]);assert residual<1e-8
    raw,_=values(root/'runs'/s['name']/f'n{a.level}',xy);qin=flux(raw,0);qout=flux(raw,6)
    assert abs(qin-.1)<.25*(1e-6+.01*.1) and abs(qout-qin)<1e-7,(qin,qout)
    observation=np.array([[6.,.5],[6.,1.],[6.,1.5]])
    b=sample(raw,observation,relative_pressure=False)
    G=b['velocity_gradient'].reshape(-1,3,3)[:,:2,:2];stress=-b['pressure'][:,0,None,None]*np.eye(2)[None]+s['nu']*(G+G.transpose(0,2,1))
    natural=float(np.max(np.abs(stress@np.array([1.,0.]))));assert natural<.01,natural
    result=dict(name=s['name'],penalties=[10000,100000],sensitivity_level=16,penalty_tolerance_fractions=ratios,high_penalty_residual=residual,flux_level=a.level,inlet_flux=qin,outlet_flux=qout,requested_rate=.1,natural_outlet_max_abs_traction=natural,
                material_equivalence='Upstream power-law n=1, K=0.08 => constant kinematic viscosity 0.08, zero viscosity derivative; symmetric stress assembler. Public material remains Newtonian.',
                boundary_approximation='Upstream weak Dirichlet function imposes the actual entitywise-constant normalized inlet profile; source facets align with profile breaks. Penalty and mesh sensitivity checked separately.')
    (root/'evidence/shaped-inlet-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
