"""Replay audited published payloads into a temporary workspace, no remote reads/solve."""
import argparse,hashlib,json,sys
from pathlib import Path
from unittest.mock import patch
import h5py,numpy as np
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'pyproject.toml').is_file());sys.path.insert(0,str(ROOT/'src'))
from utils.PDEBench.selection import make_selection
from utils.PDEBench.pipeline import workspace_init,prepare_entry,prepare_examples,verify
from utils.PDEBench.storage import Budget,NetworkBudget,atomic_json
from utils.PDEBench.models import BY_TASK
from utils.PDEBench.checks import source_geometry
from caeoj.sdk import load_problem,load_result
parser=argparse.ArgumentParser();parser.add_argument('--cache-repo',type=Path,required=True);parser.add_argument('--workspace',type=Path,required=True);args=parser.parse_args()
b=Path(__file__).parent;audit=json.loads((b/'source-audit.json').read_text());entries=[];by_id={}
for i,record in enumerate(audit['records'],1):
 entries.append({'task':'darcy-flow-2d','source_id':record['source']['id'],'index':record['source_index'],'frames':[0],'role':'case','id':f'{i:03d}'})
 by_id[record['source']['id']]=record
selection=make_selection(entries,examples={'darcy-flow-2d':{'01':{'case':'001'},'02':{'case':'005'}}});w=args.workspace.resolve();disk=Budget([w],500_000_000);network=NetworkBudget(0);workspace_init(w,selection,disk)
def cached(entry,*unused,**kwargs):
 record=by_id[entry['source_id']];p=args.cache_repo/record['cached_payload'];assert hashlib.sha256(p.read_bytes()).hexdigest()==record['payload_sha256'];assert entry['index']==record['source_index']
 with h5py.File(p) as h:
  coords=[h[a+'-coordinate'][...] for a in 'xy'];times=np.array([0.]);config={'beta':record['beta_attribute']};values={k:h[k][...] for k in ('state','diffusivity')}
 source_geometry(BY_TASK['darcy-flow-2d'],entry['source'],coords,times,config)
 return coords,times,config,values
with patch('utils.PDEBench.pipeline.read_entry',cached):
 for entry in selection['entries']:prepare_entry(w,entry,w/'cache',disk,None,1,network)
prepare_examples(w,selection,disk);report=verify(w,selection);assert report['assembly_ready'] and report['case_count']==5
for entry in selection['entries']:
 task=next(w.glob('qbank/*/*/darcy-flow-2d'));problem=load_problem(task/'cases'/entry['id']/'problem.json');result=load_result(problem,task/'reference'/entry['id']/'reference.h5')
 with h5py.File(args.cache_repo/by_id[entry['source_id']]['cached_payload']) as h:np.testing.assert_array_equal(result['state'],h['state'][...].reshape(1,-1,1))
report['network']=network.report();report['scope']='Five pre-existing source-cache samples replayed with audited beta attributes; source transport not rerun. No source values modified, no solver or numerical screening.'
atomic_json(w/'replay-report.json',report);print(json.dumps({'status':report['status'],'cases':5,'examples':len(report['examples']),'network':network.report()}))
