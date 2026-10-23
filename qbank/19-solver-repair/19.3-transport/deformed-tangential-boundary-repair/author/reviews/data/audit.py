"""Independent full payload and raw solver audit; does not execute solvers."""
import json, math, hashlib, sys, copy
from pathlib import Path
import numpy as np
import h5py
ROOT=Path(__file__).resolve().parents[3]
TASK=ROOT/'qbank/19-solver-repair/19.3-transport/deformed-tangential-boundary-repair'
WORK=ROOT/'work/repair-22/aspect-6818'
OUT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(TASK/'extension'))
from caeoj.sdk import load_problem, load_result, write_result
from caeoj_task_ext.deformed_tangential import check
report={'inputs':{},'native':{},'elmer':{},'convergence':{},'variants':{}}
def arrays(f):
 with h5py.File(f) as h:
  assert not h.attrs
  for k in h:
   a=h[k];assert isinstance(a,h5py.Dataset) and not a.attrs and not a.is_virtual and not a.external
   assert isinstance(h.get(k,getlink=True),h5py.HardLink)
   assert a.compression in (None,'gzip') and a.scaleoffset is None
   assert np.isfinite(a[:]).all()
  return {k:h[k][:] for k in h}
def audit_input(path,refpath):
 p=load_problem(path);m=p.manifest;a=arrays(path.parent/m['data_file']);v={k:x['value'] for k,x in m['physics']['parameters'].items()};d=m['spatial_dimension'];model=m['physics']['model'];q=a['probe_coordinates'];t=a['times'];ids=a['probe_ids']
 e=[];check(p,e);assert not e,e
 assert set(a)=={'probe_ids','probe_coordinates','times'}
 assert ids.dtype==np.dtype('int64') and np.all(ids>=0) and np.all(np.diff(ids)>0)
 assert q.dtype==np.dtype('float64') and q.shape==(len(ids),d) and t.dtype==np.dtype('float64')
 assert 1<=len(ids)<=128
 # Independent parameter/geometry and full time-axis checks from DATA.
 assert all(lo<=v[k]<=hi for k,lo,hi in [('density',.1,10),('viscosity',.1,10),('temperature',200,1000),('time_step',.05,1)])
 if 'annulus' in model:
  assert d==2 and v['end_time']==0 and np.array_equal(t,[0.])
  margin=1e-4*min(v['inner_radius'],v['outer_radius']-v['inner_radius']);r=np.linalg.norm(q,axis=1)
  dist=np.minimum(r-v['inner_radius'],v['outer_radius']-r)
 else:
  n=round(v['end_time']/v['time_step']);assert 1<=n<=8 and np.array_equal(t,np.arange(n+1)*v['time_step'])
  lengths=[v['width'],v['height']]+([v['depth']] if d==3 else []);margin=1e-4*min(lengths)
  ds=[q[:,0],v['width']-q[:,0]]
  if d==3:ds += [q[:,1],v['depth']-q[:,1]]
  for tt in t:
   if 'parallel' in model:
    slope=tt*np.array([v['rate_x']]+([v['rate_y']] if d==3 else []));bottom=q[:,:d-1]@slope;norm=math.sqrt(1+slope@slope)
    ds += [(q[:,-1]-bottom)/norm,(v['height']+bottom-q[:,-1])/norm]
   else:
    slope=tt*v['rate_x'];top=v['height']+slope*(q[:,0]-v['width']/2)
    ds += [q[:,1],(top-q[:,1])/math.sqrt(1+slope*slope)]
  dist=np.min(ds,axis=0)
 assert min(dist)>=margin
 r=arrays(refpath);assert set(r)=={'probe_ids','times','velocity','pressure'}
 assert np.array_equal(ids,r['probe_ids']) and np.array_equal(t,r['times'])
 assert r['velocity'].shape==(len(t),len(ids),d) and r['pressure'].shape==(len(t),len(ids),1)
 assert r['velocity'].dtype==r['pressure'].dtype==np.dtype('float64')
 item={'model':model,'dimension':d,'parameters':v,'N':len(ids),'T':len(t),'times':t.tolist(),'minimum_boundary_distance':float(min(dist)),'required_margin':margin,'input_arrays':{k:{'dtype':str(x.dtype),'shape':list(x.shape),'min':float(x.min()),'max':float(x.max())} for k,x in a.items()},'output_arrays':{k:{'dtype':str(x.dtype),'shape':list(x.shape),'min':float(x.min()),'max':float(x.max())} for k,x in r.items()}}
 if 'wedge' not in model:
  exact=np.zeros_like(r['velocity'])
  if 'parallel' in model:
   exact[:,:,0]=v['velocity_x'];rate=v['rate_x']*v['velocity_x']
   if d==3:exact[:,:,1]=v['velocity_y'];rate+=v['rate_y']*v['velocity_y']
   exact[:,:,-1]=t[:,None]*rate
  else:exact[0]=v['angular_speed']*np.stack([-q[:,1],q[:,0]],axis=1)
  item['analytic_velocity_error']=float(np.max(abs(exact-r['velocity'])));item['analytic_pressure_error']=float(np.max(abs(r['pressure'])))
  assert item['analytic_velocity_error']<1e-5 and item['analytic_pressure_error']<1e-6
 return p,r,item
cases={}
for c in sorted((TASK/'cases').iterdir()):
 p,r,item=audit_input(c/'problem.json',TASK/'reference'/c.name/'reference.h5');cases[c.name]=(p,r);report['inputs'][c.name]=item
 g=json.loads((TASK/'reference'/c.name/'grading.json').read_text());pol=g['checks'][0]['policy']['quantities'];wedge='wedge' in item['model']
 for k,atol,unit in [('velocity',1e-4 if wedge else 1e-5,'m/s'),('pressure',2e-3 if wedge else 1e-6,'Pa')]:
  assert pol[k]['unit']==unit and pol[k]['rule']=={'metric':'pointwise','time':'per_time','components':'per_component','atol':atol,'rtol':1e-5}
 # Compare every native row, not writer metadata or author's report.
 report['native'][c.name]={}
 for version,filename in [('reference','reference.h5'),('defect','result.h5')]:
  base=WORK/'formal'/version/c.name;raw=np.loadtxt(base/'native-replay/native/point_values.txt');raw=raw.reshape(len(r['times']),len(r['probe_ids']),-1);d=p.manifest['spatial_dimension']
  assert raw.shape[-1]==2*d+3
  assert np.allclose(raw[:,:,0],p.arrays['times'][:,None],atol=1e-12,rtol=5e-6)
  assert np.allclose(raw[:,:,1:1+d],p.arrays['probe_coordinates'][None],atol=1e-12,rtol=5e-6)
  rr=arrays(base/filename)
  assert np.array_equal(raw[:,:,1+d:1+2*d],rr['velocity']) and np.array_equal(raw[:,:,1+2*d:2+2*d],rr['pressure'])
  if version=='reference':assert all(np.array_equal(r[k],rr[k]) for k in r)
  cfg=(base/'native-replay/input.prm').read_text();assert 'set Use natural coordinates = false' in cfg and 'set List of postprocessors = point values' in cfg
  report['native'][c.name][version]={'rows':int(np.prod(raw.shape[:2])),'all_values_exactly_mapped':True,'all_frames_and_coordinates':True}
for sample in sorted((TASK/'samples').iterdir()):
 p,r,item=audit_input(sample/'input/problem.json',sample/'output/result.h5');report['inputs']['sample-'+sample.name]=item
 assert all(np.array_equal(r[k],arrays(sample/'reference/reference.h5')[k]) for k in r)

# Elmer ASCII node fields: independently parse actual node-ID rows and integrate
# quadratic top boundary with Gauss quadrature using a fixed pressure baseline.
for case in ['09-wedge-negative','10-wedge-positive','11-wedge-static']:
 p,ref=cases[case];v={k:x['value'] for k,x in p.manifest['physics']['parameters'].items()};bygrid={}
 for grid in ['h02','h01']:
  vals=[];items=[]
  for ti,t in enumerate(p.arrays['times']):
   folder=WORK/'independent-formal'/case/f't{ti}-{grid}'
   nodes=np.loadtxt(folder/'mesh/mesh.nodes');ids=nodes[:,0].astype(int);xyz=nodes[:,2:5];assert np.array_equal(ids,np.arange(1,len(ids)+1))
   elem=np.loadtxt(folder/'mesh/mesh.elements',dtype=int);assert np.all(elem[:,2]==306)
   triangles=xyz[elem[:,3:6]-1,:2];edge1=triangles[:,1]-triangles[:,0];edge2=triangles[:,2]-triangles[:,0]
   determinants=edge1[:,0]*edge2[:,1]-edge1[:,1]*edge2[:,0];assert np.all(determinants>0) or np.all(determinants<0)
   mesh_area=float(np.sum(abs(determinants))/2);assert abs(mesh_area-v['width']*v['height'])<1e-8
   assert 'ELMER SOLVER FINISHED AT' in (folder/'solver.stdout.log').read_text()
   lines=(folder/'mesh/flow.result').read_text().splitlines();fields={};perm=None
   for name in ['velocity 1','velocity 2','pressure']:
    at=lines.index(name)+1
    if 'use previous' not in lines[at]:
     count=int(lines[at].split()[1]);perm=np.array([list(map(int,x.split())) for x in lines[at+1:at+1+count]]);at+=count+1
    else:at+=1
    assert len(perm)==len(nodes) and sorted(perm[:,0])==list(ids)
    fields[name]=np.array([float(x) for x in lines[at:at+len(nodes)]])
   ep=(folder/'mesh/flow.ep').read_text().splitlines();n=int(ep[0].split()[0]);assert n==len(nodes)
   assert np.allclose(np.array([list(map(float,x.split())) for x in ep[2:2+n]]),xyz,atol=1e-8,rtol=1e-8)
   st=next(i for i,x in enumerate(ep) if x.startswith('#time'))+1;epv=np.array([list(map(float,x.split())) for x in ep[st:st+n]])
   assert np.max(abs(epv[:,:2]-np.stack([fields['velocity 1'],fields['velocity 2']],axis=1)))<2e-7
   bcs=[list(map(int,x.split())) for x in (folder/'mesh/mesh.boundary').read_text().splitlines()];top=[x for x in bcs if x[1]==3]
   assert top
   pressure=fields['pressure'];offset=float(pressure[0]);integ=length=0.
   for b in top:
    assert b[4]==203;ix=np.array(b[5:8])-1;a,bp,mid=xyz[ix];assert np.allclose(mid,(a+bp)/2,atol=1e-12)
    ds=np.linalg.norm(bp-a);pv=pressure[ix]-offset
    # integrate Lagrange polynomial at three Gauss points (independent from Simpson reader)
    s,w=np.polynomial.legendre.leggauss(3);L=np.stack([s*(s-1)/2,s*(s+1)/2,1-s*s],axis=1)
    integ+=ds/2*float(w@(L@pv));length+=ds
    assert np.max(abs(xyz[ix,1]-(v['height']+t*v['rate_x']*(xyz[ix,0]-v['width']/2))))<1e-9
   mean_relative=integ/length;sample=[]
   for point in p.arrays['probe_coordinates']:
    matches=np.flatnonzero(np.linalg.norm(xyz[:,:2]-point,axis=1)<1e-10);assert len(matches)==1;i=matches[0]
    sample.append([fields['velocity 1'][i],fields['velocity 2'][i],(pressure[i]-offset)-mean_relative])
   sample=np.array(sample);vals.append(sample)
   old=json.loads((folder/'native-probe-values.json').read_text());oldval=np.array([[*x['velocity'],x['pressure']] for x in old['samples']]);delta=float(np.max(abs(oldval-sample)))
   assert delta<3e-6
   sif=(folder/'case.sif').read_text();assert 'Flow Model = Stokes' in sif and 'Normal-Tangential Velocity = Logical True' in sif
   items.append({'frame':float(t),'nodes':n,'triangles':len(elem),'minimum_abs_determinant':float(np.min(abs(determinants))),'mesh_area':mesh_area,'top_elements':len(top),'top_length':length,'raw_pressure_offset':offset+mean_relative,'independent_normalization_difference':delta,'embedded_probes':len(sample)})
  arr=np.array(vals);bygrid[grid]=arr
  report['elmer'][case+'-'+grid]={'frames':items,'max_velocity_error':float(np.max(abs(arr[:,:,:2]-ref['velocity']))),'max_pressure_error':float(np.max(abs(arr[:,:,2:]-ref['pressure'])))}
 report['elmer'][case+'-refinement']={'velocity':float(np.max(abs(bygrid['h02'][:,:,:2]-bygrid['h01'][:,:,:2]))),'pressure':float(np.max(abs(bygrid['h02'][:,:,2]-bygrid['h01'][:,:,2])))}
 assert report['elmer'][case+'-h01']['max_velocity_error']<1e-4
 assert report['elmer'][case+'-h01']['max_pressure_error']<2e-3
for folder in sorted((WORK/'formal-convergence').iterdir()):
 p,ref=cases[folder.name];d=p.manifest['spatial_dimension'];raw=np.loadtxt(folder/'native/point_values.txt').reshape(len(ref['times']),len(ref['probe_ids']),-1)
 report['convergence'][folder.name]={'velocity':float(np.max(abs(raw[:,:,1+d:1+2*d]-ref['velocity']))),'pressure':float(np.max(abs(raw[:,:,1+2*d:2+2*d]-ref['pressure'])))}
(OUT/'full-audit.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'inputs':len(report['inputs']),'native_runs':sum(map(len,report['native'].values())),'elmer_runs':30,'convergence':report['convergence']},indent=2))

