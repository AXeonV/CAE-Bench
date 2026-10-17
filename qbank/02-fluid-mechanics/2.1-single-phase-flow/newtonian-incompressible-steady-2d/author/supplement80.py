"""Additional upstream Lethe experiments; adapters only, no PDE implementation.

Run subcommands on Linux with the pinned producer and its dependencies.
"""
from pathlib import Path
import argparse, concurrent.futures, hashlib, json, os, subprocess, time
import numpy as np
from prepare_supplement import build_mesh, configuration, wall_velocity, inside
from convert_supplement import probes, sample, vtu, write_case


def specifications():
    # Paired drives change vortex topology and competition, not just magnitudes.
    shapes = [
        ('wide-shallow',[[0,0,6,2]],[]),
        ('tall-narrow',[[0,0,2,6]],[]),
        ('upper-shelf',[[0,0,5,4]],[[0,2,2,3]]),
        ('double-shelf',[[0,0,6,4]],[[0,1,2,2],[4,2,6,3]]),
        ('bottom-comb',[[0,0,6,4]],[[1,0,2,2],[3,0,4,1],[5,0,6,2]]),
        ('hanging-comb',[[0,0,6,4]],[[1,2,2,4],[3,3,4,4],[5,2,6,4]]),
        ('hourglass',[[0,0,3,2],[1,2,2,3],[0,3,3,5]],[]),
        ('horizontal-neck',[[0,0,2,4],[2,1,3,2],[3,0,5,4]],[]),
        ('two-window',[[0,0,6,4]],[[2,0,3,1],[2,2,3,3]]),
        ('three-islands',[[0,0,6,5]],[[1,1,2,2],[3,2,4,3],[4,1,5,2]]),
        ('square-ring',[[0,0,5,5]],[[1,1,4,4]]),
        ('eccentric-ring',[[0,0,6,5]],[[1,1,4,3]]),
        ('thin-vertical-island',[[0,0,5,5]],[[2,1,3,4]]),
        ('thin-horizontal-island',[[0,0,6,4]],[[1,2,5,3]]),
        ('staircase',[[0,0,2,4],[2,1,3,4],[3,2,4,4],[4,3,5,4]],[]),
        ('downward-staircase',[[0,0,5,1],[0,1,4,2],[0,2,3,3],[0,3,2,4]],[]),
        ('plus-offset',[[0,1,6,3],[1,0,3,5]],[]),
        ('upper-arch',[[0,0,2,4],[2,2,4,4],[4,0,6,4]],[]),
        ('lower-arch',[[0,0,6,2],[0,2,2,4],[4,2,6,4]],[]),
        ('three-lobes',[[0,0,2,3],[2,1,4,2],[4,0,6,3],[2,2,3,4]],[]),
        ('deep-left-pocket',[[0,2,6,4],[0,0,1,2]],[]),
        ('central-well',[[0,2,6,4],[2,0,4,2]],[]),
        ('twin-wells',[[0,2,6,4],[1,0,2,2],[4,0,5,2]],[]),
        ('interdigitated',[[0,0,6,5]],[[1,0,2,3],[3,2,4,5],[5,0,6,3]]),
        ('unequal-twin-islands',[[0,0,6,5]],[[1,1,2,2],[3,1,5,3]]),
        ('corner-cut-island',[[0,0,6,5]],[[2,1,4,2],[2,2,3,3]]),
        ('stepped-island',[[0,0,6,5]],[[1,1,3,2],[2,2,4,3]]),
        ('diagonal-gaps',[[0,0,6,5]],[[0,1,3,2],[3,3,6,4]]),
        ('three-chambers',[[0,0,2,4],[2,1,3,3],[3,0,5,4],[5,2,6,3]],[]),
    ]
    result=[]
    for i,(shape,boxes,holes) in enumerate(shapes):
        for regime in ('wall','competing'):
            s=dict(name=f'x80-{shape}-{regime}',boxes=boxes,holes=holes,
                   drive=('lid' if regime=='wall' else ['opposed','side-opposed','circulation'][i%3]),
                   nu=(.08 if regime=='wall' else .025),rho=[1.,10.,997.][i%3],
                   difficulty=('medium' if regime=='wall' else 'hard'),
                   purpose=f'{shape}: '+('wall-driven penetration and secondary eddies' if regime=='wall' else 'competing walls and non-conservative body drive; inertia and vortex topology'))
            if regime=='competing': s['force']=[['0.002*y','-0.003*x'],['-0.002*y','0.001*x'],['0.003*y','0']][i%3]
            if i%3==1 and shape!='square-ring':s['coordinate_rotation_radians']=[.23,.51,.79][i%3 if regime=='wall' else (i+1)%3]
            if regime=='competing' and i in (1,7,16,25,26,28):s['input_n']={1:20,7:24,16:24,25:28,26:28,28:32}[i]
            result.append(s)
    periodic=[
        ('straight',[],{},['0.002','0']),
        ('central-island',[[2,1,3,2]],{},['0.003','0']),
        ('floor-rib',[[2,0,3,1]],{},['0.004','0']),
        ('staggered-ribs',[[1,0,2,1],[4,2,5,3]],{},['0.003','0']),
        ('slip-ceiling',[[2,0,3,1]],{'slip':[2]},['0.003','0']),
        ('counter-wall',[],{'drive':'opposed'},['0.002','0']),
    ]
    for label,holes,extra,force in periodic:
        s=dict(name='x80-periodic-'+label,boxes=[[0,0,6,3]],holes=holes,drive='force',force=force,
               nu=.08,rho=3.,periodic=True,difficulty='medium',purpose='zero pressure-jump periodic transport: '+label)
        s.update(extra);result.append(s)
    assert len(result)==64 and len({s['name'] for s in result})==64
    return result


def prm(s,b):
    text=configuration(s,b)
    if s.get('periodic'):
        # Only the principal side is declared; Lethe adds its paired neighbour.
        start=text.index('subsection boundary conditions')
        bc='subsection boundary conditions\n set number = '+str(len(b)-1)+'\n'
        idx=0
        for k in b:
            if k==5: continue
            bc+=f' subsection bc {idx}\n set id = {k}\n';idx+=1
            if k==4:bc+=' set type = periodic\n set periodic id = 5\n set periodic direction = 0\n'
            elif k in s.get('slip',[]):bc+=' set type = slip\n'
            else:
                ux,uy=wall_velocity(s,k)
                bc+=f' set type = function\n subsection u\n set Function expression = {ux}\n end\n subsection v\n set Function expression = {uy}\n end\n'
            bc+=' end\n'
        text=text[:start]+bc+'end\n'
    return text


def run_one(root,s,n,solver,slot):
    d=root/'runs'/s['name']/f'n{n}';d.mkdir(parents=True,exist_ok=True)
    if (d/'execution.json').exists():
        old=json.loads((d/'execution.json').read_text())
        if old['returncode']==0:return old
    xyz,q,ids,b=build_mesh(s,n,d)
    (d/'case.prm').write_text(prm(s,b));(d/'definition.json').write_text(json.dumps(s,indent=2))
    cpus=sorted(os.sched_getaffinity(0))[slot*4:slot*4+4]
    env={**os.environ,'OMP_NUM_THREADS':'4','DEAL_II_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'1'}
    t=time.monotonic()
    with (d/'solver.log').open('w') as log:
        p=subprocess.run(['/usr/bin/time','-v','-o','resource.txt','timeout','590','taskset','-c',','.join(map(str,cpus)),solver,'case.prm'],cwd=d,env=env,stdout=log,stderr=subprocess.STDOUT)
    record=dict(returncode=p.returncode,seconds=time.monotonic()-t,cells=len(q),nodes=len(xyz),cpu_ids=cpus)
    (d/'execution.json').write_text(json.dumps(record,indent=2))
    print(s['name'],n,record,flush=True)
    return record


def worker(root,jobs,solver,slot):
    for s,n in jobs:
        # gmsh is process-global, so each worker is a separate process.
        run_one(root,s,n,solver,slot)


def run(a):
    specs=specifications()
    if a.names:specs=[s for s in specs if s['name'] in a.names]
    jobs=[(s,n) for n in a.levels for s in specs]
    with concurrent.futures.ProcessPoolExecutor(a.workers) as pool:
        fs=[pool.submit(worker,a.root,jobs[i::a.workers],a.solver,i) for i in range(a.workers)]
        for f in fs:f.result()


def convert(a):
    import h5py
    policy=json.loads(a.policy.read_text());records=[]
    for s in specifications():
        xy=probes(s);levels={}
        for d in sorted((a.root/'runs'/s['name']).glob('n*'),key=lambda p:int(p.name[1:])):
            if not (d/'execution.json').exists():continue
            r=json.loads((d/'execution.json').read_text())
            if r['returncode']!=0:continue
            paths=sorted(d.glob('solution.*.00000.vtu'))
            if not paths:continue
            raw=vtu(paths[-1]);v=sample(raw,xy)
            # Lethe writes kinematic pressure and normalized point gauge.
            v['pressure']*=s['rho']
            if 'coordinate_rotation_radians' in s:
                angle=s['coordinate_rotation_radians'];R=np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
                v['velocity']=v['velocity']@R.T
            levels[int(d.name[1:])]=(v,r,paths[-1])
        ns=sorted(levels)
        if len(ns)<2:raise ValueError(('insufficient runs',s['name'],ns))
        lo,hi=ns[-2:];metrics={}
        for q in ('velocity','pressure','shear_rate'):
            x=levels[lo][0][q];y=levels[hi][0][q];rule=policy['quantities'][q]['rule']
            metrics[q]=float(np.max(np.abs(x-y)/(rule['atol']+rule['rtol']*np.abs(y))))
        accepted=max(metrics.values())<.25
        rec=dict(name=s['name'],definition=s,levels={str(n):r for n,(_,r,_) in levels.items()},comparison=metrics,accepted=accepted)
        records.append(rec)
        if not accepted: print('REFINE',s['name'],metrics,flush=True)
        meshdir=a.root/'input-meshes'/s['name'];meshdir.mkdir(parents=True,exist_ok=True)
        write_case(s,xy,levels[hi][0],a.source,meshdir,policy,input_n=s.get('input_n',4))
        inp=a.source/'cases'/s['name'];j=json.loads((inp/'problem.json').read_text())
        j['materials']['liquid']['density']['parameters']['density']['value']=s['rho']
        j['materials']['liquid']['viscosity']['parameters']['dynamic_viscosity']['value']=s['rho']*s['nu']
        if s.get('periodic'):
            for c in j['conditions']:
                if c['location'] in ('wall_4','wall_5'):
                    k=int(c['location'][-1]);c['operator']='periodic'
                    c['data']=dict(partner={'location':'wall_'+str(9-k)},translation_x={'value':6. if k==4 else -6.,'unit':'m'},translation_y={'value':0.,'unit':'m'})
            # Periodic moving plates have constant speed, including the seam.
            with h5py.File(inp/'input.h5','r+') as h:
                for k in (2,3):
                    key=f'wall_{k}_velocity'
                    if key in h:h[key][...]=np.array(wall_velocity(s,k))[None,None,:]
        (inp/'problem.json').write_text(json.dumps(j,indent=2)+'\n')
        with h5py.File(a.source/'reference'/s['name']/'reference.h5','r+') as h:
            h['density'][...]=s['rho'];h['dynamic_viscosity'][...]=s['rho']*s['nu']
        if 'coordinate_rotation_radians' in s:
            import gmsh
            # A rigid change of Cartesian coordinates, not a different PDE solve.
            angle=s['coordinate_rotation_radians'];R=np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
            gmsh.initialize();gmsh.option.setNumber('General.Terminal',0);gmsh.open(str(inp/'mesh.msh'))
            tags,coordinates,_=gmsh.model.mesh.getNodes()
            for tag,point in zip(tags,np.array(coordinates).reshape(-1,3)):
                point[:2]=point[:2]@R.T;gmsh.model.mesh.setNode(int(tag),point,[])
            gmsh.write(str(inp/'mesh.msh'));gmsh.finalize()
            with h5py.File(inp/'input.h5','r+') as h:
                for key in ('probe_xy','pin_xy'):h[key][...]=h[key][:]@R.T
                for f in j['fields'].values():
                    if f['kind']=='vector':h[f['array']][...]=h[f['array']][:]@R.T
        rec['raw_sha256']={str(n):hashlib.sha256(p.read_bytes()).hexdigest() for n,(_,_,p) in levels.items()}
    (a.root/'numerical-validation.json').write_text(json.dumps(records,indent=2)+'\n')
    print('ACCEPTED',sum(r['accepted'] for r in records),len(records),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='action',required=True)
    r=sub.add_parser('run');r.add_argument('root',type=Path);r.add_argument('--levels',nargs='+',type=int,default=[4,8,16]);r.add_argument('--workers',type=int,default=8);r.add_argument('--solver',required=True);r.add_argument('--names',nargs='+')
    c=sub.add_parser('convert');c.add_argument('root',type=Path);c.add_argument('source',type=Path);c.add_argument('policy',type=Path)
    a=p.parse_args();run(a) if a.action=='run' else convert(a)
