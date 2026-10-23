from pathlib import Path
import hashlib,json,subprocess,sys
root=Path('/opt/meep-upstream/meep-85e107771808a4b89e4b4514007512f48c1c121b')
expected=json.loads(Path('/audit/baseline-tree.json').read_text())
actual={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
changed=[n for n in expected if actual.get(n)!=expected[n]]
assert changed==([] if sys.argv[1]=='base' else ['src/step_db.cpp']),changed
print(json.dumps({'mode':sys.argv[1],'original_file_count':len(expected),'actual_file_count':len(actual),'changed_original_files':changed,'changed_digests':{n:actual[n] for n in changed},'extra_files':sorted(set(actual)-set(expected)),'driver_sha256':hashlib.sha256(Path('/opt/meep-driver/driver.cpp').read_bytes()).hexdigest(),'cmake_sha256':hashlib.sha256(Path('/opt/meep-repair-cmake/CMakeLists.txt').read_bytes()).hexdigest(),'ldd':subprocess.check_output(['ldd','/opt/meep-repair-build/bin/cylindrical-driver'],text=True)},indent=2))
