from pathlib import Path
import hashlib,json,zipfile,sys,subprocess,copy,math
import numpy as np,h5py
B=Path(r'C:/Users/Jim Zhou/.codex/tmp/repair22-moose22074-final-candidate')
R=Path(r'D:/Code/CAE-Bench-OJ/runs/candidate-review/repair22-moose22074-final')
Z=Path(r'C:/Users/Jim Zhou/.cache/caeoj-repair22/moose22074-dist-v1/solid-fluid-energy-observation-repair-agent.zip')
Q=B/'qbank/19-solver-repair/19.4-observations/solid-fluid-energy-observation-repair'
sys.path.insert(0,str(B/'src'))
from caeoj.sdk import load_problem,write_result
sha=lambda x:hashlib.sha256(x).hexdigest()
with zipfile.ZipFile(Z) as z:
    manifest={'zip':str(Z),'sha256':sha(Z.read_bytes()),'member_count':len(z.infolist()),'members':[{'path':i.filename,'size':i.file_size,'sha256':sha(z.read(i.filename))} for i in z.infolist()]}
manifest['explanatory_materials']=[m for m in manifest['members'] if m['path'].endswith(('/instruction.md','/DATA.md','/CONTRACT.md'))]
(R/'materials.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
log={'commands':[],'samples':{},'understanding_inputs':{}}
def cli(*args):
    cmd=[sys.executable,'-m','caeoj',*map(str,args)]
    p=subprocess.run(cmd,text=True,capture_output=True,env={**__import__('os').environ,'PYTHONPATH':str(B/'src')})
    log['commands'].append({'argv':cmd,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
    assert p.returncode==0,(cmd,p.stdout,p.stderr)
def arrays(path):
    with h5py.File(path) as h:
        return {k:{'dtype':str(h[k].dtype),'shape':list(h[k].shape),'values':h[k][()].tolist()} for k in h}
for n in ('01','02'):
    s=Q/'samples'/n; p=s/'input/problem.json'; problem=load_problem(p)
    log['samples'][n]={str(f.relative_to(s)):arrays(f) for f in s.rglob('*.h5')}
    cli('validate-input',p)
    cli('info','--input',p)
    cli('validate-output','--input',p,'--output',s/'output/result.h5')
    cli('validate-output','--input',p,'--output',s/'reference/reference.h5')
    cli('grade','--input',p,'--output',s/'output/result.h5','--grading',s/'reference/grading.json')
    with h5py.File(s/'output/result.h5') as h:
        fields={v['array']:h[v['array']][()] for v in problem.manifest['outputs'].values()}
    out=B/f'roundtrip-{n}.h5';write_result(out,problem,fields)
    assert arrays(out)==arrays(s/'output/result.h5')
    cli('grade','--input',p,'--output',out,'--grading',s/'reference/grading.json')
# Two complete legal inputs, without a solver or numerical reference generation.
base=json.loads((Q/'samples/01/input/problem.json').read_text())
for name,model in [('rz-ad-renamed','explicit-rz-ad-renamed-v1'),('transient-initial','coupled-rz-transient-v1')]:
    d=copy.deepcopy(base); d['spatial_dimension']=2;d['physics']['model']=model
    vals={'length_z':0.,'nz':0,'density_solid':1.,'density_fluid':1.,'specific_heat_solid':1.,'specific_heat_fluid':1.,'source_constant':1.,'source_radial':0.,'source_axial':0.}
    if name=='transient-initial': vals.update(inlet_speed=.1,dt=.1,step_count=2,source_time_slope=1.)
    for k,v in vals.items():d['physics']['parameters'][k]['value']=v
    folder=B/name;folder.mkdir(exist_ok=True); (folder/'problem.json').write_text(json.dumps(d,indent=2))
    t=np.zeros((1,1,10));u=np.zeros((1,1,12))
    if name=='rz-ad-renamed':t[0,0,0]=300;t[0,0,1]=2;u[0,0,1]=1
    with h5py.File(folder/'input.h5','w') as h:
        for k,v in {'experiment_ids':np.array([1],dtype=np.int64),'initial_time':np.array([0.]),'times':np.arange(3)*.1 if name=='transient-initial' else np.array([0.]),'temperature_coefficients':t,'velocity_coefficients':u}.items():h.create_dataset(k,data=v)
    cli('validate-input',folder/'problem.json');loaded=load_problem(folder/'problem.json')
    log['understanding_inputs'][name]={'path':str(folder/'problem.json'),'manifest_sha256':sha((folder/'problem.json').read_bytes()),'arrays':arrays(folder/'input.h5')}
log['understanding_inputs']['rz-ad-renamed']['analytic_observation_interpretation']={'energy_solid':451*math.pi/6,'energy_fluid':1357*math.pi/6,'advection_power':7*math.pi/6,'source_power':math.pi/4,'robin_power':0,'wrong_planar_advection':.75,'boundary_enthalpy_power':(7+2*1357)*math.pi/6}
log['understanding_inputs']['transient-initial']['initial_interpretation']={'energy_solid':75*math.pi,'energy_fluid':225*math.pi,'advection_power':0,'source_power':math.pi/4,'robin_power':0,'source_power_all_frames':[math.pi/4*(1+t) for t in (0,.1,.2)],'no_initial_storage_difference':True,'later_thermal_outputs':'not calculated; require native coupled solve'}
(R/'verification.json').write_text(json.dumps(log,indent=2),encoding='utf-8')
print(json.dumps({'samples':log['samples'],'understanding_inputs':log['understanding_inputs'],'commands':[(x['argv'][3],x['exit_code']) for x in log['commands']]},indent=2))
