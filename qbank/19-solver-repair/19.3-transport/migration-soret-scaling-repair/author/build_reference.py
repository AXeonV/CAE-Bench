"""Build the exact full upstream PR872 patch over the production baseline runtime."""
import argparse,shutil,subprocess
from pathlib import Path
TASK=Path(__file__).resolve().parents[1]
DOCKER='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);p.add_argument('--image',default='caeoj-elmer870-reference:production');a=p.parse_args()
 a.work.mkdir(parents=True,exist_ok=False);shutil.copyfile(TASK/'author/generated/AdvectionDiffusion.F90',a.work/'AdvectionDiffusion.F90')
 (a.work/'Dockerfile').write_text('FROM caeoj-elmer870-runtime:base\nCOPY AdvectionDiffusion.F90 /opt/elmer-source/fem/src/modules/AdvectionDiffusion.F90\nRUN touch /opt/elmer-source/fem/src/modules/AdvectionDiffusion.F90 && rm -f /opt/elmer-build/fem/src/modules/CMakeFiles/AdvectionDiffusion.dir/AdvectionDiffusion.F90-pp.f90 /opt/elmer-build/fem/src/modules/CMakeFiles/AdvectionDiffusion.dir/AdvectionDiffusion.F90.o /opt/elmer-build/fem/src/modules/AdvectionDiffusion.so && cmake --build /opt/elmer-build --target AdvectionDiffusion -j2 && chmod -R go-w /opt/elmer-source /opt/elmer-build\n',encoding='utf-8',newline='\n')
 subprocess.run([DOCKER,'build','--pull=false','--progress','plain','-t',a.image,str(a.work)],check=True)
