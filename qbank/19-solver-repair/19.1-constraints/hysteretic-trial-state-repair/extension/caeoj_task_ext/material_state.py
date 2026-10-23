"""Validate the public direct-material experiment declarations."""
CHECKPOINTS=['committed','returned','accepted','continued','rolled_back','reset']
INPUTS={
 'material_kind':('material_kind','1',['value']),
 'positive_count':('positive_point_count','1',['value']), 'negative_count':('negative_point_count','1',['value']),
 'positive_strain':('positive_envelope_strain','1',[f'point_{i}' for i in range(7)]),
 'positive_stress':('positive_envelope_stress','Pa',[f'point_{i}' for i in range(7)]),
 'negative_strain':('negative_envelope_strain','1',[f'point_{i}' for i in range(7)]),
 'negative_stress':('negative_envelope_stress','Pa',[f'point_{i}' for i in range(7)]),
 'pinching':('pinching_parameters','1',['pinch_x','pinch_y']), 'beta':('unloading_exponent','1',['value']),
 'history_count':('history_step_count','1',['value']), 'history':('committed_strain_history','1',[f'step_{i}' for i in range(8)]),
 'trial_count':('trial_step_count','1',['value']), 'trials':('uncommitted_strain_probes','1',[f'step_{i}' for i in range(8)]),
 'return_delta':('return_strain_increment','1',['value']),
 'continuation_count':('continuation_step_count','1',['value']), 'continuation':('continuation_strain_history','1',[f'step_{i}' for i in range(8)]),
 'rollback_probe':('rollback_trial_strain','1',['value'])}
OUTPUTS={'strain':('strain','1',CHECKPOINTS),'stress':('stress','Pa',CHECKPOINTS),
 'tangent':('tangent_modulus','Pa',CHECKPOINTS),'work_density':('committed_work_density','Pa',CHECKPOINTS)}
def spec(name,description,output=False):
 q,u,c=description
 d={'array':name,'quantity':q,'unit':u,'location':'programs','time_axis':'instant','dtype':'float64','kind':'scalar' if len(c)==1 else 'components','component_shape':[len(c)],'components':c,'value_kind':'point'}
 if not output:d['sampling']={'space':'uniform','time':'constant','extrapolation':'forbid'}
 return d

def check(problem,errors):
 import numpy as np
 from caeoj.validation import issue
 m=problem.manifest;a=problem.arrays
 def fail(path,expected,actual):errors.append(issue('E_MATERIAL_STATE',path,expected,str(actual),'Outside the public material-state DATA contract.'))
 if m.get('task')!='hysteretic-trial-state-repair' or m['spatial_dimension']!=1 or m.get('physics')!={'model':'hysteretic-trial-state-v1','parameters':{}} or m['geometries'] or m['meshes'] or m['conditions']:
  fail('$','independent uniaxial material programs',m.get('physics'));return
 ids=a.get('program_ids',np.array([]))
 if m['locations']!={'programs':{'kind':'entities','ids':'program_ids'}} or not 1<=len(ids)<=32 or np.any(ids<=0) or len(set(ids.tolist()))!=len(ids):
  fail('$.locations','1..32 unique positive program identities',m['locations']);return
 if m['time_axes']!={'instant':'times'} or not np.array_equal(a.get('times'),[0.]):fail('$.time_axes','one zero instant',m['time_axes'])
 for group,descriptions,output in [('fields',INPUTS,False),('outputs',OUTPUTS,True)]:
  if set(m[group])!=set(descriptions):fail('$.'+group,'exact DATA field set',list(m[group]));return
  for name,description in descriptions.items():
   if m[group][name]!=spec(name,description,output):fail('$.'+group+'.'+name,str(spec(name,description,output)),m[group][name]);return
 for i in range(len(ids)):
  row={k:a[k][0,i] for k in INPUTS}
  def scalar(k):return float(row[k][0])
  def bad(message):fail(f'$.programs[{i}]',message,{k:v.tolist() for k,v in row.items()})
  integers=['material_kind','positive_count','negative_count','history_count','trial_count','continuation_count']
  if any(scalar(k)!=int(scalar(k)) for k in integers):bad('integer kind/count values');continue
  kind=int(scalar('material_kind'));np_=int(scalar('positive_count'));nn=int(scalar('negative_count'))
  if kind not in (0,1) or not 2<=np_<=7 or not 2<=nn<=7 or (kind==0 and (np_!=nn or np_ not in (2,3))):bad('Hysteretic 2/3 points each with equal counts, or SM 2..7 points each');continue
  good=True
  for side,n,sgn in [('positive',np_,1),('negative',nn,-1)]:
   x=row[side+'_strain'];y=row[side+'_stress'];xx=sgn*x[:n];yy=sgn*y[:n]
   if np.any(x[n:]!=0) or np.any(y[n:]!=0) or np.any(xx<1e-4) or np.any(xx>.1) or np.any(yy<1e3) or np.any(yy>1e9) or np.any(np.diff(xx)<=0) or np.any(np.diff(yy)<=0):good=False;break
   slopes=np.diff(np.r_[0.,yy])/np.diff(np.r_[0.,xx])
   if np.any(np.diff(slopes)>1e-12*np.maximum(slopes[:-1],slopes[1:])):good=False;break
  if not good:bad('bounded strictly increasing signed envelopes with positive nonincreasing segment slopes and zero padding');continue
  if np.any(row['pinching']<.05) or np.any(row['pinching']>1) or not 0<=scalar('beta')<=1:bad('pinching .05..1 and beta 0..1');continue
  nh=int(scalar('history_count'));nt=int(scalar('trial_count'));nc=int(scalar('continuation_count'))
  if not 0<=nh<=8 or not 1<=nt<=8 or not 1<=nc<=8:bad('history 0..8, trials/continuation 1..8');continue
  h=row['history'][:nh];tr=row['trials'][:nt];c=row['continuation'][:nc]
  if np.any(row['history'][nh:]!=0) or np.any(row['trials'][nt:]!=0) or np.any(row['continuation'][nc:]!=0):bad('zero step padding');continue
  lower=row['negative_strain'][nn-1];upper=row['positive_strain'][np_-1]
  steps=np.r_[h,tr,c,scalar('rollback_probe')]
  if np.any(steps<lower) or np.any(steps>upper):bad('all steps within final negative/positive envelope strains');continue
  direction=np.sign(c[0]);committed=h[-1] if nh else 0.;delta=scalar('return_delta');requested=committed+delta
  if direction==0 or (nh and (np.any(direction*h<=0) or np.any(np.diff(np.r_[0.,direction*h])<1e-7))) or abs(delta)>1e-8:
   bad('one nonzero monotonic history direction, step increments >=1e-7 and |delta|<=1e-8');continue
  trigger=abs(requested-committed)<np.finfo(float).eps
  returned=committed if trigger else requested
  if (not trigger and direction*(requested-committed)<0) or direction*returned<0 or np.any(np.diff(np.r_[direction*returned,direction*c])<1e-7):
   bad('nontrigger return and continuation advance along the committed direction by specified minimum steps');continue
  knots=np.r_[row['positive_strain'][:np_],row['negative_strain'][:nn]]
  scored=np.array([committed,returned,c[-1]])
  if any(e!=0 and np.min(abs(knots-e))<1e-7 for e in scored):bad('nonzero scored strains at least 1e-7 from every nonzero backbone knot');continue
