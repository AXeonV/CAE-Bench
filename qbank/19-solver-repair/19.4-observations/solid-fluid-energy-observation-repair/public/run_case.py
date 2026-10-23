"""Construct real MOOSE FE programs and read its native observer CSV."""
import argparse,csv,os,subprocess,tempfile
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem,write_result
APP='/opt/moose-source-2022/modules/navier_stokes/navier_stokes-opt'
ENV='source /environment && export PETSC_DIR=/opt/petsc2022 LIBMESH_DIR=/opt/libmesh2022 LD_LIBRARY_PATH=/opt/libmesh2022/lib:/opt/petsc2022/lib:$LD_LIBRARY_PATH && unset PETSC_ARCH SLEPC_DIR && '
NATIVE={'energy_solid':'energy_0','energy_fluid':'energy_1','advection_power':'advection','source_power':'source','robin_power':'convective_heat_transfer'}
def model_settings(model):
 if model.startswith('explicit-'):
  _,coord,mode,names,_=model.split('-');return dict(program_kind=0,coordinate_system=int(coord=='rz'),ad_mode=int(mode=='ad'),property_name_set=int(names=='renamed'))
 return dict(program_kind=1 if model=='coupled-rz-steady-v1' else 2,coordinate_system=1,ad_mode=1,property_name_set=0)
def number(x):return format(float(x),'.17g')
def quote(x):return "'"+' '.join(str(v) for v in x)+"'"
def block(name,p):return '  ['+name+']\n'+''.join('    '+k+' = '+str(v)+'\n' for k,v in p.items())+'  []\n'
def expression(coeff,terms):return '+'.join('('+number(c)+')*('+t+')' for c,t in zip(coeff,terms))
def coordinates(p):return ['(x/'+number(p['length_x'])+')','(y/'+number(p['length_y'])+')','(z/'+number(p['length_z'])+')' if p['coordinate_system']==0 else '0']
def observations(p,explicit=False):
 execute=quote(['INITIAL','TIMESTEP_END']) if p['program_kind']==2 else ('INITIAL' if explicit else 'TIMESTEP_END')
 s='[Postprocessors]\n'
 for b in [0,1]:
  s+=block('temp_integral_'+str(b),{'type':'ElementIntegralVariablePostprocessor','variable':'T','block':b,'execute_on':execute})
  s+=block('energy_'+str(b),{'type':'LinearCombinationPostprocessor','pp_names':'temp_integral_'+str(b),'pp_coefs':number(p['density_'+('solid' if b==0 else 'fluid')]*p['specific_heat_'+('solid' if b==0 else 'fluid')]),'execute_on':execute})
 cp,rho=('cp','rho') if p['property_name_set']==0 else ('heat_capacity','mass_density')
 s+=block('advection',{'type':'INSADElementIntegralEnergyAdvection' if p['ad_mode'] else 'INSElementIntegralEnergyAdvection','temperature':'T','velocity':'velocity','cp':cp,'rho':rho,'block':1,'execute_on':execute})
 x,y,z=coordinates(p);src='('+expression([p['source_constant'],p['source_radial'],p['source_axial']],['1',x,y])+')*(1+('+number(p['source_time_slope'])+')*t)'
 s+=block('source',{'type':'FunctionElementIntegral','function':quote([src]),'block':0,'execute_on':execute})
 s+=block('convective_heat_transfer',({'type':'Receiver','default':0} if explicit else {'type':'ConvectiveHeatTransferSideIntegral','T_solid':'T','T_fluid':number(p['temperature_reference']),'htc':number(p['heat_transfer_coefficient']),'boundary':'right'})|{'execute_on':execute})
 s+='[]\n[Outputs]\n console = false\n file_base = result\n'+block('csv',{'type':'CSV','precision':17,'execute_on':execute})+'[]\n';return s

def explicit_program(p,arrays):
 rz=p['coordinate_system']==1;lx=p['length_x'];ly=p['length_y'];lz=p['length_z']
 mesh={'type':'GeneratedMeshGenerator','dim':2 if rz else 3,'nx':p['nx'],'ny':p['ny'],'xmax':number(lx),'ymax':number(ly),'elem_type':'QUAD9' if rz else 'HEX27'}
 if not rz:mesh.update(nz=p['nz'],zmax=number(lz))
 s='[Mesh]\n'+block('gen',mesh)+block('split',{'type':'SubdomainBoundingBoxGenerator','input':'gen','bottom_left':quote([number(lx/2),0,0]),'top_right':quote([number(lx),number(ly),number(lz)]),'block_id':1})+(' coord_type = RZ\n' if rz else '')+'[]\n'
 s+='[Variables]\n'+block('dummy',{})+'[]\n[AuxVariables]\n'+block('T',{'order':'SECOND'})+block('velocity',{'order':'SECOND','family':'LAGRANGE_VEC','block':1})+'[]\n'
 x,y,z=coordinates(p);terms=['1',x,y,z,x+'^2',x+'*'+y,x+'*'+z,y+'^2',y+'*'+z,z+'^2']
 T=expression(np.asarray(arrays['temperature_coefficients']).ravel(),terms);u=np.asarray(arrays['velocity_coefficients']).reshape(3,4)
 s+='[ICs]\n'+block('thermal',{'type':'FunctionIC','variable':'T','function':quote([T])})+block('flow',{'type':'VectorFunctionIC','variable':'velocity','block':1,**{'function_'+axis:quote([expression(row,['1',x,y,z])]) for axis,row in zip('xyz',u)}})+'[]\n[Kernels]\n'+block('dummy',{'type':'Reaction','variable':'dummy'})+'[]\n[Materials]\n'
 cp,rho=('cp','rho') if p['property_name_set']==0 else ('heat_capacity','mass_density')
 for b,name in enumerate(['solid','fluid']):s+=block(name,{'type':'ADGenericConstantMaterial' if p['ad_mode'] else 'GenericConstantMaterial','prop_names':quote([cp,rho]),'prop_values':quote([number(p['specific_heat_'+name]),number(p['density_'+name])]),'block':b})
 return s+'[]\n[Executioner]\n type = Steady\n solve_type = NEWTON\n[]\n'+observations(p,True)

def coupled_program(p):
 s=Path(__file__).with_name('thermal_template.i').read_text()
 s=s[:s.index('[Outputs]')]
 s=s.replace('nx = 10','nx = '+str(p['nx'])).replace('ny = 10','ny = '+str(p['ny'])).replace('    dim = 2','    dim = 2\n    elem_type = QUAD9\n    xmax = '+number(p['length_x'])+'\n    ymax = '+number(p['length_y']))
 s=s.replace("bottom_left = '0.5 0 0'",'bottom_left = '+quote([number(p['length_x']/2),0,0])).replace("top_right = '1 1 0'",'top_right = '+quote([number(p['length_x']),number(p['length_y']),0]))
 s=s.replace('  [T][]','  [T]\n    initial_condition = '+number(p['temperature_reference'])+'\n  []')
 s=s.replace('  [velocity]\n','  [velocity]\n    order = '+('FIRST' if p['velocity_order']==1 else 'SECOND')+'\n',1)
 chi='((x-'+number(p['length_x']/2)+')/'+number(p['length_x']/2)+')'
 s=s.replace('    function_y = 1','    function_y = '+quote(['4*('+number(p['inlet_speed'])+')*'+chi+'*(1-'+chi+')']))
 s=s.replace('    T_infinity = 0','    T_infinity = '+number(p['temperature_reference'])).replace('    heat_transfer_coefficient = 1','    heat_transfer_coefficient = '+number(p['heat_transfer_coefficient']))
 x,y,z=coordinates(p);src='('+expression([p['source_constant'],p['source_radial'],p['source_axial']],['1',x,y])+')*(1+('+number(p['source_time_slope'])+')*t)'
 s=s.replace("    function = 'x + y'",'    function = '+quote([src]))
 start=s.index('  [constant]',s.index('[Materials]'));end=s.index('  []',start)+len('  []\n')
 materials=''
 for b,name in enumerate(['solid','fluid']):materials+=block(name,{'type':'ADGenericConstantMaterial','prop_names':quote(['cp','rho','k','mu']),'prop_values':quote([number(p['specific_heat_'+name]),number(p['density_'+name]),number(p['conductivity_'+name]),number(p['viscosity'])]),'block':b})
 s=s[:start]+materials+s[end:]
 if p['program_kind']==2:
  s=s.replace('[Kernels]\n','[Kernels]\n'+block('momentum_time',{'type':'INSADMomentumTimeDerivative','variable':'velocity','block':1})+block('solid_thermal_time',{'type':'ADHeatConductionTimeDerivative','variable':'T','specific_heat':'cp','density_name':'rho','block':0})+block('fluid_thermal_time',{'type':'INSADHeatConductionTimeDerivative','variable':'T','block':1}))
  s=s.replace('  type = Steady','  type = Transient\n  scheme = implicit-euler\n  dt = '+number(p['dt'])+'\n  num_steps = '+str(p['step_count']))
 return s+observations(p)

def prepare(parameters,arrays,directory):
 s=explicit_program(parameters,arrays) if parameters['program_kind']==0 else coupled_program(parameters)
 (directory/'case.i').write_text(s,encoding='utf-8',newline='\n');return s

def extract(directory,p,times):
 with (directory/'result.csv').open() as f:rows=list(csv.DictReader(f))
 if len(rows)!=len(times):raise ValueError('Unexpected native observation row count')
 if p['program_kind']!=1 and not np.allclose([float(r['time']) for r in rows],times,rtol=1e-12,atol=1e-12):raise ValueError('Unexpected native time coordinates')
 return {key:np.array([float(r[col]) for r in rows],dtype=np.float64).reshape(-1,1,1) for key,col in NATIVE.items()}
def run(input_path,output_path):
 problem=load_problem(input_path);p={k:v['value'] for k,v in problem.manifest['physics']['parameters'].items()};p.update(model_settings(problem.manifest['physics']['model']))
 with tempfile.TemporaryDirectory() as tmp:
  d=Path(tmp);prepare(p,problem.arrays,d)
  r=subprocess.run(['/bin/bash','-lc',ENV+'exec '+APP+' -i case.i'],cwd=d,env=os.environ.copy(),capture_output=True,text=True)
  if r.returncode:raise RuntimeError(f'Native MOOSE failed {r.returncode}: {r.stdout[-3000:]} {r.stderr[-3000:]}')
  values=extract(d,p,problem.arrays['times'])
 write_result(output_path,problem,values)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();run(args.input,args.output)
