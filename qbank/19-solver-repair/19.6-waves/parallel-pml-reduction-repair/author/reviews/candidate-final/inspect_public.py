import hashlib, json, pathlib, zipfile, sys, subprocess, os
import h5py, numpy as np
ROOT=pathlib.Path('D:/Code/CAE-Bench-OJ')
OUT=ROOT/'runs/candidate-review/repair22-specfem661-final'
Q=ROOT/'qbank/19-solver-repair/19.6-waves/parallel-pml-reduction-repair'
z=zipfile.ZipFile(ROOT/'dist/parallel-pml-reduction-repair-agent.zip')
runtime=OUT/'runtime'
for name in z.namelist():
    if name.startswith('src/') or name=='pyproject.toml':
        target=runtime/name; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(z.read(name))
sys.path.insert(0,str(runtime/'src'))
from caeoj.sdk import load_problem, load_result
from caeoj.validation import read_mesh
files=[ROOT/'docs/CONTRACT.md',Q/'instruction.md',Q/'DATA.md',Q/'public-materials.json',ROOT/'dist/parallel-pml-reduction-repair-agent.zip']
files += [Q/f['path'] for f in json.loads((Q/'public-materials.json').read_text())['files']]
audit={'archive_sha256':hashlib.sha256(z.filename and pathlib.Path(z.filename).read_bytes()).hexdigest(),'samples':{}}
for i in ['01','02']:
    base=Q/'samples'/i
    for f in ['input/problem.json','input/input.h5','input/mesh.msh','reference/grading.json','reference/reference.h5','output/result.h5']:
        files.append(base/f)
    p=load_problem(base/'input/problem.json')
    mesh=read_mesh(base/'input/mesh.msh',geometry=True)
    info={'input_validation':'passed','arrays':{},'mesh_nodes':len(mesh['nodes']),'mesh_elements':len(mesh['connectivity'])}
    for k,a in p.arrays.items():
        info['arrays'][k]={'shape':list(a.shape),'dtype':str(a.dtype),'min':float(a.min()),'max':float(a.max()),'finite':bool(np.isfinite(a).all())}
    pars={k:v['value'] for k,v in p.manifest['physics']['parameters'].items()}
    a=p.arrays;t=a['times']; h=None
    comp=[]
    for tag in a['cell_ids']:
        coords=np.array([mesh['node_coordinates'][n][:2] for n in mesh['connectivity'][int(tag)][1]])
        dx=coords[1]-coords[0];dz=coords[3]-coords[0]
        if h is None:h=float(dx[0])
        assert np.allclose(dx,[h,0]) and np.allclose(dz,[0,h]) and np.allclose(coords[2],coords[0]+dx+dz)
        comp.append(coords.mean(axis=0))
    comp=np.array(comp)
    info['square_h']=h
    info['cfl']=pars['p_speed']*pars['time_step']/(0.1726731646460114*h)
    info['time_grid_max_error']=float(np.max(abs(t-(-1.2/pars['frequency']+np.arange(len(t))*pars['time_step']))))
    info['duration_Nt_dt']=len(t)*pars['time_step']
    info['source_probe_min_distance']=float(np.min(np.linalg.norm(a['source_coordinates'][:,None,:]-a['probe_coordinates'][None,:,:],axis=-1)))
    info['pml_layer_pattern']=bool(np.array_equal(a['pml_region'][0,:,0],np.where((comp[:,1]<3*h)|(comp[:,1]>800-3*h),2,0))) if np.any(a['pml_region']) else 'disabled'
    nodes={}
    for tag in a['cell_ids']:
        for n in mesh['connectivity'][int(tag)][1]:nodes.setdefault(n,[]).append(int(tag))
    remaining=set(map(int,a['cell_ids']));components=[]
    while remaining:
        todo=[remaining.pop()]; group=set(todo)
        while todo:
            tag=todo.pop()
            for n in mesh['connectivity'][tag][1]:
                for other in nodes[n]:
                    if other in remaining:remaining.remove(other);group.add(other);todo.append(other)
        coords=np.array([mesh['node_coordinates'][n] for tag in group for n in mesh['connectivity'][tag][1]])
        components.append({'elements':len(group),'min':coords.min(axis=0).tolist(),'max':coords.max(axis=0).tolist()})
    info['components']=components
    for role in ['source_coordinates','probe_coordinates']:
        distances=[]
        for xy in a[role]:
            boxes=[c for c in components if c['min'][0]<xy[0]<c['max'][0] and c['min'][1]<xy[1]<c['max'][1]]
            assert len(boxes)==1
            c=boxes[0];distances.append(min(xy[0]-c['min'][0],c['max'][0]-xy[0],xy[1]-c['min'][1],c['max'][1]-xy[1]))
        info[role+'_min_wall_distance']=float(min(distances))
    info['outputs']={}
    for role,f in [('reference','reference/reference.h5'),('example_output','output/result.h5')]:
        with h5py.File(base/f,'r') as hd:
            vals={k:hd[k][()] for k in hd}
            info['outputs'][role]={k:{'shape':list(v.shape),'dtype':str(v.dtype),'min':float(v.min()),'max':float(v.max()),'finite':bool(np.isfinite(v).all())} for k,v in vals.items()}
            info['outputs'][role]['initial_sample_max_abs']=float(np.max(abs(vals['wave_response'][0])))
        try:
            load_result(p,base/f); info['outputs'][role]['sdk_validation']='passed'
        except Exception as e: info['outputs'][role]['sdk_validation']=str(e)
    with h5py.File(base/'reference/reference.h5') as r,h5py.File(base/'output/result.h5') as o:
        info['reference_output_equal']=all(np.array_equal(r[k][()],o[k][()]) for k in r)
    env=os.environ.copy();env['PYTHONPATH']=str(runtime/'src')
    graded=subprocess.run([sys.executable,'-m','caeoj','grade','--input',str(base/'input/problem.json'),'--output',str(base/'output/result.h5'),'--grading',str(base/'reference/grading.json')],env=env,capture_output=True,text=True)
    info['grade_exit']=graded.returncode; info['grade_status']=json.loads(graded.stdout)['status']
    audit['samples'][i]=info
manifest=[]
for f in files:
    entry={'path':f.relative_to(ROOT).as_posix(),'exists':f.is_file()}
    if f.is_file():entry['sha256']=hashlib.sha256(f.read_bytes()).hexdigest()
    manifest.append(entry)
audit['materials']=manifest
audit['archive_matches']={e['path']:hashlib.sha256(z.read(e['path'])).hexdigest()==e['sha256'] for e in manifest if e.get('sha256') and e['path'] in z.namelist()}
(OUT/'evidence.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'sha':audit['archive_sha256'],'samples':{k:{x:y for x,y in v.items() if x not in ['arrays','outputs']} for k,v in audit['samples'].items()}},ensure_ascii=False,indent=2))
