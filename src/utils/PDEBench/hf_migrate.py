"""One bounded advection source batch with a durable, replayable HF checkpoint."""
import hashlib,json,os,signal,time,re,base64,io,zipfile
from pathlib import Path


def extract_span(source,first,count,target):
    if not os.environ.get('JOB_ID'):raise RuntimeError('Source arrays must stay in HF Jobs')
    if not 1<=count<=1000 or first<0 or first+count>10000:raise ValueError('Invalid source batch range')
    import fsspec,h5py,numpy as np
    from huggingface_hub import hf_hub_url
    start=time.monotonic();fs=fsspec.filesystem('http',client_kwargs={'trust_env':True})
    url=hf_hub_url(source['repo_id'],source['file'],repo_type='dataset',revision=source['revision'])
    with fs.open(url,'rb',block_size=8*1024*1024,cache_type='blockcache',cache_options={'maxblocks':8}) as raw:
        with h5py.File(raw,'r') as data,h5py.File(target,'w') as subset:
            n,frames,nx=data['tensor'].shape
            if n!=10000 or frames!=201 or nx!=1024:raise ValueError('Pinned source layout differs')
            subset['source_indices']=np.arange(first,first+count,dtype=np.int64)
            subset['t-coordinate']=data['t-coordinate'][:frames];subset['x-coordinate']=data['x-coordinate'][:]
            field=subset.create_dataset('tensor',(count,frames,nx),dtype=data['tensor'].dtype,
                chunks=(1,16,nx),compression='gzip',compression_opts=1,shuffle=True)
            for offset in range(0,count,100):
                length=min(100,count-offset);values=data['tensor'][first+offset:first+offset+length]
                if not np.isfinite(values).all():raise ValueError('Nonfinite source batch')
                field[offset:offset+length]=values
    return {'elapsed_seconds':time.monotonic()-start,'records':count,
        'logical_field_bytes_read':count*frames*nx*4,'subset_sha256':hashlib.sha256(Path(target).read_bytes()).hexdigest(),
        'whole_source_checksum_verified':False}


def runtime_identity(payload):
    """Bind archive contents, independent of ZIP timestamps and compression."""
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(payload))) as archive:
        rows=[(name,hashlib.sha256(archive.read(name)).hexdigest()) for name in sorted(archive.namelist())]
    return hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest()


def validate_state(state,key,recipe):
    if (state.get('version')!=1 or state.get('batch_key')!=key or state.get('recipe')!=recipe
            or state.get('status') not in ('planned','prepared','verified')):
        raise RuntimeError('Unknown or mismatched migration checkpoint')
    if state['status']!='planned' and not all(k in state for k in ('selection','transport_sha256')):
        raise RuntimeError('Incomplete bound checkpoint')


def transition(previous,state):
    validate_state(state,state['batch_key'],state['recipe'])
    if previous is None:
        if state['status']!='planned':raise RuntimeError('Checkpoint must start planned')
        return
    validate_state(previous,state['batch_key'],state['recipe'])
    ranks={'planned':0,'prepared':1,'verified':2}
    if ranks[state['status']]<ranks[previous['status']]:raise RuntimeError('Checkpoint status cannot regress')
    for key in ('selection','transport_sha256'):
        if key in previous and previous[key]!=state.get(key):raise RuntimeError('Bound checkpoint identity changed: '+key)


def save(args,state):
    from huggingface_hub import HfApi,hf_hub_download,CommitOperationAdd
    from caeoj_tools import data_pool as pool
    api=HfApi();head=api.repo_info(args.repo_id,repo_type='dataset',revision=args.revision).sha
    name=args.prefix+'/batches/'+state['batch_key']+'.json'
    exists=api.get_paths_info(args.repo_id,[name],repo_type='dataset',revision=head)
    previous=pool.checked_json(hf_hub_download(args.repo_id,name,repo_type='dataset',revision=head)) if exists else None
    transition(previous,state)
    return api.create_commit(repo_id=args.repo_id,repo_type='dataset',revision=args.revision,parent_commit=head,
        operations=[CommitOperationAdd(path_in_repo=name,path_or_fileobj=pool.encoded(state))],
        commit_message='Checkpoint source-batch migration '+state['batch_key'][:16]).oid


def consume(args,state,revision):
    from caeoj_tools import data_pool as pool
    from caeoj.case_grading import grade_case
    task=Path('/tmp/migration-consumed');task.mkdir()
    choice=state['selection'];pool.write_json(task/'data-manifest.json',choice)
    backing=pool.HubStore(args.repo_id,revision,cache_dir='/tmp/migration-consume-cache')
    pool.assemble(task,choice,backing);pool.verify(task,strict=True)
    for directory in (task/'cases').iterdir():
        ref=task/'reference'/directory.name
        if grade_case(directory/'problem.json',ref/'reference.h5',ref/'grading.json')['status']!='accepted':
            raise RuntimeError('Replayed batch reference failed real grading')
    if len(choice['cases'])!=state['recipe']['count']:raise RuntimeError('Migrated row accounting mismatch')
    return len(choice['cases'])


def prepare(args,source_report,runtime):
    from huggingface_hub import HfApi,hf_hub_download
    from caeoj_tools import data_pool as pool
    signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(TimeoutError('Migration internal deadline')))
    signal.alarm(25*60)
    sources=[x for x in source_report['sources'] if x['family']=='advection' and x['file']==args.source_file]
    if len(sources)!=1:raise ValueError('Choose one of the eight pinned Advection source files')
    source=sources[0]
    import __main__
    script=Path(__main__.__file__).read_text()
    script,count=re.subn(r'^RUNTIME_ZIP = .*$',"RUNTIME_ZIP = ''",script,flags=re.MULTILINE)
    if count!=1:raise RuntimeError('Cannot bind the submitted producer template')
    recipe={'repo_id':source['repo_id'],'revision':source['revision'],'file':source['file'],
        'source_sha256':source['source_lfs_sha256'],'first':args.batch_start,'count':args.batch_count,
        'producer_code_sha256':hashlib.sha256(script.encode()).hexdigest(),
        'runtime_contents_sha256':runtime_identity(__main__.RUNTIME_ZIP),
        'contract_sha256':hashlib.sha256((runtime/args.task_rel/'instruction.md').read_bytes()+(runtime/args.task_rel/'DATA.md').read_bytes()).hexdigest()}
    key=hashlib.sha256(pool.encoded(recipe)).hexdigest();api=HfApi()
    head=api.repo_info(args.repo_id,repo_type='dataset',revision=args.revision).sha
    state_name=args.prefix+'/batches/'+key+'.json'
    exists=api.get_paths_info(args.repo_id,[state_name],repo_type='dataset',revision=head)
    state={'version':1,'status':'planned','batch_key':key,'recipe':recipe,'first_job_id':os.environ['JOB_ID']}
    if exists:
        state=pool.checked_json(hf_hub_download(args.repo_id,state_name,repo_type='dataset',revision=head))
        validate_state(state,key,recipe)
        if 'selection' in state:
            root=args.task_rel+'/pool/index.json'
            if api.get_paths_info(args.repo_id,[root],repo_type='dataset',revision=head):
                view=pool.consumer_store(state['selection'],pool.HubStore(args.repo_id,head,cache_dir='/tmp/migration-replay-cache'))
                matches=[]
                for entry in state['selection']['cases'].values():
                    item=view.lookup(entry['case_id'])
                    if item is not None and item['sha256']!=entry['case']['sha256']:
                        raise RuntimeError('Recovered case binding differs')
                    matches.append(item is not None)
                if all(matches):
                    count=consume(args,state,head)
                    state.update(status='verified',pool_revision=head,last_job_id=os.environ['JOB_ID'],
                        resumed_without_source_read=True,verified_cases=count)
                    commit=save(args,state)
                    print(json.dumps({'status':'migration_batch_replayed','cases':count,'state_revision':commit,'source_records_read':0}),flush=True)
                    return None
    args.migration_state=state
    if not exists:save(args,state)
    target=Path('/tmp/migration-source.h5')
    state['source_read']=extract_span(source,args.batch_start,args.batch_count,target)
    return [{**source,'local_subset':str(target),'subset_sha256':state['source_read']['subset_sha256']}]


def finish(args,bundle,report):
    from caeoj_tools import data_pool as pool
    state=args.migration_state;choice=pool.manifest(bundle/'selection.json')
    physical=Path('/tmp/migration-physical');pool.shard_bundle(bundle,physical)
    prepared={**state,'status':'prepared','selection':choice,'producer_report':report,
        'transport_sha256':pool.digest(physical/'transport.json')}
    transition(state,prepared);state=prepared
    save(args,state)  # Bind expected case identities before any publication.
    receipt=pool.upload(physical,revision=args.revision)
    count=consume(args,state,receipt['revision'])
    state.update(status='verified',pool_revision=receipt['revision'],verified_cases=count,
        last_job_id=os.environ['JOB_ID'],resumed_without_source_read=False,upload_receipt=receipt)
    commit=save(args,state);signal.alarm(0)
    print(json.dumps({'status':'migration_batch_verified','cases':count,'pool_revision':receipt['revision'],
        'state_revision':commit,'batch_key':state['batch_key']}),flush=True)
    return 0
