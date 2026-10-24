# RC5 环境补丁 v1：无需重新下载题库

适用发行版：`caeoj-qbank-20261024-rc5`，正式数据、参考、题面和评分规则均不修改。原来三个大分片可以继续下载和使用；只需额外下载这个小补丁。

已确认问题：部分题面承诺提供 SciPy，但原运行装配没有保证独立判题环境安装它，可能出现 `ModuleNotFoundError: No module named 'scipy'`。这种环境失败不能作为有效模型零分。仅在宿主机或考生容器执行 pip install 不能修复独立判题容器。

## 先判断自己属于哪种使用方式

- 已有生成的 Harbor task：执行下面的 **A**，同时修补考生和独立判题环境。
- 直接使用 RC5 解压出的单题项目，自己管理容器或环境：执行 **B**。
- 只有完整题库下载／解压目录：先按原 `release.py extract` 提取题目，再按 A 或 B 操作。不要把 `apply.py --harbor-task` 指向整个发行目录或单题 SDK 项目。

补丁目标是题面规定的 **Linux AMD64** 数值运行环境，原 Harbor Docker 使用 Python 3.14。补丁固定 `scipy==1.18.1`；该版本要求 Python≥3.12。使用旧 Python 3.11 的团队请新建 Python 3.14 容器／环境，不要忽略安装失败。Windows／macOS 可管理 Docker，但不是本补丁认证的原生求解环境。

## A. 修补已经生成的 Harbor task

停止受影响任务的启动队列，等待或停止自己的当前 trial；保留原日志与冻结提交。以下路径请替换为实际路径，补丁可放在任意目录。

```bash
python /path/rc5-environment-v1/apply.py --harbor-task /path/generated-task --dry-run
python /path/rc5-environment-v1/apply.py --harbor-task /path/generated-task
```

脚本核对两侧 `agent.zip` 都匹配原 RC5 公共包、题目身份相同且 verifier 声明无网络，然后只改生成任务的环境文件：

- 两侧 `requirements.txt` 补充固定 SciPy 版本。
- 两侧 Dockerfile 添加功能自检，构建失败就不会进入求解或判题。
- `tests/test.sh` 在可信 judge 之前再次自检；失败退出，不进入逐例判分、不生成新的 reward。
- 原文件备份及修改前后摘要保存在任务内 `.caeoj-rc5-environment-v1/receipt.json` 和 `before/`；再次应用只核验，不重复修改。中途失败的备份目录须先检查，脚本不会覆盖。

**需要重建两侧镜像；正在运行的旧容器不会自动修复。** 可先独立构建验证，无需调用模型：

```bash
docker build -t rc5-task-agent-patched /path/generated-task/environment
docker build -t rc5-task-verifier-patched /path/generated-task/tests
docker run --rm --network none rc5-task-agent-patched python /opt/caeoj-rc5-patch/gate.py
docker run --rm --network none rc5-task-verifier-patched python /opt/caeoj-rc5-patch/gate.py
```

两个检查都应输出含 `"status": "passed"` 的 JSON。之后用**新的 job 名称**按原 Harbor 命令启动，保持原 CPU、内存、时限和无网络判题设置。Harbor 0.24 按构建上下文摘要区分镜像，文件改变后会构建新镜像；自建调度器必须显式重建，不能复用旧容器。

若既有 requirements 与固定 SciPy 版本冲突，脚本或 pip 会明确失败，不能忽略失败继续运行。保留原约束并由维护者确认兼容版本／建立独立环境，不要为使安装成功而静默删去题目依赖。

不要把 `tests/`、隐藏 case 或参考复制进 `environment/`。本补丁不会这样做。若以后重新运行旧源码里的 `prepare_harbor.py` 生成任务，需要对新生成的任务再次应用本补丁；永久装配修复由 RC6 提供。

## B. 自己管理解题／判题环境

在**解题和独立判题各自使用的 Python 环境中**，安装原单题项目以及补丁依赖。解题侧安装对应公开包；判题侧使用维护者提取的项目。不能把私有参考给考生。

```bash
python -m pip install /path/task-project -r /path/rc5-environment-v1/runtime-requirements.txt
python /path/rc5-environment-v1/gate.py
```

自检还要求题面承诺的系统依赖：bash、git、curl、g++／OpenMP、Open MPI、HDF5 开发工具、Gmsh 所需动态库、util-linux。Debian 系镜像可在**构建阶段**安装：

```bash
apt-get update
apt-get install -y bash git curl ca-certificates g++ openmpi-bin libopenmpi-dev libhdf5-dev hdf5-tools util-linux libglu1-mesa libgl1 libxrender1 libxcursor1 libxfixes3 libxft2 libfontconfig1 libxinerama1 libgomp1
```

把检查接入实际启动流程，避免“装过一次就默认永远正确”：

```bash
python /path/rc5-environment-v1/gate.py -- python /path/your-benchmark-runner.py
```

独立判题环境应在禁网状态运行同一 gate，再进入可信 judge。必须对解题、判题两侧分别检查。gate 失败退出 2，不执行后面的命令；这是基础设施错误，不是考生得分 0。检查覆盖 Python 模块、SciPy 稀疏求解、HDF5 Python／原生读写、Gmsh API、C++ OpenMP 双线程和 MPI 双 rank 归约。`--` 后的命令只是示例，替换为团队现有入口。

## 已经产生的成绩和验证边界

- 保留原 trial、日志、提交及无效成绩，注明环境缺陷。停止将这种导入失败计为模型能力零分。
- 可在修复后的环境对**原封不动的冻结提交**重判，无须重新调用模型；重判记录必须链接原 trial 和环境补丁版本，不能覆盖原始证据。
- 若解题侧当时也缺少承诺依赖，原求解过程存在环境偏差；重判不能消除这种偏差。正式比较应另列，新增模型求解须另行授权。
- 本补丁不认证参考精度、全部题目的数值正确性、所有第三方求解软件或所有机器的资源预算。它阻止已覆盖的环境缺陷再次静默变成考生零分；题面新增依赖时仍须扩展并实测环境自检。

数据包、公共 ZIP 和原发行校验文件保持原样，因此原 RC5 `release.py verify` 仍可使用。补丁自己的文件摘要见 `PATCH-MANIFEST.json`，下载 ZIP 的 SHA256 另附于 Release。
