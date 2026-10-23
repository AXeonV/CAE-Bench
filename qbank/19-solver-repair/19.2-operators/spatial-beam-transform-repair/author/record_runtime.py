"""Record actual immutable image IDs, compiler and solver/driver hashes."""
import hashlib,json,subprocess
from pathlib import Path
TASK=Path(__file__).resolve().parents[1];DOCKER='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
CODE=r'''
import hashlib,json,pathlib,subprocess
paths=['/opt/kratos-source/applications/StructuralMechanicsApplication/custom_elements/beam_elements/timoshenko_beam_element_3D2N.cpp','/opt/beam-build/libbeam_repair.so','/opt/beam-build/beam_driver','/opt/kratos-build/kratos/libKratosCore.so','/opt/beam-driver/driver.cpp']
print(json.dumps({'files_sha256':{p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for p in paths},'compiler':subprocess.check_output(['clang++','--version'],text=True),'driver_linked_libraries':subprocess.check_output(['ldd','/opt/beam-build/beam_driver'],text=True)}))
'''
if __name__=='__main__':
    records={}
    for mode,image in [('baseline','caeoj-kratos14657-runtime:base'),('upstream','caeoj-kratos14657-upstream:fixed'),('author_supplemented','caeoj-kratos14657-reference:fixed')]:
        iid=json.loads(subprocess.check_output([DOCKER,'image','inspect',image]))[0]['Id'];r=json.loads(subprocess.check_output([DOCKER,'run','--rm','--network','none',iid,'python','-c',CODE]));r['image_id']=iid;r['local_tag']=image;records[mode]=r
    record={'source_evidence_sha256':hashlib.sha256((TASK/'author/data-evidence/source.json').read_bytes()).hexdigest(),'images':records,'verifier_image_id':json.loads(subprocess.check_output([DOCKER,'image','inspect','caeoj-kratos14657-verifier:preflight']))[0]['Id']}
    (TASK/'author/data-evidence/runtime-images.json').write_text(json.dumps(record,indent=2)+'\n');print({k:v['image_id'] for k,v in records.items()})
