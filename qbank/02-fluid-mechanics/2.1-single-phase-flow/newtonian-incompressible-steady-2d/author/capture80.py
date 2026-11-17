"""Record the actual installed upstream producers without modifying them."""
from pathlib import Path
import argparse,hashlib,json,platform,subprocess,sys
import gmsh,h5py,numpy


def command(*args):return subprocess.check_output(args,text=True).strip()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--lethe-source',type=Path,required=True);p.add_argument('--lethe-binary',type=Path,required=True)
    p.add_argument('--openfoam-source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    producers=[]
    for name,source,binaries,url in [
        ('Lethe lethe-fluid',a.lethe_source,[a.lethe_binary],'https://github.com/chaos-polymtl/lethe'),
        ('OpenFOAM Foundation incompressibleFluid',a.openfoam_source,[a.openfoam_source/'platforms/linux64GccDPInt32Opt'/folder/file for folder,file in [('bin','foamRun'),('bin','blockMesh'),('bin','checkMesh'),('bin','mapFields'),('lib','libincompressibleFluidSolver.so'),('lib','libfiniteVolume.so'),('lib','libsampling.so')]],'https://github.com/OpenFOAM/OpenFOAM-dev')]:
        commit=command('git','-C',str(source),'rev-parse','HEAD');status=command('git','-C',str(source),'status','--porcelain','--untracked-files=no');assert not status
        producers.append(dict(name=name,source=url,commit=commit,tracked_changes=status,binary_sha256={b.name:hashlib.sha256(b.read_bytes()).hexdigest() for b in binaries}))
    a.output.write_text(json.dumps(dict(producers=producers,runtime=dict(platform=platform.platform(),python=sys.version,gmsh=gmsh.__version__,h5py=h5py.__version__,numpy=numpy.__version__,compiler=command('g++','--version'))),indent=2)+'\n')
