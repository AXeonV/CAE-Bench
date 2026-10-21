"""Configure native conservative global-time relaxation to a steady state."""
import json
from pathlib import Path
from code_saturne import cs_package
from code_saturne.model.XMLengine import Case
from code_saturne.model.TimeStepModel import TimeStepModel
from code_saturne.model.SolutionDomainModel import SolutionDomainModel
c=Case(package=cs_package.package(),file_name='/work/native/study/cavity/DATA/setup.xml')
SolutionDomainModel(c).setMeshInput('/work/native/mesh_input')
t=TimeStepModel(c);t.setTimePassing(1);t.setTimeStep(.001);t.setMaxCourant(.5);t.setMaxFourier(10.);t.setTimeStepMaxFactor(1.e9);t.setStopCriterion('iterations',5000)
from code_saturne.model.InitializationModel import InitializationModel
params=json.loads(Path('/work/design.json').read_text())['detailed_spec']['parameters']
i=InitializationModel(c);i.setDensityStatus('1','on');i.setDensityFormula('1','density = '+str(params['mean_density']['value'])+';');i.setTemperatureStatus('1','on');i.setTemperatureFormula('1','temperature = '+str(params['reference_temperature']['value'])+';');i.setPressureStatus('1','off');i.setEnergyStatus('1','off')
c['xmlfile']='/work/native/study/cavity/DATA/setup.xml';c.xmlSaveDocument()
