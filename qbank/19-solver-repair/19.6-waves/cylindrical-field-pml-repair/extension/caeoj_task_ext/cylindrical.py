"""Public declarations for cylindrical vacuum FDTD; never compute fields or flux."""
import numpy as np
TASK='cylindrical-field-pml-repair';MODEL='cylindrical-vacuum-pml-v1'
PARAMETERS={'radius','half_height','radial_pml','axial_pml','resolution','mode','source_amplitude'}
INTEGERS=PARAMETERS-{'source_amplitude'}
def locations():
 return {'faces':{'kind':'mesh','mesh':'observation','entity':'element','dimension':1,'ids':'face_ids'},'field_probe':{'kind':'points','ids':'probe_ids','coordinates':'probe_coordinates'}}
def descriptions():
 def spec(name,quantity,components,location,value_kind='point'):
  return {'array':name,'quantity':quantity,'unit':'1','location':location,'time_axis':'instant','dtype':'float64','kind':'scalar' if len(components)==1 else 'components','component_shape':[len(components)],'components':components,'value_kind':value_kind}
 return {},{'spectral_flux':spec('spectral_flux','normalized_spectral_surface_flux',['value'],'faces','integral'),'observed_dft':spec('observed_dft','normalized_centered_finite_dft',[c+'_'+part for c in ['Er','Ephi','Ez','Hr','Hphi','Hz'] for part in ['real','imag']],'field_probe'),'time_step':spec('time_step','normalized_time_step',['value'],'field_probe'),'window_end':spec('window_end','normalized_window_end',['value'],'field_probe')}
def check(problem,errors):
 from caeoj.validation import issue,read_mesh,resolve_file
 m=problem.manifest;a=problem.arrays
 def fail(path,expected,actual):errors.append(issue('E_CYL_PML',path,expected,actual,'Outside the public cylindrical vacuum PML DATA contract.'))
 physics=m.get('physics',{});par=physics.get('parameters',{})
 if m.get('task')!=TASK or m['spatial_dimension']!=2 or physics.get('model')!=MODEL or set(par)!=PARAMETERS:
  fail('$.physics','exact cylindrical model and parameters',physics);return
 v={}
 for n,item in par.items():
  if set(item)!={'value','unit'} or item.get('unit')!='1' or type(item.get('value')) not in (int,float) or not np.isfinite(item['value']) or n in INTEGERS and type(item['value']) is not int:
   fail('$.physics.parameters.'+n,'finite normalized scalar; specified integers are JSON integers',item);return
  v[n]=item['value']
 for n,allowed in {'radius':(2,3),'half_height':(1,2),'radial_pml':(1,2),'axial_pml':(1,2),'resolution':(30,40),'mode':(-1,1)}.items():
  if v[n] not in allowed:fail('$.physics.parameters.'+n,str(allowed),v[n])
 if not .25<=abs(v['source_amplitude'])<=1:fail('$.physics.parameters.source_amplitude','absolute amplitude .25..1',v['source_amplitude'])
 if errors:return
 if m['geometries'] or m['conditions'] or m['meshes']!={'observation':{'file':'surfaces.msh'}}:fail('$.meshes','only observation surfaces.msh, no conditions/geometries',m['meshes']);return
 if m['locations']!=locations() or m['time_axes']!={'instant':'times'} or not np.array_equal(a.get('times'),[0.]):fail('$.locations','exact faces and field_probe with one zero static label',m['locations']);return
 inputs,outputs=descriptions()
 if m['fields']!=inputs or m['outputs']!=outputs:fail('$.fields/outputs','exact empty input fields and four declared outputs',m['outputs']);return
 if set(a)!={'face_ids','probe_ids','probe_coordinates','times'} or not np.array_equal(a['face_ids'],[11,17,23]) or not np.array_equal(a['probe_ids'],[7]):fail('$.data_file','exact arrays and ordered fixed observation IDs',list(a));return
 res=v['resolution'];point=np.array([[(2*res+1)*(.5/res),.5/res]])
 if not np.array_equal(a['probe_coordinates'],point):fail('$.locations.field_probe','canonical centered point coordinates',a['probe_coordinates'])
 mesh=read_mesh(resolve_file(problem.path.parent,'surfaces.msh','.msh'),geometry=True);R=v['radius'];Z=v['half_height'];nodes={1:(0,Z,0),2:(R,Z,0),3:(R,-Z,0),4:(0,-Z,0)}
 if mesh['nodes']!=set(nodes) or any(not np.array_equal(mesh['node_coordinates'][n],xyz) for n,xyz in nodes.items()):fail('$.meshes.observation','four exact mother-line endpoints',mesh['node_coordinates']);return
 points=[row[1][0] for row in mesh['connectivity'].values() if row[0]==15]
 if len(points)!=len(set(points)):fail('$.meshes.observation','at most one optional type15 element per node',points)
 lines={tag:row for tag,row in mesh['connectivity'].items() if row[0]!=15}
 if lines!={11:(1,(1,2)),17:(1,(2,3)),23:(1,(3,4))}:fail('$.meshes.observation','three oriented Gmsh type1 observation lines',lines)
