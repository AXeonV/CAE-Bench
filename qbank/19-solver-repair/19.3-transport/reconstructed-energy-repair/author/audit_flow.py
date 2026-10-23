"""Independent physical checks of native real-CFD fields, not driver formulas."""
from pathlib import Path
import csv,json,sys
import numpy as np
Q=Path(__file__).resolve().parents[1];sys.path.insert(0,str(Q/'public'))
from read_vtk import read
def audit(native):
    native=Path(native);xyz,a=read(native/'observed.vtk');wxyz,wall=read(native/'wall.vtk');lines=(native/'mesh.su2').read_text().splitlines()
    center=(xyz[:,:2].max(0)+xyz[:,:2].min(0))/2;markers=[];i=0
    while i<len(lines):
        if not lines[i].startswith('MARKER_TAG'):i+=1;continue
        tag=lines[i].split('=')[1].strip();n=int(lines[i+1].split('=')[1]);i+=2;mass=energy=0.;momentum=np.zeros(2)
        for line in lines[i:i+n]:
            typ,p,q=map(int,line.split()[:3]);assert typ==3
            edge=xyz[q,:2]-xyz[p,:2];normal=np.array([edge[1],-edge[0]])
            if np.dot(normal,(xyz[p,:2]+xyz[q,:2])/2-center)<0:normal=-normal
            ids=[p,q];rho=a['Density'][ids,0];u=a['Velocity'][ids,:2];P=a['Pressure'][ids,0];E=a['Energy'][ids,0];un=u@normal
            mass+=float(np.mean(rho*un));energy+=float(np.mean((E+P)*un));momentum+=np.mean(rho[:,None]*u*un[:,None]+P[:,None]*normal,axis=0)
        markers.append({'marker':tag,'mass_flux_kg_m_s':mass,'inviscid_energy_flux_W_m':energy,'inviscid_momentum_flux_N_m':momentum.tolist()});i+=n
    bulk=xyz[:,1]>1e-10;rho=a['Density'][:,0];P=a['Pressure'][:,0];T=a['Temperature'][:,0];u=a['Velocity'][:,:2];E=a['Energy'][:,0];k=a['Turb_Kin_Energy'][:,0]
    expected_E=rho*287.058*T/.4+.5*rho*np.sum(u*u,axis=1)+rho*k
    eos=abs(rho-P/(287.058*T))/rho;energy_state=abs(E-expected_E)/abs(E)
    order=np.argsort(wxyz[:,0]);drag=.5*1.4*115056*.2**2*float(np.trapezoid(wall['Skin_Friction_Coefficient'][order,0],wxyz[order,0]))
    mass=sum(x['mass_flux_kg_m_s'] for x in markers);energy=sum(x['inviscid_energy_flux_W_m'] for x in markers);mom=np.sum([x['inviscid_momentum_flux_N_m'] for x in markers],axis=0)
    with (native/'history.csv').open() as f:r=[{k.strip():float(v) for k,v in row.items()} for row in csv.DictReader(f,skipinitialspace=True)]
    cd=np.array([x['CD'] for x in r[-101:]])
    result={'markers':markers,'nonwall_EOS_max_relative_error':float(max(eos[bulk])),'nonwall_RANS_energy_max_relative_error':float(max(energy_state[bulk])),
            'wall_stored_EOS_max_relative_error':float(max(eos[~bulk])),'wall_stored_energy_max_relative_error':float(max(energy_state[~bulk])),
            'external_mass_relative_imbalance':mass/max(abs(x['mass_flux_kg_m_s']) for x in markers),
            'external_inviscid_energy_relative_imbalance':energy/max(abs(x['inviscid_energy_flux_W_m']) for x in markers),
            'wall_drag_N_m':drag,'inviscid_momentum_net_N_m':mom.tolist(),'streamwise_momentum_plus_drag_N_m':float(mom[0]+drag),
            'final_iteration':r[-1]['Inner_Iter'],'final_density_log10_residual':r[-1]['rms[Rho]'],'final_energy_log10_residual':r[-1]['rms[RhoE]'],
            'last100_CD_relative_range':float(np.ptp(cd)/abs(cd[-1])),'all_native_fields_finite':all(np.isfinite(v).all() for v in a.values()),
            'wall_reported_heat_flux_max_abs':float(np.max(abs(wall['Heat_Flux']))),
            'scope':'Exact nonwall ideal-state/RANS energy identities up to native ASCII rounding. External flux estimates use trapezoid inviscid quadrature and omit open viscous work/diffusive heat; they are not exact finite-volume conservation. Staged wall EOS differences and external TMR Cf discrepancy remain disclosed.'}
    result['passed']=bool(result['all_native_fields_finite'] and result['nonwall_EOS_max_relative_error']<2e-6 and result['nonwall_RANS_energy_max_relative_error']<2e-6 and abs(result['external_mass_relative_imbalance'])<.001 and abs(result['external_inviscid_energy_relative_imbalance'])<.001 and result['wall_reported_heat_flux_max_abs']<1e-8 and result['last100_CD_relative_range']<=.001)
    return result
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--native',type=Path,required=True);p.add_argument('--output',type=Path,required=True);v=p.parse_args();r=audit(v.native);v.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));raise SystemExit(0 if r['passed'] else 1)
