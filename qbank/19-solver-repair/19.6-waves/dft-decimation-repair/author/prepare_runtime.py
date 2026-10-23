"""Build genuine out-of-tree Meep behind the common trusted CMake interface."""
import argparse,json,shutil,subprocess
from pathlib import Path
from prepare_source import TASK,REPLACEMENTS,prepare,BASE
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',required=True,type=Path);p.add_argument('--proxy');p.add_argument('--docker',default='docker');p.add_argument('--wheelhouse',required=True,type=Path);p.add_argument('--build',action='store_true');a=p.parse_args();work=prepare(a.work,a.proxy);context=work/'runtime-context';context.mkdir(exist_ok=True)
 for src,dest in [(TASK/'author/runtime.Dockerfile',context/'Dockerfile'),(work/'source.tar.gz',context/'source.tar.gz'),(TASK/'public/driver.cpp',context/'driver.cpp'),(TASK/'public/CMakeLists.txt',context/'CMakeLists.txt')]:shutil.copyfile(src,dest)
 shutil.copytree(a.wheelhouse,context/'offline-wheels',dirs_exist_ok=True)
 if a.build:subprocess.run([a.docker,'build','-t','caeoj-meep2408-runtime:base',str(context)],check=True)
 code="from pathlib import Path;import json;p=Path('/opt/meep-repair-build');files=[str(q) for q in (p/'upstream/src').rglob('*') if q.is_file() and not q.is_symlink() and q.suffix in ('.o','.lo','.la')];files += ['/opt/meep-repair-build/upstream/src/.libs/libmeep.so.30.0.0','/opt/meep-repair-build/CMakeFiles/dft_driver.dir/opt/meep-driver/driver.cpp.o','/opt/meep-repair-build/bin/dft-driver'];assert all(Path(x).is_file() and not Path(x).is_symlink() for x in files);print(json.dumps(sorted(set(files))))"
 rebuild=json.loads(subprocess.check_output([a.docker,'run','--rm','--network','none','caeoj-meep2408-runtime:base','python','-c',code],text=True))
 probe="import subprocess,json,gmsh,numpy,h5py; assert hasattr(gmsh.lib,'gmshInitialize'); r=json.loads(subprocess.check_output(['/opt/meep-repair-build/bin/dft-driver'],input='12 10 1 .3 .3 .01 3 3 0 0 -4 4 1 1 4.05 1 .3',text=True)); assert r['stride']==1 and len(r['spectrum'])==1; print('actual baseline Meep ready')"
 config={'version':1,'base_image':'caeoj-meep2408-runtime:base','replacements':[{'submission':n,'target':'/opt/meep-upstream/meep-'+BASE+'/src/'+n} for n in REPLACEMENTS],'build_directory':'/opt/meep-repair-build','build_target':'repair_sources','rebuild_files':rebuild,'build_timeout_seconds':300,'baseline_timeout_seconds':300,'max_source_bytes':1048576,'runner':'/app/qbank/19-solver-repair/19.6-waves/dft-decimation-repair/public/run_case.py','baseline_probe':['/usr/local/bin/python','-c',probe]}
 (TASK/'harbor/source-repair.json').write_text(json.dumps(config,indent=2)+'\n');(TASK/'author/data-evidence/rebuild-files.json').write_text(json.dumps(rebuild,indent=2)+'\n')
 ref=work/'production-reference-context';ref.mkdir(exist_ok=True)
 for n in REPLACEMENTS:shutil.copyfile(TASK/'author/generated'/n,ref/n)
 dockerfile='FROM caeoj-meep2408-runtime:base\n'+''.join('COPY '+n+' /opt/meep-upstream/meep-'+BASE+'/src/'+n+'\n' for n in REPLACEMENTS)+'RUN rm -f '+' '.join(rebuild)+' && cmake --build /opt/meep-repair-build --target repair_sources --parallel 4\n';(ref/'Dockerfile').write_bytes(dockerfile.encode())
 if a.build:subprocess.run([a.docker,'build','-t','caeoj-meep2408-reference:production',str(ref)],check=True)
