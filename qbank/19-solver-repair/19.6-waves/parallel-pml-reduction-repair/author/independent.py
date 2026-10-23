"""Independent two dimensional scalar Green kernel and exact wall image solution.

References: MIT 18.325 Waves and Imaging (2015), Chapter 1;
https://www.math.toronto.edu/courses/apm346h1/20151/L26.html .
This evaluates the continuum kernel, never a replacement SEM/FDM/FEM solver.
"""
import argparse,json
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem,load_result
from caeoj.validation import read_mesh

def rectangles(problem):
    mesh=read_mesh(problem.path.parent/'mesh.msh',geometry=True)
    parent={n:n for n in mesh['nodes']}
    def find(n):
        while parent[n]!=n:parent[n]=parent[parent[n]];n=parent[n]
        return n
    for typ,row in mesh['connectivity'].values():
        for n in row[1:]:parent[find(n)]=find(row[0])
    groups={}
    for n,xyz in mesh['node_coordinates'].items():groups.setdefault(find(n),[]).append(xyz[:2])
    return [(np.min(x,axis=0),np.max(x,axis=0)) for x in groups.values()]

def kernel(times,r,c,f,order):
    tau=r/c;t0=1.2/f;answer=np.zeros_like(times);valid=times+t0>tau
    gx,gw=np.polynomial.legendre.leggauss(order)
    vmax=np.arccosh((times[valid]+t0)/tau)
    v=(gx[None,:]+1)*vmax[:,None]/2
    source_time=times[valid,None]-tau*np.cosh(v)
    q=(np.pi*f*source_time)**2
    force=(1-2*q)*np.exp(-q)
    answer[valid]=np.sum(force*gw,axis=1)*vmax/2/(2*np.pi*c*c)
    return answer

def evaluate(problem,order=128,open_z_override=None):
    p={n:v['value'] for n,v in problem.manifest['physics']['parameters'].items()};a=problem.arrays
    p['wave_branch']={'parallel-scalar-sh-v1':0,'parallel-scalar-acoustic-potential-v1':1}[problem.manifest['physics']['model']]
    acoustic=p['wave_branch']==1;c=p['p_speed'] if acoustic else p['s_speed']
    open_z=np.any(a['pml_region']) if open_z_override is None else open_z_override;result=np.zeros((len(a['times']),len(a['probe_ids']),1))
    for lo,hi in rectangles(problem):
        L,H=hi-lo
        for source,amplitude in zip(a['source_coordinates'],a['source_amplitude'][0,:,0]):
            if not np.all((source>lo)&(source<hi)):continue
            source=source-lo
            for j,receiver in enumerate(a['probe_coordinates']):
                if not np.all((receiver>lo)&(receiver<hi)):continue
                receiver=receiver-lo
                for m in range(-2,3):
                    for n in ([0] if open_z else range(-2,3)):
                        for sx in (-1,1):
                            for sz in ([1] if open_z else (-1,1)):
                                image=np.array([2*m*L+sx*source[0],2*n*H+sz*source[1]])
                                r=np.linalg.norm(receiver-image)
                                if r/c>a['times'][-1]+1.2/p['frequency']:continue
                                coefficient=amplitude if acoustic else -amplitude/p['density']
                                result[:,j,0]+=coefficient*kernel(a['times'],r,c,p['frequency'],order)
    return result

def audit(dataset):
    rows=[]
    for path in sorted((dataset/'cases').glob('*/problem.json')):
        problem=load_problem(path);actual=load_result(problem,dataset/'reference'/path.parent.name/'reference.h5')['wave_response']
        expected=evaluate(problem);refined=evaluate(problem,256)
        relative=np.linalg.norm(actual-expected,axis=0)/np.linalg.norm(expected,axis=0)
        integration=np.linalg.norm(refined-expected,axis=0)/np.linalg.norm(refined,axis=0)
        row={'case':path.parent.name,'per_probe_relative_l2':relative.ravel().tolist(),
             'quadrature_relative_l2_128_vs_256':integration.ravel().tolist(),
             'passed':bool(np.max(relative)<.02 and np.max(integration)<1e-7),
             'scope':'all physical output time samples and receivers; PML checked against ideal open-z continuation with residual absorption and discretization error'}
        if np.any(problem.arrays['pml_region']):
            reflecting=evaluate(problem,open_z_override=False)
            late=problem.arrays['times']>.35
            boundary_signal=np.linalg.norm((reflecting-expected)[late],axis=0)
            residual=np.linalg.norm((actual-expected)[late],axis=0)/boundary_signal
            row['late_pml_residual_over_unabsorbed_z_return_l2']=residual.ravel().tolist()
            row['passed']=row['passed'] and bool(np.all(residual<.05))
        rows.append(row);print(row['case'],max(row['per_probe_relative_l2']),row['passed'],flush=True)
    return {'method':'independent continuum Green/Duhamel plus Neumann images; no SEM code or fitted amplitude','cases':rows,'passed':all(r['passed'] for r in rows)}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--dataset',type=Path,required=True);a=p.parse_args();result=audit(a.dataset)
    (a.dataset/'independent-report.json').write_text(json.dumps(result,indent=2))
    if not result['passed']:raise SystemExit(1)
