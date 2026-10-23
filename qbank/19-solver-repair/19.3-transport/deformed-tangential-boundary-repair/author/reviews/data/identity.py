import hashlib,json,tarfile,zipfile,subprocess,importlib.util,sys
from pathlib import Path
import h5py
ROOT=Path(__file__).resolve().parents[3];WORK=ROOT/'work/repair-22/aspect-6818';TASK=ROOT/'qbank/19-solver-repair/19.3-transport/deformed-tangential-boundary-repair';OUT=Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=json.loads((TASK/'author/data-evidence/source.json').read_text());report={'hashes':{},'migration':{}}
for file,key in [('aspect-baseline.tar.gz','original_archive_sha256'),('baseline-core.cc','baseline_core_sha256'),('reference-core.cc','reference_core_sha256'),('aspect-baseline.native','baseline_binary_sha256'),('aspect-reference.native','reference_binary_sha256'),('aspect-source-closure.tar.gz','public_source_closure_sha256'),('FlowSolve.F90','independent_elmer_original_FlowSolve_sha256')]:
 value=sha(WORK/file);assert value==source[key];report['hashes'][file]=value
with tarfile.open(WORK/'aspect-baseline.tar.gz') as t:
 core=next(m for m in t.getmembers() if m.name.endswith('/source/simulator/core.cc'));assert t.extractfile(core).read()==(WORK/'baseline-core.cc').read_bytes()
 members=[m for m in t.getmembers() if m.isfile()];prefix=t.getmembers()[0].name+'/'
 original={m.name.removeprefix(prefix):hashlib.sha256(t.extractfile(m).read()).hexdigest() for m in members}
 report['original_source_files']=len(original)
# Compare every original file still in production source, omissions are intentional
# closure exclusions (tests/doc/manual), not silently counted as compared.
code="""import json,hashlib,pathlib
p=pathlib.Path('/opt/aspect');print(json.dumps({str(x.relative_to(p)):hashlib.sha256(x.read_bytes()).hexdigest() for x in p.rglob('*') if x.is_file() and not x.is_symlink()}))"""
actual=json.loads(subprocess.check_output(['docker','exec','-w','/opt/aspect','caeoj-aspect6818-prototype','python3','-c',code],text=True))
common=set(original)&set(actual);diff=[k for k in common if original[k]!=actual[k]];assert not diff,diff
report['source_comparison']={'matching_original_files':len(common),'original_absent_from_runtime':sorted(set(original)-set(actual)),'differing':diff,'runtime_additions':sorted(set(actual)-set(original))}
for filename in ['point_values.cc','helper_functions.cc']:
 path='source/'+('postprocess/' if filename=='point_values.cc' else 'simulator/')+filename
 data=subprocess.check_output(['docker','exec','-w','/opt/aspect','caeoj-aspect6818-prototype','cat','/opt/aspect/'+path]);(OUT/filename).write_bytes(data)
data=subprocess.check_output(['docker','exec','caeoj-aspect6818-elmer','cat','/opt/elmer-source/fem/src/ModelDescription.F90']);(OUT/'ModelDescription.F90').write_bytes(data)
def mod(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
old=mod('old_adapter',WORK/'run_case.py');new=mod('new_adapter',TASK/'public/run_case.py')
for c in sorted((TASK/'cases').iterdir()):
 orig=WORK/'model-migration-original'/c.name
 with h5py.File(c/'input.h5') as h:pts=h['probe_coordinates'][:]
 a=old.configuration(json.loads((orig/'problem.json').read_text()),pts,Path('/native'));b=new.configuration(json.loads((c/'problem.json').read_text()),pts,Path('/native'))
 assert a==b and sha(orig/'input.h5')==sha(c/'input.h5')
 assert sha(TASK/'reference'/c.name/'reference.h5')==sha(WORK/'formal/reference'/c.name/'reference.h5')
 report['migration'][c.name]={'native_configuration_sha256':hashlib.sha256(a.encode()).hexdigest(),'input_sha256':sha(c/'input.h5'),'reference_sha256':sha(TASK/'reference'/c.name/'reference.h5')}
zip=ROOT/'dist/deformed-tangential-boundary-repair-agent.zip'
report['zip']={'sha256':sha(zip),'members':len(zipfile.ZipFile(zip).namelist())};assert report['zip']=={'sha256':'9acb735ced6dcc52c86ffb187a5c7b3ae34e784713ba5b963f6d412e3e6b63ee','members':40}
(OUT/'identity.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k not in ('migration','source_comparison')});print('source matching',len(common),'differences',len(diff))
