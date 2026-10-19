"""Partitioned pool discovery and immutable batch publication.

Case/selection contracts are unchanged. A small root index routes case IDs to
64 hash partitions; each entry binds a case descriptor and immutable transport.
"""
import hashlib
from pathlib import Path
import re
import tempfile
from . import data_pool as p


def bucket(case_id):
    if not re.fullmatch('case-[0-9a-f]{24}',case_id): raise p.PoolError('Invalid partitioned case ID')
    return f'{int(case_id[5:7],16)//4:02x}'


class PartitionStore:
    def __init__(self,backing,prefix,cache,index=None):
        self.backing=backing; self.prefix=p.relative(prefix); self.root=Path(cache).absolute()
        self.revision=backing.revision
        self.index=index or p.checked_json(backing.get(self.prefix+'/pool/index.json'))
        if (self.index.get('schema_version')!=4 or self.index.get('kind')!='partitioned-case-pool'
                or not isinstance(self.index.get('partitions'),dict)):
            raise p.PoolError('Invalid partitioned pool index')
        total=0
        for key,entry in self.index['partitions'].items():
            if not re.fullmatch('[0-3][0-9a-f]',key) or type(entry.get('case_count')) is not int or entry['case_count']<1:
                raise p.PoolError('Invalid partition count/key')
            p.relative(entry['path']);p.check_entry(entry);total+=entry['case_count']
        if total!=self.index.get('case_count'):raise p.PoolError('Partition root count mismatch')
        self.partitions={}; self.transports={}

    def bound(self,entry):
        path=self.backing.get(self.prefix+'/'+p.relative(entry['path']))
        if not p.matches(path,entry):raise p.PoolError('Partition/transport digest mismatch')
        return path

    def partition(self,key):
        if key not in self.partitions:
            entry=self.index['partitions'].get(key)
            if entry is None:return {}
            data=p.checked_json(self.bound(entry))
            if data.get('schema_version')!=1 or not isinstance(data.get('cases'),dict):
                raise p.PoolError('Invalid case partition')
            if len(data['cases'])!=entry['case_count'] or any(bucket(cid)!=key for cid in data['cases']):
                raise p.PoolError('Wrong partition membership/count')
            self.partitions[key]=data['cases']
        return self.partitions[key]

    def lookup(self,cid):return self.partition(bucket(cid)).get(cid)

    def get(self,name):
        name=p.relative(name)
        if name==self.prefix+'/pool/index.json':return self.backing.get(name)
        base=self.prefix+'/pool/cases/'
        if not name.startswith(base):raise p.PoolError('Path outside partitioned task')
        cid=name[len(base):].split('/')[0];entry=self.lookup(cid)
        if entry is None:raise p.PoolError('Unknown partitioned case')
        if name==self.prefix+'/'+entry['path'] and 'descriptor' in entry:
            target=self.root/'descriptors'/cid/'case.json'
            p.write_json(target,entry['descriptor'])
            if p.digest(target)!=entry['sha256']:raise p.PoolError('Embedded descriptor digest mismatch')
            return target
        binding=entry['transport'];transport=p.relative(binding['path'])
        if not transport.startswith('pool/batches/') or not transport.endswith('/transport.json'):
            raise p.PoolError('Transport must be inside task batch storage')
        if transport not in self.transports:
            self.bound(binding)
            self.transports[transport]=p.ShardStore(self.backing,self.prefix+'/'+transport.rsplit('/',1)[0],
                self.root/hashlib.sha256(transport.encode()).hexdigest())
            if self.transports[transport].task!=self.prefix:raise p.PoolError('Transport task differs')
        return self.transports[transport].get(name)


def stage_plan(index,new_cases,transport,read_partition,*,update=False):
    """Pure merge planner, shared by offline checks and live optimistic writes."""
    partitions={}; added=0
    for cid,binding in new_cases.items():
        key=bucket(cid)
        if key not in partitions:partitions[key]=dict(read_partition(key))
        previous=partitions[key].get(cid)
        entry={**binding,'transport':transport}
        if previous:
            # Repacking identical logical cases must not redirect old entries.
            if all(previous.get(k)==binding.get(k) for k in ('path','sha256','input_complete','reference_complete')):
                if 'descriptor' in binding:
                    partitions[key][cid]={**previous,'descriptor':binding['descriptor']}
                continue
            if not update:raise p.PoolError('Remote case differs; review and use --update: '+cid)
        else:added+=1
        partitions[key][cid]=entry
    return partitions,added


def publish(directory,*,revision='main',update=False,atomic=False,extra_operations=()):
    from huggingface_hub import HfApi,CommitOperationAdd
    directory=Path(directory).absolute();selection=p.manifest(directory/'selection.json')
    prefix=selection['repository']['path'];repo=selection['repository']['repo_id']
    catalog=p.checked_json(directory/'transport.json')
    if catalog.get('task_path')!=prefix:raise p.PoolError('Transport/selection task differs')
    if not p.matches(directory/'index.json',catalog['index']):raise p.PoolError('Corrupt transport index')
    index=p.checked_json(directory/'index.json')
    if index.get('schema_version')!=3 or not index.get('cases') or catalog.get('case_count')!=len(index['cases']):
        raise p.PoolError('Invalid staged case index')
    assets=[e[k]['path'] for e in catalog['shards'] for k in ('archive','locator')]+['index.json','selection.json','transport.json']
    actual={x.relative_to(directory).as_posix() for x in directory.rglob('*') if x.is_file() and 'evidence' not in x.relative_to(directory).parts}
    if actual!=set(assets):raise p.PoolError('Undeclared/missing transport file')
    # All indexed cases, including those outside default selection, are consumed.
    descriptors={}
    with tempfile.TemporaryDirectory(prefix='caeoj-shard-validate-') as tmp:
        store=p.ShardStore(p.LocalStore(directory.parent),directory.name,Path(tmp)/'members')
        for cid,binding in index['cases'].items():
            item=p.bound(store,prefix,binding)
            if hashlib.sha256(p.encoded(item)).hexdigest()!=binding['sha256']:
                raise p.PoolError('Descriptor must use canonical JSON encoding')
            descriptors[cid]=item
            if (item.get('case_id')!=cid or binding.get('input_complete')!=item['input']['complete']
                    or binding.get('reference_complete')!=item['reference']['complete']):
                raise p.PoolError('Index/descriptor identity or completeness differs')
        all_items={**selection,'cases':{str(i):{'case_id':cid,'case':{k:b[k] for k in ('path','sha256')}}
                     for i,(cid,b) in enumerate(index['cases'].items())},'samples':{}}
        p.fetch(selection,store)
        p.fetch(all_items,store)
    batch=hashlib.sha256(p.encoded(catalog)).hexdigest()
    batch_prefix='pool/batches/'+batch
    api=HfApi();head=api.repo_info(repo,repo_type='dataset',revision=revision).sha
    paths=[prefix+'/'+batch_prefix+'/'+p.relative(x) for x in assets]
    existing={x.path:x for x in api.get_paths_info(repo,paths,repo_type='dataset',revision=head)}
    operations=[];skipped=0
    for logical,remote_name in zip(assets,paths):
        path=p.within(directory,logical);prev=existing.get(remote_name)
        if prev:
            if prev.lfs:same=prev.lfs.sha256==p.digest(path)
            else:
                git=hashlib.sha1(f'blob {path.stat().st_size}\0'.encode())
                with path.open('rb') as stream:
                    for block in iter(lambda:stream.read(1024*1024),b''):git.update(block)
                same=prev.blob_id==git.hexdigest()
            if not same:raise p.PoolError('Immutable batch changed: '+remote_name)
            skipped+=1
        else:operations.append(CommitOperationAdd(path_in_repo=remote_name,path_or_fileobj=path))
    # Group immutable writes, not one commit per payload file. Unknown commit
    # outcomes propagate; the next invocation reconciles remote content hashes.
    asset_operations=list(operations)
    staged=0
    for offset in range(0,0 if atomic else len(operations),50):
        group=operations[offset:offset+50]
        commit=api.create_commit(repo_id=repo,repo_type='dataset',revision=revision,parent_commit=head,
            operations=group,commit_message='Stage immutable task batch '+batch[:16])
        head=commit.oid;staged+=len(group)
    remote=p.HubStore(repo,head)
    root_name=prefix+'/pool/index.json'
    found=api.get_paths_info(repo,[root_name],repo_type='dataset',revision=head)
    if found:
        previous=p.checked_json(remote.get(root_name))
        if previous.get('schema_version')!=4:
            raise p.PoolError('Explicitly migrate flat pool before publishing partitioned batches')
        view=PartitionStore(remote,prefix,Path(tempfile.gettempdir()).resolve()/'caeoj-index-reads',previous)
        read_partition=view.partition
    else:
        previous={'schema_version':4,'kind':'partitioned-case-pool','case_count':0,'partitions':{}}
        read_partition=lambda key:{}
    transport={'path':batch_prefix+'/transport.json',**p.identity(directory/'transport.json')}
    partitions,added=stage_plan(previous,{cid:{**b,'descriptor':descriptors[cid]} for cid,b in index['cases'].items()},transport,read_partition,update=update)
    merged={**previous,'case_count':previous['case_count']+added,'partitions':dict(previous['partitions'])}
    operations=[]
    for key,cases in partitions.items():
        data=p.encoded({'schema_version':1,'cases':cases});sha=hashlib.sha256(data).hexdigest()
        binding={'path':f'pool/partitions/{key}/{sha}.json','sha256':sha,'size_bytes':len(data),'case_count':len(cases)}
        if previous['partitions'].get(key)==binding:continue
        merged['partitions'][key]=binding
        operations.append(CommitOperationAdd(path_in_repo=prefix+'/'+binding['path'],path_or_fileobj=data))
    if merged!=previous:
        operations.append(CommitOperationAdd(path_in_repo=root_name,path_or_fileobj=p.encoded(merged)))
    if atomic:
        operations=asset_operations+operations+list(extra_operations)
    elif extra_operations:
        raise p.PoolError('Checkpoint operations require atomic publication')
    if operations:
        if atomic:
            # Preupload immutable LFS objects before atomically exposing their
            # paths, partitions, root and bound prepared checkpoint together.
            api.preupload_lfs_files(repo_id=repo,repo_type='dataset',revision=revision,
                additions=operations,free_memory=False)
            # Budget request size after the server selects regular vs LFS mode.
            # LFS blobs are already staged; do not count their payload as NDJSON.
            regular=sum(4*((op.upload_info.size+2)//3) for op in operations
                if getattr(op,'_upload_mode',None)!='lfs')
            lfs_count=sum(getattr(op,'_upload_mode',None)=='lfs' for op in operations)
            if regular>900_000_000 or lfs_count>25000:
                raise p.PoolError('Atomic publication exceeds reviewed request limits; replan before committing')
        commit=api.create_commit(repo_id=repo,repo_type='dataset',revision=revision,parent_commit=head,
            operations=operations,commit_message='Atomically publish task hash partitions '+selection['task_id'])
        head=commit.oid
    verified=p.HubStore(repo,head)
    p.fetch(selection,verified)
    return {'revision':head,'batch_id':batch,'case_count':merged['case_count'],'added_cases':added,
            'uploaded_files':staged+len(operations),'skipped_files':skipped,'format':'partitioned-case-pool'}
