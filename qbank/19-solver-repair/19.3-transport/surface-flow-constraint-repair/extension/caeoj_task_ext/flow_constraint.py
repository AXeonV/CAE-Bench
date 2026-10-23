"""Validate the complete public catalytic-flow declaration; never compute its solution."""
import numpy as np
from caeoj.validation import issue
TASK='surface-flow-constraint-repair'
MODEL='catalytic-flow-state-v1'
MULTI=False
FIELDS={'species_order': ('species_order', '1', ['value'], 'int64'), 'temperature': ('temperature', 'K', ['value'], 'float64'), 'pressure': ('pressure', 'Pa', ['value'], 'float64'), 'inlet_speed': ('speed', 'm/s', ['value'], 'float64'), 'surface_area_to_volume': ('area_volume_ratio', '1/m', ['value'], 'float64'), 'site_density': ('surface_site_density', 'kmol/m^2', ['value'], 'float64'), 'adsorption_rate': ('adsorption_rate_constant', 'm^3/(kmol*s)', ['value'], 'float64'), 'desorption_rate': ('rate_constant', '1/s', ['value'], 'float64'), 'conversion_rate': ('rate_constant', '1/s', ['value'], 'float64'), 'distance': ('distance', 'm', ['value'], 'float64'), 'inlet_mole_fractions': ('mole_fraction', '1', ['A', 'B', 'I'], 'float64')}
OUTPUTS={'mass_fractions': ('mass_fraction', '1', ['A', 'B', 'I'], 'float64'), 'coverages': ('site_coverage', '1', ['S', 'AS'], 'float64'), 'pressure': ('pressure', 'Pa', ['value'], 'float64'), 'density': ('density', 'kg/m^3', ['value'], 'float64'), 'speed': ('speed', 'm/s', ['value'], 'float64')}
def spec(k,v,output=False):
 quantity,unit,components,dtype=v;c=len(components)
 d={'array':k,'quantity':quantity,'unit':unit,'location':'states','time_axis':'instant','dtype':dtype,'kind':'scalar' if c==1 else 'components','component_shape':[c],'components':components,'value_kind':'point'}
 if not output:d['sampling']={'space':'uniform','time':'constant','extrapolation':'forbid'}
 return d

def check(problem,errors):
 m,a=problem.manifest,problem.arrays
 def fail(path,expected,actual):errors.append(issue('E_CATALYTIC_FLOW',path,expected,str(actual),'Outside the public catalytic-flow DATA contract.'))
 if m.get('task')!=TASK or m['spatial_dimension']!=1 or m['geometries'] or m['meshes'] or m['conditions'] or m['physics']!={'model':MODEL,'parameters':{}}:fail('$','independent isothermal catalytic-flow states',m.get('task'))
 if m['locations']!={'states':{'kind':'entities','ids':'state_ids'}} or not 1<=len(a.get('state_ids',[]))<=32:fail('$.locations','1..32 independent axial observations',m['locations'])
 if m['time_axes']!={'instant':'times'} or not np.array_equal(a.get('times'),[0.]):fail('$.time_axes','instant=[0]',m['time_axes'])
 for group,fields in [('fields',FIELDS),('outputs',OUTPUTS)]:
  if set(m[group])!=set(fields):fail('$.'+group,'exact declared fields',m[group]);return
  for k,v in fields.items():
   if m[group][k]!=spec(k,v,group=='outputs'):fail('$.'+group+'.'+k,str(spec(k,v,group=='outputs')),m[group][k])
 ranges={'temperature':(500,1500),'pressure':(1e4,1e6),'inlet_speed':(.01,1),'surface_area_to_volume':(10,10000),'site_density':(1e-9,1e-6),'adsorption_rate':(0,1e15 if MULTI else 1e8),'desorption_rate':(100,1e6),'conversion_rate':(0,1e6),'distance':(0,2)}
 for k,(lo,hi) in ranges.items():
  if np.any(a[k]<lo) or np.any(a[k]>hi):fail('$.fields.'+k,f'{lo}..{hi}',a[k])
 if not np.isin(a['species_order'],range(6)).all():fail('$.fields.species_order','integer0..5',a['species_order'])
 x=a['inlet_mole_fractions'][0]
 if np.any(x<0) or np.any(abs(x.sum(axis=1)-1)>1e-12) or np.any(x[:,2]<.05):fail('$.fields.inlet_mole_fractions','nonnegative sum1, I>=.05',x)
 if MULTI:
  raw=a['coverage_mode'][0,:,0];theta=a['initial_coverages'][0];total=theta.sum(axis=1)
  if not np.isin(raw,[0,1]).all() or np.any(theta<.001) or np.any(theta>1.499) or np.any(total<.5) or np.any(total>1.5) or np.any(abs(total[raw==0]-1)>1e-12):fail('$.fields.initial_coverages','positive sum.5..1.5; normalized sum1 for mode0',theta)
