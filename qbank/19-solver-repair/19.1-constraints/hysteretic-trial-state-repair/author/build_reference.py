"""Build the exact upstream two-file reference over the genuine baseline runtime."""
import argparse,shutil,subprocess
from pathlib import Path
TASK=Path(__file__).resolve().parents[1]
DOCKER='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--image',default='caeoj-opensees1817-reference:fixed');a=p.parse_args()
 a.work.mkdir(parents=True,exist_ok=False)
 for n in ['HystereticMaterial','HystereticSMMaterial']:shutil.copyfile(TASK/'author/generated'/(n+'.cpp'),a.work/(n+'.cpp'))
 (a.work/'Dockerfile').write_text('FROM caeoj-opensees1817-runtime:base\nCOPY HystereticMaterial.cpp HystereticSMMaterial.cpp /opt/opensees-source/SRC/material/uniaxial/\nRUN touch /opt/opensees-source/SRC/material/uniaxial/Hysteretic*.cpp && cmake --build /opt/material-build -j4 && chmod -R go-w /opt/opensees-source /opt/material-build\n',encoding='utf-8',newline='\n')
 subprocess.run([DOCKER,'build','--pull=false','--progress','plain','-t',a.image,str(a.work)],check=True)
if __name__=='__main__':main()
