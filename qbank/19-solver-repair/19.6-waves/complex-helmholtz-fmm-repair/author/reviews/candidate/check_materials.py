import hashlib,json,zipfile,sys
from pathlib import Path
import numpy as np,h5py
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
Q=Path('qbank/19-solver-repair/19.6-waves/complex-helmholtz-fmm-repair')
zpath=ROOT/'dist/complex-helmholtz-fmm-repair-agent.zip'
z=zipfile.ZipFile(zpath)
man=json.loads(z.read('MANIFEST.json'))
hashes={n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if not n.endswith('/')}
assert all(hashes[n]==sha for n,sha in man['files'].items())
assert set(hashes)==set(man['files'])|{'MANIFEST.json'}
paths=[Path('docs/CONTRACT.md'),Q/'instruction.md',Q/'DATA.md',Q/'public-materials.json']
paths += [Q/'public'/n for n in ['driver.py','CMakeLists.txt','run_case.py']]
for s in ['01','02']:
    paths += list((ROOT/Q/'samples'/s/'input').iterdir())
    paths += [Q/'samples'/s/'reference'/n for n in ['grading.json','reference.h5']]
records=[]
for p in paths:
    p=p if p.is_absolute() else ROOT/p
    rel=p.relative_to(ROOT).as_posix();sha=hashlib.sha256(p.read_bytes()).hexdigest()
    if rel in hashes:assert sha==hashes[rel],rel
    records.append({'path':rel,'sha256':sha,'bundle_match':rel in hashes})
(OUT/'materials-sha256.json').write_text(json.dumps({'mode':'exam-materials','archive':{'path':str(zpath.relative_to(ROOT)),'sha256':hashlib.sha256(zpath.read_bytes()).hexdigest()},'materials':records,'zip_members':hashes},indent=2),encoding='utf-8')
bundle=OUT/'bundle'
z.extractall(bundle)
sys.path.insert(0,str(bundle/'src'))
from caeoj.sdk import load_problem,load_result
from caeoj.validation import read_mesh
summaries=[]
for s in ['01','02']:
    p=bundle/Q/'samples'/s/'input'/'problem.json'
    obj=load_problem(p)
    ref=p.parent.parent/'reference/reference.h5'
    load_result(obj,ref)
    desc={'sample':s,'manifest':obj.manifest,'arrays':{},'reference_arrays':{}}
    for file,key in [(p.parent/'input.h5','arrays'),(ref,'reference_arrays')]:
        with h5py.File(file) as f:
            assert not f.attrs
            for n in f:
                d=f[n];a=d[()]
                assert not d.attrs and np.isfinite(a).all()
                desc[key][n]={'shape':list(a.shape),'dtype':str(a.dtype),'minimum':float(a.min()),'maximum':float(a.max()),'elements_read':a.size}
    if s=='01':
        a=obj.arrays;x=a['source_coordinates'];t=a['target_coordinates']
        dd=np.linalg.norm(x[:,None]-x[None,:],axis=2);np.fill_diagonal(dd,np.inf)
        desc['geometry']={'source_count':len(x),'target_count':len(t),'source_spacing':float(dd.min()),'source_target_distance':float(np.linalg.norm(t[:,None]-x[None,:],axis=2).min()),'source_aabb_diagonal':float(np.linalg.norm(np.ptp(x,axis=0)))}
    else:
        mesh=read_mesh(p.parent/'surface.msh',geometry=True)
        ids=obj.arrays['node_ids'];ix={int(n):i for i,n in enumerate(ids)}
        v=np.array([mesh['node_coordinates'][int(n)] for n in ids]);tri=np.array([[ix[n] for n in row[1]] for row in mesh['connectivity'].values()]);t=v[tri]
        c=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);norm=np.linalg.norm(c,axis=1)
        plane=np.einsum('tnc,tc->tn',v[None]-t[:,0,None],c/norm[:,None]);q=t-v.mean(axis=0)
        from caeoj_task_ext.helmholtz import triangle_distances
        dist,signed=triangle_distances(obj.arrays['target_coordinates'],v,tri)
        desc['geometry']={'nodes':len(v),'triangles':len(tri),'node_tags':[int(ids.min()),int(ids.max())],'minimum_area':float(norm.min()/2),'minimum_edge':float(np.linalg.norm(t[:,[1,2,0]]-t,axis=2).min()),'volume':float(np.einsum('tc,tc->t',q[:,0],np.cross(q[:,1],q[:,2])).sum()/6),'maximum_support_plane_offset':float(plane.max()),'minimum_target_surface_distance':float(dist.min()),'each_target_exterior':bool(np.all(signed.max(axis=1)>0)),'source_aabb_diagonal':float(np.linalg.norm(np.ptp(v,axis=0)))}
    summaries.append(desc)
(OUT/'sample-checks.json').write_text(json.dumps(summaries,indent=2),encoding='utf-8')
print(json.dumps([{'sample':d['sample'],'arrays':d['arrays'],'reference_arrays':d['reference_arrays'],'geometry':d['geometry']} for d in summaries],indent=2))
