"""Persist the release fix, observed checks and unchanged-content evidence."""
import hashlib,json,shutil,zipfile
from pathlib import Path
ROOT=Path('D:/Code/CAE-Bench-OJ');WORK=ROOT/'runs/releases/rc6-authoring'
RELEASE=ROOT/'runs/releases/caeoj-qbank-20261024-rc6'
EVIDENCE=ROOT/'qbank/design/reviews/rc6-environment-2026-10-24'
def load(path):return json.loads(path.read_text(encoding='utf-8'))
delivery=load(WORK/'delivery.json');assert delivery['status']=='passed'
assert load(WORK/'final-release-verification.json')['status']=='passed'
validation=load(WORK/'environment-validation-final/validation.json');assert validation['phase']=='passed' and len(validation['tasks'])==82
EVIDENCE.mkdir(exist_ok=True);(EVIDENCE/'.gitattributes').write_bytes(b'* -text -whitespace\n')
for name in ['dependency-audit.json','dependency-audit.md','implementation-review.md','implementation-review-sha256.json',
             'implementation-artifact-checks.json','independent-final-environment-review.json','rc5-rc6-comparison.json','restored-requirements.json',
             'harbor-tests.log','harbor-tests-fixed.log','release-tests.log','final-regression.log',
             'runtime-build-final.log','environment-validation-final.log','final-release-verification.json','delivery.json',
             'rc5-erratum-verification.json','negative-environment-gate.json']:
    shutil.copyfile(WORK/name,EVIDENCE/name)
shutil.copyfile(WORK/'environment-validation-final/validation.json',EVIDENCE/'environment-validation.json')
for name in ['catalog.json','SHA256SUMS.json']:shutil.copyfile(RELEASE/name,EVIDENCE/name)
scripts=EVIDENCE/'scripts';scripts.mkdir(exist_ok=True)
for name in ['build_bank.py','prepare_environment.py','run_final_validation.py','finalize.py','package.py','record.py','negative_gate.py','prepare_github.py']:
    shutil.copyfile(WORK/name,scripts/name)
with zipfile.ZipFile(EVIDENCE/'container-install-logs.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
    for path in sorted((WORK/'environment-validation-final').glob('*.log')):archive.write(path,path.name)
image=validation['image_id']
(EVIDENCE/'README.md').write_text(f'''# RC6：发行环境依赖修复

交付[完整RC6 ZIP](<{Path(delivery['archive']).as_posix()}>), {delivery['bytes']} bytes，SHA256 `{delivery['sha256']}`。使用[发行README](<{RELEASE.as_posix()}/README.md>)和[环境安装步骤](<{RELEASE.as_posix()}/environment/README.md>)。

## 变化与边界

RC5漏带71份题内harbor/requirements.txt（其中69份包含SciPy），43道第二章题明确承诺SciPy。协议SDK锁本来只拥有协议依赖，不能替代完整科学计算环境。根因和全部82题账本见[独立盘点](dependency-audit.md)。

RC6补回71份配置，加入共享数值题科学环境、安装和真实检查入口。全部旧RC5题内文件字节及82个公开ZIP均不变：题面、DATA、case/sample身份、647个正式case的输入／参考／评分、执行资源及96个随机格式样例保持原样。见[逐题对照](rc5-rc6-comparison.json)、[独立实际产物审计](implementation-artifact-checks.json)。新增requirements按工作树实际字节绑定；部分CRLF与Git对象LF摘要不同，内容已归一化核对，不能说新增文件与Git对象逐字节相同。

环境配方首次构建联网，提供固定Python依赖和基础镜像digest；未上传预建第三方镜像二进制。系统仓库包可能随构建日期变化，异机应重新构建并执行检查。数据完整离线，构建后SDK装包和检查断网。

## 实际验证

- Harbor回归32项＋12子测试，release回归28项通过／1项跳过；两项旧fixture断言闭环，早期日志保留。最终合并回归见final-regression.log。
- [最终164容器证据](environment-validation.json)：82题每题新候选容器＋独立新verifier容器，164个不同container ID，均network=none。实际离线安装每题原公开包及恢复的requirements，pip check、严格provider绑定、科学库实际导入、SciPy稀疏求解、h5py读写、Gmsh初始化、C++/OpenMP两线程、系统HDF5建文件重开和MPI双rank归约全部通过。镜像ID `{image}`。逐容器原始安装日志见container-install-logs.zip。
- [负例](negative-environment-gate.json)：人为移除SciPy后，实际判题入口在可信judge运行前中止，不生成report/reward；不涉及已有考生提交或成绩更正。
- [独立审阅](implementation-review.md)和最终文件/外层ZIP摘要校验通过。环境验证不执行考生模型，不读取隐藏参考求解，不认证参考数值精度或正式资源达标。

## 发布与既有成绩

按用户明确要求，本次不更正历史成绩、不重复模型调用。原试跑重判控制器在任何纯重判开始前已停止，原始模型trial及报告保留。由缺少承诺依赖产生的零分不应解释为模型能力成绩。

RC5已先加勘误。另一个独立任务已为RC5追加小型补丁并保留原大分片；本次不再操作或覆盖RC5 Release。已下载RC5的团队可使用其补丁，RC6供需要完整修正版的新下载。RC5与先前验证记录保留追溯。本版仍是内部预发布RC，未完成全体参考精度及异机资源资格。
''',encoding='utf-8')
checks={p.relative_to(EVIDENCE).as_posix():{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
        for p in EVIDENCE.rglob('*') if p.is_file() and p.name!='evidence-sha256.json'}
(EVIDENCE/'evidence-sha256.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('RC6 evidence recorded',flush=True)
