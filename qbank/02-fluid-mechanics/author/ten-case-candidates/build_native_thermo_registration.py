"""Register a combination of existing OpenCFD thermophysical templates.

No transport/EOS/thermo equation or solver is implemented or changed here.
logPolynomial exactly represents the specified power laws in ln(T).
"""
import argparse
import json
import os
import subprocess
import time
from pathlib import Path
from native_closed_cavity import IMAGE, SOCKET, put, save, digest
from titan_resources import reservation

SOURCE='''// Runtime registration only. All physical implementations are stock v2512.
#include "makeThermo.H"
#include "psiThermo.H"
#include "hePsiThermo.H"
#include "pureMixture.H"
#include "specie.H"
#include "thermo.H"
#include "perfectGas.H"
#include "hConstThermo.H"
#include "sensibleInternalEnergy.H"
#include "logPolynomialTransport.H"
namespace Foam {
makeThermos
(
    psiThermo,
    hePsiThermo,
    pureMixture,
    logPolynomialTransport,
    sensibleInternalEnergy,
    hConstThermo,
    perfectGas,
    specie
);
}
'''


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--resume-build',action='store_true');args=ap.parse_args();work=args.root/'maintenance/native-thermo-registration';assert not work.exists() or args.resume_build
    if work.exists():assert '\n'.join(l for l in (work/'registration.C').read_text().splitlines() if not l.startswith('#include'))=='\n'.join(l for l in SOURCE.splitlines() if not l.startswith('#include'))
    work.mkdir(exist_ok=args.resume_build);put(work/'registration.C',SOURCE);put(work/'Make/files','registration.C\nLIB = /work/libcaeojNativeThermo\n');put(work/'Make/options','EXE_INC = -I$(LIB_SRC)/thermophysicalModels/basic/lnInclude -I$(LIB_SRC)/transportModels/compressible/lnInclude -I$(LIB_SRC)/thermophysicalModels/specie/lnInclude -I$(LIB_SRC)/thermophysicalModels/thermophysicalProperties/lnInclude -I$(LIB_SRC)/finiteVolume/lnInclude -I$(LIB_SRC)/meshTools/lnInclude\nLIB_LIBS = -lfluidThermophysicalModels -lcompressibleTransportModels -lspecie -lthermophysicalProperties -lfiniteVolume -lmeshTools\n');state={'stage':'queued','image':IMAGE,'physics_changes':False};save(work/'status.json',state);name='ch02-native-thermo-build-'+str(time.time_ns())[-9:]
    with reservation(args.root,name):
        cmd=['docker','--host',SOCKET,'run','--rm','--name',name,'--network','none','--cpus','1','--memory','768m','--user',f'{os.getuid()}:{os.getgid()}','-e','OMP_NUM_THREADS=1','-v',f'{work.resolve()}:/work',IMAGE,'bash','-c','source /usr/lib/openfoam/openfoam2512/etc/bashrc && cd /work && wmake libso'];save(work/'build.json',{'image':IMAGE,'command':cmd,'registration_sha256':digest(work/'registration.C'),'started_unix':time.time(),'physics_changes':False,'implementation':'stock logPolynomialTransport + hConstThermo + perfectGas, registered by stock makeThermos macro'});state['stage']='building';save(work/'status.json',state)
        with (work/'build.log').open('w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
        binary=work/'libcaeojNativeThermo.so';assert binary.is_file();state.update(stage='built',library=str(binary),library_sha256=digest(binary),finished_unix=time.time());save(work/'status.json',state);print(json.dumps(state))


if __name__=='__main__':main()
