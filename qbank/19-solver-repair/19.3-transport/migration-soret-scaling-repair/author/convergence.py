"""Mesh refinement against continuum, using actual 2D Elmer and no solver-source formula."""
import hashlib,json,subprocess,sys
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem
from independent import reference
from mesh import generate,SIDES
TASK=Path(__file__).resolve().parents[1];ROOT=TASK.parents[3];sys.path.insert(0,str(TASK/'public'))
import run_case
from native_result import read_result
DOCKER='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
if __name__=='__main__':
 image=json.loads(subprocess.check_output([DOCKER,'image','inspect','caeoj-elmer870-reference:production']))[0]['Id'];rows=[]
 for ny in [100,200,400]:
  d=ROOT/'work/repair-22/elmer-870/convergence'/str(ny);mesh=generate(d,width=.0001,length=.001,nx=1,ny=ny)
  p=load_problem(TASK/'cases/01-migration-relative-public/problem.json');p.meshes['main'].update(mesh);p.arrays['node_ids']=np.array(sorted(mesh['nodes']),dtype='int64')
  for side,tag in SIDES.items():p.arrays[side+'_ids']=np.array(sorted(mesh['groups'][1,tag]['elements']),dtype='int64')
  run_case.prepare(p,d)
  result=subprocess.run([DOCKER,'run','--rm','--network','none','--cpus','2','--memory','2g','--user','1000:1000','--mount',f'type=bind,source={d.resolve()},target=/job','--workdir','/job',image,run_case.ELMER,'case.sif'],capture_output=True,text=True,timeout=30)
  (d/'stdout.log').write_text(result.stdout);(d/'stderr.log').write_text(result.stderr)
  if result.returncode:raise RuntimeError(result.stderr)
  fields,_=read_result(d/'mesh/case.result');actual=fields['conc'][None,:,None];exact=reference(p);discrete=reference(p,discrete=True)
  rows.append({'ny':ny,'nodes':len(p.arrays['node_ids']),'continuum_max_error':float(abs(actual-exact['concentration']).max()),'independent_discrete_max_error':float(abs(actual-discrete['concentration']).max()),'raw_native_result_sha256':hashlib.sha256((d/'mesh/case.result').read_bytes()).hexdigest()})
 ratios=[rows[i]['continuum_max_error']/rows[i+1]['continuum_max_error'] for i in range(2)]
 assert all(3.9<x<4.1 for x in ratios) and max(r['independent_discrete_max_error'] for r in rows)<1e-9
 (TASK/'author/data-evidence/convergence.json').write_text(json.dumps({'image_id':image,'mechanism':'constant-temperature nonzero-charge electromigration, true 2D QUAD4 mesh nx=1, ny refinement','independent_discrete_derivation':'For uniform spacing h=L/ny, standard Galerkin gives adjacent difference ratio r=(1-a/(2ny))/(1+a/(2ny)); a_eff=2ny*atanh(a/(2ny)). Boundary-normalized geometric recurrence is independent of Elmer implementation.','cases':rows,'error_ratios':ratios,'passed':True},indent=2)+'\n')
