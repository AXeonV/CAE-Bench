"""Independent qualification, not reference production: original dense weak API,
analytic P1 mass matrix, and independently integrated exterior Green kernels."""
from pathlib import Path
import argparse
import hashlib,json,subprocess,time
import numpy as np
ROOT=Path(__file__).resolve().parents[5]
TASK=ROOT/'qbank/19-solver-repair/19.6-waves/complex-helmholtz-fmm-repair'
parser=argparse.ArgumentParser();parser.add_argument('--dataset',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
DATA=args.dataset.resolve()
OUT=args.output.resolve()
OUT.mkdir(parents=True,exist_ok=True)
DOCKER='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
image=json.loads(subprocess.check_output([DOCKER,'image','inspect','caeoj-bempp20-runtime:base']))[0]['Id']
worker=(TASK/'public/driver.py').read_text().replace("assembler='fmm'","assembler='dense'").replace('.strong_form()', '.weak_form()')
assert worker.count("assembler='dense'")==2 and '.strong_form()' not in worker
(OUT/'dense-weak-worker.py').write_text(worker,encoding='utf-8')
report={'image_id':image,'worker_sha256':hashlib.sha256(worker.encode()).hexdigest(),'reference_producer':False,'cases':[]}
def complex_values(raw):
    a=np.asarray(raw);return a[:,0::2]+1j*a[:,1::2]
def compare(actual,expected):
    # Public grading treats real/imaginary scalar components separately.
    a=np.stack([actual.real,actual.imag],axis=-1);e=np.stack([expected.real,expected.imag],axis=-1)
    ratio=abs(a-e)/(1e-6+1e-5*abs(e))
    return {'max_absolute_error':float(abs(a-e).max()),'max_tolerance_fraction':float(ratio.max()),'passed':bool(np.all(ratio<=1))}
for case in sorted((DATA/'cases').iterdir()):
    payload=json.loads((case/'native-payload.json').read_text())
    if payload['operation']!=1:continue
    out=OUT/case.name;out.mkdir(exist_ok=True)
    cmd=[DOCKER,'run','--rm','--network','none','--cpus','4','--memory','4g','--user','1000:1000','--read-only','--tmpfs','/tmp:rw,size=512m','-v',str(OUT)+':/audit:ro','-e','HOME=/tmp','-w','/tmp','-i',image,'/opt/bempp-env/bin/python','/audit/dense-weak-worker.py']
    start=time.monotonic();run=subprocess.run(cmd,input=json.dumps(payload),text=True,capture_output=True,timeout=600)
    (out/'stdout.json').write_text(run.stdout,encoding='utf-8');(out/'stderr.log').write_text(run.stderr,encoding='utf-8')
    assert run.returncode==0,(case.name,run.stderr)
    dense=json.loads(run.stdout)
    # Actual FMM producer payload, not a regenerated theoretical reference.
    actual=json.loads((DATA/'replay/reference'/case.name/'stdout.json').read_text())
    v=np.asarray(payload['vertices']);tri=np.asarray(payload['triangles']);rho=complex_values(payload['density']).ravel()
    cross=np.cross(v[tri[:,1]]-v[tri[:,0]],v[tri[:,2]]-v[tri[:,0]])
    area2=np.linalg.norm(cross,axis=1);normal=cross/area2[:,None]
    mass=np.zeros((len(v),len(v)))
    for ids,a2 in zip(tri,area2):mass[np.ix_(ids,ids)]+=a2/24*(np.ones((3,3))+np.eye(3))
    row={'case':case.name,'dense_command':cmd,'dense_seconds':time.monotonic()-start,'comparisons':{},'mass_condition_number':float(np.linalg.cond(mass))}
    for name in ['single_layer','double_layer','hypersingular']:
        key='boundary_'+name
        row['comparisons'][key]=compare(complex_values(actual[key]),np.linalg.solve(mass,complex_values(dense[key])))
    for name in ['single_layer','double_layer']:
        key='potential_'+name;row['comparisons']['dense_'+key]=compare(complex_values(actual[key]),complex_values(dense[key]))
    targets=np.asarray(payload['targets']);k=complex(payload['wavenumber_real'],payload['wavenumber_imag'])
    estimates={}
    for order in [16,24]:
        gx,gw=np.polynomial.legendre.leggauss(order);a=(gx+1)/2;wa=gw/2
        aa,bb=np.meshgrid(a,a,indexing='ij');weights=(np.outer(wa,wa)*(1-aa)).ravel()
        bary=np.stack([(1-aa)*(1-bb),aa,(1-aa)*bb],axis=-1).reshape(-1,3)
        points=np.einsum('qj,ejc->eqc',bary,v[tri]);density=np.einsum('qj,ej->eq',bary,rho[tri])
        diff=targets[:,None,None,:]-points[None,:,:,:];r=np.linalg.norm(diff,axis=-1)
        green=np.exp(1j*k*r)/(4*np.pi*r)
        derivative=-green*(1j*k-1/r)*np.einsum('teqc,ec->teq',diff,normal)/r
        estimates[order]={}
        for name,kernel in [('single_layer',green),('double_layer',derivative)]:
            value=np.einsum('teq,eq,q,e->t',kernel,density,weights,area2)[:,None]
            estimates[order][name]=value
            row['comparisons'][f'quadrature{order}_potential_'+name]=compare(complex_values(actual['potential_'+name]),value)
    row['quadrature_convergence']={name:float(abs(estimates[24][name]-estimates[16][name]).max()) for name in estimates[16]}
    row['passed']=all(x['passed'] for x in row['comparisons'].values())
    report['cases'].append(row);report['passed']=all(x['passed'] for x in report['cases'])
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(case.name,row['passed'],row['comparisons'],flush=True)
    assert row['passed'],row
