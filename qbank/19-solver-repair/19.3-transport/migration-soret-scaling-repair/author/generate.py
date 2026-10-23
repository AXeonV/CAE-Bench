"""Generate distinct real-mesh transport inputs with explicit unit-mode comparisons."""
import sys,json
from pathlib import Path
import numpy as np
from caeoj.storage import write_hdf5
from caeoj.validation import write_json
from mesh import generate,SIDES
TASK=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(TASK/'extension'))
from caeoj_task_ext.transport import outputs,units
CASES=[
 ('01-migration-relative-public','migration',False,1200.,1e-9,0.,1,298.15,298.15,0.,.05,1.,0.,1,400,.001,(0.,0.),False,'M1'),
 ('02-soret-absolute-public','soret',True,1000.,1e-9,5e-6,0,300.,400.,0.,0.,.001,None,1,400,.001,(0.,0.),False,'S1'),
 ('03-migration-absolute-pair','migration',True,1200.,1e-9,0.,1,298.15,298.15,0.,.05,1.,0.,1,400,.001,(0.,0.),False,'M1'),
 ('04-soret-relative-pair','soret',False,1000.,1e-9,5e-6,0,300.,400.,0.,0.,.001,None,1,400,.001,(0.,0.),False,'S1'),
 ('05-negative-ion-low-density','migration',False,.2,3e-9,0.,-2,450.,450.,.1,.12,.3,.8,2,320,.0008,(.01,-.02),False,None),
 ('06-unit-density-active-migration','migration',True,1.,2e-9,0.,2,320.,320.,.2,.17,.5,.05,2,240,.002,(0.,0.),False,None),
 ('07-negative-soret-cooling','soret',False,1.,2e-10,-.004,0,400.,360.,.1,.1,.25,None,2,300,.003,(0.,0.),False,None),
 ('08-negative-soret-warming','soret',True,250.,3e-9,-.003,0,300.,380.,-.1,-.1,.1,None,3,280,.006,(0.,0.),False,None),
 ('09-zero-ion-diffusion-control','migration',True,3.,3e-10,0.,0,500.,500.,.25,.30,.1,.9,3,200,.004,(.2,-.3),False,None),
 ('10-zero-soret-control','soret',False,.5,5e-10,0.,0,290.,350.,.2,.2,.4,None,2,160,.002,(.1,.1),False,None),
 ('11-weak-drive-dense-fluid','migration',False,5000.,7e-10,0.,1,298.15,298.15,0.,.0001,.7,.2,1,300,.005,(-.2,-.1),True,None),
 ('12-low-density-absolute-soret','soret',True,.2,8e-9,.003,0,280.,360.,0.,0.,.6,None,3,400,.012,(-.1,.2),True,None)]
def main():
 records=[]
 for name,mode,absolute,rho,D,gamma,z,t0,t1,phi0,phi1,y0,y1,nx,ny,L,origin,sparse,pair in CASES:
  directory=TASK/'cases'/name;mesh=generate(directory,width=L*.1,length=L,nx=nx,ny=ny,origin=origin,sparse=sparse)
  ids=np.array(sorted(mesh['nodes']),dtype='int64');arrays={'node_ids':ids,'times':np.array([0.])}
  locations={'nodes':{'kind':'mesh','mesh':'main','entity':'node','ids':'node_ids'}}
  for side,tag in SIDES.items():
   arrays[side+'_ids']=np.array(sorted(mesh['groups'][1,tag]['elements']),dtype='int64');locations[side]={'kind':'mesh','mesh':'main','entity':'element','dimension':1,'ids':side+'_ids','physical_group':{'dimension':1,'tag':tag}}
  scale=rho if absolute else 1.;_,unit,soret_unit=units(absolute)
  constant=lambda value,u:{'value':value,'unit':u}
  params={'mode':constant(0 if mode=='migration' else 1,'1'),'concentration_units':constant(1 if absolute else 0,'1'),'density':constant(rho,'kg/m3'),'diffusivity':constant(D,'m2/s'),'soret_diffusivity':constant(gamma*D*scale,soret_unit),'ion_charge':constant(z,'1')}
  conditions=[]
  for variable,u,bottom,top in [('temperature','K',t0,t1),('potential','V',phi0,phi1),('concentration',unit,y0*scale,y1*scale if y1 is not None else None)]:
   for side,value in [('bottom',bottom),('top',top)]:
    natural=value is None
    conditions.append({'role':'boundary','variable':variable,'location':side,'operator':'zero_total_diffusive_thermal_flux' if natural else 'dirichlet','data':{'value':constant(0. if natural else value,'kg/(m2.s)' if natural else u)}})
  manifest={'task':'migration-soret-scaling-repair','spatial_dimension':2,'data_file':'input.h5','geometries':{},'meshes':{'main':{'file':'mesh.msh'}},'locations':locations,'time_axes':{'instant':'times'},'fields':{},'outputs':outputs(absolute),'physics':{'model':'steady-migration-soret-strip-v1','parameters':params},'conditions':conditions}
  write_json(directory/'problem.json',manifest);write_hdf5(directory/'input.h5',arrays)
  records.append({'case':name,'mode':mode,'units':'absolute_mass' if absolute else 'relative_mass','density':rho,'diffusivity':D,'soret_ratio_in_mass_fraction_per_K':gamma,'charge':z,'bottom_temperature_K':t0,'top_temperature_K':t1,'bottom_potential_V':phi0,'top_potential_V':phi1,'bottom_mass_fraction':y0,'top_mass_fraction':y1 if y1 is not None else y0-gamma*(t1-t0),'nx':nx,'ny':ny,'length_m':L,'nodes':len(ids),'physical_unit_pair':pair,'sparse_tags':sparse,'origin':'author adaptation of fixed issue870/PR872 source mechanisms; upstream unmodified original replays archived separately'})
 write_json(TASK/'author/data-evidence/cases.json',records)
if __name__=='__main__':main()
