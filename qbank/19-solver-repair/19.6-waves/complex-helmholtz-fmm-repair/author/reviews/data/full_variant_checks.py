from pathlib import Path
import copy,importlib.util,json,shutil
import h5py,numpy as np
from caeoj.sdk import load_problem
from caeoj.validation import check_problem
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent;TASK=ROOT/'qbank/19-solver-repair/19.6-waves/complex-helmholtz-fmm-repair';DATA=ROOT/'work/repair-22/bempp-20/dataset-v2'
sp=importlib.util.spec_from_file_location('decl',TASK/'extension/caeoj_task_ext/helmholtz.py');ext=importlib.util.module_from_spec(sp);sp.loader.exec_module(ext)
point=load_problem(DATA/'cases/01-point-real/problem.json');surface=load_problem(DATA/'cases/07-boundary-complex/problem.json');rows=[]
def test(name,valid,base,edit,mesh_edit=None):
 p=copy.deepcopy(base);edit(p);dest=OUT/'variants'/name;dest.mkdir(parents=True,exist_ok=True)
 (dest/'problem.json').write_text(json.dumps(p.manifest))
 with h5py.File(dest/p.manifest['data_file'],'w') as h:
  for key,value in p.arrays.items():h[key]=value
 if base.manifest['meshes']:
  text=(base.path.parent/'surface.msh').read_text()
  if mesh_edit:text=mesh_edit(text)
  (dest/'surface.msh').write_text(text)
 prob,diag=check_problem(dest/'problem.json');errors=diag['errors']
 if prob and not errors:ext.check(prob,errors)
 rows.append(dict(name=name,expected_valid=valid,actual_valid=not errors,passed=valid==(not errors),errors=errors))
def nop(p):pass
for name,key in [('point-zero','strength'),('surface-zero','density')]:test(name,True,point if key=='strength' else surface,lambda p:p.arrays[key].fill(0))
for value in [.5,3.0]:test('kreal-'+str(value),True,point,lambda p:p.manifest['physics']['parameters']['wavenumber_real'].update(value=value))
for value in [0,1.2]:test('kimag-'+str(value),True,surface,lambda p:p.manifest['physics']['parameters']['wavenumber_imag'].update(value=value))
for name,edit in [
 ('filename-mismatch',lambda p:p.manifest.update(data_file='other.h5')),
 ('negative-source-id',lambda p:p.arrays['source_ids'].__setitem__(0,-1)),
 ('unsorted-source-id',lambda p:p.arrays['source_ids'].__setitem__(0,p.arrays['source_ids'][1]+1)),
 ('wrong-source-dtype',lambda p:p.arrays.update(source_ids=p.arrays['source_ids'].astype('int32'))),
 ('wrong-strength-shape',lambda p:p.arrays.update(strength=p.arrays['strength'][0])),
 ('nan-strength',lambda p:p.arrays['strength'].__setitem__((0,0,0),np.nan)),
 ('nan-target',lambda p:p.arrays['target_coordinates'].__setitem__((0,0),np.nan)),
 ('nonzero-time',lambda p:p.arrays['times'].__setitem__(0,1)),
 ('extra-dataset',lambda p:p.arrays.update(extra=np.array([0.]))),
 ('missing-field',lambda p:p.arrays.pop('strength')),
 ('too-large-charge',lambda p:p.arrays['strength'].__setitem__((0,0,0),2.01)),
 ('wave-bool',lambda p:p.manifest['physics']['parameters']['wavenumber_real'].update(value=True)),
 ('op-float',lambda p:p.manifest['physics']['parameters']['operation'].update(value=0.0)),
 ('source-target-collision',lambda p:p.arrays['target_coordinates'].__setitem__(0,p.arrays['source_coordinates'][0])),
 ('source-source-collision',lambda p:p.arrays['source_coordinates'].__setitem__(0,p.arrays['source_coordinates'][1])),
 ('target-target-collision',lambda p:p.arrays['target_coordinates'].__setitem__(0,p.arrays['target_coordinates'][1])),
]:test(name,False,point,edit)
test('nonnegative-zero-source-id',True,point,lambda p:p.arrays['source_ids'].__setitem__(0,0))
for name,edit in [('interior-target',lambda p:p.arrays['target_coordinates'].__setitem__(0,[0.,0.,0.])),('density-too-large',lambda p:p.arrays['density'].__setitem__((0,0,0),-2.01)),('node-identity-mismatch',lambda p:p.arrays['node_ids'].__setitem__(0,1))]:test(name,False,surface,edit)
def flip(text,first_only=False):
 before,after=text.split('$Elements\n');lines=after.splitlines();count=0
 for i in range(2,len(lines)-1):
  bits=lines[i].split()
  if len(bits)==4 and (not first_only or count==0):bits[2],bits[3]=bits[3],bits[2];lines[i]=' '.join(bits);count+=1
 return before+'$Elements\n'+'\n'.join(lines)+'\n'
test('inward-surface',False,surface,nop,flip);test('inconsistent-orientation',False,surface,nop,lambda s:flip(s,True))
(OUT/'full-variant-evidence.json').write_text(json.dumps(rows,indent=2)+'\n');print(len(rows),'cases',[(x['name'],x['actual_valid']) for x in rows if not x['passed']])
