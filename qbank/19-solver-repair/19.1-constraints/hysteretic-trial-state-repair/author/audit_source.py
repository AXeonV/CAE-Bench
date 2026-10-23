"""Check the real compiler closure and source bytes in the fixed baseline image."""
import hashlib,json,subprocess
from pathlib import Path
TASK=Path(__file__).resolve().parents[1]
DOCKER='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
def main():
 image=json.loads(subprocess.check_output([DOCKER,'image','inspect','caeoj-opensees1817-runtime:base']))[0]['Id']
 deps=subprocess.check_output([DOCKER,'run','--rm','--network','none',image,'ninja','-C','/opt/material-build','-t','deps'],text=True)
 paths=sorted({line.strip().removeprefix('/opt/opensees-source/') for line in deps.splitlines() if line.strip().startswith('/opt/opensees-source/')})
 packed=json.loads((TASK/'author/data-evidence/source-closure.json').read_text());expected={x['file']:x['sha256'] for x in packed['files']}
 assert set(paths)==set(expected)-{'COPYRIGHT'},(set(paths)-set(expected),set(expected)-set(paths))
 code="import pathlib,hashlib,json;root=pathlib.Path('/opt/opensees-source');print(json.dumps({str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}))"
 actual=json.loads(subprocess.check_output([DOCKER,'run','--rm','--network','none',image,'python','-c',code],text=True));assert actual==expected
 record={'baseline_image_id':image,'actual_compiler_source_and_header_count':len(paths),'public_source_count_including_copyright':len(expected),'compiler_dependencies_exactly_equal_public_closure_except_copyright':True,'all_actual_image_source_hashes_match_pinned_public_archive':True,'dependencies':paths}
 (TASK/'author/data-evidence/source-closure-audit.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in record.items() if k!='dependencies'}))
if __name__=='__main__':main()
