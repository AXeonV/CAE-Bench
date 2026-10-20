"""Bounded checkpoint sampling and public assembly for the 20 kinetic cases.

Wait for active primary runs. No interruption or numerical retry loop.
The only source patch is the separately archived read-only event observer.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time
import traceback
from pathlib import Path
from native_closed_cavity import SOCKET, save, put, digest
from native_sparta import IMAGE
from sparta_reference import package
from titan_resources import reservation, identity


def await_primary(root,job,deadline):
    while time.monotonic()<deadline:
        state=json.loads((job/'status.json').read_text()) if (job/'status.json').exists() else {'status':'queued'}
        if state['status']=='native_complete_pending_conversion':return state
        if state['status']=='unvalidated_candidate':return state
        if state['status']=='needs_attention':
            repair=root/'maintenance/sparta-trial-repair.json'
            if job.name=='ch02-2-10-4-01-pressure_duct' and repair.exists():
                j=json.loads(repair.read_text())
                if identity(j['pid'])==str(j['starttime']):time.sleep(30);continue
            raise RuntimeError('primary native run failed; no automatic retry: '+str(state.get('error')))
        time.sleep(30)
    raise RuntimeError('24h bounded primary wait expired; active solver left untouched')


def run(root,e,g):
    job=root/'cases'/e['design_id'];sample=job/'sampling';status=sample/'status.json';deadline=time.monotonic()+24*3600
    if status.exists():return json.loads(status.read_text())
    while not (job/'status.json').exists() and time.monotonic()<deadline:time.sleep(30)
    assert (job/'status.json').exists(),'primary case was not scheduled within 24h'
    sample.mkdir(parents=True,exist_ok=True);state={'design_id':e['design_id'],'status':'waiting_primary'};save(status,state)
    try:
        primary=await_primary(root,job,deadline)
        if primary['status']=='unvalidated_candidate':return primary
        save(job/'native-primary-completion.json',primary);save(job/'assembly-design.json',e)
        build=root/'maintenance/sparta-observer-build'
        while time.monotonic()<deadline:
            bs=json.loads((build/'status.json').read_text())
            if bs['stage']=='built':break
            controller=json.loads((root/'maintenance/sparta-observer-build-controller.json').read_text());assert identity(controller['pid'])==str(controller['starttime']),'observer build controller ended without a built binary';time.sleep(30)
        else:raise RuntimeError('24h bounded build wait expired')
        binary=Path(bs['binary']);assert digest(binary)==bs['binary_sha256'];checkpoint=job/'native/burn.restart';assert checkpoint.is_file()
        origin=(job/'native/in.sparta').read_text();physics=[line for line in origin.splitlines() if line.startswith(('collide ','surf_collide ','surf_modify ','bound_modify ','region ','fix emit'))]
        for name in ('collision.vss',):
            if (job/'native'/name).exists():shutil.copy2(job/'native'/name,sample/name)
        script='seed 112359\nread_restart /original/burn.restart\n'+'\n'.join(physics)+'\nstats 1000\nstats_style step cpu np ncoll\n'
        script+='compute state grid all gas massrho u v w\ncompute thermal thermal/grid all gas temp press\ncompute stress pflux/grid all gas momxx momyy momzz momxy momyz momxz\ncompute heat eflux/grid all gas heatx heaty heatz\nfix average ave/grid all 10 1000 10000 c_state[*] c_thermal[*] c_stress[*] c_heat[*]\ndump result grid all 10000 moments.grid id xc yc zc f_average[*]\n'
        # Exactly one boundary compute activates the diagnostic callback only
        # on the selected 1-in-10 sampling timesteps. Native tally stays intact.
        script+='compute boxwatch boundary gas n\nfix boxwatchavg ave/time 10 1 10 c_boxwatch[*] mode vector file box-native-tallies.dat\n'
        if (job/'native/walls.surf').exists():script+='compute surfacewatch surf all gas fx fy fz ke\nfix surfaceaverage ave/surf all 10 1000 10000 c_surfacewatch[*]\ndump wallresult surf all 10000 surface-moments.dat id f_surfaceaverage[*]\n'
        script+='run 10000\n';put(sample/'in.sample',script);name='ch02sparta-sample-'+hashlib.sha256(e['design_id'].encode()).hexdigest()[:12]+'-'+str(time.time_ns())[-9:]
        with reservation(root,name):
            command=['docker','--host',SOCKET,'run','--name',name,'--network','none','--cpus','1','--memory','768m','--user',f'{os.getuid()}:{os.getgid()}','-e','OMP_NUM_THREADS=1','-e','CAEOJ_BOUNDARY_EVENTS=/work/boundary-events.dat','-v',f'{sample.resolve()}:/work','-v',f'{(job/"native").resolve()}:/original:ro','-v',f'{binary.parent.resolve()}:/producer:ro','-w','/work','--entrypoint','/usr/bin/stdbuf',IMAGE,'-oL','/producer/'+binary.name,'-in','in.sample']
            record={'producer':'SPARTA 27Aug2026 + read-only boundary event observer','image':IMAGE,'binary_sha256':bs['binary_sha256'],'patch_sha256':digest(build/'boundary-observer.patch'),'checkpoint_sha256':digest(checkpoint),'original_execution':'execution.json','observer_build':'maintenance/sparta-observer-build/build.json','command':command,'seed':112359,'sample_steps':10000,'sampling_stride':10,'script_sha256':digest(Path(__file__)),'conversion_script_sha256':digest(Path(__file__).with_name('sparta_reference.py')),'start_unix':time.time(),'physics_changes':False,'numerical_validation':False};save(sample/'execution.json',record);state.update(status='running',stage='boundary_sampling',container=name);save(status,state);save(job/'status.json',state)
            with (sample/'solver.log').open('w') as f:cp=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT)
            assert cp.returncode==0,f'native sampling exit {cp.returncode}'
            state.update(stage='converting');save(status,state);save(job/'status.json',state);state.update(package(job,e));save(job/'reference/grading.json',g);save(job/'producer.json',{**record,'source':'https://github.com/sparta/sparta','source_location':'Pinned image source plus diagnostic-only patch, both archived on Titan','reference_scope':'All six declared quantities from this checkpoint sampling run; no numerical validation'});state.update(status='unvalidated_candidate',stage='assembled',ended_unix=time.time())
        save(status,state);save(job/'status.json',state);return state
    except Exception as ex:
        state.update(status='needs_attention',error=repr(ex),traceback=traceback.format_exc(),ended_unix=time.time());save(status,state)
        # Preserve a still-active primary run's ownership/status on timeout.
        current=json.loads((job/'status.json').read_text()) if (job/'status.json').exists() else {}
        if current.get('status') not in ('running','preparing','queued') or current.get('stage') in ('boundary_sampling','converting'):save(job/'status.json',state)
        return state


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int,default=20);ap.add_argument('--only');args=ap.parse_args();tasks=[];freeze=json.loads((args.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text())
    for p in args.snapshot.glob('qbank/02-fluid-mechanics/*/*/author/chapter02-ten-20261020/design.json'):
        r=json.loads(p.read_text())
        if r['question'] not in ('2.10.3','2.10.4'):continue
        assert digest(p)==freeze['designs'][p.relative_to(args.snapshot).as_posix()]
        for e in r['proposed_cases']:
            if args.only and args.only not in e['design_id']:continue
            tasks.append(({**e,'task':r['task'],'model':r['model']},json.loads((p.parents[1]/'grading-template.json').read_text())))
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=min(args.workers,len(tasks))) as pool:states=list(pool.map(run,[args.root]*len(tasks),[e for e,g in tasks],[g for e,g in tasks]))
    states=[json.loads((args.root/'cases'/e['design_id']/'status.json').read_text()) for e,g in tasks]
    save(args.root/'maintenance/sparta-reference-summary.json',states);print(json.dumps({'completed':sum(s['status']=='unvalidated_candidate' for s in states),'attention':[s for s in states if s['status']=='needs_attention']}))


if __name__=='__main__':main()
