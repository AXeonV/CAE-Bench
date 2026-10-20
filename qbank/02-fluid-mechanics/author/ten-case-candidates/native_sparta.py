"""Stock SPARTA hard-sphere / collisionless native computation stage.

Native emission, Maxwell reflection and DSMC moments; no custom PDE solver.
Steady burn-in and statistical errors remain unverified.
"""
import argparse
import hashlib
import json
import os
import subprocess
import time
import traceback
from pathlib import Path
import numpy as np
from native_closed_cavity import SOCKET, save, put, digest
from elmer_flow_mesh import select, generate
from titan_resources import reservation

IMAGE='sha256:2935438c074847a45e250dcddac72bb3b791540624a5aebe3a52b6b4ab75c2c6'
EXEC='/opt/sparta/source/src/spa_serial'
KB=1.380649e-23


def supported(e):
    return e['detailed_spec']['geometry']['operation'] in ('box','polygon_extrusion','union_extrusion')


def geometry(job,e):
    s=e['detailed_spec'];L=np.array(s['geometry']['bounding_lengths']);m=generate(s);np.savez(job/'native-input-mesh.npz',**m);x=m['x'];b=m['b'];mid=x[b].mean(axis=1);ports={}
    for i,bc in enumerate(s['boundaries']):
        if bc['operator']!='gas_reservoir':continue
        name=bc['selection'];selection=s['geometry']['ports']['bottom' if name.startswith('bottom') else 'top'] if name.startswith(('bottom','top')) else name
        take=select(s,selection,mid);assert take.any();points=x[np.unique(b[take])];low=points.min(axis=0);high=points.max(axis=0);axes=np.flatnonzero(np.isclose(low,high,atol=max(L)*1e-9,rtol=0));assert len(axes)==1;axis=int(axes[0]);side=0 if abs(low[axis])<max(L)*1e-8 else 1;assert abs(low[axis]-side*L[axis])<max(L)*1e-8
        ports[i]={'face':'xyz'[axis]+('lo' if side==0 else 'hi'),'low':low.tolist(),'high':high.tolist()}
    exterior=np.any(np.all(np.isclose(x[b],0,atol=max(L)*1e-9),axis=1)|np.all(np.isclose(x[b],L,atol=max(L)*1e-9),axis=1),axis=1);inside=b[~exterior].copy();norm=m['normal'][~exterior]
    if len(inside):
        cross=np.cross(x[inside[:,1]]-x[inside[:,0]],x[inside[:,2]]-x[inside[:,0]]);flip=np.einsum('ij,ij->i',cross,norm)>0;inside[flip,1],inside[flip,2]=inside[flip,2].copy(),inside[flip,1].copy();nodes=np.unique(inside);lookup={int(v):i+1 for i,v in enumerate(nodes)}
        lines=['SPARTA solid-side surfaces; normals point into gas','',f'{len(nodes)} points',f'{len(inside)} triangles','','Points','']+[str(i+1)+' '+' '.join(map(str,x[j])) for i,j in enumerate(nodes)]+['','Triangles','']+[str(i+1)+' '+' '.join(str(lookup[int(v)]) for v in row) for i,row in enumerate(inside)]
        put(job/'native/walls.surf',chr(10).join(lines)+chr(10))
    save(job/'native-geometry.json',{'ports':ports,'gas_volume_m3':float(m['volume'].sum()),'surface_triangles':len(inside),'public_mesh_stage':'native-input-mesh.npz is a tetrahedral geometry snapshot; public package not yet assembled'})
    return ports,float(m['volume'].sum()),len(inside)


def prepare(job,e):
    s=e['detailed_spec'];p={k:v['value'] for k,v in s['parameters'].items()};g=s['geometry'];L=g['bounding_lengths'];nn=s['mesh_recipe']['base_divisions'];assert len(L)==3 and supported(e) and not s['sources'];n=job/'native';n.mkdir(exist_ok=True)
    ports,gas_volume,ntri=geometry(job,e);mass=p['molecule_mass'];nc=int(np.prod(nn));particles=100*nc;rho0=np.mean([b['data']['density_kg_m3'] for b in s['boundaries'] if b['operator']=='gas_reservoir']);fnum=rho0/mass*gas_volume/particles
    dt=.1*min(np.array(L)/nn)/np.sqrt(3*KB*p['reference_temperature']/mass)
    # Fixed finite production schedule, not a stationarity/Monte Carlo test.
    burn=max(10000,int(np.ceil(30*max(L)/np.sqrt(KB*p['reference_temperature']/mass)/dt)));burn=int(np.ceil(burn/10000))*10000;sample_steps=10000
    opened={v['face'] for v in ports.values()};bounds=' '.join(''.join('o' if a+side in opened else 's' for side in ('lo','hi')) for a in 'xyz')
    text=f'seed 112358\ndimension 3\nunits si\nglobal gridcut {min(L)*1e-4} nrho {rho0/mass} fnum {fnum}\nboundary {bounds}\ncreate_box 0 {L[0]} 0 {L[1]} 0 {L[2]}\ncreate_grid {nn[0]} {nn[1]} {nn[2]}\nspecies species.dat Ar\nmixture gas Ar temp {p["reference_temperature"]} vstream 0 0 0\n'
    put(n/'species.dat',f'# ID molwt mass rotdof rotrel vibdof vibrel vibtemp weight charge\nAr {mass/1.66053906660e-27} {mass} 0 0 0 0 0 1 0\n')
    if e['model']=='fluid-reduced-transition-gas-v1':
        put(n/'collision.vss',f'# hard spheres: omega=.5, alpha=1\nAr {p["molecule_diameter"]} 0.5 {p["reference_temperature"]} 1\n');text+='collide vss gas collision.vss\n'
    else:assert e['model']=='fluid-reduced-free-molecular-v1'
    if ntri:text+='read_surf walls.surf\n'
    if ntri:
        data=s['boundaries'][0]['data'];assert data['velocity']['expression']==[0.,0.,0.];text+=f'surf_collide inner diffuse {data["temperature_K"]} {data["accommodation"]}\nsurf_modify all collide inner\n'
    for name,axis,side in [(a+suffix,j,k) for j,a in enumerate('xyz') for k,suffix in enumerate(('lo','hi'))]:
        if name in opened:continue
        point=np.array(L)/2;point[axis]=L[axis]*side;bc=s['boundaries'][0]
        for b in s['boundaries'][1:]:
            if b['operator']=='gas_wall' and select(s,b['selection'],point[None])[0]:bc=b
        data=bc['data'];vel=data['velocity']['expression'];assert all(isinstance(a,(int,float)) for a in vel)
        text+=f'surf_collide {name} diffuse {data["temperature_K"]} {data["accommodation"]} translate '+ ' '.join(map(str,vel))+f'\nbound_modify {name} collide {name}\n'
    for i,b in enumerate(s['boundaries']):
        if b['operator']!='gas_reservoir':continue
        a=b['data'];vel=a['velocity']['expression'];assert vel==[0.,0.,0.]
        port=ports[i];lo=np.array(port['low']);hi=np.array(port['high']);pad=max(L)*1e-7;lo-=pad;hi+=pad;region=' '.join(str(v) for pair in zip(lo,hi) for v in pair)
        text+=f'mixture res{i} Ar nrho {a["density_kg_m3"]/mass} temp {a["temperature_K"]} vstream 0 0 0\nregion port{i} block {region}\nfix emit{i} emit/face res{i} {port["face"]} region port{i}\n'
    text+=f'create_particles gas n {particles}\nstats 1000\nstats_style step cpu np ncoll\ntimestep {dt}\nrun {burn}\nwrite_restart burn.restart\n'
    text+='compute state grid all gas massrho u v w\ncompute thermal thermal/grid all gas temp press\ncompute stress pflux/grid all gas momxx momyy momzz momxy momyz momxz\ncompute heat eflux/grid all gas heatx heaty heatz\n'
    text+=f'fix average ave/grid all 10 1000 {sample_steps} c_state[*] c_thermal[*] c_stress[*] c_heat[*]\ndump result grid all {sample_steps} moments.grid id xc yc zc f_average[*]\nrun {sample_steps}\n'
    put(n/'in.sparta',text);save(job/'sampling-plan.json',{'burn_steps':burn,'sample_steps':sample_steps,'sampling_stride':10,'native_dt_s':dt,'initial_particles':particles,'real_molecules_per_particle':fnum,'seed':112358,'steady_and_sampling_error_verified':False})


def run(root,e,g):
    job=root/'cases'/e['design_id'];status=job/'status.json'
    if status.exists():return json.loads(status.read_text())
    job.mkdir(parents=True);save(job/'design.json',e);state={'design_id':e['design_id'],'status':'queued'};save(status,state);name='ch02sparta-'+hashlib.sha256(e['design_id'].encode()).hexdigest()[:12]+'-'+str(time.time_ns())[-9:]
    try:
        with reservation(root,name):
            prepare(job,e);cmd=['docker','--host',SOCKET,'run','--name',name,'--network','none','--cpus','1','--memory','768m','--user',f'{os.getuid()}:{os.getgid()}','-e','OMP_NUM_THREADS=1','-v',f'{job.resolve()}:/work','-w','/work/native','--entrypoint','/usr/bin/stdbuf',IMAGE,'-oL',EXEC,'-in','in.sparta'];save(job/'execution.json',{'producer':'unmodified SPARTA 27Aug2026 serial, VSS hard-sphere limit or no collisions','image':IMAGE,'source':'https://github.com/sparta/sparta','command':cmd,'script_sha256':digest(Path(__file__)),'start_unix':time.time(),'numerical_validation':False});state.update(status='running',container=name);save(status,state)
            with (job/'solver.log').open('w') as f:cp=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
            assert cp.returncode==0,f'native exit {cp.returncode}'
        save(job/'grading-template.json',g);state.update(status='native_complete_pending_conversion',native_moments_sha256=digest(job/'native/moments.grid'),pending='Tetrahedral public mesh and wall-frame boundary moment extraction; do not count raw grid moments as public reference.')
    except Exception as ex:state.update(status='needs_attention',error=repr(ex),traceback=traceback.format_exc())
    state['ended_unix']=time.time();save(status,state);return state


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int,default=40);ap.add_argument('--only');args=ap.parse_args();tasks=[];freeze=json.loads((args.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text())
    for p in args.snapshot.glob('qbank/02-fluid-mechanics/*/*/author/chapter02-ten-20261020/design.json'):
        r=json.loads(p.read_text())
        if r['question'] not in ('2.10.3','2.10.4'):continue
        assert digest(p)==freeze['designs'][p.relative_to(args.snapshot).as_posix()]
        for e in r['proposed_cases']:
            if not supported(e) or (args.only and args.only not in e['design_id']):continue
            tasks.append(({**e,'task':r['task'],'model':r['model']},json.loads((p.parents[1]/'grading-template.json').read_text())))
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=min(args.workers,len(tasks))) as pool:states=list(pool.map(run,[args.root]*len(tasks),[e for e,g in tasks],[g for e,g in tasks]))
    save(args.root/'maintenance/sparta-summary.json',states);print(json.dumps({'native_completed_pending_conversion':sum(s['status']=='native_complete_pending_conversion' for s in states),'attention':[s for s in states if s['status']=='needs_attention']}))


if __name__=='__main__':main()
