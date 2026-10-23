import pathlib, zipfile, hashlib, json, sys, subprocess
import numpy as np, h5py
ROOT=pathlib.Path('D:/Code/CAE-Bench-OJ'); OUT=ROOT/'runs/candidate-review/repair22-moose30236-statements'
P=pathlib.Path('C:/Users/Jim Zhou/.cache/caeoj-repair22/moose30236-dist-v1/grand-potential-derivatives-repair-agent.zip')
z=zipfile.ZipFile(P); base=OUT/'exam-public'; q='qbank/19-solver-repair/19.2-operators/grand-potential-derivatives-repair/'
for name in z.namelist():
    if name.startswith('src/') or name.startswith(q+'samples/') or name in [q+'instruction.md',q+'DATA.md','docs/CONTRACT.md','pyproject.toml']:
        f=base/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(z.read(name))
sys.path.insert(0,str(base/'src'))
from caeoj.sdk import load_problem,load_result
audit={'archive_sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'materials':[],'samples':{}}
for name in z.namelist():
    audit['materials'].append({'path':name,'sha256':hashlib.sha256(z.read(name)).hexdigest(),'read_role':'hash-only' if 'moose-source' in name or '/public/' in name else 'public-material'})
audit['statement_matches']={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==hashlib.sha256(z.read(name)).hexdigest() for name in [q+'instruction.md',q+'DATA.md','docs/CONTRACT.md']}
for i in ['01','02']:
    b=base/q/'samples'/i;p=load_problem(b/'input/problem.json')
    info={'input_validation':'passed','arrays':{},'outputs':{},'grading':json.loads((b/'reference/grading.json').read_text())}
    for k,a in p.arrays.items():info['arrays'][k]={'shape':list(a.shape),'dtype':str(a.dtype),'min':float(a.min()),'max':float(a.max()),'finite':bool(np.isfinite(a).all())}
    for label,f in [('reference','reference/reference.h5'),('output','output/result.h5')]:
        r=load_result(p,b/f)
        with h5py.File(b/f) as hd:
            info['outputs'][label]={k:{'shape':list(hd[k].shape),'dtype':str(hd[k].dtype),'finite':bool(np.isfinite(hd[k][()]).all())} for k in hd}
    with h5py.File(b/'reference/reference.h5') as r,h5py.File(b/'output/result.h5') as o:info['reference_output_equal']=all(np.array_equal(r[k][()],o[k][()]) for k in r)
    env=__import__('os').environ.copy();env['PYTHONPATH']=str(base/'src')
    res=subprocess.run([sys.executable,'-m','caeoj','grade','--input',str(b/'input/problem.json'),'--output',str(b/'output/result.h5'),'--grading',str(b/'reference/grading.json')],env=env,capture_output=True,text=True)
    info['grade_exit']=res.returncode;info['grade_status']=json.loads(res.stdout)['status'];info['grade_stderr']=res.stderr
    audit['samples'][i]=info
(OUT/'evidence.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'archive_sha256':audit['archive_sha256'],'statement_matches':audit['statement_matches'],'samples':{k:{'input_validation':v['input_validation'],'output_count':len(v['outputs']['output']),'grade_exit':v['grade_exit'],'reference_output_equal':v['reference_output_equal']} for k,v in audit['samples'].items()}},indent=2))
