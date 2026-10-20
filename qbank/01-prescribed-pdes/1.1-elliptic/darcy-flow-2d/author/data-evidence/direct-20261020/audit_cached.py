"""Audit existing five-file Darcy payloads; zero admitted network, no solves."""
import hashlib,json,sys
from pathlib import Path
import h5py,numpy as np
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--repo',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
ROOT=args.repo.resolve();sys.path.insert(0,str(ROOT/'src'))
from utils.PDEBench.sources import open_source
from utils.PDEBench.storage import Budget,NetworkBudget,atomic_json
b=args.output.resolve();b.mkdir(parents=True,exist_ok=True);cache=ROOT/'runs/pdebench/cache';catalog=json.loads((ROOT/'src/utils/PDEBench/catalog.json').read_text());net=NetworkBudget(0);records=[]
for source in sorted((s for s in catalog['files'] if s['id'] in range(133217,133222)),key=lambda s:s['id']):
 with open_source(source,cache,Budget([cache],20_000_000_000),network=net) as h:
  beta=float(h.attrs['beta']);assert beta==float(source['filename'].split('beta')[1].split('_')[0])
  layout={k:{'shape':list(h[k].shape),'dtype':str(h[k].dtype)} for k in h}
  coords=[np.asarray(h[a+'-coordinate']) for a in 'xy'];assert all(np.array_equal(c,(np.arange(128)+.5)/128) for c in coords)
  assert h['tensor'].shape==(10000,1,128,128) and h['nu'].shape==(10000,128,128)
  source_times=h['t-coordinate'][...].tolist() if 't-coordinate' in h else None
  paths=sorted((cache/'selections'/str(source['id'])).glob('*-9.h5'));assert paths
  p=paths[0];cert=json.loads(p.with_suffix('.json').read_text());assert cert['source']==source and hashlib.sha256(p.read_bytes()).hexdigest()==cert['sha256']
  with h5py.File(p) as selected:
   a=selected['diffusivity'][...];u=selected['state'][...];assert a.shape==u.shape==(1,128,128,1);assert np.isfinite(a).all() and np.isfinite(u).all();assert np.all(np.isclose(a,.1,rtol=0,atol=1e-7)|np.isclose(a,1,rtol=0,atol=1e-7))
   assert int(selected.attrs['source_id'])==source['id'];index=int(selected.attrs['sample_index'])
   for axis,c in zip('xy',coords):assert np.array_equal(c,selected[axis+'-coordinate'][...])
   raw_a=np.asarray(h['nu'][index]) if index==0 else None
   if raw_a is not None:assert np.allclose(raw_a,a[0,:,:,0],rtol=0,atol=1e-7)
   records.append({'source':source,'beta_attribute':beta,'layout':layout,'source_t_coordinate':source_times,'output_time_semantics':'steady placeholder [0.0], not source transient initial frame','cached_payload':str(p.relative_to(ROOT)),'payload_sha256':cert['sha256'],'source_index':index,'selected_state_range':[float(u.min()),float(u.max())],'coefficient_values':np.unique(a).tolist(),'grid':{'shape':[128,128],'first_center':float(coords[0][0]),'last_center':float(coords[0][-1]),'axis_order':'x,y, inferred from pinned generator; hdf5 has no dimension labels'},'integrity_scope':'pre-existing selected payload SHA and provenance receipt; source header/coordinates from certified range cache; not a fresh remote byte reread or full-source MD5'})
atomic_json(b/'source-audit.json',{'status':'passed_for_examined_cached_samples','samples':5,'records':records,'network':net.report(),'no_pde_solve':True,'no_reference_change':True,'no_precision_filter':True,'limitations':['Published HDF5 does not identify exact generator commit or certify convergence.','Residual/convergence screening not performed.','Array layout does not independently prove point values versus cell averages; finite-volume cell observation is the retained task convention.']})
print('5 files / 5 cached samples; zero network; no reference changed')
