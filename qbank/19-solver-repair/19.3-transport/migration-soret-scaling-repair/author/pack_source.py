"""Pack the real Core, three actual modules, build inputs and retained licenses."""
import gzip,hashlib,json,tarfile
from pathlib import Path
from prepare_source import SOURCE,TASK
KEEP={'cmake','cpack','elmergrid','fhutiter','license_texts','matc','mathlibs','meshgen2d','umfpack'}
MODULES={'AdvectionDiffusion.F90','HeatSolve.F90','StatCurrentSolve.F90','CMakeLists.txt'}
def selected(rel):
 parts=rel.parts
 if len(parts)==1:return True
 if parts[0] in KEEP:return not any(x in {'tests','examples','.git','.github'} for x in parts)
 if parts[0]=='fem':
  if len(parts)==2:return True
  if parts[1]!='src':return False
  if parts[2:3]==('modules',):return len(parts)==4 and parts[-1] in MODULES
  return True
 return False
def main():
 files=[p for p in sorted(SOURCE.rglob('*')) if p.is_file() and selected(p.relative_to(SOURCE))]
 target=TASK/'public/elmer-source.tar.gz';target.parent.mkdir(exist_ok=True);records=[]
 with target.open('wb') as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0,compresslevel=6) as zipped,tarfile.open(fileobj=zipped,mode='w') as tar:
  for p in files:
   rel=p.relative_to(SOURCE).as_posix();info=tar.gettarinfo(str(p),arcname=rel);info.mode=0o644;info.uid=info.gid=0;info.uname=info.gname='root';info.mtime=0
   with p.open('rb') as stream:tar.addfile(info,stream)
   records.append({'file':rel,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 (TASK/'author/data-evidence/source-closure.json').write_text(json.dumps({'count':len(records),'files':records,'archive_sha256':hashlib.sha256(target.read_bytes()).hexdigest()},indent=2)+'\n',encoding='utf-8',newline='\n')
 print('public source',len(records),'files',target.stat().st_size,'bytes')
if __name__=='__main__':main()
