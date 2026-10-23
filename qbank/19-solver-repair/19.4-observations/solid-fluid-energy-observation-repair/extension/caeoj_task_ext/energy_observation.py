"""Validate declared experiment inputs, without evaluating any energy or flow answer."""
import numpy as np
MODELS=['explicit-'+c+'-'+a+'-'+n+'-v1' for c in ['cartesian','rz'] for a in ['normal','ad'] for n in ['standard','renamed']]+['coupled-rz-steady-v1','coupled-rz-transient-v1']
def parameter_units():
 return {'length_x':'m','length_y':'m','length_z':'m','nx':'1','ny':'1','nz':'1','density_solid':'kg/m3','density_fluid':'kg/m3','specific_heat_solid':'J/(kg*K)','specific_heat_fluid':'J/(kg*K)','conductivity_solid':'W/(m*K)','conductivity_fluid':'W/(m*K)','viscosity':'Pa*s','heat_transfer_coefficient':'W/(m2*K)','temperature_reference':'K','inlet_speed':'m/s','source_constant':'W/m3','source_radial':'W/m3','source_axial':'W/m3','source_time_slope':'1/s','dt':'s','step_count':'1','velocity_order':'1'}
def desc(name,unit,components,axis):
 return {'array':name,'quantity':name,'unit':unit,'location':'experiments','time_axis':axis,'dtype':'float64','kind':'scalar' if len(components)==1 else 'components','component_shape':[len(components)],'components':components,'value_kind':'point'}
def inputs():
 r={'temperature_coefficients':desc('temperature_coefficients','K',['constant','xi','eta','zeta','xi2','xi_eta','xi_zeta','eta2','eta_zeta','zeta2'],'initial'),'velocity_coefficients':desc('velocity_coefficients','m/s',[a+'_'+b for a in 'xyz' for b in ['constant','xi','eta','zeta']],'initial')}
 for d in r.values():d['sampling']={'space':'uniform','time':'constant','extrapolation':'forbid'}
 return r
def outputs():return {n:desc(n,'J' if n.startswith('energy_') else 'W',['value'],'frames') for n in ['energy_solid','energy_fluid','advection_power','source_power','robin_power']}
def check(problem,errors):
 from caeoj.validation import issue
 m=problem.manifest;a=problem.arrays
 def fail(path,expect,actual):errors.append(issue('E_ENERGY_OBSERVATION',path,expect,str(actual),'Outside the public solid/fluid observation contract.'))
 model=m.get('physics',{}).get('model');rz='-rz-' in str(model);explicit=str(model).startswith('explicit-');transient=model=='coupled-rz-transient-v1'
 if model not in MODELS or m.get('task')!='solid-fluid-energy-observation-repair' or m['spatial_dimension']!=(2 if rz else 3) or m['geometries'] or m['meshes'] or m['conditions']:fail('$','DATA model and empty geometries/meshes/conditions',model);return
 if m['locations']!={'experiments':{'kind':'entities','ids':'experiment_ids'}} or m['time_axes']!={'initial':'initial_time','frames':'times'} or not np.array_equal(a['experiment_ids'],[1]) or not np.array_equal(a['initial_time'],[0.]):fail('$.locations/time_axes','one experiment id1 and initial zero',m['locations']);return
 if m['fields']!=inputs() or m['outputs']!=outputs():fail('$.fields/outputs','exact DATA fields/outputs',m['fields']);return
 par=m['physics']['parameters'];units=parameter_units()
 if set(par)!=set(units) or any(set(par[k])!={'value','unit'} or par[k]['unit']!=u for k,u in units.items()):fail('$.physics.parameters','exact DATA scalar parameter units',par);return
 p={k:v['value'] for k,v in par.items()}
 if any(not isinstance(v,(int,float)) or not np.isfinite(v) for v in p.values()):fail('$.physics.parameters','finite numeric scalars',p);return
 for k in ['nx','ny','nz','step_count','velocity_order']:
  if type(p[k]) is not int:fail('$.physics.parameters.'+k,'integer',p[k]);return
 if not (.1<=p['length_x']<=1 and .1<=p['length_y']<=1 and (p['length_z']==0 if rz else .1<=p['length_z']<=1) and 4<=p['nx']<=8 and p['nx']%2==0 and 2<=p['ny']<=8 and (p['nz']==0 if rz else 2<=p['nz']<=8)):fail('$.physics.parameters','DATA domain and mesh bounds',p);return
 if any(not 1<=p['density_'+b]<=2000 or not 1<=p['specific_heat_'+b]<=5000 for b in ['solid','fluid']):fail('$.physics.parameters','positive bounded density and heat capacity',p);return
 T=a['temperature_coefficients'];u=a['velocity_coefficients']
 if T.shape!=(1,1,10) or u.shape!=(1,1,12):fail('$.fields','one initial experiment with10/12 coefficients',(T.shape,u.shape));return
 if explicit:
  if not (250<=T[0,0,0]<=350 and np.all(abs(T.ravel()[1:])<=10) and np.all(abs(u)<=1) and p['velocity_order']==2):fail('$.fields','DATA polynomial coefficient bounds',T);return
  if rz and (np.any(T.ravel()[[3,6,8,9]]!=0) or np.any(u.reshape(3,4)[:,3]!=0) or np.any(u.reshape(3,4)[2]!=0)):fail('$.fields','zero RZ inactive coefficients',u);return
  fixed={'conductivity_solid':1,'conductivity_fluid':1,'viscosity':1,'heat_transfer_coefficient':1,'temperature_reference':300,'inlet_speed':0,'source_time_slope':0,'dt':0,'step_count':0}
  if any(p[k]!=v for k,v in fixed.items()) or any(abs(p[k])>100 for k in ['source_constant','source_radial','source_axial']):fail('$.physics.parameters','explicit family fixed controls and source bounds',p);return
 else:
  if np.any(T!=0) or np.any(u!=0) or p['velocity_order'] not in [1,2]:fail('$.fields','zero unused polynomial coefficients',T);return
  if any(not 1<=p['density_'+b]<=20 or not 1<=p['specific_heat_'+b]<=20 or not .5<=p['conductivity_'+b]<=5 for b in ['solid','fluid']) or not .1<=p['viscosity']<=2 or not .5<=p['heat_transfer_coefficient']<=5 or not 250<=p['temperature_reference']<=350 or not .1<=p['inlet_speed']<=1 or p['density_fluid']*p['inlet_speed']*p['length_x']/2/p['viscosity']>10:fail('$.physics.parameters','coupled material, temperature and low-Re bounds',p);return
  if any(not 0<=p[k]<=10 for k in ['source_constant','source_radial','source_axial']) or sum(p[k] for k in ['source_constant','source_radial','source_axial'])<=0 or not 0<=p['source_time_slope']<=1:fail('$.physics.parameters','nonzero nonnegative source and bounded slope',p);return
  if transient:
   if not .05<=p['dt']<=.2 or not 1<=p['step_count']<=4:fail('$.physics.parameters','Euler time controls',p);return
  elif p['dt']!=0 or p['step_count']!=0 or p['source_time_slope']!=0:fail('$.physics.parameters','steady zero time controls',p);return
 times=np.arange(int(p['step_count'])+1,dtype=float)*p['dt'] if transient else np.array([0.])
 if not np.array_equal(a['times'],times):fail('$.time_axes.frames','exact DATA frame times',a['times'])
