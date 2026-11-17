"""Collect actual producer convergence/resources and independent OpenFOAM runs."""
from pathlib import Path
import argparse,hashlib,json,re,shutil
import h5py,numpy as np
from assess_openfoam import sample as foam_sample,metrics
from convert_supplement import sample,vtu,probes
from supplement80 import specifications


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def collect(root):
    evidence=root/'evidence';evidence.mkdir(exist_ok=True)
    rows=json.loads((root/'numerical-validation.json').read_text());assert len(rows)==64 and all(r['accepted'] for r in rows)
    executions=[];validation=[]
    for row in rows:
        name=row['name']
        for n in map(int,row['levels']):
            d=root/'runs'/name/f'n{n}';r=json.loads((d/'execution.json').read_text());log=(d/'solver.log').read_text()
            residuals=re.findall(r'alpha\s*=.*?res\s*=\s*([\deE.+-]+)',log)
            tolerance=1e-8 if row['definition'].get('open_shaped') else 1e-10
            assert r['returncode']==0 and residuals and float(residuals[-1])<=tolerance,(d,residuals[-1:])
            resource=(d/'resource.txt').read_text();rss=int(re.search(r'Maximum resident set size \(kbytes\):\s*(\d+)',resource).group(1))
            assert r['seconds']<600 and rss<4*1024*1024 and len(r['cpu_ids'])==4
            r.update(name=name,level=n,last_nonlinear_residual=float(residuals[-1]),nonlinear_tolerance=tolerance,peak_rss_kib=rss)
            dest=evidence/'lethe'/name/f'n{n}';dest.mkdir(parents=True,exist_ok=True)
            for f in ('case.prm','solver.log','execution.json','definition.json','resource.txt'):shutil.copyfile(d/f,dest/f)
            # Exact sampled data from every solved level remain available without raw download.
            spec=row['definition'];xy=probes(spec);path=sorted(d.glob('solution.*.00000.vtu'))[-1];values=sample(vtu(path),xy,relative_pressure=not spec.get('open_shaped'));values['pressure']*=spec['rho']
            angle=spec.get('coordinate_rotation_radians',0.);R=np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
            values['velocity']=values['velocity']@R.T
            # velocity_gradient preserves the producer frame; xy/velocity use the
            # case frame. The rotation and invariant shear norm are documented.
            np.savez_compressed(dest/'samples.npz',xy=xy@R.T,**values)
            executions.append(r)
        if name in ('x80-periodic-straight','x80-periodic-counter-wall'):
            spec=row['definition'];n=max(map(int,row['levels']));d=root/'runs'/name/f'n{n}';xy=probes(spec);values=sample(vtu(sorted(d.glob('solution.*.00000.vtu'))[-1]),xy)
            y=xy[:,1];u=.002/(2*spec['nu'])*y*(3-y);du=.002/(2*spec['nu'])*(3-2*y)
            if name.endswith('counter-wall'):u+=-.1+.2*y/3;du+=.2/3
            ratios=dict(velocity=float(np.max(np.abs(values['velocity']-np.column_stack((u,np.zeros(len(y)))))/(.001+.01*np.abs(np.column_stack((u,np.zeros(len(y)))))))),
                        pressure=float(np.max(np.abs(values['pressure']*spec['rho'])/.1)),shear_rate=float(np.max(np.abs(values['shear_rate'][:,0]-np.abs(du))/(.01+.01*np.abs(du)))))
            assert max(ratios.values())<1,ratios
            validation.append(dict(name=name,independent_basis='MIT published Couette-Poiseuille formula, acceleration equivalent to pressure drive with zero periodic pressure jump',tolerance_fractions=ratios))
    (evidence/'lethe-executions.json').write_text(json.dumps(executions,indent=2)+'\n')
    (evidence/'periodic-analytic-check.json').write_text(json.dumps(validation,indent=2)+'\n')
    cross=[]
    for folder in sorted((root/'openfoam').iterdir()):
        if not folder.is_dir():continue
        name=folder.name;inp=root/'source/cases'/name;ref=root/'source/reference'/name
        j=json.loads((inp/'problem.json').read_text());mat=j['materials']['liquid'];rho=mat['density']['parameters']['density']['value'];mu=mat['viscosity']['parameters']['dynamic_viscosity']['value']
        with h5py.File(inp/'input.h5') as h:xy=h['probe_xy'][:];ids=h['probe_ids'][:];clock=h['clock'][:]
        with h5py.File(ref/'reference.h5') as h:reference={q:h[q][0] for q in ('velocity','pressure','shear_rate','density','dynamic_viscosity')}
        levels={};comp={};exe={}
        for d in sorted(folder.glob('n*'),key=lambda p:int(p.name[1:])):
            if not (d/'execution.json').exists():raise ValueError(('unfinished independent run',d))
            n=int(d.name[1:]);execution=json.loads((d/'execution.json').read_text());assert execution['solver']['returncode']==0 and execution['converged']
            assert 'Mesh OK.' in (d/'checkMesh.log').read_text()
            mapping=json.loads((d/'translation.json').read_text());assert mapping['input_hashes']=={p.name:sha(p) for p in inp.iterdir() if p.is_file()},(name,'input changed after independent solve')
            values,path=foam_sample(d,xy,rho,mu);levels[n]=values;exe[str(n)]=execution
            comp[str(n)]={q:metrics(values[q],reference[q],atol,xy,ids) for q,atol in [('velocity',.001),('pressure',.1),('shear_rate',.01)]}
            dest=evidence/'openfoam'/name/f'n{n}';dest.mkdir(parents=True,exist_ok=True)
            for f in ('solver.log','execution.json','translation.json','checkMesh.log','blockMesh.log'):shutil.copyfile(d/f,dest/f)
            shutil.copyfile(path,dest/'observations.xy')
            for foldername in ('0','constant','system'):
                for p in (d/foldername).iterdir():
                    if p.is_file():
                        target=dest/foldername/p.name;target.parent.mkdir(exist_ok=True);shutil.copyfile(p,target)
            with h5py.File(dest/'result.h5','w') as h:
                h['clock']=clock;h['probe_ids']=ids
                for q,v in values.items():h[q]=v[None].astype(float)
        ns=sorted(levels);assert len(ns)>=3
        lo,hi=ns[-2:];mesh={q:metrics(levels[lo][q],levels[hi][q],atol,xy,ids) for q,atol in [('velocity',.001),('pressure',.1),('shear_rate',.01)]}
        cross.append(dict(name=name,levels=exe,comparison=comp,final_mesh_comparison=mesh,
                          accepted=max(v['max_tolerance_fraction'] for v in comp[str(hi)].values())<=1 and max(v['max_tolerance_fraction'] for v in mesh.values())<.25))
    (evidence/'openfoam-comparison.json').write_text(json.dumps(cross,indent=2)+'\n')
    print('independent',[(r['name'],r['accepted'],max(v['max_tolerance_fraction'] for v in r['comparison'][str(max(map(int,r['levels'])))].values()),max(v['max_tolerance_fraction'] for v in r['final_mesh_comparison'].values())) for r in cross],flush=True)
    assert len(cross)==8 and all(r['accepted'] for r in cross)
    summary=dict(numerical_cases=64,analytic_cases=16,lethe_runs=len(executions),all_lethe_converged=True,max_seconds=max(r['seconds'] for r in executions),max_peak_rss_kib=max(r['peak_rss_kib'] for r in executions),max_grid_tolerance_fraction=max(max(r['comparison'].values()) for r in rows),
                 independent_openfoam_cases=8,independent_openfoam_runs=sum(len(r['levels']) for r in cross),independent_periodic_analytic_cases=2,
                 max_cross_tolerance_fraction=max(v['max_tolerance_fraction'] for r in cross for v in r['comparison'][str(max(map(int,r['levels'])))].values()))
    (evidence/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args();collect(a.root)
