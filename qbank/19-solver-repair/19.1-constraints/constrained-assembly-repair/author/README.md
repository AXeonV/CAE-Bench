# 制作、验证与运行

本题来源为 [Chrono #846](https://github.com/projectchrono/chrono/issues/846) 与已合并 [PR #852](https://github.com/projectchrono/chrono/pull/852)。固定缺陷基线为 `c6acd4e5a199f56052ba74b8e9d735a2157ba613`，上游修复为 `23c679076915d893ccd949fd0f8a2af0fc906982`。完整取证及完成状态见[实施记录](../../../../design/reviews/chrono-846-repair-implementation.md)。

## 源码及真实构建

`fetch_source.py --output <缓存目录>` 下载两个固定源码归档并记录 SHA-256。`build_runtime.py --source <缓存目录>/base --work <构建目录>` 创建包含原始缺陷核心及可信驱动的镜像。运行时仅依赖 src、cmake、根构建文件和模板工程；几何资产不参与本题。`pack_source.py --source <构建目录>/context/source` 打包相同的公开源码闭包，并生成 `public-materials.json` 的严格资产白名单。

可信驱动的唯一源文件位于 `public/driver.cpp`，通过独立 CMake 工程链接真实 Chrono 核心；它不计算参考力学解。固定上游修复文件由下载目录复制到忽略的 `author/generated/ChAssemblyAnalysis.cpp`，用于 Oracle 和私有参考镜像。公开镜像及公开 ZIP 不得包含这个修复文件。

修复参考镜像从缺陷核心镜像派生，仅替换上游修复的 `ChAssemblyAnalysis.cpp` 并重新编译核心。上游同一 PR 对 `ChSystem.cpp` 的步长恢复修改不在本题要求内；本题无时间推进，该差别不影响观测。不要把本镜像标成整个仓库完整修复提交的构建。

## 输入、参考与独立核对

1. `generate.py --output <空数据目录>` 产生 20 个自包含输入和独立核对量；它不产生判题 reference。
2. `replay.py --dataset <数据目录> --image <修复参考镜像> --mode reference` 实际在 4 CPU、8 GiB、无网络、UID 1000 容器中调用真实 Chrono，保存原始驱动输入/输出及日志；通过独立核对后写 reference.h5 和逐例 grading.json。
3. 同一脚本 `--image <缺陷基线镜像> --mode defect` 重放原始缺陷版，记录检出结果。不能把编译成功代替这一步。
4. 原始驱动进程输出留在工作缓存，摘要、实际生产者、输入与输出绑定见 `data-evidence/`。两组公开样例与计分 case 明确共享身份，必须在清单和报告标出。

对于边 e=(a,b)，令 `r=q_b-q_a`、`u=r/|r|`。解析微分给出约束 `u·(a_b-a_a)=-|v_b-v_a|²/L`，这里相对速度已与连线垂直。对活动体平移自由度建立单位方向雅可比 J、质量对角阵 M、外力 F；独立核对采用：

`(J M^-1 J^T) μ = -s - J M^-1 F`，`a=M^-1(F+J^T μ)`，`reaction_e=μ_e u_e`。

固定体的自由度从求解中排除，其加速度为零；第二端点为固定体时仍保留该约束的作用力方向。重力已加入 F。此解析约束微分与上游实现对约束函数作有限差分是不同的数学求值路径；它用于全量核对真实求解器输出，不能将这些 Python 核对量说成上游求解器生产的参考。单摆的闭式结果及反力方向还与固定上游测试源码交叉核对。位置回归采用单固定点的径向投影，速度回归采用质量加权投影。

当前实测参考 20/20 通过独立核对；原始缺陷版为 7/20。各项误差及评分容差占比见 `reference-replay.json`，不外推为全部可能输入的误差证明。多体链、分支、闭环、自由系统、固定第二端点及加载网络是作者控制的改编工况，不冒称为原 issue 的原始输入。原始单摆情境与静止/运动对照保留，参数及尺度变体服务于缺陷检出。

## 数据池与评测

按仓库 `caeoj-maint data pack/assemble/verify` 管理数据，稳定身份 `caeoj-190101`。本地制池后已上传任务专用 HF 分支，并从固定提交通过官方 HubStore 重新装配90个文件、严格核验全部20例及2个公开样例。提交及操作证据以 `data-evidence/hf-upload.json` 为准。默认传输的上传后重取曾等待，独立 HTTP 传输核验完成后退役该冗余进程；未将其空日志当作完成依据。

通过现有 `src/utils/publish_dist.py` 和 `src/utils/prepare_harbor.py` 装配。`harbor/source-repair.json` 选择可信源码修复后端：检查原始基线构建，再替换限定源文件、删除对应 object/so 强制重编译，冻结构建产物后逐例运行不可修改的驱动。编译失败与基础设施失败区分。Harbor 原有 solve.py 提交模式保持独立。

Luna Benchmark 启动前必须保存公开包/任务/评分/数据/镜像及模型参数的冻结摘要，核对共享 Viewer；只进行一次 medium、并发 1、重试 0 的独立求解。逐例结果、实际运行计划、耗时和费用留 runs，维护记录只保留有证据的摘要。
