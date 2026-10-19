"""Two-job recovery of bounded batches through the installed maintenance CLI."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

TASK='linear-periodic-transport-1d'
TASK_REL='qbank/01-prescribed-pdes/1.3-scalar-transport/'+TASK
SOURCE_REV='c9d55b73f3bb654db0a05885e2031396c88a4377'
SOURCE_PREFIX='migration-trials/pdebench/2026-10-18/preflight-v1/existing80'
GROUPS={'A':['001','021','041','061'],'B':['011','031','051','080']}


def cli(runtime,*arguments):
    command=[sys.executable,'-m','caeoj_tools.cli','data',*arguments,'--root',str(runtime)]
    result=subprocess.run(command,text=True,capture_output=True,timeout=600)
    if result.returncode:raise RuntimeError('Maintenance CLI failed: '+result.stderr[-1200:])
    return json.loads(result.stdout)


def code_identity(runtime):
    digest=hashlib.sha256()
    files=sorted((runtime/'src').rglob('*.py'))+[runtime/'support/hf_readiness.py']
    files+=[runtime/TASK_REL/'instruction.md',runtime/TASK_REL/'DATA.md']
    for path in files:digest.update(path.relative_to(runtime).as_posix().encode()+b'\0'+path.read_bytes())
    return digest.hexdigest()


def run(args,runtime):
    from huggingface_hub import HfApi,hf_hub_download
    from caeoj_tools import data_pool as pool
    from caeoj.case_grading import grade_case
    signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(TimeoutError('Readiness internal 20 minute deadline')))
    signal.alarm(20*60)
    start=time.monotonic();api=HfApi();job=os.environ['JOB_ID']
    state_path=args.prefix+'/state.json'
    code_id=code_identity(runtime)
    cold={'source_materializations':[],'detected_existing':[]}
    source_choice_path=hf_hub_download(args.repo_id,SOURCE_PREFIX+'/selection.json',repo_type='dataset',revision=SOURCE_REV)
    original=pool.manifest(source_choice_path)
    if not args.resume:
        state={'version':1,'status':'planned','code_id':code_id,'first_job_id':job,'source_revision':SOURCE_REV,
            'groups':{g:{n:original['cases'][n] for n in names} for g,names in GROUPS.items()},
            'completed':{},'formal_selection_changed':False}
    else:
        path=hf_hub_download(args.repo_id,state_path,repo_type='dataset',revision=args.revision)
        state=pool.checked_json(path)
        if state['first_job_id']==job or state['code_id']!=code_id or state['source_revision']!=SOURCE_REV:
            raise RuntimeError('Recovery requires a fresh Job and the exact frozen plan/code')
        if state['completed']:raise RuntimeError('Expected unacknowledged first batch, not a fabricated checkpoint')
    def persist():
        path=Path('/tmp/readiness-state.json');pool.write_json(path,state)
        return api.upload_file(repo_id=args.repo_id,repo_type='dataset',revision=args.revision,
            path_or_fileobj=path,path_in_repo=state_path,commit_message='Checkpoint bounded migration readiness').oid
    if not args.resume:persist()
    (runtime/TASK_REL).mkdir(parents=True,exist_ok=True)
    pool.write_json(runtime/TASK_REL/'data-manifest.json',{**original,'cases':{},'samples':{}})
    old_store=None
    for group,names in GROUPS.items():
        head=api.repo_info(args.repo_id,repo_type='dataset',revision=args.revision).sha
        backing=pool.HubStore(args.repo_id,head,cache_dir='/tmp/readiness-current-cache')
        root_exists=bool(api.get_paths_info(args.repo_id,[TASK_REL+'/pool/index.json'],repo_type='dataset',revision=head))
        present=False
        if root_exists:
            view=pool.consumer_store(original,backing)
            present=all(view.lookup(state['groups'][group][n]['case_id']) is not None for n in names)
            if present:
                for n in names:
                    item=view.lookup(state['groups'][group][n]['case_id'])
                    if item['sha256']!=state['groups'][group][n]['case']['sha256']:
                        raise RuntimeError('Recovered descriptor differs from frozen source binding')
                chosen=pool.select(original,backing,[n+'='+state['groups'][group][n]['case_id'] for n in names],[])
                pool.fetch(chosen,backing)
                cold['detected_existing'].append(group)
        if not present:
            cold['source_materializations'].append(group)
            if old_store is None:
                old_store=pool.ShardStore(pool.HubStore(args.repo_id,SOURCE_REV,cache_dir='/tmp/readiness-source-cache'),
                    SOURCE_PREFIX,'/tmp/readiness-source-members')
            choice=pool.select(original,old_store,[n+'='+original['cases'][n]['case_id'] for n in names],[])
            generated=Path('/tmp/readiness-generated-'+group);generated.mkdir()
            pool.write_json(generated/'data-manifest.json',choice)
            pool.assemble(generated,choice,old_store);pool.verify(generated,strict=True)
            for n in names:
                descriptor=pool.bound(old_store,TASK_REL,choice['cases'][n]['case'])
                pool.write_json(generated/'reference'/n/'certificate.json',descriptor['origin']['certificate_identity'])
            physical=Path('/tmp/readiness-physical-'+group)
            cli(runtime,'pack','--task',TASK,'--source',str(generated),'--output',str(physical),'--shard-mib','4')
            receipt=cli(runtime,'upload','--bundle',str(physical),'--revision',args.revision)
            head=receipt['revision']
            if not args.resume:
                # Deliberately lose the WHOLE worker, after root publication but
                # before marking completion. The next Job has no tmp volumes.
                print(json.dumps({'status':'intentional_whole_job_loss','group':group,'published_revision':head,
                    'checkpoint_has_completion':False,'source_materializations':cold['source_materializations']}),flush=True)
                os._exit(75)
        state['completed'][group]={'revision':head,'job_id':job,'reconciled_existing':present}
        persist()
    if not args.resume:raise RuntimeError('First Job should stop after its first committed batch')
    # Real installed CLI selection, assembly and strict verification across batches.
    head=api.repo_info(args.repo_id,repo_type='dataset',revision=args.revision).sha
    arguments=['select','--task',TASK,'--revision',head,'--output',str(runtime/TASK_REL/'data-manifest.json')]
    for group,names in GROUPS.items():
        for n in names:arguments+=['--case',n+'='+state['groups'][group][n]['case_id']]
    selected=cli(runtime,*arguments)
    assembled=cli(runtime,'assemble','--task',TASK,'--revision',head,'--cache-dir','/tmp/readiness-cli-cache')
    verified=cli(runtime,'verify','--task',TASK,'--strict')
    repeat=cli(runtime,'assemble','--task',TASK,'--revision',head,'--cache-dir','/tmp/readiness-cli-cache')
    accepted=0
    for directory in (runtime/TASK_REL/'cases').iterdir():
        ref=runtime/TASK_REL/'reference'/directory.name
        if grade_case(directory/'problem.json',ref/'reference.h5',ref/'grading.json')['status']!='accepted':
            raise RuntimeError('Recovered case failed actual grading')
        accepted+=1
    if accepted!=8 or not verified['valid'] or repeat['changed']!=0 or cold['source_materializations']!=['B'] or cold['detected_existing']!=['A']:
        raise RuntimeError('Cold recovery/cross-batch invariants failed')
    state.update(status='readiness_verified',second_job_id=job,installed_cli_selection=selected,
        installed_cli_assembly=assembled,installed_cli_verify=verified,repeat_changed=repeat['changed'],
        cold_recovery=cold,accepted_cases=accepted,pool_revision=head,elapsed_seconds=time.monotonic()-start,
        installation='non-editable uv pip install; CLI --root points to author workspace',
        private_selection_scope='Only the HF Job temporary runtime; repository formal selection unchanged')
    commit=persist()
    signal.alarm(0)
    print(json.dumps({'status':state['status'],'state_revision':commit,'pool_revision':head,'accepted_cases':accepted,
        'elapsed_seconds':state['elapsed_seconds']}),flush=True)
    return 0
