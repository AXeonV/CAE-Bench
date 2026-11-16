"""Compare every selected raw source value to the resulting case, without Reader/converter."""
import argparse,importlib.util,json,sys
from pathlib import Path
import numpy as np,h5py,yaml
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'src'))
from utils.PDEBench.sources import open_source
from utils.PDEBench.storage import Budget,NetworkBudget
from caeoj.sdk import load_problem
from caeoj.validation import read_mesh
from caeoj_tools.task_paths import task_directory
spec=importlib.util.spec_from_file_location('inventory',ROOT/'.agents/skills/caeoj-data-review/scripts/inventory.py'); inv=importlib.util.module_from_spec(spec);spec.loader.exec_module(inv)
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-root',type=Path,required=True)
b=parser.parse_args().run_root.resolve();ws=b/'workspace';selection=json.loads((b/'selection.json').read_text());rows=[]
network=NetworkBudget(0);disk=Budget([b],3_000_000_000)
for e in selection['entries']:
 t=task_directory(e['task'],ws);p=load_problem(t/'cases'/e['id']/'problem.json');m=p.manifest;f=e['frames'];cfg={}
 with open_source(e['source'],b/'cache',disk,network=network) as h:
  if e['task']=='compressible-navier-stokes-2d':
   arrays={n:np.asarray(h[k][e['index'],f],dtype=np.float64)[...,None] for n,k in [('density','density'),('pressure','pressure')]}
   arrays['velocity']=np.stack([h[k][e['index'],f] for k in ('Vx','Vy')],axis=-1).astype(np.float64)
   times=np.asarray(h['t-coordinate'][f],dtype=np.float64)
   axes=[np.asarray(h[k],dtype=np.float64) for k in ('x-coordinate','y-coordinate')]
  else:
   g=h[f"{e['index']:04d}"];raw=np.asarray(g['data'][f],dtype=np.float64)
   cfg=yaml.safe_load(g.attrs['config'])
   times=np.asarray(g['grid/t'][f],dtype=np.float64)
   axes=[np.asarray(g['grid'][a],dtype=np.float64) for a in ('x','y')[:m['spatial_dimension']]]
   if e['task']=='reaction-diffusion-2d':raw=raw.transpose(0,2,1,3)
   names={'diffusion-sorption-1d':['concentration'],'reaction-diffusion-2d':['activator','inhibitor'],'shallow-water-2d':['depth']}[e['task']]
   arrays={n:raw[...,j:j+1] for j,n in enumerate(names)}
  with h5py.File(t/'reference'/e['id']/'reference.h5') as r:
   assert np.array_equal(r['times'][:],times)
   for n,a in arrays.items():assert np.array_equal(r[m['outputs'][n]['array']][:],a.reshape(len(f),-1,a.shape[-1])),(e['task'],n)
  initial={n:s for n,s in m['fields'].items() if n.startswith('initial_') and n!='initial_momentum'}
  for n,s in initial.items():
   key=n.removeprefix('initial_');v=p.arrays[s['array']]
   if e['task']=='reaction-diffusion-2d':
    allids=p.arrays['initial_cell_ids']; ids=p.arrays['cell_ids'];pos=np.searchsorted(allids,ids)
    assert np.array_equal(allids[pos],ids)
    assert v.shape==(1,512**2,1)
    assert np.array_equal(v[:,pos,:],arrays[key][0:1].reshape(1,-1,1))
   else:assert np.array_equal(v,arrays[key][0:1].reshape(v.shape))
  mesh=read_mesh(p.path.parent/m['meshes']['main']['file'],geometry=True); dim=m['spatial_dimension']
  ids=p.arrays['cell_ids']
  centers=np.asarray([np.mean([mesh['node_coordinates'][n][:dim] for n in mesh['connectivity'][int(tag)][1]],axis=0) for tag in ids])
  expected=np.stack([a.ravel() for a in np.meshgrid(*axes,indexing='ij')],axis=1)
  assert np.allclose(centers,expected,rtol=0,atol=2e-7),(e['task'],'source coordinate / mesh element ID order')
  if e['task']=='shallow-water-2d':
   assert np.all(p.arrays['initial_momentum']==0)
   xx,yy=np.meshgrid(*axes,indexing='ij');radius=cfg['sim']['dam_radius'] if 'dam_radius' in cfg.get('sim',{}) else cfg.get('sim',{}).get('rad')
   # Published cell values must still form a centered circular 1/2 dam.
   depth=arrays['depth'][0,...,0];rr=xx**2+yy**2
   assert set(np.unique(depth))=={1.,2.}
   assert rr[depth==2].max()<rr[depth==1].min()
   assert arrays['depth'].min()>0
  if e['task']=='diffusion-sorption-1d':assert len(np.unique(p.arrays['initial_concentration']))==1
 rows.append({'task':e['task'],'case':e['id'],'source_id':e['source_id'],'index':e['index'],'frames':f,'times':times.tolist(),'grid_shape':[len(a) for a in axes], 'source_configuration':cfg,'fields':{n:{'shape':list(a.shape),'minimum':float(a.min()),'maximum':float(a.max()),'all_reference_values_equal_source':True} for n,a in arrays.items()},'parameters':m['physics']['parameters'],'conditions':m['conditions'],'input_arrays':{k:{'shape':list(v.shape),'dtype':str(v.dtype)} for k,v in p.arrays.items()},'source_coordinate_order_matches_mesh':True,'initial_matches_source':True,'initial_coverage':('all published initial samples within reconstructed full 512x512 fields; other fine-cell values are reconstruction' if e['task']=='reaction-diffusion-2d' else 'full published initial fields')})
 print(e['task'],e['id'],'source parity passed',flush=True)
(b/'source-audit.json').write_text(json.dumps({'records':rows,'network':network.report(),'scope':'all selected values and initial subset; inherited source discretization; no independent PDE solve'},indent=2)+'\n')
for task in sorted({e['task'] for e in selection['entries']}):
 result=inv.inventory(task_directory(task,ws));assert not result['gaps'];assert result['case_count']==2 and result['sample_count']==1
 (b/f'inventory-{task}.json').write_text(json.dumps(result,indent=2)+'\n')
