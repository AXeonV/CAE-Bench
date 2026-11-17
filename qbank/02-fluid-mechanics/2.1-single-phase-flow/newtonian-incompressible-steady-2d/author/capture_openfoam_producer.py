"""Capture installed independent producer provenance in a sourced OpenFOAM shell."""
from pathlib import Path
import hashlib,json,os,platform,subprocess,sys
import gmsh,h5py,numpy

def command(*args):return subprocess.check_output(args,text=True).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
root=Path(os.environ['WM_PROJECT_DIR']);plat=root/'platforms'/os.environ['WM_OPTIONS']
commit=command('git','-C',str(root),'rev-parse','HEAD')
files=[plat/'bin'/n for n in ('foamRun','blockMesh','checkMesh','mapFields')]
files += [plat/'lib'/n for n in ('libincompressibleFluidSolver.so','libfiniteVolume.so','libsampling.so','libfieldFunctionObjects.so','libincompressibleMomentumTransportModels.so','libmomentumTransportModels.so')]
data=dict(producer='OpenFOAM Foundation incompressibleFluid (foamRun)',source='https://github.com/OpenFOAM/OpenFOAM-dev',
          commit=commit,git_status=command('git','-C',str(root),'status','--porcelain'),
          source_urls={name:f'https://github.com/OpenFOAM/OpenFOAM-dev/blob/{commit}/{path}' for name,path in dict(
              solver='applications/modules/incompressibleFluid/incompressibleFluid.C',
              momentum='applications/modules/incompressibleFluid/momentumPredictor.C',
              pressure='applications/modules/incompressibleFluid/correctPressure.C',
              source_model='src/fvModels/general/codedFvModel/codedFvModel.H',
              steady_tutorial='tutorials/incompressibleFluid/pitzDailySteady/system/fvSolution',
              sampling='src/sampling/sampledSet/points/points.H').items()},
          runtime=dict(platform=platform.platform(),python=sys.version,numpy=numpy.__version__,h5py=h5py.__version__,gmsh=gmsh.__version__,
                       compiler=command('g++','--version'),mpi=command('mpicc','--showme:version'),wm_options=os.environ['WM_OPTIONS']),
          executables_and_libraries={str(p.relative_to(root)):sha(p) for p in files},
          independence='Separate upstream finite-volume solver and mesh/field adapter; no Lethe code, numerical output, or candidate submission used as a solve or initial guess.',
          source_adapter='codedFvModel only evaluates frozen affine acceleration and inserts -V*a into the standard fvModels source. No PDE implementation is replaced.',
          frozen_hf_commit='fbe115effe8131bd575c0cde1c9ca87a9d87fd3a')
Path(sys.argv[1]).write_text(json.dumps(data,indent=2)+'\n')
