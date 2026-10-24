"""Patch only the generated RC5 Harbor execution contexts; never touch data."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tomllib
import zipfile

HERE=Path(__file__).resolve().parent
RECEIPT='.caeoj-rc5-environment-v1'
MARKER='# CAEOJ RC5 ENVIRONMENT PATCH V1'
def digest(data):return hashlib.sha256(data).hexdigest()
def checked_path(root,name):
    target=root/name
    if not target.resolve().is_relative_to(root):raise ValueError('Path escapes task: '+name)
    cursor=target
    while cursor!=root:
        if cursor.is_symlink():raise ValueError('Linked patch target is unsupported: '+name)
        cursor=cursor.parent
    return target
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--harbor-task',required=True,type=Path)
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args();root=args.harbor_task.resolve()
    manifest=json.loads((HERE/'PATCH-MANIFEST.json').read_text(encoding='utf-8'))
    for name,expected in manifest['files'].items():
        if digest((HERE/name).read_bytes())!=expected:raise ValueError('Patch checksum mismatch: '+name)
    if not (root/'task.toml').is_file() or (root/'tests/source-repair.json').exists():
        raise ValueError('Expected a generated numerical RC5 Harbor task, not a release directory or repair task')
    receipt_root=checked_path(root,RECEIPT)
    receipt_path=receipt_root/'receipt.json'
    receipt=json.loads(receipt_path.read_text(encoding='utf-8')) if receipt_path.exists() else None
    if receipt_root.exists() and receipt is None:raise ValueError('Incomplete prior patch; inspect its backups before retrying')
    public=[]
    for folder in ('environment','tests'):
        archive=checked_path(root,folder+'/agent.zip');data=archive.read_bytes();sha=digest(data)
        if sha not in manifest['rc5_public_archives']:raise ValueError('Public ZIP does not match official RC5: '+str(archive))
        with zipfile.ZipFile(archive) as z:public.append(json.loads(z.read('MANIFEST.json'))['task'])
    if len(set(public))!=1:raise ValueError('Agent and verifier public task identities differ')
    config=tomllib.loads((root/'task.toml').read_text(encoding='utf-8'))
    verifier=config.get('verifier',{})
    if verifier.get('environment_mode')!='separate' or verifier.get('network_mode')!='no-network':
        raise ValueError('Verifier must use separate and no-network modes')
    if receipt is not None:
        if receipt['task']!=public[0]:raise ValueError('Previously patched task identity changed')
        for name,expected in receipt['after_sha256'].items():
            if digest(checked_path(root,name).read_bytes())!=expected:raise ValueError('Previously patched file changed: '+name)
        print(json.dumps({'status':'already_applied','task':receipt['task'],'receipt':str(receipt_path)}));return
    changes={};before={}
    for folder in ('environment','tests'):
        name=folder+'/requirements.txt';path=checked_path(root,name);text=path.read_text(encoding='utf-8')
        for line in text.splitlines():
            if line.strip().lower().startswith('scipy==') and line.strip()!='scipy==1.18.1':
                raise ValueError('Conflicting existing SciPy pin: '+line)
        if 'scipy==1.18.1' not in text.splitlines():text=text.rstrip()+'\nscipy==1.18.1\n'
        changes[name]=text.encode('utf-8')
        name=folder+'/Dockerfile';path=checked_path(root,name);text=path.read_text(encoding='utf-8').replace('\r\n','\n')
        if MARKER in text:raise ValueError('Partial patch detected; no receipt')
        if 'python:3.14-slim' not in text and 'python@sha256:' not in text:raise ValueError('Unsupported base image')
        if 'pip install' not in text or 'requirements.txt' not in text:raise ValueError('Expected dependency install step missing')
        text=text.rstrip()+'\n'+MARKER+'\nCOPY rc5_patch_check_environment.py /opt/caeoj-rc5-patch/check_environment.py\nCOPY rc5_patch_gate.py /opt/caeoj-rc5-patch/gate.py\nRUN python /opt/caeoj-rc5-patch/gate.py\n'
        changes[name]=text.encode('utf-8')
        changes[folder+'/rc5_patch_check_environment.py']=(HERE/'check_environment.py').read_bytes()
        changes[folder+'/rc5_patch_gate.py']=(HERE/'gate.py').read_bytes()
    name='tests/test.sh';text=checked_path(root,name).read_text(encoding='utf-8').replace('\r\n','\n')
    if text.count('python /tests/judge.py')!=1:raise ValueError('Expected trusted judge invocation missing or ambiguous')
    changes[name]=text.replace('python /tests/judge.py',MARKER+'\npython /opt/caeoj-rc5-patch/gate.py\npython /tests/judge.py').encode('utf-8')
    for name in changes:
        path=checked_path(root,name)
        before[name]=digest(path.read_bytes()) if path.exists() else None
        if before[name] is not None and name.endswith(('rc5_patch_gate.py','rc5_patch_check_environment.py')):
            raise ValueError('Refusing to overwrite unexpected file: '+name)
    if args.dry_run:
        print(json.dumps({'status':'dry_run','task':public[0],'files':list(changes),'data_modified':False}));return
    receipt_root.mkdir()
    for name,content in changes.items():
        path=checked_path(root,name)
        if path.exists():
            backup=receipt_root/'before'/name;backup.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,backup)
        path.write_bytes(content)
    receipt={'patch':'rc5-environment-v1','task':public[0],'before_sha256':before,
             'after_sha256':{name:digest(data) for name,data in changes.items()},
             'data_modified':False,'public_archives_modified':False,'rebuild_required':True}
    receipt_path.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'applied','task':public[0],'receipt':str(receipt_path),'rebuild_required':True}))

if __name__=='__main__':main()
