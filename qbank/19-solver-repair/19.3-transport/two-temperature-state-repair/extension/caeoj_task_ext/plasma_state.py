"""Validate public plasma state data; never compute answers."""
import numpy as np
from caeoj.validation import issue
FIELDS={'mode':('state_constraint','1',1),'temperature':('temperature','K',1),'electron_temperature':('temperature','K',1),'final_electron_temperature':('temperature','K',1),'constraint_value':('state_constraint_value','1',1),'mole_fractions':('mole_fraction','1',3)}
OUT={'pressure':('pressure','Pa',1),'electron_pressure':('electron_pressure','Pa',1),'density':('density','kg/m^3',1),'concentrations':('molar_concentration','kmol/m^3',3)}
def check(problem,errors):
 m,a=problem.manifest,problem.arrays
 def fail(path,expected,actual):errors.append(issue('E_PLASMA',path,expected,str(actual),'Outside public plasma-state DATA contract.'))
 if m.get('task')!='two-temperature-state-repair' or m['spatial_dimension']!=1 or m['meshes'] or m['geometries'] or m['conditions'] or m['physics']['parameters']:
  fail('$','independent plasma states',m.get('task'))
 if m['locations']!={'states':{'kind':'entities','ids':'state_ids'}} or not 1<=len(a.get('state_ids',[]))<=32:fail('$.locations','1..32 states',m['locations'])
 if m['time_axes']!={'instant':'times'} or not np.array_equal(a.get('times'),[0.]):fail('$.time_axes','instant=[0]',m['time_axes'])
 for group,fields in [('fields',FIELDS),('outputs',OUT)]:
  if set(m[group])!=set(fields):fail('$.'+group,'exact specified fields',m[group]);return
  for k,(quantity,unit,c) in fields.items():
   d={'array':k,'quantity':quantity,'unit':unit,'location':'states','time_axis':'instant','dtype':'int64' if k=='mode' else 'float64','kind':'scalar' if c==1 else 'components','component_shape':[c],'components':['value'] if c==1 else ['O2','O','E'],'value_kind':'point'}
   if group=='fields':d['sampling']={'space':'uniform','time':'constant','extrapolation':'forbid'}
   if m[group][k]!=d:fail('$.'+group+'.'+k,str(d),m[group][k])
 mode=a['mode'][0,:,0];v=a['constraint_value'][0,:,0];x=a['mole_fractions'][0]
 if not np.isin(mode,[0,1]).all():fail('$.fields.mode','0 or1',mode)
 for k,lo,hi in [('temperature',200,3000),('electron_temperature',200,100000),('final_electron_temperature',200,100000)]:
  if np.any(a[k]<lo) or np.any(a[k]>hi):fail('$.fields.'+k,f'{lo}..{hi}',a[k])
 if np.any(x<0) or np.any(x[:,2]>.8) or np.any(abs(x.sum(axis=1)-1)>1e-12):fail('$.fields.mole_fractions','nonnegative, sum1, E<=.8',x)
 if np.any(v[mode==0]<1e-5) or np.any(v[mode==0]>10) or np.any(v[mode==1]<10) or np.any(v[mode==1]>1e7):fail('$.fields.constraint_value','documented per-mode range',v)
