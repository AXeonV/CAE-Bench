"""Adapted regression families; independent ideal-mixture check is not solver reference."""
from pathlib import Path
import json,shutil
import numpy as np
from caeoj.storage import write_hdf5
from caeoj.validation import write_json
Q=Path(__file__).resolve().parents[1]
W=Path('work/repair-22/cantera-1872/generated')
FIELDS={'mode':('state_constraint','1',1),'temperature':('temperature','K',1),
'electron_temperature':('temperature','K',1),'final_electron_temperature':('temperature','K',1),
'constraint_value':('state_constraint_value','1',1),'mole_fractions':('mole_fraction','1',3)}
OUT={'pressure':('pressure','Pa',1),'electron_pressure':('electron_pressure','Pa',1),
'density':('density','kg/m^3',1),'concentrations':('molar_concentration','kmol/m^3',3)}
def spec(k,v,out=False):
 quantity,unit,c=v
 d={'array':k,'quantity':quantity,'unit':unit,'location':'states','time_axis':'instant',
 'dtype':'int64' if k=='mode' else 'float64','kind':'scalar' if c==1 else 'components',
 'component_shape':[c],'components':['value'] if c==1 else ['O2','O','E'],'value_kind':'point'}
 if not out:d['sampling']={'space':'uniform','time':'constant','extrapolation':'forbid'}
 return d

def make(name,mode,kind,seed):
 rng=np.random.default_rng(seed);n=12
 t=rng.uniform(250,2500,n);te=rng.uniform(300,50000,n);te2=rng.uniform(300,80000,n)
 xe=rng.uniform(.001,.75,n);o=rng.uniform(0,1,n)*(1-xe)
 if kind=='equilibrium':te=t.copy();te2=t.copy()
 if kind=='zero-electron':xe[:]=0;o=rng.uniform(0,1,n)
 if kind=='cold-electron':te2=rng.uniform(200,240,n)
 if kind=='unchanged':te2=te.copy()
 if kind=='trace-electron':xe=rng.uniform(1e-7,1e-4,n);o=rng.uniform(0,.5,n)
 if kind=='issue':t[:]=300;te[:]=300;te2=np.geomspace(300,100000,n);xe[:]=.5;o[:]=0
 x=np.column_stack([1-xe-o,o,xe]);v=np.geomspace(1e-4,5,n) if mode==0 else np.geomspace(100,5e6,n)
 if kind=='issue':v[:]=.6415
 arrays={'state_ids':np.arange(n,dtype='int64')*17+3,'times':np.array([0.]),
 'mode':np.full((1,n,1),mode,dtype='int64'),'temperature':t[None,:,None],
 'electron_temperature':te[None,:,None],'final_electron_temperature':te2[None,:,None],
 'constraint_value':v[None,:,None],'mole_fractions':x[None]}
 meta={'task':'two-temperature-state-repair','spatial_dimension':1,'data_file':'input.h5',
 'geometries':{},'meshes':{},'conditions':[],'physics':{'model':'two-temperature-state-v1','parameters':{}},
 'locations':{'states':{'kind':'entities','ids':'state_ids'}},'time_axes':{'instant':'times'},
 'fields':{k:spec(k,a) for k,a in FIELDS.items()},'outputs':{k:spec(k,a,True) for k,a in OUT.items()}}
 case=Q/'cases'/name;case.mkdir(parents=True,exist_ok=True);write_hdf5(case/'input.h5',arrays);write_json(case/'problem.json',meta)
 mw=x@np.array([31.998,15.999,.0005485799088728283]);tm=t*(1-xe)+te2*xe;R=8314.46261815324
 rho=v if mode==0 else v*mw/(R*tm);c=rho/mw;p=c*R*tm;pe=c*xe*R*te2
 y={'pressure':p[None,:,None],'electron_pressure':pe[None,:,None],'density':rho[None,:,None],'concentrations':(c[:,None]*x)[None]}
 W.mkdir(parents=True,exist_ok=True);write_json(W/(name+'.json'),{k:a.tolist() for k,a in y.items()})
 return {'case':name,'mode':mode,'family':kind,'seed':seed,'origin':'author adaptation of Cantera issue1872; issue family retains original T/rho/X and varies final Te'}
if __name__=='__main__':
 families=[('01-issue-public',0,'issue'),('02-equilibrium-public',1,'equilibrium'),
 ('03-density-mixture',0,'mixed'),('04-pressure-mixture',1,'mixed'),
 ('05-density-cold',0,'cold-electron'),('06-pressure-cold',1,'cold-electron'),
 ('07-density-zero-electron',0,'zero-electron'),('08-pressure-zero-electron',1,'zero-electron'),
 ('09-density-unchanged',0,'unchanged'),('10-pressure-unchanged',1,'unchanged'),
 ('11-density-trace',0,'trace-electron'),('12-pressure-trace',1,'trace-electron')]
 write_json(Q/'author/data-evidence/cases.json',[make(n,m,k,187200+i) for i,(n,m,k) in enumerate(families)])
