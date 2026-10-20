"""Audit real local references without promoting unfinished or failed checks.

Run after build_local.py using the repository Python. This never computes a PDE,
changes thresholds, publishes data, selects formal cases, or invokes candidates.
"""
import hashlib,json
from pathlib import Path
import numpy as np
from scipy.interpolate import CubicSpline,RectBivariateSpline
from catalog import WORK,SECTION,catalog
from analytic import evaluate,gaussian_modes
from build_local import observation_grid,differences,numerical,fourier


def load(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def scalar_result(c,a,b,w):return differences(c,a,b,w)
def main():
    summaries={r['index']:r for r in load(WORK/'local-validation-summary.json')}
    analytic=load(WORK/'independent-analytic.json');ode=load(WORK/'independent-ode-evp.json')
    acceptance=load(SECTION/'author/reference-acceptance.json').get('case_overrides',{}) if (SECTION/'author/reference-acceptance.json').exists() else {}
    rows=[]
    for c in catalog():
        i=c['index'];case=WORK/'local-pool'/c['task']/f'C{i:02}-base';s=summaries[i]
        xy,w=observation_grid(c);checks=dict(s['comparisons']);missing=[];limits=[]
        if i in (1,2,4,7,8,9,11,13):checks['independent_representation']=analytic[f'C{i:02}']
        if i==3:checks['clawpack_exact_Riemann']=load(WORK/'clawpack-sod-comparison.json')['comparison']
        if i in (2,5,8):
            files=sorted((WORK/'independent-source-checks').glob(f'C{i:02}-N*.npz'),key=lambda p:int(p.stem.split('-N')[1]))
            if not files:missing.append('independent source refinement')
            for path in files:
                with np.load(path) as a:
                    values=dict(u=CubicSpline(a['x'],a['u'])(xy[:,0]) if i in (2,5) else RectBivariateSpline(a['y'],a['x'],a['u'])(xy[:,1],xy[:,0],grid=False))
                    checks['source_'+path.stem]=differences(c,values,evaluate(i,xy),w)
        if i in (10,14,15,16):
            for l in range(3):
                path=WORK/'independent-elliptic'/f'C{i:02}'/f'L{l}'/'values.npy'
                if path.exists():checks[f'independent_FEM_L{l}']=differences(c,{c['fields'][0]:np.load(path)},evaluate(i,xy),w)
                elif l==2:missing.append('fine independent FEM')
            if i==16:
                k=np.arange(1,257)*np.pi/2;lam=k[:,None]**2+k[None,:]**2
                modes=gaussian_modes(2,-1,0,.1,256)
                bound=float(np.sum(np.abs(200*np.outer(modes,modes)*(1-1/lam))*np.exp(-3*lam)))
                limits.append({'steady_comparison_uniform_transient_bound':bound,'method':'sum of absolute heat-mode coefficients; higher modes exponentially suppressed'})
        if i==17:checks['independent_flux_BVP']=differences(c,{'u':np.array(ode['cess'][-1]['u'])},evaluate(i,xy),w)
        if i==6:
            selected=numerical(c,xy,2,2)
            for l in range(3):
                path=WORK/'independent-burgers'/f'L{l}'/'native.npz'
                if not path.exists():path=WORK/'independent-burgers'/f'L{l}'/'values.npy'
                if path.exists() and selected is not None:
                    if path.suffix=='.npy':u=np.load(path)
                    else:
                        with np.load(path) as a:u=a['u'].ravel()
                    checks[f'independent_FEM_L{l}']=differences(c,dict(u=u,v=u.copy()),selected,w)
            if 'independent_FEM_L2' not in checks:missing.append('independent Burgers FEM')
        if i in (12,18):
            selected=numerical(c,xy,2,2)
            for n in (64,128):
                path=WORK/'independent-cavity-openfoam'/f'C{i:02}'/f'N{n}'/'native.npz'
                if path.exists() and selected is not None:
                    with np.load(path) as a:checks[f'independent_OpenFOAM_N{n}']=differences(c,{f:a[f].ravel() for f in c['fields']},selected,w)
            if 'independent_OpenFOAM_N128' not in checks:missing.append('fine independent cavity OpenFOAM')
        if i==19:
            selected=numerical(c,xy,2,1)
            for l,d in ((0,1),(1,1),(2,1),(2,2)):
                path=WORK/'cylinder-fem'/f'L{l}-dt{d}'/'native.npz'
                if selected is not None and path.exists():
                    with np.load(path) as a:checks[f'independent_FEM_L{l}_dt{d}']=differences(c,{f:a[f].ravel() for f in c['fields']},selected,w)
            if 'independent_FEM_L2_dt2' not in checks:missing.append('fine independent cylinder FEM and time check')
            limits.append('OpenFOAM psi/omega are reconstructed from velocity; reconstruction and exterior streamfunction closure require separate audit')
        if i==20:
            path=WORK/'independent-kdv-rk443/native.npz';receipt=path.with_name('process.json');selected=numerical(c,xy,2,2)
            if path.exists() and receipt.exists() and load(receipt).get('returncode')==0 and selected is not None:
                with np.load(path) as a:checks['RK443_vs_SBDF2']=differences(c,dict(u=fourier(a['u'],a['x'],xy[:,0],10)),selected,w)
            else:missing.append('independent RK443 time integration')
        if i in (20,21,22):limits.append('Space/time checks use the same Dedalus engine and equation configuration; not an independent solver cross-validation')
        if i==23:
            selected=numerical(c,xy,2,1)
            if selected is not None:checks['independent_Galerkin']={c['fields'][0]:dict(max_abs=abs(float(next(iter(selected.values()))[0])-ode['pipe'][-1]['eigenvalue_real']))}
            limits.append({'independent_Galerkin_mass_condition':ode['pipe'][-1]['mass_condition'],'note':'Ill-conditioning recorded; convergence at order32/48 is required along with residuals'})
        expected=['truncation_128_256'] if i in {1,2,3,4,5,7,8,9,10,11,13,14,15,16,17} else ['space_L1_L2']
        if i in (6,12,18,20,21,22):expected.append('half_dt')
        required_independent={1:'independent_representation',2:'source_C02-N801',3:'clawpack_exact_Riemann',4:'independent_representation',5:'source_C05-N8193',6:'independent_FEM_L2',7:'independent_representation',8:'source_C08-N241',9:'independent_representation',10:'independent_FEM_L2',11:'independent_representation',12:'independent_OpenFOAM_N128',13:'independent_representation',14:'independent_FEM_L2',15:'independent_FEM_L2',16:'independent_FEM_L2',17:'independent_flux_BVP',18:'independent_OpenFOAM_N128',19:'independent_FEM_L2_dt2',20:'RK443_vs_SBDF2',23:'independent_Galerkin',24:'independent_regular_IVP'}
        if i in required_independent:expected.append(required_independent[i])
        override=acceptance.get(str(i))
        if override:
            if set(override) != {'metric','limit','comparison','basis','selected_native','scope','limitations'} or override['metric']!='nmse' or override['comparison']!='strict_less' or override['limit']!=0.01 or i!=19:raise ValueError('Unreviewed reference acceptance override')
            limits.append(override['limitations'])
        failed=[]
        for key in expected:
            if key not in checks:missing.append(key);continue
            for f,value in checks[key].items():
                metric='max_abs' if i==23 else 'nrmse';threshold=1e-5 if i==23 else .01
                if override:metric,threshold=override['metric'],override['limit']
                if (value[metric]>=threshold if override else value[metric]>threshold):failed.append(dict(check=key,field=f,metric=metric,value=value[metric],limit=threshold))
        ref=case/'reference/reference.h5'
        if not ref.exists() or not s.get('reference_sha256'):missing.append('selected complete reference')
        elif sha(ref)!=s['reference_sha256']:missing.append('reference SHA256 mismatch')
        for source in s.get('production_sources',[]):
            file=(WORK.parent.parent if source.get('base')=='repository' else WORK)/source['file']
            if not file.exists() or sha(file)!=source['sha256']:missing.append('production source SHA256 mismatch: '+source['file'])
        if i not in {1,2,3,4,5,7,8,9,10,11,13,14,15,16,17} and not s.get('production_sources'):missing.append('bound production-source fingerprints')
        status='verification_pending' if missing else 'verification_failed' if failed else 'verified_with_stated_limits'
        row=dict(index=i,task=c['task'],case_id=s['case_id'],status=status,missing=sorted(set(missing)),failed=failed,limitations=limits,checks=checks,reference_sha256=s.get('reference_sha256'))
        if override:row['reference_acceptance']=override
        (case/'certification.json').write_text(json.dumps(row,indent=2,ensure_ascii=False),encoding='utf-8');rows.append(row)
    (WORK/'certification.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding='utf-8')
    from datetime import datetime,timezone
    index=dict(schema_version=1,updated_utc=datetime.now(timezone.utc).isoformat(),source_revision=__import__('catalog').REVISION,raw_evidence_root=WORK.relative_to(WORK.parent.parent).as_posix(),scope='reference_numerical_verification',assembly_index='local-assembly-index.json',release_index='hf-release-index.json',resource_index='resource-calibration-index.json',
        rows=[{k:r[k] for k in ('index','task','case_id','status','missing','failed','limitations','reference_sha256')} for r in rows],
        scripts={p.name:sha(p) for p in sorted((SECTION/'author').glob('*.py'))})
    (SECTION/'author/evidence-index.json').write_text(json.dumps(index,indent=2,ensure_ascii=False),encoding='utf-8')
    for r in rows:print(json.dumps({k:r[k] for k in ('index','status','missing','failed')},ensure_ascii=False))
if __name__=='__main__':main()
