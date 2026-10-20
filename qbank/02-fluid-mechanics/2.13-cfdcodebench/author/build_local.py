"""Build local-only case inputs and bind only actually computed references.

No HF/network operations or modification of formal selections. Numeric status is
independent of contract/grading-chain status; unfinished cases never get a fake
reference. Run with the repository .venv Python.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
from scipy.interpolate import BarycentricInterpolator, CubicSpline, RectBivariateSpline
from catalog import catalog,WORK,REVISION,SECTION
from analytic import evaluate
from render import grading,dumps
from caeoj.sdk import load_problem
from caeoj.storage import write_hdf5
from caeoj.case_grading import prepare_case

ANALYTIC={1,2,3,4,5,7,8,9,10,11,13,14,15,16,17}

def observation_grid(c):
    d=c['domain'];i=c['index']
    if i==23:return np.empty((1,0)),np.ones(1)
    if i==19:
        faces=.5+9.5*(.5-.5*np.cos(np.linspace(0,np.pi,65)))
        r=(faces[1:]+faces[:-1])/2;phi=(np.arange(64)+.5)*2*np.pi/64
        pp,rr=np.meshgrid(phi,r)
        xy=np.column_stack((rr.ravel()*np.cos(pp.ravel()),rr.ravel()*np.sin(pp.ravel())))
        return xy,np.repeat((faces[1:]**2-faces[:-1]**2)/2,64)*2*np.pi/64
    if c['dimension']==1:
        if i==3:x=d[0]+(np.arange(201)+.5)*(d[1]-d[0])/201
        else:x=np.linspace(d[0],d[1],201)
        w=np.ones(len(x));w[[0,-1]]=.5
        if i==24:
            faces=np.r_[0,(x[1:]+x[:-1])/2,1];w=np.diff(faces**3)/3
        return x[:,None],w
    x=d[0]+(np.arange(41)+.5)*(d[1]-d[0])/41
    y=d[2]+(np.arange(41)+.5)*(d[3]-d[2])/41
    xx,yy=np.meshgrid(x,y)
    return np.column_stack((xx.ravel(),yy.ravel())),np.ones(xx.size)

def input_case(c,path,xy,weights):
    n=len(weights);ids=np.arange(n,dtype='int64')*3+7;times=np.array([c['time']],dtype='float64')
    loc=dict(kind='entities' if c['index']==23 else 'points',ids='ids')
    arrays=dict(ids=ids,times=times,weights=weights[None,:,None].astype('float64'))
    if c['index']!=23:loc['coordinates']='coordinates';arrays['coordinates']=xy.astype('float64')
    def field(name,quantity):return dict(array=name,quantity=quantity,location='observations',time_axis='output',
        dtype='float64',kind='scalar',component_shape=[1],components=['value'],unit='1',value_kind='point')
    manifest=dict(task=c['task'],spatial_dimension=c['dimension'],data_file='input.h5',
        geometries={},meshes={},locations=dict(observations=loc),time_axes=dict(output='times'),
        fields=dict(weights=field('weights','observation_weight')),
        outputs={name:field(name,name) for name in c['fields']},conditions=[],
        physics=dict(model=f"cfdcodebench-c{c['index']:02}-v1",parameters={}))
    path.mkdir(parents=True,exist_ok=True)
    (path/'problem.json').write_text(dumps(manifest),encoding='utf-8');write_hdf5(path/'input.h5',arrays)
    return ids,times

def fourier(values,native,target,L,axis=0):
    coeff=np.fft.fft(values,axis=axis)/len(native)
    freq=2*np.pi*np.fft.fftfreq(len(native),d=L/len(native))
    phase=np.exp(1j*(target[:,None]-native[0])*freq[None,:])
    return np.moveaxis(np.tensordot(phase,np.moveaxis(coeff,axis,0),axes=(1,0)),0,axis).real

def numerical_directory(c,level,factor):
    i=c['index']
    if i in (12,18):job=WORK/'cavity-p3'/f'C{i:02}'/f'L{level}-dt{factor}'
    elif i==6:job=WORK/'burgers'/f'L{level}-dt{factor}'
    elif i==19:
        if factor!=1:return None
        job=WORK/'cylinder-openfoam'/f'R{64*2**level}-P{96*2**level}'
    else:job=WORK/'spectral'/c['source_id']/f'L{level}-dt{factor}'
    return job


def numerical(c,xy,level,factor):
    i=c['index'];job=numerical_directory(c,level,factor)
    if job is None:return None
    process=job/'process.json'
    if not process.exists() or json.loads(process.read_text()).get('returncode')!=0:return None
    if i in (23,24):
        values=np.load(next(job.glob('PDE_Benchmark/results/solution/*.npy')))
        return {c['fields'][0]:values.reshape(1) if i==23 else CubicSpline(np.linspace(0,1,len(values)),values)(xy[:,0])}
    file=job/'native.npz'
    if not file.exists():return None
    with np.load(file) as a:
        if not np.isclose(float(a['time']),c['time'],rtol=0,atol=1e-11):raise ValueError('Wrong terminal time '+str(job))
        if i in (12,18,19):return {n:a[n].ravel().copy() for n in c['fields']}
        if i==6:return {n:RectBivariateSpline(a['y'],a['x'],a[n])(xy[:,1],xy[:,0],grid=False) for n in c['fields']}
        if i==20:return dict(u=fourier(a['u'],a['x'],xy[:,0],10))
        out={};nx=41;x=xy[:nx,0];z=xy[::nx,1]
        for n in c['fields']:
            v=fourier(a[n],a['x'],x,c['domain'][1]-c['domain'][0])
            if i==21:v=BarycentricInterpolator(a['z'],v,axis=1)(z)
            else:v=fourier(v,a['z'],z,2,axis=1)
            out[n]=v.T.ravel()
        return out

def differences(c,a,b,w):
    result={}
    for n in c['fields']:
        v,r=np.array(a[n]),np.array(b[n])
        if c['pressure'] and n=='p':v-=np.average(v,weights=w);r-=np.average(r,weights=w)
        if n=='T':v-=c['offset'];r-=c['offset']
        rms=float(np.sqrt(np.average((v-r)**2,weights=w)))
        rrms=float(np.sqrt(np.average(r*r,weights=w)))
        E=rms/max(rrms,1e-6)
        result[n]=dict(rmse=rms,reference_rms=rrms,nrmse=E,nmse=E*E,max_abs=float(np.max(np.abs(v-r))))
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--only',type=int,nargs='*');args=parser.parse_args()
    records=[]
    for c in catalog():
        i=c['index']
        if args.only and i not in args.only:continue
        case=WORK/'local-pool'/c['task']/f'C{i:02}-base';xy,w=observation_grid(c)
        ids,times=input_case(c,case/'input',xy,w)
        problem=load_problem(case/'input/problem.json')
        record=dict(index=i,task=c['task'],case_id=f'C{i:02}-base',source_revision=REVISION,
                    input_contract='passed',reference_status='pending',comparisons={})
        if i in ANALYTIC:
            vals=[evaluate(i,xy,modes=n) for n in (64,128,256)]
            expected=vals[-1]
            record['producer']='published representation; see formula audit'
            record['comparisons']['truncation_64_128']=differences(c,vals[0],vals[1],w)
            record['comparisons']['truncation_128_256']=differences(c,vals[1],vals[2],w)
            record['reference_status']='formula-evaluated-needs-independent-audit'
        else:
            levels=[numerical(c,xy,l,1) for l in (0,1,2)]
            expected=levels[-1]
            for l in (0,1):
                if levels[l] is not None and levels[l+1] is not None:
                    record['comparisons'][f'space_L{l}_L{l+1}']=differences(c,levels[l],levels[l+1],w)
            if i not in (23,24):
                half=numerical(c,xy,2,2)
                if half is not None and expected is not None:record['comparisons']['half_dt']=differences(c,expected,half,w);expected=half
                elif expected is not None:record['reference_status']='computed-time-check-pending'
            if i==24 and expected is not None:
                record['comparisons']['independent_regular_IVP']=differences(c,expected,evaluate(24,xy),w)
            if expected is not None and record['reference_status']=='pending':record['reference_status']='computed-needs-independent-audit'
        if expected is not None:
            if set(expected)!=set(c['fields']) or any(not np.all(np.isfinite(v)) for v in expected.values()):raise ValueError('Invalid computed fields')
            ref=case/'reference';ref.mkdir(exist_ok=True)
            values={n:np.asarray(expected[n],dtype='float64').reshape(1,len(w),1) for n in c['fields']}
            values.update(ids=ids,times=times)
            write_hdf5(ref/'reference.h5',values)
            (ref/'grading.json').write_text(dumps(grading(c)),encoding='utf-8')
            prepared=prepare_case(problem,ref/'grading.json');result=prepared.evaluate(values)
            if result['score']!=1:raise ValueError(result)
            record['reference_self_grade']='passed'
            if i not in ANALYTIC:
                record['production_sources']=[]
                for level,factor in ((0,1),(1,1),(2,1),(2,2)):
                    directory=numerical_directory(c,level,factor)
                    if directory is None:continue
                    receipt=directory/'process.json'
                    if not receipt.exists() or json.loads(receipt.read_text()).get('returncode')!=0:continue
                    files=[receipt,directory/'native.npz'] if i not in (23,24) else [receipt,*directory.glob('PDE_Benchmark/results/solution/*.npy')]
                    for file in files:
                        if file.exists():record['production_sources'].append(dict(file=file.relative_to(WORK).as_posix(),sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
            record['reference_sha256']=hashlib.sha256((ref/'reference.h5').read_bytes()).hexdigest()
            (case/'self-grade.json').write_text(dumps(result),encoding='utf-8')
        if expected is None and (case/'reference').exists():
            # Preserve an earlier producer's unselected assets without exposing
            # them as this unfinished producer's current reference.
            import time
            old=case/'reference';target=case/f'reference-unselected-{time.time_ns()}'
            old.resolve().relative_to(WORK.resolve());target.resolve().relative_to(WORK.resolve())
            old.rename(target);record['unselected_previous_reference']=target.relative_to(WORK).as_posix()
        if i in ANALYTIC and expected is not None:
            record['production_sources']=[dict(file=(SECTION/'author/analytic.py').relative_to(WORK.parent.parent).as_posix(),sha256=hashlib.sha256((SECTION/'author/analytic.py').read_bytes()).hexdigest(),base='repository')]
        (case/'validation.json').write_text(dumps(record),encoding='utf-8')
        records.append(record);print(json.dumps(dict(index=i,status=record['reference_status'])),flush=True)
    summary=WORK/'local-validation-summary.json'
    if args.only and summary.exists():
        existing=json.loads(summary.read_text(encoding='utf-8'));done={r['index'] for r in records}
        records+=[r for r in existing if r['index'] not in done];records.sort(key=lambda r:r['index'])
    summary.write_text(dumps(records),encoding='utf-8')

if __name__=='__main__':main()
