"""Prepare an offline source/dependency Docker context and minimal reference context."""
import argparse,hashlib,json,shutil
from pathlib import Path
Q=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--sdk-wheels',type=Path,required=True);a=p.parse_args()
source=Q/'public/cantera-source.tar.gz';expected=json.loads((Q/'author/data-evidence/source.json').read_text())['source_sha256'];assert hashlib.sha256(source.read_bytes()).hexdigest()==expected
context=a.output/'context';context.mkdir(parents=True,exist_ok=True)
for name in ['cantera-source.tar.gz','driver.cpp','plasma.yaml','CMakeLists.txt']:shutil.copyfile(Q/'public'/name,context/name)
shutil.copyfile(Q/'author/runtime.Dockerfile',context/'Dockerfile');shutil.copytree(a.sdk_wheels,context/'wheels',dirs_exist_ok=True)
reference=a.output/'reference-context';reference.mkdir(parents=True,exist_ok=True);shutil.copyfile(Q/'author/generated/PlasmaPhase.h',reference/'PlasmaPhase.h')
(reference/'Dockerfile').write_text('FROM caeoj-cantera1872-core:offline-sdk\nCOPY PlasmaPhase.h /opt/cantera-source/include/cantera/thermo/PlasmaPhase.h\nRUN cmake --build /opt/cantera-source/build --target repair_sources\n')
print(context,reference)
