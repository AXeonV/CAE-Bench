"""Freeze actual environment evidence and complete the RC6 integrity manifest."""
import hashlib,json,shutil
from pathlib import Path
from caeoj_tools.release import verify
ROOT=Path('D:/Code/CAE-Bench-OJ');WORK=ROOT/'runs/releases/rc6-authoring'
RELEASE=ROOT/'runs/releases/caeoj-qbank-20261024-rc6'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def record(p):
    with p.open('rb') as f:return {'sha256':hashlib.file_digest(f,'sha256').hexdigest(),'size_bytes':p.stat().st_size}
validation=read(WORK/'environment-validation-final/validation.json')
assert validation['phase']=='passed' and len(validation['tasks'])==82 and validation['expected_containers']==164
assert validation['new_model_calls']==validation['score_corrections']==0
assert len({r['container_id'] for t in validation['tasks'] for r in t['roles']})==164
assert all(len(t['roles'])==2 and all(r['network']=='none' and r['fresh_container'] and r['report']['pip_check'] for r in t['roles']) for t in validation['tasks'])
shutil.copyfile(WORK/'environment-validation-final/validation.json',RELEASE/'environment/validation.json')
shutil.copyfile(WORK/'rc5-rc6-comparison.json',RELEASE/'environment/rc5-rc6-comparison.json')
shutil.copyfile(WORK/'restored-requirements.json',RELEASE/'environment/restored-requirements.json')
catalog=read(RELEASE/'catalog.json')
catalog['capabilities'].update(environment_recipe_included=True,prebuilt_container_image_included=False,
    environment_dependencies_validated_tasks=82,environment_dependencies_validation_containers=164,
    environment_initial_build_requires_network=True,historical_scores_corrected=False)
(RELEASE/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
readme=(RELEASE/'README.md').read_text(encoding='utf-8')
intro='''## RC6 环境修正与安装

本版补回RC5遗漏的71份题内环境requirements，并提供固定依赖与完整Docker构建配方。82题的全部既有文件（题面、DATA、正式输入、参考、评分、资源、随机格式样例）及公开包均保持RC5字节；仅增加环境和发行使用材料。详见[环境说明](environment/README.md)及[逐题对照](environment/rc5-rc6-comparison.json)。不更正历史成绩。

```sh
python release.py verify
python environment/build_runtime.py
python environment/check_tasks.py --jobs 2 --output ../rc6-environment-checks
```

首次构建需要网络；数据已完整随包提供，不需要重新从HF下载。环境配方提供Linux AMD64科学计算库和编译工具链，未分发预建镜像二进制；构建完成后公开SDK安装和环境检查使用断网容器。不能仅用`pip install .`安装协议SDK就认为题面承诺的全部科学环境已齐备。

实际完成82题、164个互不复用容器的离线安装、pip check、严格题目绑定和环境功能检查，见[验证记录](environment/validation.json)。此处不执行模型、不更正旧成绩、不认证参考数值精度或正式资源达标。RC5保留追溯；本版仍为预发布RC。

'''
first,remaining=readme.split('\n',1)
(RELEASE/'README.md').write_text(first+'\n\n'+intro+remaining.lstrip('\n'),encoding='utf-8')
checks={p.relative_to(RELEASE).as_posix():record(p) for p in sorted(RELEASE.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.json'}
(RELEASE/'SHA256SUMS.json').write_text(json.dumps({'schema_version':1,'files':checks},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
report=verify(RELEASE)
(WORK/'final-release-verification.json').write_text(json.dumps({'status':'passed',**report,'tasks':82,'formal_cases':647,'format_samples':96,'validated_containers':164,'no_score_correction':True},indent=2),encoding='utf-8')
print('RC6 final integrity check passed',report,flush=True)
