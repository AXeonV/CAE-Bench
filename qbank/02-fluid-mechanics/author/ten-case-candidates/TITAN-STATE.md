# Titan保存位置与维护记录

本批独立目录：

```text
/home/zhouzhiyu/code/docker/chapter02-ten-reference-candidates-20261020
```

当前冻结设计归档：`maintenance/design-v6-snapshot.tar.gz`。
SHA256：`093a98554b79ed3fe95f2734eff88bf9b1083de5b62f6d22603d28a50b180175`。
解包位置为`snapshots/design-v6`；`CURRENT.json`指向它。
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
全部产物仅为`unvalidated_candidate`。未修改HF或GitHub，未运行LLM考生或Agent benchmark。

已接通的执行队列都是有界队列，已退出；剩余条目没有伪装成后台在算。
旧FOAMBench目录、停止标记和暂停的监测任务未改动。
