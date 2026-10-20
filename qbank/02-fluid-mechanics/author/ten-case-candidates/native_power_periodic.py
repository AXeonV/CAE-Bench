"""Native OpenCFD bounded-power-law/Newtonian closed or cyclic producers.

Only stock blockMesh, simpleFoam/pimpleFoam, powerLaw and fvOptions are used.
The compact initial curl is INPUT construction, not a reference PDE solver.
"""
import argparse
import hashlib
import itertools
import json
import os
import re
import subprocess
import time
from pathlib import Path
import h5py
import numpy as np
from native_closed_cavity import IMAGE,SOCKET,header,vector,put,save,digest,prepare_native,native_mesh,field
from native_elmer_incompressible import evaluate,mu_of
from elmer_flow_mesh import select
from polytropic_reference import gmsh
from titan_resources import reservation


def prepare(job,e):
    s=e['detailed_spec'];d=e['spatial_dimension'];L=s['geometry']['bounding_lengths'];assert s['geometry']['operation']=='box';holes=s['geometry']['holes'];assert not holes or (len(holes)==1 and np.allclose(holes[0]['xy_corners'],[[.4*L[0],.3*L[1]],[.6*L[0],.5*L[1]]]));periodic=any(b['operator']=='periodic' for b in s['boundaries']);rho=s['materials']['density']['parameters']['density']['value'];v=s['materials']['viscosity'];vp={k:q['value'] for k,q in v['parameters'].items()};transient=s['analysis_kind']=='transient';end=(s['time_interval_s'] or [0,1])[1];ht=np.array([0,.1*end,.4*end,.6*end,end] if transient else [0.]);native=job/'native'
    p={'spatial_dimension':d,'length_m':L if d==3 else [*L,.05],'target_cells_xyz':s['mesh_recipe']['base_divisions'] if d==3 else [*s['mesh_recipe']['base_divisions'],1],'obstacle_xy_fraction':bool(holes),'wall_speed_multiplier_linear_table':[[0,0],[.1,1],[1,1]],'wall_velocity_vectors_m_s':{},'dynamic_viscosity_Pa_s':.01,'density_kg_m3':rho,'time_interval_s':[0,end],'native_dt_s':end/1000};prepare_native(native,p)
    bm=native/'system/blockMeshDict';text=bm.read_text()
    if periodic:
        for name,partner in [('left','right'),('right','left')]:text=re.sub(r'(?m)^'+name+r' \{ type wall;',name+' { type cyclic; neighbourPatch '+partner+';',text)
        bm.write_text(text)
    names=['left','right','bottom','top_left','top_right','front','back']+(['obstacle'] if holes else []);centre={'left':[0,L[1]/2],'right':[L[0],L[1]/2],'bottom':[L[0]/2,0],'top_left':[L[0]/4,L[1]],'top_right':[.75*L[0],L[1]],'obstacle':[.5*L[0],.4*L[1]]}
    if d==3:
        centre={k:[*val,L[2]/2] for k,val in centre.items()};centre.update(front=[L[0]/2,L[1]/2,0],back=[L[0]/2,L[1]/2,L[2]])
    ubc=[];pbc=[]
    for name in names:
        if d==2 and name in ('front','back'):typ='empty'
        elif periodic and name in ('left','right'):typ='cyclic'
        else:typ=None
        if typ:ubc.append(name+' { type '+typ+'; }');pbc.append(name+' { type '+typ+'; }');continue
        bc=s['boundaries'][0]
        for b in s['boundaries'][1:]:
            if b['operator']!='periodic' and select(s,b['selection'],np.array([centre[name]]))[0]:bc=b
        if bc['operator']=='slip':ubc.append(name+' { type slip; }')
        else:
            expr=bc['data']['velocity']['expression'] if bc['operator']=='moving_wall' else [0]*d
            vals=[np.pad(evaluate(expr,np.array([centre[name]]),t,s)[0],(0,3-d)) for t in ht]
            if transient:ubc.append(name+' { type uniformFixedValue; uniformValue table ('+' '.join(f'({t} {vector(a)})' for t,a in zip(ht,vals))+'); value uniform '+vector(vals[0])+'; }')
            else:ubc.append(name+' { type fixedValue; value uniform '+vector(vals[0])+'; }')
        pbc.append(name+' { type zeroGradient; }')
    put(native/'0/U',header('volVectorField','U')+'dimensions [0 1 -1 0 0 0 0];\ninternalField uniform (0 0 0);\nboundaryField {\n'+'\n'.join(ubc)+'\n}\n');put(native/'0/p',header('volScalarField','p')+'dimensions [0 2 -2 0 0 0 0];\ninternalField uniform 0;\nboundaryField {\n'+'\n'.join(pbc)+'\n}\n')
    if v['kind']=='power_law':
        pwr=vp['power_index'];k=vp['reference_viscosity']/rho*vp['reference_shear_rate']**(1-pwr);bounds=[vp['reference_viscosity']/rho*(g/vp['reference_shear_rate'])**(pwr-1) for g in [vp['minimum_shear_rate'],vp['maximum_shear_rate']]]
        transport=f'transportModel powerLaw;\npowerLawCoeffs {{ k [0 2 -1 0 0 0 0] {k}; n [0 0 0 0 0 0 0] {pwr}; nuMin [0 2 -1 0 0 0 0] {min(bounds)}; nuMax [0 2 -1 0 0 0 0] {max(bounds)}; }}\n'
    else:assert v['kind']=='newtonian';transport=f'transportModel Newtonian; nu [0 2 -1 0 0 0 0] {vp["dynamic_viscosity"]/rho};\n'
    put(native/'constant/transportProperties',header('dictionary','transportProperties')+transport);put(native/'constant/turbulenceProperties',header('dictionary','turbulenceProperties')+'simulationType laminar;\n')
    if s['sources']:
        assert set(s['sources'])=={'acceleration'};expr=s['sources']['acceleration']['expression'];values=[np.pad(evaluate(expr,np.zeros((1,d)),t,s)[0],(0,3-d)) for t in ht];su='explicit table ('+' '.join(f'({t} {vector(a)})' for t,a in zip(ht,values))+');' if transient else 'explicit constant '+vector(values[0])+';'
        put(native/'constant/fvOptions',header('dictionary','fvOptions')+'acceleration { type vectorSemiImplicitSource; selectionMode all; volumeMode specific; sources { U { '+su+' implicit none; } } }\n')
    app='pimpleFoam' if transient else 'simpleFoam';put(native/'system/controlDict',header('dictionary','controlDict')+f'application {app}; startFrom startTime; startTime 0; stopAt endTime; endTime {end if transient else 10000}; deltaT {end/1000 if transient else 1}; writeControl timeStep; writeInterval {1 if transient else 10000}; purgeWrite 0; writeFormat ascii; writePrecision 16; writeCompression off; timeFormat general; timePrecision 12; runTimeModifiable false;\nfunctions {{ gradU {{ type grad; libs (fieldFunctionObjects); field U; result gradU; executeControl writeTime; writeControl writeTime; }} }}\n')
    put(native/'system/fvSchemes',header('dictionary','fvSchemes')+'ddtSchemes { default '+('Euler' if transient else 'steadyState')+'; } gradSchemes { default Gauss linear; } divSchemes { default none; div(phi,U) Gauss linearUpwind grad(U); div((nuEff*dev2(T(grad(U))))) Gauss linear; } laplacianSchemes { default Gauss linear corrected; } interpolationSchemes { default linear; } snGradSchemes { default corrected; } fluxRequired { default no; p; }\n')
    fv='solvers { p { solver PCG; preconditioner DIC; tolerance 1e-9; relTol 0; } pFinal { $p; relTol 0; } U { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-9; relTol 0; } UFinal { $U; relTol 0; } }\n'
    fv+='PIMPLE { nOuterCorrectors 2; nCorrectors 2; nNonOrthogonalCorrectors 0; pRefCell 0; pRefValue 0; } relaxationFactors { equations { U 1; } }\n' if transient else 'SIMPLE { nNonOrthogonalCorrectors 0; pRefCell 0; pRefValue 0; residualControl { p 1e-9; U 1e-9; } } relaxationFactors { fields { p 0.3; } equations { U 0.5; } }\n'
    if periodic and not transient:
        # The transverse velocity and pressure are nearly zero in this family;
        # normalized initial residuals become dominated by roundoff. These are
        # production stop tolerances, not an accuracy or acceptance threshold.
        fv=fv.replace('residualControl { p 1e-9; U 1e-9; }','residualControl { p 1e-2; U 1e-3; }')
    put(native/'system/fvSolution',header('dictionary','fvSolution')+fv);return app


def input_mesh(job,e):
    s=e['detailed_spec'];d=e['spatial_dimension'];xx,quads,patches,volume=native_mesh(job/'native',d);x=xx[:,:d];q=np.array(quads,dtype=np.int64)-1
    if d==2:c=np.concatenate((q[:,[0,1,2]],q[:,[0,2,3]]));parent=np.tile(np.arange(len(q)),2)
    else:
        pattern=[(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1)];indices={v:i for i,v in enumerate(pattern)};parts=[]
        for perm in itertools.permutations(range(3)):
            v=[0,0,0];ids=[0]
            for j in perm:v[j]=1;ids.append(indices[tuple(v)])
            parts.append(q[:,ids])
        c=np.concatenate(parts);parent=np.tile(np.arange(len(q)),6)
    A=x[c][:,1:]-x[c][:,:1];det=np.linalg.det(A);negative=det<0;c[negative,1],c[negative,2]=c[negative,2].copy(),c[negative,1].copy();vol=np.abs(det)/(2 if d==2 else 6);counts={};owners={}
    for i,row in enumerate(c):
        for j in range(d+1):f=tuple(sorted(np.delete(row,j)));counts[f]=counts.get(f,0)+1;owners[f]=i
    b=np.array([f for f,v in counts.items() if v==1]);bp=np.array([owners[tuple(row)] for row in b]);mid=x[b].mean(axis=1);cc=x[c].mean(axis=1)
    if d==2:t=x[b[:,1]]-x[b[:,0]];measure=np.linalg.norm(t,axis=1);normal=np.column_stack((t[:,1],-t[:,0]))/measure[:,None]
    else:v=np.cross(x[b[:,1]]-x[b[:,0]],x[b[:,2]]-x[b[:,0]]);measure=np.linalg.norm(v,axis=1)/2;normal=v/(2*measure[:,None])
    normal[np.einsum('ij,ij->i',normal,mid-cc[bp])<0]*=-1
    initial=np.zeros((len(c),d));init=s['initial'].get('velocity',{}).get('expression')
    if isinstance(init,str):
        L=np.array(s['geometry']['bounding_lengths'])
        if init.startswith('C from compact'):
            centre=np.full(d,.5)*L;radius=.2*L
            if 'entirely inside a' in init:centre[1]=.25*L[1];radius=np.full(d,.05*min(L))
            potential=np.maximum(1-np.sum(((x-centre)/radius)**2,axis=1),0)**4;boundary=np.unique(b);touch=np.any(np.isin(c,boundary),axis=1);potential[np.unique(c[touch])]=0
        else:
            assert init.startswith('C from nodal psi=sin(pi*X)*sin(pi*Y)')
            potential=np.sin(np.pi*x[:,0]/L[0])*np.sin(np.pi*x[:,1]/L[1])
            if d==3:potential*=np.cos(np.pi*x[:,2]/L[2])
        grad=np.linalg.solve(x[c][:,1:]-x[c][:,:1],(potential[c][:,1:]-potential[c][:,:1])[...,None])[...,0];initial[:,0]=grad[:,1];initial[:,1]=-grad[:,0];maximum=np.linalg.norm(initial,axis=1).max();assert maximum>0;initial*=(.01 if 'max speed .01 m/s' in init else .1)/maximum
        u=np.zeros((len(q),d));np.add.at(u,parent,initial*vol[:,None]);u/=volume[:,None];up=job/'native/0/U';txt=up.read_text();replacement='internalField nonuniform List<vector>\n'+str(len(q))+'\n(\n'+'\n'.join(vector(np.pad(v,(0,3-d))) for v in u)+'\n);';up.write_text(re.sub(r'internalField uniform \(0 0 0\);',lambda _:replacement,txt))
    np.savez(job/'adapter-data.npz',x=x,c=c,b=b,volume=vol,parent=parent,bp=bp,normal=normal,measure=measure,initial=initial,native_volume=volume)
    return dict(np.load(job/'adapter-data.npz'))


def convert(job,e,m):
    s=e['detailed_spec'];d=e['spatial_dimension'];x=m['x'];c=m['c'];b=m['b'];nc=len(c);mid=x[b].mean(axis=1);L=np.array(s['geometry']['bounding_lengths']);transient=s['analysis_kind']=='transient';end=(s['time_interval_s'] or [0,1])[1];hist=np.array([0,.1*end,.4*end,.6*end,end] if transient else [0.]);rho=s['materials']['density']['parameters']['density']['value'];parent=m['parent'];nparent=len(m['native_volume'])
    groups=np.zeros(len(b),dtype=int);periodic=any(bc['operator']=='periodic' for bc in s['boundaries'])
    for i,bc in enumerate(s['boundaries'][1:],1):
        if bc['operator']=='periodic':groups[np.isclose(mid[:,0],0)]=i;groups[np.isclose(mid[:,0],L[0])]=i+1
        else:groups[select(s,bc['selection'],mid)]=i
    ns=[[] for _ in x]
    for i,row in enumerate(b):
        for node in row:ns[node].append(m['normal'][i])
    singular=np.array([len(v)>0 and not np.allclose(v,v[0]) for v in ns]);traces=np.flatnonzero(~np.any(singular[b],axis=1));integral=np.flatnonzero(np.isclose(mid[:,1],L[1])&(mid[:,0]>.25*L[0])&(mid[:,0]<.75*L[0]));inp=job/'input';ref=job/'reference';inp.mkdir(exist_ok=True);ref.mkdir(exist_ok=True);gmsh(inp/'mesh.msh',x,c,b,d)
    def loc(key,dim):return {'kind':'mesh','mesh':'main','entity':'element','dimension':dim,'ids':key}
    arrays={'cells':np.arange(1,nc+1,dtype=np.int64),'traces':(nc+traces+1).astype(np.int64),'integral_faces':(nc+integral+1).astype(np.int64),'aggregate':np.array([1],dtype=np.int64),'requested':np.array(s['output_times_s']),'history':hist,'initial':np.array([0.])};locations={'domain':loc('cells',d),'traces':loc('traces',d-1),'integral_faces':loc('integral_faces',d-1),'aggregate':{'kind':'aggregate','source':'integral_faces','ids':'aggregate','operation':'sum'}};fields={};conditions=[]
    def desc(q,where,unit,components=1,axis='requested',vk='average',input=False):
        z={'array':q,'quantity':q,'location':where,'time_axis':axis,'dtype':'float64','kind':'scalar' if components==1 else 'vector','component_shape':[components],'components':['value'] if components==1 else list('xyz'[:components]),'unit':unit,'value_kind':vk}
        if input:z['sampling']={'space':'piecewise_constant','time':'linear' if transient and axis=='history' else 'constant','extrapolation':'forbid'}
        return z
    if transient:
        arrays['initial_velocity']=m['initial'][None];fields['initial_velocity']=desc('velocity','domain','m/s',d,'initial',input=True);fields['initial_velocity']['array']='initial_velocity';conditions.append({'role':'initial','variable':'velocity','operator':'assign','location':'domain','data':{'value':{'field':'initial_velocity'}}})
    if s['sources']:
        arrays['acceleration']=np.array([evaluate(s['sources']['acceleration']['expression'],x[c].mean(axis=1),t,s) for t in hist]);fields['acceleration']=desc('acceleration','domain','m/s2',d,'history',input=True);conditions.append({'role':'source','variable':'velocity','operator':'acceleration','location':'domain','data':{'value':{'field':'acceleration'}}})
    boundary_records=[(i,bc) for i,bc in enumerate(s['boundaries']) if bc['operator']!='periodic']
    for i,bc in enumerate(s['boundaries']):
        if bc['operator']=='periodic':boundary_records.extend([(i,{**bc,'side':1}),(i+1,{**bc,'side':-1})])
    for i,bc in boundary_records:
        ids=np.flatnonzero(groups==i)
        if not len(ids):continue
        key=f'boundary{i}';arrays[key]=(nc+ids+1).astype(np.int64);locations[key]=loc(key,d-1);data={}
        if bc['operator']=='moving_wall':
            fk=key+'velocity';arrays[fk]=np.array([evaluate(bc['data']['velocity']['expression'],mid[ids],t,s) for t in hist]);fields[fk]=desc('velocity',key,'m/s',d,'history',input=True);fields[fk]['array']=fk;data={'velocity':{'field':fk}}
        elif bc['operator']=='periodic':
            data={'partner':{'location':f'boundary{i+1 if bc["side"]==1 else i-1}'},**{f'translation_{axis}':{'value':float(L[0]*bc['side']) if j==0 else 0.,'unit':'m'} for j,axis in enumerate('xyz'[:d])}}
        conditions.append({'role':'boundary','variable':'flow','operator':bc['operator'],'location':key,'data':data})
    a=s['analysis'];analysis={'type':s['analysis_kind'],'compressibility':'incompressible','flow_regime':'laminar','temperature':{'value':a['temperature_K'],'unit':'K'},'pressure':{'representation':'gauge','reference_pressure':{'value':a['reference_pressure_Pa'],'unit':'Pa'}},'pressure_gauge':{'kind':'mean','location':'domain','value':{'value':0.,'unit':'Pa'}}}
    if transient:analysis['time_interval']={'start':0.,'end':end}
    outputs={}
    for r in s['observation_requests']:
        q=r['quantity'];where='traces' if q=='traction' else 'aggregate' if q in ('force','volume_flow','mass_flow') else 'domain';outputs[q]=desc(q,where,r['unit'],d if q in ('velocity','traction','force') else 1,vk=r['value_kind'])
    save(inp/'problem.json',{'task':e['task'],'contract_version':2,'profile':'cfd-2.1','spatial_dimension':d,'analysis':analysis,'materials':{'fluid':{'region':'domain',**s['materials']}},'data_file':'input.h5','geometries':{},'meshes':{'main':{'file':'mesh.msh'}},'locations':locations,'time_axes':{'requested':'requested','history':'history','initial':'initial'},'fields':fields,'conditions':conditions,'outputs':outputs})
    with h5py.File(inp/'input.h5','w') as f:
        for key,v in arrays.items():f[key]=v
    tdirs={round(float(p.name),12):p for p in (job/'native').iterdir() if p.is_dir() and re.fullmatch(r'[\d.eE+-]+',p.name)};result={key:[] for key in outputs}
    for t in s['output_times_s']:
        folder=tdirs[round(t,12)] if transient else tdirs[max(tdirs)];assert folder.name!='0';u=field(folder/'U',3,nparent)[:,:d][parent];p=field(folder/'p',1,nparent)[parent]*rho;p-=np.dot(m['volume'],p[:,0])/sum(m['volume']);grad=field(folder/'gradU',9,nparent).reshape(nparent,3,3)[:,:d,:d][parent];twod=grad+np.swapaxes(grad,1,2);g=np.sqrt(.5*np.sum(twod**2,axis=(1,2)));v=s['materials']['viscosity'];vp={k:q['value'] for k,q in v['parameters'].items()};mu=np.full(nc,vp['dynamic_viscosity']) if v['kind']=='newtonian' else vp['reference_viscosity']*(np.clip(g,vp['minimum_shear_rate'],vp['maximum_shear_rate'])/vp['reference_shear_rate'])**(vp['power_index']-1);bp=m['bp'];traction=np.einsum('bij,bj->bi',mu[bp,None,None]*twod[bp]-p[bp,:,None]*np.eye(d),m['normal']);flux=np.einsum('ij,ij->i',u[bp],m['normal']);vals={'velocity':u,'pressure':p,'density':np.full((nc,1),rho),'dynamic_viscosity':mu[:,None],'shear_rate':g[:,None],'traction':traction[traces],'force':-np.sum(traction[integral]*m['measure'][integral,None],axis=0)[None],'volume_flow':np.array([[np.dot(m['measure'][integral],flux[integral])]]),'mass_flow':np.array([[rho*np.dot(m['measure'][integral],flux[integral])]])}
        for key in outputs:assert np.isfinite(vals[key]).all();result[key].append(vals[key])
    with h5py.File(ref/'reference.h5','w') as f:
        for key in {locations[o['location']]['ids'] for o in outputs.values()}|{'requested'}:f[key]=arrays[key]
        for key,v in result.items():f[key]=np.array(v)
    return {'reference_sha256':digest(ref/'reference.h5'),'cells':nc,'native_cells':nparent,'frames':len(s['output_times_s']),'mapping':'Native FV cells split into conforming simplices; native piecewise constant cell reconstructions retain their averages. Gradients use native gradU. Compact P1-potential curl initial data are volume-averaged into native FV cells, with no Leray projection. Native viscosity bounds are exact transformed shear-rate cutoffs. No numerical validation.'}


def run(root,e,g):
    job=root/'cases'/e['design_id'];status=job/'status.json'
    if status.exists():return json.loads(status.read_text())
    job.mkdir(parents=True);save(job/'design.json',e);state={'design_id':e['design_id'],'status':'queued'};save(status,state);name='ch02power-'+hashlib.sha256(e['design_id'].encode()).hexdigest()[:12]+'-'+str(time.time_ns())[-9:]
    try:
        with reservation(root,name):
            app=prepare(job,e);common=['docker','--host',SOCKET,'run','--network','none','--cpus','1','--memory','768m','--user',f'{os.getuid()}:{os.getgid()}','-e','OMP_NUM_THREADS=1','-v',f'{job.resolve()}:/work','-w','/work/native'];cmd=common+['--rm',IMAGE,'bash','-c','source /usr/lib/openfoam/openfoam2512/etc/bashrc && cd /work/native && blockMesh > ../blockMesh.log 2>&1'];subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT);data=input_mesh(job,e);cmd=common+['--name',name,IMAGE,'bash','-c',f'source /usr/lib/openfoam/openfoam2512/etc/bashrc && cd /work/native && {app} > ../solver.log 2>&1'];save(job/'execution.json',{'producer':f'unmodified OpenCFD {app}, stock bounded powerLaw/fvOptions','image':IMAGE,'source':'image:/usr/lib/openfoam/openfoam2512/src/transportModels/incompressible/viscosityModels/powerLaw/powerLaw.C','command':cmd,'script_sha256':digest(Path(__file__)),'start_unix':time.time(),'numerical_validation':False});state.update(status='running',container=name);save(status,state)
            with (job/'docker.log').open('w') as log:cp=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
            assert cp.returncode==0,f'native exit {cp.returncode}'
        if e['detailed_spec']['analysis_kind']=='steady' and 'SIMPLE solution converged' not in (job/'solver.log').read_text():state['status']='native_iteration_limit'
        else:state.update(convert(job,e,data));save(job/'reference/grading.json',g);state['status']='unvalidated_candidate'
    except Exception as ex:state.update(status='needs_attention',error=repr(ex))
    state['ended_unix']=time.time();save(status,state);return state


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int,default=40);ap.add_argument('--only');args=ap.parse_args();tasks=[];freeze=json.loads((args.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text())
    for p in args.snapshot.glob('qbank/02-fluid-mechanics/*/*/author/chapter02-ten-20261020/design.json'):
        r=json.loads(p.read_text())
        if r['family'] not in ('generalized_flow','closed_flow'):continue
        assert digest(p)==freeze['designs'][p.relative_to(args.snapshot).as_posix()]
        for i,e in enumerate(r['proposed_cases']):
            if i not in ([1,9] if r['family']=='generalized_flow' else [3,5]):continue
            if args.only and args.only not in e['design_id']:continue
            tasks.append(({**e,'task':r['task']},json.loads((p.parents[1]/'grading-template.json').read_text())))
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=min(args.workers,len(tasks))) as pool:states=list(pool.map(run,[args.root]*len(tasks),[e for e,g in tasks],[g for e,g in tasks]))
    save(args.root/'maintenance/power-periodic-summary.json',states);print(json.dumps({'completed':sum(s['status']=='unvalidated_candidate' for s in states),'attention':[s for s in states if s['status']=='needs_attention']}))


if __name__=='__main__':main()
