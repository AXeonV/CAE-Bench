"""Author mechanism adaptations of the genuine third-harmonic source example."""
import argparse,importlib.util,json
from pathlib import Path
import numpy as np
from caeoj.storage import write_hdf5
from caeoj.validation import write_json
TASK=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('dft_contract',TASK/'extension/caeoj_task_ext/dft.py');contract=importlib.util.module_from_spec(spec);spec.loader.exec_module(contract)
def cases():
 base={'length':100.,'resolution':20,'pml_width':1.,'source_frequency':1/3,'envelope_width':60,'source_amplitude':1.,'cutoff':5,'after_sources':150,'chi2':0.,'chi3':.01,'nonlinear_lo':-50.,'nonlinear_hi':50.,'num_chunks':1,'decimation':0}
 raw=[('01-third-harmonic-auto-public',{},'cubic harmonic and source-bandwidth alias; adaptation of original tutorial'),('02-second-harmonic-auto-public',{'chi2':.03,'chi3':0.},'quadratic nonlinearity requires detection independently of cubic'),('03-mixed-nonlinearity',{'chi2':-.01,'chi3':.015,'source_amplitude':.75},'mixed even/odd harmonic phase and negative quadratic coefficient'),('04-local-cubic-three-chunks',{'chi3':.02,'nonlinear_lo':-20.,'nonlinear_hi':10.,'num_chunks':3},'nonlinearity away from source and monitor, spanning genuine serial chunks'),('05-local-quadratic-two-chunks',{'length':60.,'pml_width':2.,'chi2':.02,'chi3':0.,'nonlinear_lo':-20.,'nonlinear_hi':0.,'num_chunks':2,'source_amplitude':-.75,'after_sources':100},'local quadratic material and source polarity through chunk partition'),('06-linear-auto',{'length':40.,'source_frequency':.4,'envelope_width':35,'chi3':0.,'nonlinear_lo':-20.,'nonlinear_hi':20.,'after_sources':60},'zero nonlinearity preserves real automatic stride greater than one'),('07-linear-explicit-one',{'length':40.,'source_frequency':.4,'envelope_width':35,'chi3':0.,'nonlinear_lo':-20.,'nonlinear_hi':20.,'after_sources':60,'decimation':1},'explicit full sampling differs from automatic policy metadata'),('08-cubic-explicit-one',{'length':60.,'resolution':15,'chi3':.02,'nonlinear_lo':-30.,'nonlinear_hi':30.,'decimation':1,'after_sources':100},'explicit full sampling regression at a different Yee timestep'),('09-mixed-explicit-four',{'length':60.,'chi2':.015,'chi3':.005,'nonlinear_lo':-30.,'nonlinear_hi':30.,'decimation':4,'after_sources':100},'explicit decimation must remain requested even for nonlinear fields')]
 for name,changes,meaning in raw:
  params={**base,**changes};n=int(params['length']*params['resolution']);params['monitor_index']=n-int(params['pml_width']*params['resolution'])-int(np.ceil(.5*params['resolution']));yield name,params,meaning
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();catalog=[]
 for i,(name,params,meaning) in enumerate(cases()):
  fc=params['source_frequency'];frequencies=np.linspace(.5*fc,4*fc,49)
  if i in [1,4]:frequencies=np.linspace(.1,.75,49)
  if i==0:frequencies=np.sort(np.r_[frequencies,.7383333333333333])
  q=len(frequencies);point=(2*params['monitor_index']+1-int(params['length']*params['resolution']))/(2*params['resolution']);arrays={'probe_ids':np.arange(q,dtype='int64')*13+7,'probe_coordinates':np.full((q,1),point),'times':np.array([0.]),'frequency':frequencies[None,:,None]};inputs,outputs=contract.descriptions();manifest={'task':TASK.name,'spatial_dimension':1,'data_file':'input.h5','geometries':{},'meshes':{},'conditions':[],'physics':{'model':'finite-window-dft-v1','parameters':{k:{'value':v,'unit':'1'} for k,v in params.items()}},'locations':{'probes':{'kind':'points','ids':'probe_ids','coordinates':'probe_coordinates'}},'time_axes':{'instant':'times'},'fields':inputs,'outputs':outputs};target=a.output/'cases'/name;target.mkdir(parents=True,exist_ok=True);write_json(target/'problem.json',manifest);write_hdf5(target/'input.h5',arrays);catalog.append({'case':name,'meaning':meaning,'frequencies':q,'parameters':params,'origin':'author mechanism adaptation of Meep2408/PR2413 and upstream tests/harmonics.cpp; not claimed original user input'})
 write_json(a.output/'catalog.json',catalog)
