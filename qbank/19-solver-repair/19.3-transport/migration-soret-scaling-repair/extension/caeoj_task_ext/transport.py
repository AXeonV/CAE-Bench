"""Validate the public strip transport declarations; never generate solution fields."""
SIDES={'bottom':1,'right':2,'top':3,'left':4}
E=1.602176634e-19
KB=1.380649e-23

def units(absolute):
 return ('mass_concentration','kg/m3','kg/(m.s.K)') if absolute else ('mass_fraction','1','m2/(s.K)')
def outputs(absolute):
 quantity,unit,_=units(absolute)
 return {name:{'array':name,'quantity':q,'unit':u,'location':'nodes','time_axis':'instant','dtype':'float64','kind':'scalar','component_shape':[1],'components':['value'],'value_kind':'point'} for name,q,u in [('concentration',quantity,unit),('temperature','temperature','K'),('potential','electric_potential','V')]}

def levels(values,tolerance):
 import numpy as np
 result=[]
 for value in sorted(values):
  if not result or value-result[-1]>tolerance:result.append(float(value))
 return np.array(result)

def check(problem,errors):
 import numpy as np
 from caeoj.validation import issue
 from caeoj.sdk import read_constant
 m=problem.manifest;a=problem.arrays
 def fail(path,expected,actual):errors.append(issue('E_STRIP_TRANSPORT',path,expected,str(actual),'Outside the public migration/Soret DATA contract.'))
 if m.get('task')!='migration-soret-scaling-repair' or m['spatial_dimension']!=2 or m.get('physics',{}).get('model')!='steady-migration-soret-strip-v1' or m['geometries'] or m['meshes']!={'main':{'file':'mesh.msh'}} or m['fields']:
  fail('$','one self-contained 2D strip mesh, declared model and no extra fields/geometry',m.get('physics'));return
 p=m['physics']['parameters'];expected={'mode','concentration_units','density','diffusivity','soret_diffusivity','ion_charge'}
 if set(p)!=expected or p.get('mode') not in [{'value':0,'unit':'1'},{'value':1,'unit':'1'}] or p.get('concentration_units') not in [{'value':0,'unit':'1'},{'value':1,'unit':'1'}]:fail('$.physics.parameters','exact DATA options/material parameters',p);return
 absolute=read_constant(p['concentration_units'])==1;mode='migration' if read_constant(p['mode'])==0 else 'soret';_,unit,soret_unit=units(absolute)
 constants={'density':'kg/m3','diffusivity':'m2/s','soret_diffusivity':soret_unit,'ion_charge':'1'}
 for key,u in constants.items():
  if set(p[key])!={'value','unit'} or p[key]['unit']!=u:fail('$.physics.parameters.'+key,'constant with unit '+u,p[key]);return
 rho=read_constant(p['density']);D=read_constant(p['diffusivity']);DT=read_constant(p['soret_diffusivity']);z=read_constant(p['ion_charge'])
 if not .2<=rho<=5000 or not 1e-12<=D<=1e-7 or z!=int(z) or not -3<=z<=3 or abs(DT)/(D*(rho if absolute else 1))>.01:
  fail('$.physics.parameters','density .2..5000, D 1e-12..1e-7, integer charge -3..3 and DATA Soret ratio bound',p);return
 expected_locations={'nodes':{'kind':'mesh','mesh':'main','entity':'node','ids':'node_ids'}}
 expected_locations.update({side:{'kind':'mesh','mesh':'main','entity':'element','dimension':1,'ids':side+'_ids','physical_group':{'dimension':1,'tag':tag}} for side,tag in SIDES.items()})
 if m['locations']!=expected_locations or m['time_axes']!={'instant':'times'} or not np.array_equal(a.get('times'),[0.]):fail('$.locations/time_axes','exact DATA node/boundary locations and one zero instant',m['locations']);return
 if m['outputs']!=outputs(absolute):fail('$.outputs','exact concentration/temperature/potential output descriptions',m['outputs']);return
 bc={};legal=[]
 for variable,u in [('temperature','K'),('potential','V'),('concentration',unit)]:
  for side in ['bottom','top']:
   op='zero_total_diffusive_thermal_flux' if mode=='soret' and variable=='concentration' and side=='top' else 'dirichlet'
   legal.append((variable,side,op,'kg/(m2.s)' if op!='dirichlet' else u))
 if len(m['conditions'])!=6:fail('$.conditions','six boundary declarations',m['conditions']);return
 for c in m['conditions']:
  key=(c['variable'],c['location']);match=[x for x in legal if x[:2]==key]
  if key in bc or len(match)!=1 or c['role']!='boundary' or c['operator']!=match[0][2] or set(c['data'])!={'value'} or set(c['data']['value'])!={'value','unit'} or c['data']['value']['unit']!=match[0][3]:
   fail('$.conditions','exact DATA boundary variables/operators/constant units',c);return
  bc[key]=read_constant(c['data']['value'])
 t0,t1=bc['temperature','bottom'],bc['temperature','top'];phi0,phi1=bc['potential','bottom'],bc['potential','top'];c0,c1=bc['concentration','bottom'],bc['concentration','top'];limit=rho if absolute else 1.
 if not 250<=t0<=700 or not 250<=t1<=700 or abs(t1-t0)>200 or max(abs(phi0),abs(phi1))>1 or abs(phi1-phi0)>.1 or not 0<=c0<=limit:
  fail('$.conditions','DATA temperature/potential bounds and physical concentration range',bc);return
 if mode=='migration':
  if t0!=t1 or DT!=0 or not 0<=c1<=limit or abs(z*E*(phi1-phi0)/(KB*t0))>3:fail('$.conditions','isothermal migration, DT=0, |a|<=3 and 0<=end concentrations<=unit scale',bc);return
 else:
  end=c0-DT/D*(t1-t0)
  if z!=0 or phi0!=phi1 or c1!=0 or end < -1e-12*limit or end>limit*(1+1e-12):fail('$.conditions','Soret z=0, constant potential, zero total top flux, 0<=profile<=unit scale with roundoff allowance',bc);return
 mesh=problem.meshes['main'];ids=a['node_ids']
 if set(map(int,ids))!=mesh['nodes'] or mesh['dimension']!=2 or set(mesh['groups'])!={(2,1),*[(1,t) for t in SIDES.values()]} or mesh['groups'][2,1]['elements']!=mesh['elements'][2]:fail('$.meshes','all nodes and QUAD4 body physical group 2/1; four boundary groups',mesh['groups'].keys());return
 if 'node_coordinates' not in mesh:raise RuntimeError('Task SDK requires installed geometry support')
 xy=np.array([mesh['node_coordinates'][int(tag)][:2] for tag in ids]);low=xy.min(axis=0);size=xy.max(axis=0)-low;W,L=size;tol=1e-9*min(W,L)
 if not 1e-4<=L<=.05 or not .05<=W/L<=.2 or np.any(abs(xy)>1):fail('$.meshes','length1e-4..05m, width/length .05...2, coordinates within1m',size);return
 xs=levels(xy[:,0],tol);ys=levels(xy[:,1],tol);nx,ny=len(xs)-1,len(ys)-1
 if not 1<=nx<=3 or not 100<=ny<=400 or len(ids)!=(nx+1)*(ny+1) or np.max(abs(np.diff(xs)-W/nx))>1e-8*W/nx or np.max(abs(np.diff(ys)-L/ny))>1e-8*L/ny:
  fail('$.meshes','complete uniform grid nx1..3, ny100..400', [nx,ny,len(ids)]);return
 index={int(tag):i for i,tag in enumerate(ids)};grid={int(tag):(int(np.argmin(abs(xs-xy[i,0]))),int(np.argmin(abs(ys-xy[i,1])))) for i,tag in enumerate(ids)}
 if len(set(grid.values()))!=len(ids):fail('$.meshes','one node per structured grid point','duplicate positions');return
 cells=set();edges={}
 for tag in mesh['elements'][2]:
  kind,nodes=mesh['connectivity'][tag];points=np.array([xy[index[x]] for x in nodes]);g=np.array([grid[x] for x in nodes]);cell=tuple(g.min(axis=0))
  local=points-points[0];area=np.sum(local[:,0]*np.roll(local[:,1],-1)-local[:,1]*np.roll(local[:,0],-1))
  if kind!=3 or area<=0 or cell in cells or set(map(tuple,g))!={(cell[0],cell[1]),(cell[0]+1,cell[1]),(cell[0]+1,cell[1]+1),(cell[0],cell[1]+1)}:fail('$.meshes','one CCW QUAD4 per structured cell',tag);return
  cells.add(cell)
  for j in range(4):edges.setdefault(frozenset((nodes[j],nodes[(j+1)%4])),[]).append(tag)
 if len(cells)!=nx*ny or cells!={(i,j) for i in range(nx) for j in range(ny)}:fail('$.meshes','complete rectangular cells',len(cells));return
 all_boundary=set()
 for side,tag in SIDES.items():
  for edge in mesh['groups'][1,tag]['elements']:
   kind,nodes=mesh['connectivity'][edge];g=np.array([grid[x] for x in nodes]);axis,level=(1,0) if side=='bottom' else (1,ny) if side=='top' else (0,0) if side=='left' else (0,nx)
   if kind!=1 or len(edges.get(frozenset(nodes),[]))!=1 or np.any(g[:,axis]!=level):fail('$.meshes','boundary LINE2 matches declared strip side',edge);return
   all_boundary.add(frozenset(nodes))
 if all_boundary!={edge for edge,parents in edges.items() if len(parents)==1} or set(mesh['elements'][1])!=set().union(*(mesh['groups'][1,t]['elements'] for t in SIDES.values())):fail('$.meshes','exact exterior boundary edges','uncovered or extra lines')
