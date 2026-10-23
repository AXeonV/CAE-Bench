"""Build deterministic closure after a streaming audit against the pinned source archive."""
from pathlib import Path,PurePosixPath
import argparse,gzip,hashlib,io,json,posixpath,tarfile
TASK=Path(__file__).resolve().parents[1]
COMMIT='03cebc8ae93747c437f53c9905f9a7322f154211'
ARCHIVE_SHA='a4b242257c81f7b33055a260d722f77830629b3f70a53869a824787316f92dc8'
def selected(name):return not any(x in ['gold','doc','docs','.github'] for x in PurePosixPath(name).parts) and not name.endswith(('.e','.exd','.mp4','.png','.jpg','.pdf'))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--built-source',type=Path,required=True);args=ap.parse_args()
 assert hashlib.file_digest(args.archive.open('rb'),'sha256').hexdigest()==ARCHIVE_SHA
 hashes={};links={};records=[];omissions=[]
 with tarfile.open(args.archive,mode='r|gz') as ar:
  prefix=None
  for m in ar:
   if prefix is None:prefix=m.name.split('/')[0]+'/'
   name=m.name[len(prefix):]
   if not name or not selected(name):continue
   if m.isfile():
    data=ar.extractfile(m).read();hashes[name]=(hashlib.sha256(data).hexdigest(),len(data),m.mode)
   elif m.issym():links[name]=posixpath.normpath(posixpath.join(posixpath.dirname(name),m.linkname))
 for name,target in links.items():
  seen=set();actual=target
  while actual in links:
   assert actual not in seen;seen.add(actual);actual=links[actual]
  if actual in hashes:hashes[name]=hashes[actual]
  else:omissions.append({'path':name,'target':target,'reason':'directory alias or optional external test asset'})
 out=TASK/'public/moose-source.tar.gz'
 with out.open('wb') as raw,gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0) as zipped,tarfile.open(fileobj=zipped,mode='w|',format=tarfile.PAX_FORMAT) as archive:
  for name,(sha,size,mode) in sorted(hashes.items()):
   data=(args.built_source/name).read_bytes();assert hashlib.sha256(data).hexdigest()==sha, name
   ti=tarfile.TarInfo(name);ti.size=size;ti.mode=0o755 if mode&0o111 else 0o644;ti.mtime=0;archive.addfile(ti,io.BytesIO(data));records.append({'path':name,'sha256':sha,'bytes':size,'source_path':links.get(name,name)})
 report={'commit':COMMIT,'upstream_archive_sha256':ARCHIVE_SHA,'closure_sha256':hashlib.file_digest(out.open('rb'),'sha256').hexdigest(),'closure_bytes':out.stat().st_size,'files':records,'omitted_links':omissions,'policy':'Exclude doc/gold/listed binary media; retain real source and licenses, materializing internal regular-file links. Every byte independently equals fixed upstream and native-built source. Streaming archive audit avoids repeated compressed random reads.'}
 (TASK/'author/data-evidence/source-closure.json').write_text(json.dumps(report,indent=2)+'\n',newline='\n');print(len(records),report['closure_bytes'],report['closure_sha256'],flush=True)
if __name__=='__main__':main()
