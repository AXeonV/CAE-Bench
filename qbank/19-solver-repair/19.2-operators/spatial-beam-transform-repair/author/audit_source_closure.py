"""Bind actual compiled dependency paths/bytes to the public upstream closure."""
import hashlib,json,subprocess
from pathlib import Path
TASK=Path(__file__).resolve().parents[1]
DOCKER='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
CODE=r'''
import hashlib,json,pathlib,re,subprocess,tarfile
used=set()
for directory in ['/opt/kratos-build','/opt/beam-build']:
    text=subprocess.check_output(['ninja','-C',directory,'-t','deps'],text=True)
    used.update(re.findall(r'^    /opt/kratos-source/(.+)$',text,re.M))
with tarfile.open('/tmp/public-source.tar.gz') as tar:
    members={m.name:m for m in tar.getmembers() if m.isfile()}
    missing=sorted(used-members.keys());different=[];hashes={}
    for name in sorted(used&members.keys()):
        actual=pathlib.Path('/opt/kratos-source',name).read_bytes();public=tar.extractfile(members[name]).read()
        if actual!=public:different.append(name)
        hashes[name]=hashlib.sha256(actual).hexdigest()
print(json.dumps({'compiled_upstream_dependencies':len(used),'public_files':len(members),'missing':missing,'different_bytes':different,'actual_dependency_hashes':hashes}))
'''
if __name__=='__main__':
    command=[DOCKER,'run','--rm','--network','none','--mount',f'type=bind,source={(TASK/"public/kratos-source.tar.gz").resolve()},target=/tmp/public-source.tar.gz,readonly','caeoj-kratos14657-runtime:base','python','-c',CODE]
    report=json.loads(subprocess.check_output(command,text=True));assert not report['missing'] and not report['different_bytes'] and report['compiled_upstream_dependencies']>100
    report['runtime_image_id']=json.loads(subprocess.check_output([DOCKER,'image','inspect','caeoj-kratos14657-runtime:base']))[0]['Id']
    report['archive_sha256']=hashlib.sha256((TASK/'public/kratos-source.tar.gz').read_bytes()).hexdigest()
    (TASK/'author/data-evidence/source-closure.json').write_text(json.dumps(report,indent=2)+'\n');print('matched actual compiled dependencies:',report['compiled_upstream_dependencies'])
