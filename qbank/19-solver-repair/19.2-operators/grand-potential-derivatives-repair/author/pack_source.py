"""Deterministic genuine-source closure, independently matched to fixed upstream bytes."""
import argparse
import gzip
import hashlib
import io
import json
import posixpath
import tarfile
from pathlib import Path, PurePosixPath

TASK = Path(__file__).resolve().parents[1]
COMMIT = '2f53071dc31d76ee1dfdbaaafe9ef34b7f2a33dd'
ARCHIVE_SHA = '74d581cc49e262c96152865b0f5a3e9831bf262306b2c2766918c023d21e99a5'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--built-source',type=Path,required=True)
    args = parser.parse_args()
    if hashlib.sha256(args.archive.read_bytes()).hexdigest() != ARCHIVE_SHA:
        raise ValueError('Wrong upstream source archive')
    target = TASK/'public/moose-source.tar.gz'
    records=[]; omissions=[]
    with tarfile.open(args.archive) as upstream, target.open('wb') as raw, gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0) as zipped, tarfile.open(fileobj=zipped,mode='w|',format=tarfile.PAX_FORMAT) as output:
        members=upstream.getmembers(); prefix=members[0].name+'/'
        by_name={m.name:m for m in members}
        for member in sorted(members,key=lambda m:m.name):
            if not member.name.startswith(prefix):continue
            name=member.name[len(prefix):];parts=PurePosixPath(name).parts
            if not parts or '..' in parts:continue
            if any(x in ['gold','doc','docs','.github'] for x in parts) or name.endswith(('.e','.exd','.mp4','.png','.jpg','.pdf')):continue
            actual=member;seen=set()
            while actual.issym():
                if actual.name in seen:raise ValueError('Source link cycle')
                seen.add(actual.name)
                resolved=posixpath.normpath(posixpath.join(posixpath.dirname(actual.name),actual.linkname))
                actual=by_name.get(resolved)
                if actual is None:break
            if actual is None or not actual.isfile():
                if member.issym():omissions.append({'path':name,'target':member.linkname,'reason':'directory alias or optional external test asset'})
                continue
            data=upstream.extractfile(actual).read()
            if (args.built_source/name).read_bytes()!=data:raise ValueError('Source differs from native-built closure: '+name)
            info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o755 if actual.mode&0o111 else 0o644;info.mtime=0
            output.addfile(info,io.BytesIO(data))
            records.append({'path':name,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'source_path':actual.name[len(prefix):]})
    report={'commit':COMMIT,'upstream_url':f'https://api.github.com/repos/idaholab/moose/tarball/{COMMIT}',
            'upstream_archive_sha256':ARCHIVE_SHA,'closure_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
            'closure_bytes':target.stat().st_size,'files':records,'omitted_links':omissions,
            'policy':'Exclude documentation, golden-output directories and listed binary media; retain canonical source and licences. Materialize genuine internal regular-file links. Every retained byte independently equals fixed upstream and the source used for genuine native build.'}
    (TASK/'author/data-evidence/source-closure.json').write_text(json.dumps(report,indent=2)+'\n',newline='\n')
    print(len(records),target.stat().st_size,report['closure_sha256'],flush=True)


if __name__=='__main__':main()
