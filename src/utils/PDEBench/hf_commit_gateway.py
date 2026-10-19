"""Gate actual commit POSTs and reconcile lost responses without duplicate writes."""
from collections import deque
from contextlib import contextmanager
from datetime import timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
import re
import time
from types import SimpleNamespace
from hf_commit_policy import next_commit_slot


def reset_delay(headers,now):
    value=headers.get('retry-after')
    if value:
        try:return max(1.,float(value))
        except ValueError:
            try:return max(1.,parsedate_to_datetime(value).timestamp()-now)
            except (TypeError,ValueError):pass
    rate=headers.get('ratelimit','')
    match=re.search(r'(?:^|[;,])\s*t=(\d+)',rate)
    return float(match[1])+2 if match else 3600.


def operation_identity(operation):
    """Capture identities before the SDK mutates upload operation objects."""
    from huggingface_hub import CommitOperationAdd
    if not isinstance(operation,CommitOperationAdd):return None
    info=operation.upload_info; git=None
    if info.size<=16*1024**2:
        h=hashlib.sha1(f'blob {info.size}\0'.encode())
        with operation.as_file() as stream:
            for data in iter(lambda:stream.read(1024**2),b''):h.update(data)
        git=h.hexdigest()
    return {'path':operation.path_in_repo,'size':info.size,'sha256':info.sha256.hex(),'git':git}


def identities_match(expected,files):
    if any(x is None for x in expected):return False
    found={f.path:f for f in files}
    for item in expected:
        remote=found.get(item['path'])
        if remote is None or remote.size!=item['size']:return False
        if remote.lfs:
            if remote.lfs.sha256!=item['sha256']:return False
        elif not item['git'] or remote.blob_id!=item['git']:return False
    return True


class CommitGateway:
    def __init__(self,worker,repo,server_timestamp,deadline,clock=time.monotonic,sleep=time.sleep):
        self.worker=worker;self.repo=repo;self.deadline=deadline;self.clock=clock;self.sleep=sleep
        self.offset=server_timestamp-clock();self.last_slot=None;self.cooldown=0.;self.exclusive=False
        self.attempts=deque();self.rate_limits=0;self.next_at=None

    def now(self):return self.clock()+self.offset

    def request(self,request):
        if request.method!='POST' or '/commit/' not in request.url.path:return
        if not request.url.path.startswith('/api/datasets/'+self.repo+'/commit/'):
            raise RuntimeError('Unapproved commit destination')
        while True:
            slot,at=next_commit_slot(self.now(),self.worker,self.last_slot,self.cooldown,self.exclusive)
            self.next_at=at
            if self.clock()+max(0,at-self.now())>=self.deadline-120:
                raise TimeoutError('Insufficient bounded runtime for next commit slot')
            while self.now()<at:self.sleep(min(10,at-self.now()))
            if self.now()>slot*46+6:continue
            self.last_slot=slot;self.attempts.append(self.now())
            while self.attempts and self.attempts[0]<=self.now()-3600:self.attempts.popleft()
            print(json.dumps({'phase':'commit_post','worker':self.worker,'slot':slot,
                'server_time':self.now(),'own_commit_posts_last_hour':len(self.attempts)}),flush=True)
            return

    def response(self,response):
        if response.status_code==429 and '/commit/' in response.request.url.path:
            self.rate_limits+=1
            self.cooldown=max(self.cooldown,self.now()+reset_delay(response.headers,self.now()))
            print(json.dumps({'phase':'rate_limited_wait','worker':self.worker,'until_server_time':self.cooldown}),flush=True)

    def snapshot(self):
        return {'own_commit_posts_last_hour':len(self.attempts),'rate_limit_events':self.rate_limits,
            'cooldown_until_server_time':self.cooldown,'next_slot_server_time':self.next_at,
            'exclusive_finalizer':self.exclusive}

    def install(self):
        import httpx
        from huggingface_hub import HfApi,set_client_factory,CommitOperationAdd,CommitOperationCopy
        from huggingface_hub.errors import HfHubHTTPError
        set_client_factory(lambda:httpx.Client(follow_redirects=True,timeout=httpx.Timeout(300,connect=30),
            event_hooks={'request':[self.request],'response':[self.response]}))
        original=HfApi.create_commit;gateway=self
        def wrapped(api,*args,**kwargs):
            if args or kwargs.get('repo_id')!=gateway.repo:raise ValueError('Explicit approved repository required')
            operations=list(kwargs['operations']);expected=[operation_identity(op) for op in operations]
            def clone(op):
                if isinstance(op,CommitOperationAdd):return CommitOperationAdd(path_in_repo=op.path_in_repo,path_or_fileobj=op.path_or_fileobj)
                if isinstance(op,CommitOperationCopy):return CommitOperationCopy(src_path_in_repo=op.src_path_in_repo,path_in_repo=op.path_in_repo,src_revision=op.src_revision)
                raise ValueError('Unapproved commit operation')
            while True:
                try:return original(api,**{**kwargs,'operations':[clone(op) for op in operations]})
                except HfHubHTTPError as exc:
                    if exc.response.status_code==429:
                        gateway.cooldown=max(gateway.cooldown,gateway.now()+reset_delay(exc.response.headers,gateway.now()))
                        continue
                    if exc.response.status_code<500:raise
                    failure=exc
                except (httpx.TransportError,httpx.TimeoutException) as exc:failure=exc
                # A transport/5xx error may hide a successful atomic commit.
                # Prove every write at the current fixed head; never blindly replay.
                head=api.repo_info(gateway.repo,repo_type='dataset',revision=kwargs['revision']).sha
                files=api.get_paths_info(gateway.repo,[x['path'] for x in expected if x],repo_type='dataset',revision=head)
                if identities_match(expected,files):return SimpleNamespace(oid=head)
                raise RuntimeError('Unknown commit outcome; stop and inspect exact checkpoint/assets') from failure
        HfApi.create_commit=wrapped
        return original
