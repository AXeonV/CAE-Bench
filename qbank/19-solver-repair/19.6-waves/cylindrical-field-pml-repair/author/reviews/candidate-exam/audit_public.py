import copy,hashlib,importlib.util,json,os,pathlib,shutil,subprocess,sys,tarfile
import h5py,numpy as np
root=pathlib.Path(__file__).resolve().parent;pkg=root/'package';task=pathlib.Path('qbank/19-solver-repair/19.6-waves/cylindrical-field-pml-repair')
e={'zip_sha256':hashlib.sha256(pathlib.Path('dist/cylindrical-field-pml-repair-agent.zip').read_bytes()).hexdigest(),'python':sys.version,'executable':sys.executable,'platform':sys.platform}
e['files']={p.relative_to(pkg).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in pkg.rglob('*') if p.is_file()}
manifest=json.loads((pkg/'MANIFEST.json').read_text());e['assembly']=manifest['assembly'];e['manifest_mismatches']=[n for n,h in manifest['files'].items() if e['files'].get(n)!=h];e['frozen_documents']={n.as_posix():pathlib.Path(n).read_bytes()==(pkg/n).read_bytes() for n in [task/'instruction.md',task/'DATA.md',pathlib.Path('docs/CONTRACT.md')]}
e['text_inventory']={}
for p in pkg.rglob('*'):
 if p.is_file() and p.suffix in ('.md','.json','.py','.cpp','.txt','.toml','.msh'):
  s=p.read_text(encoding='utf8');e['text_inventory'][p.relative_to(pkg).as_posix()]={'characters':len(s),'lines':len(s.splitlines())}
  if p.suffix=='.json':json.loads(s)
e['source_archive']=[]
with tarfile.open(pkg/task/'public/meep-source.tar.gz','r:gz') as tar:
 for m in tar.getmembers():
  r={'name':m.name,'size':m.size,'type':str(m.type),'linkname':m.linkname}
  if m.isfile():r['sha256']=hashlib.sha256(tar.extractfile(m).read()).hexdigest()
  e['source_archive'].append(r)
e['arrays']={}
for p in (pkg/task/'samples').rglob('*.h5'):
 with h5py.File(p,'r') as f:
  values={}
  for k in f:
   d=f[k];a=d[()];values[k]={'dtype':str(a.dtype),'shape':list(a.shape),'values':a.tolist(),'finite':bool(np.isfinite(a).all()),'attrs':dict(d.attrs),'compression':d.compression}
  e['arrays'][p.relative_to(pkg).as_posix()]={'attrs':dict(f.attrs),'datasets':values}
sys.path.insert(0,str(pkg/'src'))
from caeoj.sdk import load_problem,load_result,write_result
from caeoj.validation import read_mesh
spec=importlib.util.spec_from_file_location('public_adapter',pkg/task/'public/run_case.py');adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
env=os.environ.copy();env['PYTHONPATH']=str(pkg/'src');env['PYTHONIOENCODING']='utf-8';e['commands']=[];e['sdk']=[];e['meshes']={}
def plain(x):
 if isinstance(x,np.ndarray):return x.tolist()
 if isinstance(x,set):return sorted(x)
 if isinstance(x,dict):return {str(k):plain(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [plain(v) for v in x]
 if isinstance(x,np.generic):return x.item()
 return x
def run(args):
 r=subprocess.run([sys.executable,*args],cwd=pkg,env=env,text=True,capture_output=True);e['commands'].append({'argv':[sys.executable,*args],'cwd':str(pkg),'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr});return r
for sid in ['01','02']:
 base=task/'samples'/sid;problem=base/'input/problem.json';p=load_problem(pkg/problem);a=load_result(p,pkg/base/'output/result.h5');fields={d['array']:a[d['array']].copy() for d in p.manifest['outputs'].values()};out=root/f'sdk-roundtrip-{sid}.h5';write_result(out,p,fields)
 raw=json.dumps({'flux':a['spectral_flux'].flatten().tolist(),'fields':a['observed_dft'].reshape(6,2).tolist(),'dt':float(a['time_step'][0,0,0]),'time':float(a['window_end'][0,0,0])});adapt=adapter.adapt(raw)
 e['sdk'].append({'sample':sid,'params':p.manifest['physics']['parameters'],'roundtrip_exact':all(np.array_equal(v,a[k]) for k,v in load_result(p,out).items()),'adapter_exact':all(np.array_equal(v,a[k]) for k,v in adapt.items()),'serialized_payload':adapter.serialize(p)})
 mesh=pkg/base/'input/surfaces.msh';e['meshes'][sid]={'text':mesh.read_text(),'parsed':plain(read_mesh(mesh,geometry=True))}
 for args in [['-m','caeoj','info','--input',str(problem)],['-m','caeoj','validate-input',str(problem)],['-m','caeoj','validate-output','--input',str(problem),'--output',str(base/'output/result.h5')],['-m','caeoj','grade','--input',str(problem),'--output',str(base/'output/result.h5'),'--grading',str(base/'reference/grading.json')],[str(task/'public/run_case.py'),'--input',str(problem),'--output',str(root/f'actual-{sid}.h5')]]:run(args)
 for key in fields:
  values={k:v.copy() for k,v in fields.items()};values[key].flat[-1]+=100;out=root/f'negative-{sid}-{key}.h5';write_result(out,p,values);run(['-m','caeoj','grade','--input',str(problem),'--output',str(out),'--grading',str(base/'reference/grading.json')])
 if sid=='01':
  for key,count in [('observed_dft',11),('spectral_flux',2)]:
   for i in range(count):
    values={k:v.copy() for k,v in fields.items()};values[key].flat[i]+=100;out=root/f'negative-{sid}-{key}-{i}.h5';write_result(out,p,values);run(['-m','caeoj','grade','--input',str(problem),'--output',str(out),'--grading',str(base/'reference/grading.json')])
  original=p
# Independent legal/illegal declaration fixtures, without solving or using references.
for name,param,value in [('valid-sign','source_amplitude',-.25),('valid-mode','mode',-original.manifest['physics']['parameters']['mode']['value']),('valid-resolution','resolution',40),('invalid-float','radius',2.),('invalid-bool','radius',True),('invalid-mode','mode',0)]:
 folder=root/name;folder.mkdir(exist_ok=True);m=copy.deepcopy(original.manifest);m['physics']['parameters'][param]['value']=value;arrays={k:v.copy() for k,v in original.arrays.items()}
 if name=='valid-resolution':arrays['probe_coordinates']=np.array([[(2*value+1)*(.5/value),.5/value]],dtype='float64')
 (folder/'problem.json').write_text(json.dumps(m,indent=2),encoding='utf8');shutil.copyfile(pkg/task/'samples/01/input/surfaces.msh',folder/'surfaces.msh')
 with h5py.File(folder/'input.h5','w') as f:
  for k,v in arrays.items():f[k]=v
 run(['-m','caeoj','validate-input',str(folder/'problem.json')])
(root/'evidence.json').write_text(json.dumps(e,ensure_ascii=False,indent=2),encoding='utf8');print(e['zip_sha256'],e['manifest_mismatches'],e['frozen_documents']);print(e['sdk']);print('commands',len(e['commands']));print([(c['argv'][-1],c['exit_code']) for c in e['commands']])
