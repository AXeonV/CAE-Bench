"""Select inexpensive validated producer resolutions for resource measurements.

No changes to reference or candidate tolerances. The actual solves are rerun in
resource-limited Docker; existing native fields only choose a viable resolution.
"""
import json,sys
from pathlib import Path
import numpy as np
from catalog import ROOT,WORK,SECTION,catalog
from build_local import ANALYTIC,numerical,observation_grid
from analytic import evaluate
from caeoj.sdk import load_problem,write_result
from caeoj.case_grading import grade_case

def main():
 out=ROOT/'runs/benchmarks/cfdcodebench-24-20261020/calibration';out.mkdir(parents=True,exist_ok=True);rows=[]
 for c in catalog():
  i=c['index'];source=WORK/'local-pool'/c['task']/f'C{i:02}-base';p=load_problem(source/'input/problem.json');xy,_=observation_grid(c)
  trials=[]
  if i in ANALYTIC or i==24:trials=[('formula',128,evaluate(i,xy,128))]
  elif i==23:
   from independent_ode_evp import pipe
   trials=[('Galerkin',32,{c['fields'][0]:np.array([pipe(32)['eigenvalue_real']])})]
  elif i==19:
   for l in range(3):
    with np.load(WORK/'cylinder-fem'/f'L{l}-dt1/native.npz') as a:trials.append(('NGSolve',l,{n:a[n].ravel().copy() for n in c['fields']}))
  else:trials=[('producer',l,numerical(c,xy,l,1)) for l in range(3)]
  chosen=None;attempts=[]
  for method,level,vals in trials:
   if vals is None:continue
   target=out/f'C{i:02}-selection-result.h5';write_result(target,p,{n:np.asarray(vals[n],dtype='float64').reshape(1,len(xy),1) for n in c['fields']})
   grade=grade_case(source/'input/problem.json',target,source/'reference/grading.json');attempts.append({'level':level,'score':grade['score']})
   if grade['score']==1:chosen={'index':i,'task':c['task'],'method':method,'level':level,'selection_score':1,'attempts':attempts};break
  if chosen is None:raise ValueError('No available practical passing resolution C'+str(i))
  rows.append(chosen)
 plan={'tasks':rows,'cpus':4,'memory_mb':8192,'purpose':'Actual producer/formula solve cost, not frozen reference replay','environment':'Docker calibration image from existing locally installed scientific environment, Python3.12; protocol/candidate image validated separately'}
 (out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8');print(json.dumps(plan))
if __name__=='__main__':main()
