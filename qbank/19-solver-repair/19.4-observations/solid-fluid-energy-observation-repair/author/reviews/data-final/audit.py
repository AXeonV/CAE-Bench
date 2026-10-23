import csv,copy,hashlib,itertools,json,math,shutil,tarfile,zipfile
from pathlib import Path
import h5py,numpy as np
from caeoj.sdk import load_problem
from caeoj import runtime
from caeoj.validation import validate_input,validate_output
from caeoj.case_grading import grade_case
R=Path(__file__).resolve().parents[3]; T=R/'qbank/19-solver-repair/19.4-observations/solid-fluid-energy-observation-repair'; O=Path(__file__).parent
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def readh(p):
 with h5py.File(p) as f:return {k:f[k][()] for k in f}
def writeh(p,a):
 with h5py.File(p,'w') as f:
  for k,v in a.items():f[k]=v
def csvread(p):
 with p.open() as f:return list(csv.DictReader(f))
names=['energy_solid','energy_fluid','advection_power','source_power','robin_power']
g,w=np.polynomial.legendre.leggauss(4);g=(g+1)/2;w=w/2
def explicit(p,a,rz):
 # Tensor polynomial arithmetic and monomial antiderivatives, no production formula calls.
 dim=2 if rz else 3; L=[p['length_x'],p['length_y'],p['length_z']]; coeff=a['temperature_coefficients'].ravel(); vel=a['velocity_coefficients'].reshape(3,4)
 exps=[(0,0,0),(1,0,0),(0,1,0),(0,0,1),(2,0,0),(1,1,0),(1,0,1),(0,2,0),(0,1,1),(0,0,2)]
 temp=dict(zip(exps,coeff)); adv={}
 for j in range(dim):
  for e,c in temp.items():
   if e[j]==0:continue
   de=list(e);de[j]-=1
   for z,v in enumerate(vel[j]):
    q=de.copy()
    if z:q[z-1]+=1
    q=tuple(q);adv[q]=adv.get(q,0)+c*e[j]/L[j]*v
 def integ(poly,phase):
  total=0
  for e,c in poly.items():
   if rz and e[2]:continue
   powers=list(e)
   if rz:powers[0]+=1
   value=c
   for j in range(dim):
    lo,hi=(phase/2,(phase+1)/2) if j==0 else (0,1)
    value*=L[j]*(hi**(powers[j]+1)-lo**(powers[j]+1))/(powers[j]+1)
   if rz:value*=2*math.pi*L[0]
   total+=value
  return total
 src={(0,0,0):p['source_constant'],(1,0,0):p['source_radial'],(0,1,0):p['source_axial']}
 return dict(zip(names,[[p['density_solid']*p['specific_heat_solid']*integ(temp,0)],[p['density_fluid']*p['specific_heat_fluid']*integ(temp,1)],[p['density_fluid']*p['specific_heat_fluid']*integ(adv,1)],[integ(src,0)],[0.]]))
def coupled(c,p,times):
 d=R/'runs/authoring/repair-22/moose-22074-field-audit'/c; paths=sorted(d.glob('result_trace_0_*.csv'))
 if 'steady' in c:paths=paths[-1:]
 assert len(paths)==len(times)
 out={k:[] for k in names}; fitmax=0;coordmax=0
 dx=p['length_x']/p['nx'];dy=p['length_y']/p['ny'];nr=p['nx']//2
 for fi,path in enumerate(paths):
  tag=path.stem.rsplit('_',1)[1];qadv=qsrc=0
  for phase in [0,1]:
   rows=csvread(d/f'result_trace_{phase}_{tag}.csv');assert len(rows)==9*nr*p['ny'];energy=0
   for cell in range(nr*p['ny']):
    ix=cell%nr+phase*nr;iy=cell//nr;chunk=rows[cell*9:cell*9+9]
    xy=np.array([[(float(r['x'])/dx-ix),(float(r['y'])/dy-iy)] for r in chunk]); expected=np.array(list(itertools.product([.2,.5,.8],repeat=2)))[:,::-1];coordmax=max(coordmax,float(abs(xy-expected).max()))
    co={}
    for field in ['T']+(['ux','uy','uz'] if phase else []):
     order=1 if field=='T' else p['velocity_order']; powers=list(itertools.product(range(order+1),repeat=2));A=np.array([[x**i*y**j for i,j in powers] for x,y in xy]);v=np.array([float(r[field])-(p['temperature_reference'] if field=='T' else 0) for r in chunk]);b=np.linalg.lstsq(A,v,rcond=None)[0];fitmax=max(fitmax,float(abs(A@b-v).max()));co[field]=(powers,b)
    def val(field,x,y,der=None):
     powers,b=co[field];s=0
     for (i,j),z in zip(powers,b):
      if der==0:
       if i:s+=z*i*x**(i-1)*y**j/dx
      elif der==1:
       if j:s+=z*j*x**i*y**(j-1)/dy
      else:s+=z*x**i*y**j
     return s
    cap=p['density_'+('fluid' if phase else 'solid')]*p['specific_heat_'+('fluid' if phase else 'solid')]
    for x,wx in zip(g,w):
     for y,wy in zip(g,w):
      radius=(ix+x)*dx;dv=2*math.pi*radius*dx*dy*wx*wy;energy+=dv*cap*(val('T',x,y)+p['temperature_reference'])
      if phase:qadv+=dv*cap*(val('ux',x,y)*val('T',x,y,0)+val('uy',x,y)*val('T',x,y,1))
      else:qsrc+=dv*(p['source_constant']+p['source_radial']*radius/p['length_x']+p['source_axial']*(iy+y)*dy/p['length_y'])*(1+p['source_time_slope']*times[fi])
   out['energy_fluid' if phase else 'energy_solid'].append(energy)
  wall=csvread(d/f'result_trace_wall_{tag}.csv');assert len(wall)==3*p['ny'];robin=0
  for j in range(p['ny']):
   chunk=wall[3*j:3*j+3];yy=np.array([float(r['y'])/dy-j for r in chunk]);v=np.array([float(r['T'])-p['temperature_reference'] for r in chunk]);b=np.linalg.lstsq(np.stack([np.ones(3),yy],axis=1),v,rcond=None)[0];assert abs(np.stack([np.ones(3),yy],axis=1)@b-v).max()<1e-9
   robin+=2*math.pi*p['length_x']*dy*p['heat_transfer_coefficient']*(b[0]+b[1]/2)
  for key,value in [('advection_power',qadv),('source_power',qsrc),('robin_power',robin)]:out[key].append(value)
 assert coordmax<1e-12 and fitmax<1e-9
 return out,{'fit_error':fitmax,'point_coordinate_error':coordmax}
records=[]
assert runtime.descriptor()['id']!='core-only','Run with the frozen normally installed task package, not bare development core.'
for c in sorted((T/'cases').iterdir()):
 m=json.loads((c/'problem.json').read_text());a=readh(c/'input.h5');p={k:v['value'] for k,v in m['physics']['parameters'].items()};ref=T/'reference'/c.name/'reference.h5';actual=readh(ref)
 assert validate_input(c/'problem.json')['valid'];assert validate_output(c/'problem.json',ref)['valid'];assert set(a)=={'experiment_ids','initial_time','times','temperature_coefficients','velocity_coefficients'};assert set(actual)==set(names+['experiment_ids','times']);assert actual['experiment_ids'].dtype==np.int64;assert np.array_equal(a['experiment_ids'],[1]);assert np.array_equal(a['initial_time'],[0.]);assert np.array_equal(a['times'],actual['times'])
 model=m['physics']['model'];stats={}
 expected=explicit(p,a,'-rz-' in model) if model.startswith('explicit') else None
 if expected is None:expected,stats=coupled(c.name,p,a['times'])
 errs={k:float(abs(actual[k].ravel()-expected[k]).max()) for k in names};assert all(np.all(abs(actual[k].ravel()-expected[k])<=1e-5+1e-9*abs(actual[k].ravel())) for k in names)
 score=grade_case(c/'problem.json',ref,T/'reference'/c.name/'grading.json');assert score['score']==1,score
 if not model.startswith('explicit'):
  balance=np.array(expected['advection_power'])+expected['robin_power']-np.array(expected['source_power'])
  if 'transient' in model:balance=balance[1:]+np.diff(np.array(expected['energy_solid'])+expected['energy_fluid'])/p['dt']
  stats['independent_energy_balance_W']=balance.tolist();assert abs(balance).max()<1e-5
 records.append({'case':c.name,'model':model,'parameters':p,'input':{k:{'dtype':str(v.dtype),'shape':list(v.shape),'values':v.tolist()} for k,v in a.items()},'expected':expected,'errors':errs,'stats':stats,'grading_status':score['status']})
for s in sorted((T/'samples').iterdir()):
 assert validate_input(s/'input/problem.json')['valid'];assert validate_output(s/'input/problem.json',s/'output/result.h5')['valid']
 assert grade_case(s/'input/problem.json',s/'output/result.h5',s/'reference/grading.json')['score']==1
(O/'data-math.json').write_text(json.dumps({'cases':records,'samples':2,'runtime_descriptor':runtime.descriptor(),'method':'Fresh monomial antiderivatives; coupled physical-coordinate Q1/Q2 least squares and 4x4 tensor Gauss; no author numerical code imported.'},indent=2)+'\n')
print('DATA_MATH_PASS',len(records),flush=True)
