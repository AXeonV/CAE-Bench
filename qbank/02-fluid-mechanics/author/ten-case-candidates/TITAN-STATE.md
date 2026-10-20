# Titan保存位置与维护记录

本批独立目录：

```text
/home/zhouzhiyu/code/docker/chapter02-ten-reference-candidates-20261020
```

当前冻结设计归档：`maintenance/design-v8-snapshot.tar.gz`。
SHA256：`758bfc55a45a9b3eab335b11b87a087bcb6cdf84f27a09c1ec76025740cebc1d`。
解包位置为`snapshots/design-v8`；`CURRENT.json`指向它。
设计冻结摘要和各题文本摘要在[design-freeze.json](design-freeze.json)。

实际进度及全部630个ID的状态以[execution-summary.json](execution-summary.json)为准，
人读表见[EXECUTION.md](EXECUTION.md)。该记录明确区分待适配和具体闭合尚未匹配的暂缓项；整个参考生产任务尚未完成。

每个已制作工况保存在`cases/<design_id>/`：

- `design.json`保留该次生产的原始设计。
- `input/`含实际自包含problem.json、input.h5、mesh.msh。
- `reference/`含实际reference.h5和逐例grading.json。
- `native/`、原生日志及`execution.json`保留求解器配置、原始场、固定镜像、命令及执行时间。
- 公式工况使用`producer.json`，记录文献、固定PDF摘要、归一化常数及公式求值脚本；没有冒称为OpenFOAM计算。
- `status.json`保留当前候选结果摘要及转换局限。

`maintenance/sources/`保留固定版本PDF、Elmer Reynolds源码和镜像内原生OpenFOAM源码。
`maintenance/python-runtime.json`记录Python、NumPy、SciPy、h5py版本。
`maintenance/solver-*.json`保留原始镜像部署信息。
历史设计归档和失败尝试未覆盖：`failed-attempts/`保留工作目录入口、pFinal配置、NumPy批量接口修复前的证据。
这些修复没有改变已生产工况的物理定义。已完成结果的原生计算没有为转换修复而重跑。

本阶段只做设计完整性、存储完整性、有限值和摘要记录；没有精度、网格加密、独立交叉比对、判分链或资源达标验证。
Elmer通量使用恢复梯度，原生VTU只有8位有效数字；文献公式采用固定阶求积；两者均未作误差认证。
已完成装配的产物仅为`unvalidated_candidate`；运行中、失败和迭代限额状态单列，不能计为已完成参考。未修改HF或GitHub，未运行LLM考生或Agent benchmark。

2026-10-20续作使用有界队列继续实际计算。控制器身份在`maintenance/*queue.json`及`*recovery*.json`，包含PID及Linux starttime；不得仅按旧PID重启。
资源证据在`maintenance/resource-scheduling.jsonl`；失败保存在`maintenance/adapter-attempts/`。现有求解任务不为扩大并发而重启。
`maintenance/producer-script-versions/`保存部署期间归档的脚本版本；实际配置、执行记录和场仍以各工况目录为准。配置/转换修复不代表数值验证。
`maintenance/source-manifest.json`索引固定Elmer源码及固定OpenCFD镜像内源码。design-v6保留作为已启动队列的冻结输入；后续设计修订另存新版本，不覆盖活跃队列的快照。
旧FOAMBench目录、停止标记和暂停的监测任务未改动。

设计v7只修订获用户确认的五项等温局部源，详情见[DESIGN-REVISIONS.md](DESIGN-REVISIONS.md)。
新增湍流有界队列为`maintenance/turbulence-queue.json`，40项2.3.1–2.3.4；按共享预约器与其他队列合计不超过40核。

当前v8归档增加稀薄气体壁面观测说明修正，物理定义不变。v6/v7活跃队列不切换快照。
`maintenance/immiscible-queue.json`记录20项两流体的已执行有界队列；`sparta-queue.json`记录12项盒形原生粒子计算，其结果不能在公共转换完成前计为候选参考。
`maintenance/turbulence-kepsilon-retry.json`保留7项原生SST达到迭代限额后、改用题面允许的k–ε进行的一次有界试算；仍达到迭代限额的项继续单列，不放宽完成条件。
`maintenance/bounded-finalizer.json`为一次性汇总脚本身份，最大等待24小时，结束或到时后刷新Titan执行索引。原试算的单项语法修复控制器为`sparta-trial-repair.json`。

`maintenance/sparta-surface-trial.json`及`sparta-geometry-queue.json`续作原8项非平凡几何；与盒形队列按已存在status去重，统一预约40核。三角形曲面和四面体几何快照保存在各项native目录及native-input-mesh.npz。
