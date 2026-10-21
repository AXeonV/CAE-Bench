"""Code_Saturne native boundary/setup API stage; no PDE execution."""
import json
from pathlib import Path
from code_saturne import cs_package
from code_saturne.model.XMLengine import Case
from code_saturne.model.LocalizationModel import Zone,LocalizationModel
from code_saturne.model.Boundary import Boundary
from code_saturne.model.SolutionDomainModel import SolutionDomainModel
from code_saturne.model.TimeStepModel import TimeStepModel

root=Path('/work/code-saturne-case-adapter')
case=Case(package=cs_package.package(),file_name='/work/code-saturne-thermodynamic-api-probe/thermodynamic-api-probe.xml')
model=LocalizationModel('BoundaryZone',case)
assert not model.getZones(),'Do not overlap existing mechanical partitions'
for label,kind,value in [('hot_wall','dirichlet',305.),('cold_wall','dirichlet',295.),('adiabatic_walls','neumann',0.)]:
    zone=Zone('BoundaryZone',case,label=label,nature='wall',localization=label)
    model.addZone(zone)
    wall=Boundary('wall',label,case)
    wall.setVelocityChoice('off')
    # Native compressible cfxtcl consumes the temperature field boundary and
    # converts it to cv*T plus the native kinetic/supplementary energy terms.
    # Do not prescribe total_energy=cv*T as a replacement for wall temperature.
    node=wall.boundNode.xmlInitNode('scalar',name='temperature')
    node['type']='model';node['choice']=kind;node.xmlSetData(kind,value)
SolutionDomainModel(case).setMeshInput('/work/code-saturne-case-adapter/mesh_input')
t=TimeStepModel(case);t.setTimePassing(-1);t.setStopCriterion('iterations',5000)
case['xmlfile']=str(root/'study/cavity/DATA/setup.xml');case.xmlSaveDocument()
(root/'boundary-setup.json').write_text(json.dumps({'stage':'Native XML boundary setup and data staging only; no PDE solved.','mechanical':'All actual boundary groups stationary no-slip walls.','thermal':{'hot_wall':{'temperature_K':305.},'cold_wall':{'temperature_K':295.},'adiabatic_walls':{'outward_heat_flux_W_m2':0.}},'native_temperature_mapping':'cfxtcl temperature wall condition performs its own cv*T+kinetic/supplementary energy conversion.','time_passing':t.getTimePassing(),'iteration_cap':5000,'reference_ready':False,'remaining':['Native compressible steady runtime and conservative mass inventory must be confirmed','Define convergence stopping and output extraction before claiming a reference'],'numerical_validation':False},indent=2))
