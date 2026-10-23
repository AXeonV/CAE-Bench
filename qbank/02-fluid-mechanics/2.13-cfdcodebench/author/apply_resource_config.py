"""Apply measured resource budgets after all24 real limited solves have passed."""
import hashlib,json,math,subprocess,sys
from pathlib import Path
from catalog import ROOT,SECTION,catalog
from caeoj_tools import data_pool

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 run=ROOT/'runs/benchmarks/cfdcodebench-24-20261020';summary=read(run/'calibration/summary.json');release=read(run/'release/release.json')
 assert summary['phase']=='completed' and summary['completed']==24 and len(summary['rows'])==24
 assert release['phase']=='verified' and release['verified_count']==24
 rows={r['index']:r for r in summary['rows']};evidence=[]
 for c in catalog():
  i=c['index'];r=rows[i];assert r['actual_solve'] and r['score']==1 and r['cpu_max']=='400000 100000' and int(r['memory_max'])==8192*1024**2
  assert r['peak_rss_kib']<8192*1024
  timeout=max(300,int(math.ceil((4*r['wall_seconds']+30)/60))*60)
  agent_seconds=5400 if i in (12,19,21,22,23) else 3600
  task=SECTION/c['task'];data_pool.verify(task,strict=True)
  config={'timeout_seconds':timeout,'max_output_bytes':None,'evaluation_timeout_seconds':60,'stage':'calibrated','verifier_budget':{'base_seconds':300,'per_case_overhead_seconds':60}}
  write(task/'judge-config.json',config)
  directory=task/'harbor';directory.mkdir(exist_ok=True)
  (directory/'task.toml').write_text(f'[agent]\ntimeout_sec = {agent_seconds}.0\n\n[environment]\ncpus = 4\nmemory_mb = 8192\nbuild_timeout_sec = 1800.0\n',encoding='utf-8')
  (directory/'requirements.txt').write_text('scipy>=1.14,<2\n',encoding='utf-8')
  detail={'index':i,'task':c['task'],'hf_commit':release['hf']['fixed_commit'],'actual_solve_measurement':r,'rule':'solver wall=max300,ceil((4*measured_wall+30)/60)*60;4CPU and8192MiB, all processes/threads share;agent3600 or5400 for heavier modelling tasks','scope':'Scientific Python3.12 producer environment in actual Docker resource limits; candidate Python3.14 protocol image separately validated. Measurements do not guarantee every numerical method fits. No reference replay used for solving cost.','judge_config_sha256':sha(task/'judge-config.json'),'harbor_config_sha256':sha(directory/'task.toml'),'measurement_report':(run/'calibration'/f'C{i:02}/measurement.json').relative_to(ROOT).as_posix()}
  write(task/'author/data-evidence/resource-calibration.json',detail);evidence.append({k:detail[k] for k in ('index','task','judge_config_sha256','harbor_config_sha256')})
 from render import main as render
 render()
 # Rendering must retain actual execution configs, and all scientific payloads.
 for c in catalog():data_pool.verify(SECTION/c['task'],strict=True)
 write(SECTION/'author/resource-calibration-index.json',{'tasks':24,'basis_sha256':sha(run/'calibration/summary.json'),'rows':evidence,'hf_commit':release['hf']['fixed_commit']})
 index_path=SECTION/'author/local-assembly-index.json';index=read(index_path);index['resource_status']='calibrated';index['resource_index']='resource-calibration-index.json';write(index_path,index)
 write(run/'resources-applied.json',{'tasks':24,'render_preserves_measured_configs':True,'rows':evidence})
 print(json.dumps({'resources_applied':24,'all_payloads_strict_verified':True}))
if __name__=='__main__':main()
