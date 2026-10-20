"""Darcy contract and unchanged source target, no numerical reference generation."""
import sys,tempfile,unittest
from pathlib import Path
import h5py,numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from utils.PDEBench.models import BY_TASK
from utils.PDEBench.sources import Reader
from utils.PDEBench.conversion import build_input
from utils.PDEBench.checks import source_geometry,source_reference
from utils.PDEBench.storage import PreparationError

class DarcyTests(unittest.TestCase):
 def test_zero_boundary_and_unconverged_published_values_retained(self):
  model=BY_TASK['darcy-flow-2d'];coords=[(np.arange(128)+.5)/128]*2
  # Deliberately not an elliptic solution: source fidelity must not turn into screening.
  state=np.linspace(-3,7,128*128).reshape(1,128,128,1)
  values={'state':state,'diffusivity':np.ones_like(state)}
  source={'filename':'2D_DarcyFlow_beta0.01_Train.hdf5'}
  with tempfile.TemporaryDirectory() as tmp:
   problem=build_input(model,source,coords,np.array([0.]),values,Path(tmp),1)
   boundaries=[c for c in problem.manifest['conditions'] if c['role']=='boundary']
   self.assertEqual({c['location'] for c in boundaries},{'left','right','bottom','top'})
   self.assertTrue(all(c['operator']=='dirichlet' and c['data']=={'value':{'value':0,'unit':'1'}} for c in boundaries))
   arrays,evidence=source_reference(model,problem,values,{'beta':.01})
   np.testing.assert_array_equal(arrays['state'],state.reshape(1,-1,1))
   self.assertEqual(evidence['blocked'],[]);self.assertFalse(evidence['continuum_error_certified'])
   self.assertTrue(any('convergence' in s for s in evidence['limitations']))
   source_geometry(model,source,coords,np.array([0.]),{'beta':.01})
   with self.assertRaisesRegex(PreparationError,'differs'):
    source_geometry(model,source,coords,np.array([0.]),{'beta':.1})
   with self.assertRaisesRegex(PreparationError,'differs'):
    source_reference(model,problem,values,{'beta':.1})
 def test_actual_attribute_required_and_source_axes_not_transposed(self):
  model=BY_TASK['darcy-flow-2d']
  with tempfile.TemporaryDirectory() as tmp:
   with h5py.File(Path(tmp)/'s.h5','w') as h:
    x=(np.arange(128)+.5)/128
    h['x-coordinate']=x;h['y-coordinate']=x;h['nu']=np.full((1,128,128),.1,dtype='f4')
    a=np.arange(128*128,dtype='f4').reshape(1,1,128,128);h['tensor']=a
    # A leftover allocation time vector must not label steady output as transient t=0.
    h['t-coordinate']=np.arange(10)*.25
    reader=Reader(h,model)
    for invalid in (None,[1.],float('nan'),2.):
     if 'beta' in h.attrs:del h.attrs['beta']
     if invalid is not None:h.attrs['beta']=invalid
     with self.assertRaisesRegex(PreparationError,'beta'):reader.metadata()
    h.attrs['beta']=1.
    coords,times,config=reader.metadata();self.assertEqual(config,{'beta':1.});np.testing.assert_array_equal(times,[0.])
    values=reader.values(0,[0]);np.testing.assert_array_equal(values['state'][...,0],a[0])
    self.assertTrue(np.all(values['diffusivity']==.1))

if __name__=='__main__':unittest.main()
