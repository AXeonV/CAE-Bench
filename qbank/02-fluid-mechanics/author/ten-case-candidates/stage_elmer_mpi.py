"""Bounded build of the same upstream Elmer with native MPI enabled.

This stage runs no PDE case and never alters active serial containers.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import time
import traceback
from native_closed_cavity import SOCKET,save,digest
from titan_resources import reservation
IMAGE='sha256:49e9458cc3b1ea3d7e7383c32056af59b0f718e74b0f30adbe3e1bccc0e7b059'
SOURCE=Path('/home/zhouzhiyu/code/docker/qbank/maintenance/solver-images/local/builds/elmer/20261017T183532.079713+0000/context/source.tar.gz')
SOURCE_SHA='1451e82f05b9661d82e1ebbf6e90ac373fc1b19482eef3889334a6df5ff0144a'

def main(repair_optional_mumps=False):
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);ap.add_argument('--workers',type=int,default=1);a=ap.parse_args();r=a.root
    assert digest(SOURCE)==SOURCE_SHA
    j=r/'maintenance/elmer-mpi-native-stage';image=IMAGE;repair_receipt=None
    if repair_optional_mumps:
        prior=json.loads((j/'stage.json').read_text());assert prior['status']=='stage_needs_attention' and 'ParMetis library not found' in (j/'build.log').read_text()
        actual=json.loads(subprocess.check_output(['docker','--host',SOCKET,'inspect',prior['container']],text=True))[0]
        assert not actual['State']['Running'] and actual['State']['Pid']==0
        assert any(m['Source']==str(j) and m['Destination']=='/work' for m in actual['Mounts'])
        archive=j/'attempts/optional-mumps';assert not archive.exists();archive.mkdir(parents=True)
        for filename in ['stage.json','build.log','build.sh']:shutil.copy2(j/filename,archive/filename)
        image=subprocess.check_output(['docker','--host',SOCKET,'commit',actual['Id'],'caeoj/elmer-ch02-mpi-deps:a19504a-20261021'],text=True).strip()
        repair_receipt={'reason':'Optional MUMPS discovery requires missing ParMETIS; use native MPI+Hypre iterative backend instead. No PDE/source modification.','previous_state':actual['State'],'mounts':actual['Mounts'],'dependency_image':image};save(archive/'repair.json',repair_receipt)
    else:
        assert not j.exists(),'Inspect prior build; no automatic repeat';j.mkdir();shutil.copy2(SOURCE,j/'source.tar.gz')
        source_mesh=r/'cases/ch02-2-2-4-02-natural_convection/native/mesh'
        (j/'partition-probe/mesh').mkdir(parents=True)
        for filename in ['mesh.header','mesh.nodes','mesh.elements','mesh.boundary']:shutil.copy2(source_mesh/filename,j/'partition-probe/mesh'/filename)
    shell='''set -e
export DEBIAN_FRONTEND=noninteractive OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
apt-get update
apt-get install -y --no-install-recommends libopenmpi-dev openmpi-bin libmetis-dev libmumps-dev libhypre-dev
dpkg-query -W > /work/packages.tsv
mkdir /work/source
tar xf /work/source.tar.gz -C /work/source --strip-components=1
cmake -S /work/source -B /work/build -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/opt/elmer-mpi -DWITH_MPI=TRUE -DWITH_OpenMP=FALSE -DWITH_ELMERGUI=FALSE -DWITH_ELMERPOST=FALSE -DWITH_Mumps=TRUE -DWITH_Hypre=TRUE -DWITH_Trilinos=FALSE -DWITH_LUA=FALSE -DWITH_NETCDF=FALSE -DWITH_ElmerIce=FALSE
cmake --build /work/build -j8
cmake --install /work/build
test -x /opt/elmer-mpi/bin/ElmerSolver_mpi
export OMPI_ALLOW_RUN_AS_ROOT=1 OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1
mpirun -np 4 sh -c 'echo rank=$OMPI_COMM_WORLD_RANK' > /work/mpi-launch.txt
cd /work/partition-probe
/opt/elmer-mpi/bin/ElmerGrid 2 2 mesh -metis 4 > /work/partition.log 2>&1
ldd /opt/elmer-mpi/bin/ElmerSolver_mpi > /work/mpi-libraries.txt
'''
    if repair_optional_mumps:shell='set -e\nexport OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1\n'+shell[shell.index('cmake -S'):].replace('-DWITH_Mumps=TRUE','-DWITH_Mumps=FALSE')
    (j/'build.sh').write_text(shell);name='ch02-elmer-mpi-build-'+str(time.time_ns())[-9:]
    cmd=['docker','--host',SOCKET,'run','--name',name,'--network','none' if repair_optional_mumps else 'bridge','--cpus','8','--memory','8g','-v',f'{j}:/work',image,'bash','/work/build.sh']
    rec={'status':'queued','container':name,'source_sha256':SOURCE_SHA,'source_commit':'a19504ac53ec222e3355e182b08f2ff280c2203a','base_image':image,'command':cmd,'script_sha256':digest(Path(__file__)),'start_unix':time.time(),'repair':repair_receipt,'scope':'Same native source, native MPI/Hypre configuration and four-rank launcher/mesh-partition preflight only. No PDE, reference verification or active task restart.'};save(j/'stage.json',rec)
    try:
        with reservation(r,name,cpu=8,memory_limit_bytes=8*1024**3):
            rec['status']='running';save(j/'stage.json',rec)
            with (j/'build.log').open('w') as log:
                try:cp=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=7200)
                except subprocess.TimeoutExpired:
                    subprocess.run(['docker','--host',SOCKET,'stop','--time','10',name],stdout=log,stderr=subprocess.STDOUT,timeout=30);raise
            assert cp.returncode==0,f'native MPI build/preflight exit{cp.returncode}'
            assert len((j/'mpi-launch.txt').read_text().splitlines())==4
            tag='caeoj/elmer-ch02-mpi:a19504a-20261021'
            image=subprocess.check_output(['docker','--host',SOCKET,'commit',name,tag],text=True).strip()
            rec.update(status='native_mpi_ready_pending_parallel_case_adapter',image=image,tag=tag,build_script_sha256=digest(j/'build.sh'),mpi_launch=(j/'mpi-launch.txt').read_text(),next='Configure one justified fresh/repair case with native mesh partition, parallel linear solver and partition-aware output assembly; no duplicate active solve or automatic retry.')
    except Exception as ex:rec.update(status='stage_needs_attention',error=repr(ex),traceback=traceback.format_exc())
    rec['ended_unix']=time.time();save(j/'stage.json',rec)
if __name__=='__main__':main()
