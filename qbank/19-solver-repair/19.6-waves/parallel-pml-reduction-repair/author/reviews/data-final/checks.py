"""Independent bounded audit: read every real value; never run a native solver."""
import copy, hashlib, importlib.util, json, math, shutil, struct, tempfile
from pathlib import Path
import h5py
import numpy as np
from caeoj.sdk import load_problem, load_result
from caeoj.case_grading import grade_case
from caeoj.validation import read_mesh, ContractError, write_json
from caeoj.storage import write_hdf5

ROOT=Path(__file__).resolve().parents[3]
TASK=ROOT/'qbank/19-solver-repair/19.6-waves/parallel-pml-reduction-repair'
WORK=ROOT/'work/repair-22/specfem-661'
OUT=Path(__file__).parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
contract=module('review_contract',TASK/'extension/caeoj_task_ext/parallel_wave.py')
adapter=module('review_adapter',TASK/'public/run_case.py')
green=module('review_green',TASK/'author/independent.py')
def arrays(path):
    with h5py.File(path) as f:
        assert not f.attrs
        result={}
        for k in f:
            d=f[k];x=d[:];assert not d.attrs and np.isfinite(x).all()
            result[k]={'dtype':str(x.dtype),'shape':list(x.shape),'minimum':float(x.min()),'maximum':float(x.max()),'sha256_values':hashlib.sha256(x.tobytes()).hexdigest()}
        return result
def db_header(path):
    b=path.read_bytes();o=0;rec=[]
    while o<len(b):
        n=struct.unpack_from('<i',b,o)[0];assert struct.unpack_from('<i',b,o+n+4)[0]==n
        rec.append(b[o+4:o+4+n]);o+=n+8
    ne=struct.unpack('<i',rec[2])[0]
    materials=[i for i,x in enumerate(rec) if len(x)==112 and struct.unpack_from('<ii',x)==(1,1)]
    k=materials[-1]+1+ne
    return dict(rank=int(path.stem[-5:]),elements=ne,interfaces=struct.unpack('<ii',rec[k])[0],sha256=sha(path))
report={'cases':[],'samples':[],'variants':[],'outputs':[],'sha256':{}}
for path in sorted((TASK/'cases').glob('*/problem.json')):
    name=path.parent.name;q=load_problem(path);a=q.arrays;p={k:v['value'] for k,v in q.manifest['physics']['parameters'].items()}
    errors=[];contract.check(q,errors);assert not errors,errors
    mesh=read_mesh(path.parent/'mesh.msh',geometry=True)
    # Force a complete traversal of every coordinate and every connectivity entry.
    allcoords=np.array(list(mesh['node_coordinates'].values()));assert np.isfinite(allcoords).all() and np.all(allcoords[:,2]==0)
    allcells=[mesh['connectivity'][int(tag)][1] for tag in a['cell_ids']]
    for cell in allcells:
        assert len(cell)==4 and all(n in mesh['nodes'] for n in cell)
    ref=TASK/'reference'/name/'reference.h5';refarrays=load_result(q,ref);response=refarrays['wave_response']
    grade=grade_case(path,ref,TASK/'reference'/name/'grading.json');assert grade['score']==1
    native=WORK/'formal-dataset/replay/reference'/name
    suffix='BXY.semd' if q.manifest['physics']['model'].endswith('sh-v1') else 'PRE.semp'
    raw=[]
    for j in range(len(a['probe_ids'])):
        trace=np.loadtxt(native/'OUTPUT_FILES'/f'AA.R{j:04d}.{suffix}');assert trace.shape==(len(a['times']),2)
        assert np.max(np.abs(trace[:,0]-a['times']))<=5e-8
        raw.append(trace[:,1]);assert np.array_equal(trace[:,1],response[:,j,0])
    with tempfile.TemporaryDirectory() as tmp:
        adapter.prepare(q,tmp)
        for f in (native/'DATA').iterdir():
            if f.is_file():assert (Path(tmp)/'DATA'/f.name).read_bytes()==f.read_bytes(),(name,f.name)
    headers=[db_header(db) for db in sorted((native/'OUTPUT_FILES').glob('Database*.bin'))]
    assert len(headers)==p['processes'] and sum(x['elements'] for x in headers)==len(a['cell_ids'])
    expected=green.evaluate(q,128);fine=green.evaluate(q,256)
    norm=np.linalg.norm(expected,axis=0);rel=np.linalg.norm(response-expected,axis=0)/norm
    quad=np.linalg.norm(fine-expected,axis=0)/np.linalg.norm(fine,axis=0)
    assert np.max(rel)<.02 and np.max(quad)<1e-7
    # Verify the finite-start Duhamel substitution with independently written
    # composite midpoint integration at representative times, away from wavefront.
    r=float(np.linalg.norm(a['probe_coordinates'][0]-a['source_coordinates'][0]));c=p['s_speed'] or p['p_speed'];tau=r/c
    testtime=max(.15,tau+.05);vmax=math.acosh((testtime+1.2/p['frequency'])/tau)
    vv=(np.arange(100000)+.5)*vmax/100000;ss=testtime-tau*np.cosh(vv);zz=(math.pi*p['frequency']*ss)**2
    midpoint=float(np.sum((1-2*zz)*np.exp(-zz))*vmax/100000/(2*math.pi*c*c))
    gl=float(green.kernel(np.array([testtime]),r,c,p['frequency'],256)[0]);assert abs(midpoint-gl)<1e-14
    # Any omitted image has |m| or |n| >=3. Even its nearest coordinate is
    # beyond 4 domain widths/heights; finite-start causality makes it zero.
    rects=green.rectangles(q);cutoff=p['p_speed']*(a['times'][-1]+1.2/p['frequency'])
    assert all(4*min(hi-lo)>cutoff for lo,hi in rects)
    row=dict(case=name,input_arrays=arrays(path.parent/'input.h5'),reference_arrays=arrays(ref),reference_grade=grade,
             nodes=len(allcoords),elements=len(allcells),rectangles=[(lo.tolist(),hi.tolist()) for lo,hi in rects],
             processes=p['processes'],branch=q.manifest['physics']['model'],source_amplitudes=a['source_amplitude'].tolist(),
             sources=a['source_coordinates'].tolist(),probes=a['probe_coordinates'].tolist(),native_partition=headers,
             all_native_traces_bitwise_equal=True,all_native_input_files_equal=True,
             green_l2=rel.ravel().tolist(),quadrature_128_256=quad.ravel().tolist(),independent_midpoint_error=abs(midpoint-gl))
    if np.any(a['pml_region']):
        reflect=green.evaluate(q,128,False);late=a['times']>.35
        boundary=np.linalg.norm((reflect-expected)[late],axis=0)
        residual=np.linalg.norm((response-expected)[late],axis=0)/boundary
        assert np.all(boundary>0) and np.max(residual)<.05
        row.update(late_window_start_exclusive=.35,late_sample_count=int(late.sum()),late_unabsorbed_return_norm=boundary.ravel().tolist(),late_pml_residual_ratio=residual.ravel().tolist())
    original=WORK/'formal-dataset/replay/original'/name/'result.h5'
    if original.exists():
        orig=load_result(q,original);row['original_complete_equal']=all(np.array_equal(orig[k],refarrays[k]) for k in orig)
        assert row['original_complete_equal']
    else:row['original_failure_tail']=(WORK/'formal-dataset/replay/original'/name/'failure.txt').read_text()[-1000:]
    report['cases'].append(row)
    print(name,'all input/mesh/reference/native/math passed',flush=True)
for path in sorted((TASK/'samples').glob('*/input/problem.json')):
    q=load_problem(path);e=[];contract.check(q,e);assert not e
    dest=path.parent.parent;result=dest/'output/result.h5';load_result(q,result)
    grade=grade_case(path,result,dest/'reference/grading.json');assert grade['score']==1
    report['samples'].append(dict(sample=dest.name,input=arrays(path.parent/'input.h5'),output=arrays(result),grade=grade))

# Mutations derive directly from DATA, using copies of real data only.
base=TASK/'cases/04-isolated-master-pml';q=load_problem(base/'problem.json')
tests=[('normal',True,None),('negative_source',True,lambda m,a:a['source_amplitude'].__imul__(-1)),
 ('nonconsecutive_ids',True,lambda m,a:a.update(probe_ids=a['probe_ids']*13+50)),
 ('process_float',False,lambda m,a:m['physics']['parameters']['processes'].update(value=3.0)),
 ('density_wrong_unit',False,lambda m,a:m['physics']['parameters']['density'].update(unit='1')),
 ('time_shift',False,lambda m,a:a.update(times=a['times']+.001)),
 ('pml_incomplete',False,lambda m,a:a['pml_region'].__setitem__((0,0,0),0)),
 ('pml_illegal_x',False,lambda m,a:a['pml_region'].__setitem__((0,0,0),1)),
 ('acoustic_nonzero_s',False,lambda m,a:m['physics']['parameters']['s_speed'].update(value=1000)),
 ('probe_wall',False,lambda m,a:a['probe_coordinates'].__setitem__((0,1),0)),
 ('source_zero',False,lambda m,a:a['source_amplitude'].__setitem__((0,0,0),0)),
 ('reverse_ids',False,lambda m,a:a.update(cell_ids=a['cell_ids'][::-1],pml_region=a['pml_region'][:,::-1,:]))]
for name,want,mutate in tests:
    m=copy.deepcopy(q.manifest);a={k:v.copy() for k,v in q.arrays.items()}
    if mutate:mutate(m,a)
    with tempfile.TemporaryDirectory() as tmp:
        d=Path(tmp);shutil.copyfile(base/'mesh.msh',d/'mesh.msh');write_json(d/'problem.json',m);write_hdf5(d/'input.h5',a)
        try:z=load_problem(d/'problem.json');e=[];contract.check(z,e);valid=not e
        except ContractError:valid=False
    assert valid==want,(name,valid,want)
    report['variants'].append(dict(name=name,expected_valid=want,valid=valid))
for case in ['01-connected-sh','04-isolated-master-pml']:
    inp=TASK/'cases'/case/'problem.json';q=load_problem(inp);ref=TASK/'reference'/case/'reference.h5';x=load_result(q,ref)
    with tempfile.TemporaryDirectory() as tmp:
        d=Path(tmp)/'out.h5';gradepath=TASK/'reference'/case/'grading.json'
        for name in ['below','equal','above','nan','axis','missing','extra','float32']:
            a={k:v.copy() for k,v in x.items()};atol=2e-9 if case.startswith('01') else 5e-6
            if name in ['below','equal','above']:a['wave_response'][0,0,0]=atol*{'below':.999,'equal':1,'above':1.001}[name]
            if name=='nan':a['wave_response'][0,0,0]=np.nan
            if name=='axis':a['times'][1]+=.00001
            if name=='missing':a.pop('probe_ids')
            if name=='extra':a['surplus']=np.zeros(1)
            if name=='float32':a['wave_response']=a['wave_response'].astype('float32')
            # raw HDF5 writing intentionally permits invalid output to reach consumer.
            with h5py.File(d,'w') as f:
                for k,v in a.items():f.create_dataset(k,data=v)
            try:g=grade_case(inp,d,gradepath);ok=g['score']==1;status=g.get('status')
            except (ContractError,ValueError) as ex:ok=False;status=type(ex).__name__
            assert ok==(name in ['below','equal']),(case,name,ok)
            report['outputs'].append(dict(case=case,name=name,passed=ok,status=status))
for parent in [TASK,ROOT/'runs/harbor/tasks/parallel-pml-reduction-repair/tests']:
    for f in sorted(parent.rglob('*')):
        if f.is_file() and '__pycache__' not in str(f) and 'specfem-source.tar.gz'!=f.name:
            report['sha256'][str(f.relative_to(ROOT))]=sha(f)
(OUT/'actualchecks.json').write_text(json.dumps(report,indent=2))
print('Independent complete read, native binding, math and contract/output checks passed')
