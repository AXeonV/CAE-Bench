"""Independent polynomial integration and actual-FE interior-point audit.
No target C++ formulas, native CSV adapter, or reference derivative generator is imported.
"""
import csv,hashlib,importlib.util,itertools,json,math,subprocess,sys
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem,load_result
TASK=Path(__file__).resolve().parents[1];ROOT=TASK.parents[3]
DOCKER='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
ENV='source /environment && export PETSC_DIR=/opt/petsc2022 LIBMESH_DIR=/opt/libmesh2022 LD_LIBRARY_PATH=/opt/libmesh2022/lib:/opt/petsc2022/lib:$LD_LIBRARY_PATH && unset PETSC_ARCH SLEPC_DIR && '
APP='/opt/moose-source-2022/modules/navier_stokes/navier_stokes-opt'
def block(name,p):return '  ['+name+']\n'+''.join('    '+k+' = '+str(v)+'\n' for k,v in p.items())+'  []\n'
def quote(x):return "'"+' '.join(str(v) for v in x)+"'"
def rule(n=5):
 g,w=np.polynomial.legendre.leggauss(n);return (g+1)/2,w/2

def exact_explicit(p,t,u,rz):
 g,w=rule();energies=[0.,0.];adv=source=0.;L=np.array([p['length_x'],p['length_y'],p['length_z'] if not rz else 1.]);dim=2 if rz else 3
 for phase in [0,1]:
  for indices in itertools.product(range(len(g)),repeat=dim):
   q=np.zeros(3);wt=1.
   for j,index in enumerate(indices):q[j]=g[index];wt*=w[index]
   q[0]=(phase+q[0])/2;volume=np.prod(L[:dim])/2*wt*(2*math.pi*q[0]*L[0] if rz else 1.);x,y,z=q
   basis=np.array([1,x,y,z,x*x,x*y,x*z,y*y,y*z,z*z]);temperature=t@basis
   energy_density=p['density_'+('solid' if phase==0 else 'fluid')]*p['specific_heat_'+('solid' if phase==0 else 'fluid')]
   energies[phase]+=volume*energy_density*temperature
   if phase:
    gradient=np.array([t[1]+2*t[4]*x+t[5]*y+t[6]*z,t[2]+t[5]*x+2*t[7]*y+t[8]*z,t[3]+t[6]*x+t[8]*y+2*t[9]*z])/L
    velocity=u@np.array([1,x,y,z]);adv+=volume*energy_density*np.dot(velocity,gradient)
   else:source+=volume*(p['source_constant']+p['source_radial']*x+p['source_axial']*y)
 return {'energy_solid':[energies[0]],'energy_fluid':[energies[1]],'advection_power':[adv],'source_power':[source],'robin_power':[0.]}

def augment(text,p):
 order='FIRST' if p['velocity_order']==1 else 'SECOND';local=[.2,.5,.8];nx=p['nx'];ny=p['ny'];lx=p['length_x'];ly=p['length_y']
 text+='\n[AuxVariables]\n'+''.join(block('u'+a,{'order':order,'block':1}) for a in 'xyz')+'[]\n[AuxKernels]\n'+''.join(block('component_'+a,{'type':'VectorVariableComponentAux','variable':'u'+a,'vector_variable':'velocity','component':a,'block':1,'execute_on':"'INITIAL TIMESTEP_END'"}) for a in 'xyz')+'[]\n[VectorPostprocessors]\n'
 for phase in [0,1]:
  pts=[((i+a)*lx/nx,(j+b)*ly/ny,0.) for j in range(ny) for i in range(phase*nx//2,(phase+1)*nx//2) for b in local for a in local]
  text+=block('trace_'+str(phase),{'type':'PointValueSampler','variable':quote(['T','ux','uy','uz']) if phase else 'T','points':quote([format(v,'.17g') for pt in pts for v in pt]),'sort_by':'id','execute_on':"'INITIAL TIMESTEP_END'"})
 pts=[(lx,(j+b)*ly/ny,0.) for j in range(ny) for b in local]
 text+=block('trace_wall',{'type':'PointValueSampler','variable':'T','points':quote([format(v,'.17g') for pt in pts for v in pt]),'sort_by':'id','execute_on':"'INITIAL TIMESTEP_END'"})+'[]\n';return text

def read_csv(path):
 with path.open() as f:return list(csv.DictReader(f))
def audit_fe(directory,p,times):
 # Reconstruct physical Q1/Q2 fields from native point evaluations; no unavailable-node DOF assumption.
 local=np.array([.2,.5,.8]);inv=np.linalg.inv(np.vander(local,3,increasing=True));g,w=rule();nx=p['nx'];ny=p['ny'];dx=p['length_x']/nx;dy=p['length_y']/ny
 expected={k:[] for k in ['energy_solid','energy_fluid','advection_power','source_power','robin_power']}
 allpaths=sorted(directory.glob('result_trace_0_*.csv'))
 if p['program_kind']==1:allpaths=allpaths[-1:]
 for frame,path in enumerate(allpaths):
  tag=path.stem.rsplit('_',1)[1];time=times[frame] if p['program_kind']==2 else 0.;adv=source=0.
  for phase in [0,1]:
   rows=read_csv(directory/f'result_trace_{phase}_{tag}.csv');assert len(rows)==9*nx//2*ny
   E=0.;rhocp=p['density_'+('solid' if phase==0 else 'fluid')]*p['specific_heat_'+('solid' if phase==0 else 'fluid')]
   for k in range(nx//2*ny):
    chunk=rows[k*9:(k+1)*9];ix=k%(nx//2)+phase*nx//2;jy=k//(nx//2)
    # Subtract known constant before polynomial fit to avoid artificial cancellation in a gradient.
    coeff={key:inv@np.array([float(r[key])-(p['temperature_reference'] if key=='T' else 0.) for r in chunk]).reshape(3,3)@inv.T for key in (['T','ux','uy'] if phase else ['T'])}
    for b,wb in zip(g,w):
     yv=np.array([1,b,b*b]);yd=np.array([0,1,2*b]);y=(jy+b)*dy
     for a,wa in zip(g,w):
      xv=np.array([1,a,a*a]);xd=np.array([0,1,2*a]);r=(ix+a)*dx;dv=wa*wb*dx*dy*2*math.pi*r
      T=yv@coeff['T']@xv+p['temperature_reference'];E+=dv*rhocp*T
      if phase:adv+=dv*rhocp*((yv@coeff['ux']@xv)*(yv@coeff['T']@xd)/dx+(yv@coeff['uy']@xv)*(yd@coeff['T']@xv)/dy)
      else:source+=dv*(p['source_constant']+p['source_radial']*r/p['length_x']+p['source_axial']*y/p['length_y'])*(1+p['source_time_slope']*time)
   expected['energy_solid' if phase==0 else 'energy_fluid'].append(E)
  wall=read_csv(directory/f'result_trace_wall_{tag}.csv');assert len(wall)==3*ny;robin=0.
  for j in range(ny):
   c=inv@np.array([float(r['T'])-p['temperature_reference'] for r in wall[3*j:3*j+3]])
   for a,wa in zip(g,w):robin+=wa*dy*2*math.pi*p['length_x']*p['heat_transfer_coefficient']*(c@np.array([1,a,a*a]))
  expected['advection_power'].append(adv);expected['source_power'].append(source);expected['robin_power'].append(robin)
 return expected

def main():
 records=[];image=json.loads(subprocess.check_output([DOCKER,'image','inspect','caeoj-moose22074-prototype:upstream2022']))[0]['Id']
 for case in sorted((TASK/'cases').iterdir()):
  problem=load_problem(case/'problem.json');p={k:v['value'] for k,v in problem.manifest['physics']['parameters'].items()};model=problem.manifest['physics']['model']
  # Read standard result HDF5 through h5py; field records may be SDK-specific wrappers.
  import h5py
  with h5py.File(TASK/'reference'/case.name/'reference.h5') as f:actual={k:np.array(f[k]).ravel() for k in problem.manifest['outputs']}
  if model.startswith('explicit'):
   expected=exact_explicit(p,problem.arrays['temperature_coefficients'].ravel(),problem.arrays['velocity_coefficients'].reshape(3,4),'-rz-' in model);method='independent polynomial exact Gauss rule'
  else:
   p['program_kind']=2 if 'transient' in model else 1;d=ROOT/'runs/authoring/repair-22/moose-22074-field-audit'/case.name;d.mkdir(parents=True,exist_ok=True)
   # Native input already replayed and SHA archived; append only generic existing samplers.
   text=(ROOT/'runs/authoring/repair-22/moose-22074-native-replay/reference'/case.name/'case.i').read_text();text=augment(text,p);(d/'case.i').write_text(text,newline='\n')
   r=subprocess.run([DOCKER,'run','--rm','--network','none','--cpus','2','--memory','4g','--user','1000:1000','--mount',f'type=bind,source={d},target=/job','--workdir','/job','--entrypoint','/bin/bash',image,'-lc',ENV+'exec '+APP+' -i case.i'],capture_output=True,text=True,timeout=120)
   (d/'stdout.log').write_text(r.stdout,newline='\n');(d/'stderr.log').write_text(r.stderr,newline='\n');assert r.returncode==0,(case.name,r.stderr[-3000:]);expected=audit_fe(d,p,problem.arrays['times']);method='native interior point evaluations; independent element polynomial, volume and wall integrations'
  errors={k:float(np.max(abs(actual[k]-np.array(v)))) for k,v in expected.items()};assert all(e<=1e-5+1e-9*max(abs(actual[k])) for k,e in errors.items()),(case.name,errors)
  record={'case':case.name,'method':method,'absolute_errors':errors,'independent_values':expected}
  if not model.startswith('explicit'):
   balance=actual['advection_power']+actual['robin_power']-actual['source_power']
   if 'transient' in model:balance=balance[1:]+np.diff(actual['energy_solid']+actual['energy_fluid'])/p['dt']
   record['native_global_energy_residual_W']=balance.tolist();assert max(abs(balance))<1e-5,(case.name,balance)
  records.append(record);print(case.name,errors,flush=True)
 report={'complete':True,'cases':records,'native_image_id':image,'scope':'Independent observation integrals conditional on actual solved FE fields; not an independent complete temperature/velocity trajectory solution.'};(TASK/'author/data-evidence/independent-audit.json').write_text(json.dumps(report,indent=2)+'\n',newline='\n')
if __name__=='__main__':main()
