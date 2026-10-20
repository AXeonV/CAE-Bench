"""Build a diagnostic-only boundary-event export in pinned SPARTA source.

Only ComputeBoundary's existing tally callback gains a read-only CSV sink.
The collision, reflection, transport, random-number and native tally code is
unchanged. Preserve the original file, unified patch and full build record.
"""
import argparse
import difflib
import hashlib
import json
import os
import subprocess
import tarfile
import time
from pathlib import Path
from native_sparta import IMAGE
from native_closed_cavity import SOCKET, save, digest
from titan_resources import reservation


INCLUDES='#include <cstdio>\n#include <cstdlib>\n'
OBSERVER=r'''
  // CAEOJ diagnostic-only boundary event export. No state or RNG mutation.
  if (istyle == SURFACE && ip && !jp) {
    const char *event_path = std::getenv("CAEOJ_BOUNDARY_EVENTS");
    if (event_path && event_path[0]) {
      static FILE *event_file = nullptr;
      if (!event_file) {
        event_file = std::fopen(event_path,"w");
        if (!event_file) error->one(FLERR,"Cannot open diagnostic event file");
        std::setvbuf(event_file,nullptr,_IOFBF,1024*1024);
      }
      std::fprintf(event_file,
        "%lld %d %.17g %.17g %.17g %.17g %.17g %.17g %.17g %.17g %.17g %.17g\n",
        static_cast<long long>(update->ntimestep),iface,
        iorig->x[0],iorig->x[1],iorig->x[2],
        iorig->v[0],iorig->v[1],iorig->v[2],ip->v[0],ip->v[1],ip->v[2],
        weightflag ? iorig->weight : 1.0);
    }
  }
'''


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);args=ap.parse_args();root=args.root;work=root/'maintenance/sparta-observer-build';assert not work.exists(),'preserve previous build; choose a new explicit directory for another build';work.mkdir();state={'stage':'queued','image':IMAGE,'physics_changes':False};save(work/'status.json',state);name='ch02sparta-observer-build-'+str(time.time_ns())[-9:]
    with reservation(root,name):
        base=['docker','--host',SOCKET,'run','--rm','--name',name,'--network','none','--cpus','1','--memory','768m']
        archive=work/'original-src.tar'
        with archive.open('wb') as f:subprocess.run(base+['--entrypoint','tar',IMAGE,'-cf','-','-C','/opt/sparta/source/src','.'],stdout=f,check=True)
        source=work/'src';source.mkdir()
        with tarfile.open(archive) as t:
            assert all(not p.name.startswith('/') and '..' not in Path(p.name).parts for p in t.getmembers());t.extractall(source)
        path=source/'compute_boundary.cpp';original=path.read_text();anchor='  // tally all values associated with group into array';assert original.count(anchor)==1
        changed=original.replace('#include "string.h"',INCLUDES+'#include "string.h"').replace(anchor,OBSERVER+'\n'+anchor)
        path.write_text(changed);(work/'compute_boundary.cpp.original').write_text(original);patch=''.join(difflib.unified_diff(original.splitlines(True),changed.splitlines(True),fromfile='stock/compute_boundary.cpp',tofile='observer/compute_boundary.cpp'));(work/'boundary-observer.patch').write_text(patch)
        command=base+['--user',f'{os.getuid()}:{os.getgid()}','-e','OMP_NUM_THREADS=1','-v',f'{work.resolve()}:/work','-w','/work/src','--entrypoint','make',IMAGE,'-j1','serial']
        save(work/'build.json',{'image':IMAGE,'source_archive_sha256':digest(archive),'original_boundary_sha256':hashlib.sha256(original.encode()).hexdigest(),'modified_boundary_sha256':hashlib.sha256(changed.encode()).hexdigest(),'patch_sha256':digest(work/'boundary-observer.patch'),'command':command,'started_unix':time.time(),'physics_changes':False,'observer':'Read-only logging in existing boundary_tally callback; only one active native boundary compute must be used.'});state['stage']='building';save(work/'status.json',state)
        with (work/'build.log').open('w') as f:subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,check=True)
        binary=source/'spa_serial';assert binary.is_file();state.update(stage='built',binary=str(binary),binary_sha256=digest(binary),finished_unix=time.time());save(work/'status.json',state);print(json.dumps(state))


if __name__=='__main__':main()
