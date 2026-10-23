from pathlib import Path
import json,hashlib,subprocess,os,sys,shutil
import h5py,numpy as np
out=Path(__file__).resolve().parent;root=out/'public';task=root/'qbank/19-solver-repair/19.3-transport/reconstructed-energy-repair';env=os.environ.copy();env['PYTHONPATH']=str(root/'src');records=[]
def cli(tag,args):
 r=subprocess.run([sys.executable,'-m','caeoj']+list(map(str,args)),cwd=root,env=env,capture_output=True,text=True);(out/(tag+'.stdout.json')).write_text(r.stdout);(out/(tag+'.stderr.log')).write_text(r.stderr);records.append({'tag':tag,'command':[sys.executable,'-m','caeoj']+list(map(str,args)),'returncode':r.returncode});return r
sha={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file() and '__pycache__' not in str(p)};(out/'sha256.json').write_text(json.dumps(sha,indent=2))
arrays=[]
for sample in sorted((task/'samples').iterdir()):
 for p in sample.rglob('*.h5'):
  with h5py.File(p) as f:
   for name in f:
    a=f[name][...];arrays.append({'file':str(p.relative_to(root)),'array':name,'shape':list(a.shape),'dtype':str(a.dtype),'finite':bool(np.isfinite(a).all()),'min':float(a.min()),'max':float(a.max()),'sha256':hashlib.sha256(a.tobytes()).hexdigest()})
 src=sample/'input/problem.json';cli('sample'+sample.name+'-info',['info','--input',src]);cli('sample'+sample.name+'-validate',['validate-input',src]);cli('sample'+sample.name+'-output',['validate-output','--input',src,'--output',sample/'output/result.h5']);cli('sample'+sample.name+'-grade',['grade','--input',src,'--output',sample/'output/result.h5','--grading',sample/'reference/grading.json'])
(out/'all-arrays.json').write_text(json.dumps(arrays,indent=2))
source=task/'samples/01/input'
for tag in ['eos-legal','eos-illegal1percent','stage-enthalpy-offset','iterations-float']:
 dest=out/'variants'/tag;shutil.copytree(source,dest,dirs_exist_ok=True);p=dest/'problem.json';m=json.loads(p.read_text());a=dest/m['data_file']
 if tag=='iterations-float':m['physics']['parameters']['iterations']['value']=float(m['physics']['parameters']['iterations']['value']);p.write_text(json.dumps(m))
 else:
  with h5py.File(a,'r+') as f:
   if tag=='stage-enthalpy-offset':f['enthalpy'][...]=f['enthalpy'][...]+123.0
   else:
    R=m['physics']['parameters']['gas_constant']['value'];rho=f['pressure'][...]/(R*f['temperature'][...]);f['density'][...]=rho+(.25*(1e-12+1e-12*abs(rho)) if tag=='eos-legal' else .01*rho)
 cli(tag,['validate-input',p])
(out/'commands.json').write_text(json.dumps(records,indent=2));print(json.dumps({'records':records,'all_arrays':len(arrays)}))
