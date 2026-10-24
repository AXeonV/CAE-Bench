"""Prepare exact RC6 release attachments after the reviewed source commit."""
import ast,hashlib,json,shutil,subprocess
from pathlib import Path
ROOT=Path('D:/Code/CAE-Bench-OJ');WORK=ROOT/'runs/github-release-rc6';ASSETS=WORK/'assets'
ASSETS.mkdir(parents=True,exist_ok=True)
delivery=json.loads((ROOT/'runs/releases/rc6-authoring/delivery.json').read_text(encoding='utf-8'))
commit=subprocess.check_output(['D:/Program Files/Git/cmd/git.exe','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
assert subprocess.check_output(['D:/Program Files/Git/cmd/git.exe','diff','--name-only'],cwd=ROOT,text=True).strip()==''
old=ROOT/'runs/github-release-rc5'
shutil.copyfile(old/'assets/restore_release.py',ASSETS/'restore_release.py')
(ASSETS/'DOWNLOAD-README.md').write_text(f'''# CAE-OJ-Bench / qbank RC6 — 完整环境修正版

本版包含82题、647个正式case、96个随机格式样例，完整输入、参考、评分、许可、公开包、安装步骤及环境构建配方。修复RC5漏带71份题内`harbor/requirements.txt`的问题，加入数值题共享科学环境和判题前环境检查。

**题面、DATA、全部旧case输入／参考／评分／资源、样例及82个公开ZIP均保持RC5字节不变；不更正任何历史成绩。** RC5及其独立小补丁保留，已下载RC5的团队可以使用小补丁，无需重新下载本完整包。

## 下载与恢复

1. 下载三个 `caeoj-qbank-20261024-rc6.zip.part001/002/003`、`DOWNLOAD-MANIFEST.json` 和 `restore_release.py` 到同一目录。
2. 执行 `python restore_release.py`，逐片及整包SHA256核验后恢复完整ZIP。单个分片不可独立解压。
3. 解压后进入 `caeoj-qbank-20261024-rc6`，运行 `python release.py verify`；题目清单用 `python release.py list`。
4. 按 `environment/README.md` 执行 `python environment/build_runtime.py`。**首次构建需联网**下载固定Python依赖与系统包，不分发预建第三方镜像二进制；构建后的公开SDK安装和检查使用无网络容器。
5. 环境自检：`python environment/check_tasks.py --jobs 2 --output ../rc6-environment-checks`。

82题均已实际验证全新考生容器与独立断网verifier容器，共164个不同CID；实际离线安装、pip check、严格题目绑定、科学库导入和C++/OpenMP/MPI/HDF5工具链通过。删除SciPy的负例在judge执行前停止，未生成分数。证据在完整包 `environment/validation.json`，源码审阅在 `qbank/design/reviews/rc6-environment-2026-10-24/`。

维护方完整题目使用 `python release.py extract TASK EMPTY_DIRECTORY`；考生仅获得对应public ZIP，不能提供隐藏参考。模型凭据和适配器沿用团队现有配置，不随包分发。本版仍为预发布RC，尚未完成全部参考精度和异机资源资格验收。

## 完整性与源码

原始完整ZIP：{delivery['bytes']} bytes，SHA256 `{delivery['sha256']}`。

源码附件对应提交 `{commit}`，包含全部已跟踪源文件、修复与审阅证据；GitHub自动生成的Source code不含大数据附件。三个分片合并后的内容与本地完整RC6完全一致。GitHub单附件限制小于2GiB，所以使用无损字节分片。
''',encoding='utf-8')
source=(old/'prepare.py').read_text(encoding='utf-8').replace('github-release-rc5','github-release-rc6').replace('caeoj-qbank-20261024-rc5','caeoj-qbank-20261024-rc6').replace('runs/continuous-scoring/delivery.json','runs/releases/rc6-authoring/delivery.json').replace('1bfbc4574f5e83cdce9eb68a412025ab2ed63f67',commit)
(WORK/'prepare.py').write_text(source,encoding='utf-8')
source=(old/'upload.py').read_text(encoding='utf-8').replace('github-release-rc5','github-release-rc6').replace('caeoj-qbank-20261024-rc5','caeoj-qbank-20261024-rc6').replace('RC5 — complete offline release','RC6 — complete environment repair').replace('1bfbc4574f5e83cdce9eb68a412025ab2ed63f67',commit)
source=source.replace("tmp.replace(STATUS)","\n    for attempt in range(100):\n        try:tmp.replace(STATUS);break\n        except PermissionError:\n            if attempt==99:raise\n            time.sleep(.05)")
source=source.replace("import requests\n","import requests\nimport atexit\n")
source=source.replace("state={'pid':", "LOCK=WORK/'upload.lock'\nwith LOCK.open('x') as handle:json.dump({'pid':os.getpid()},handle)\natexit.register(lambda:LOCK.unlink(missing_ok=True))\nstate={'pid':")
ast.parse(source);(WORK/'upload.py').write_text(source,encoding='utf-8')
source=(old/'verify_remote.py').read_text(encoding='utf-8').replace('github-release-rc5','github-release-rc6').replace('caeoj-qbank-20261024-rc5','caeoj-qbank-20261024-rc6').replace('1bfbc4574f5e83cdce9eb68a412025ab2ed63f67',commit)
ast.parse(source);(WORK/'verify_remote.py').write_text(source,encoding='utf-8')
(WORK/'source-commit.json').write_text(json.dumps({'commit':commit,'tag':'caeoj-qbank-20261024-rc6'},indent=2),encoding='utf-8')
print('RC6 GitHub scripts prepared for reviewed commit '+commit,flush=True)
