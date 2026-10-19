# DaRUS → 现有题目 case

本目录只负责 PDEBench 来源数据的按需读取、显式选样、格式转换与消费检查。保持第一章现有题面和 DATA，不经过 HF 迁移，不运行 PDE 求解器或重算参考。模型评测继续使用项目现有发布器、Harbor 与判题器。

## 安装与查看来源

从仓库根目录运行，Python ≥3.11；Gmsh 系统依赖按项目安装说明准备：

```sh
python -m pip install -e '.[pdebench]'
python src/utils/PDEBench/prepare.py list --task advection-1d
```

`list`、`plan` 仅依赖标准库，不联网、不自动安装依赖。catalog 固定 DaRUS DOI `10.18419/DARUS-2986`、V8、文件 ID、大小及 MD5。不要把全局 generator_commit 当成每个发布文件已核实的生成版本。

需要实际布局时显式探测，不扫描所有轨迹：

```sh
python src/utils/PDEBench/prepare.py inspect --task advection-1d --source-id 255674 --index 0 --network-mb 16
```

返回真实轨迹数、空间形状、时间坐标及网络账目。分组文件不猜总轨迹数，只确认指定 group 存在；不可压缩流只探测指定初始时间戳，避免扫描分散的压缩时间 chunk。

## 显式选样

在忽略的运行目录创建 `spec.json`，内容为列表。例如同一源文件的不同轨迹分别作公开样例、隐藏测试：

```json
[
  {"task":"advection-1d","source_id":255674,"index":0,"frames":[0,1,7,61,200],"role":"sample","id":"01"},
  {"task":"advection-1d","source_id":255674,"index":1,"frames":[0,1,7,61,200],"role":"case","id":"001"}
]
```

```sh
python src/utils/PDEBench/prepare.py plan --spec runs/my-trial/spec.json --output runs/my-trial/selection.json
```

- 每条明确 task、来源文件 ID、零基轨迹索引、原始帧索引、sample/case 角色、本地数字 ID。
- 帧索引严格递增且含 0，样例最多 5 帧、隐藏最多 9 帧；索引是否越界及实际时间在读取源元数据后检查，不重新生成时间值。
- 可选任意合法轨迹，工具不先扫描候选池；随机选择应先在真实已知索引范围生成 spec，保存种子及选择依据。当前 CLI 不自动随机选样。
- 同一来源轨迹不能重复使用；制作时再以初态指纹排除本次同题重复，不把时间裁剪或重编号当成独立 case。
- selection 绑定 catalog、题面/DATA、评分模板和转换器摘要；任一变更需新计划、新工作目录。少量选择仅表示本次子集，不替换正式选样或改变题面总例数。

## 制作、核验、装配

```sh
python src/utils/PDEBench/prepare.py prepare --selection runs/my-trial/selection.json --workspace runs/my-trial/workspace --network-mb 64 --disk-mb 2048
python src/utils/PDEBench/prepare.py verify --selection runs/my-trial/selection.json --workspace runs/my-trial/workspace
python src/utils/PDEBench/prepare.py assemble --selection runs/my-trial/selection.json --workspace runs/my-trial/workspace
```

每个工作根必须为空或属于同一 selection。代码目录和原题库不写入数据；本地得到：

```text
workspace/qbank/<chapter>/<section>/<task>/
  instruction.md、DATA.md                    原文件不变
  samples/01/input/{problem.json,input.h5,mesh.msh}
  samples/01/output/result.h5                 完整 example
  samples/01/reference/{reference.h5,grading.json}
  cases/001/{problem.json,input.h5,mesh.msh}
  reference/001/{reference.h5,grading.json}
workspace/evidence/                          逐例来源、映射、文件摘要及状态
workspace/verification.json
workspace/dist/<task>-agent.zip
workspace/runs/harbor/tasks/<task>/
```

`prepare` 最后执行相同的 `verify`。验证覆盖实际输入和参考加载、公开 example、自判分正例及明显错误数值反例、选择覆盖、文件摘要。自比较通过证明格式与判题链相容，不证明连续 PDE 精度。example 是源参考转换得到的完整输出，不是可复用求解器。

`assemble` 使用现有 `publish_dist.publish` 与 `prepare_harbor.prepare`，不启动考生。两者 CLI 也支持 `--root <workspace>`；运行方式见[评测维护说明](../../../qbank/maintenance/EVALUATION.md)和[运行技能](../../../.agents/skills/caeoj-run-benchmark/SKILL.md)。首次真实模型运行需明确模型、推理档、次数与预算；本工具不默认调用模型或重用历史提交。

存在未通过来源适用性检查的条目时只生成 input 与私有 `candidate.h5`，不生成可判分参考或假 example，返回退出码 2，`assemble` 不产出评测包。具体限制：

- 一维反应扩散、Darcy、二维不可压缩流保留历史发现的参考或来源解释缺口；当前直接模式明确阻断判分，尚未实现逐例审核后解锁的接口。
- FHN 恢复题面要求的完整 512² 初态，必须逐值匹配发布初值子集；不重新求解 PDE。其他族也校验源参数、边界映射、真实网格/时间和首帧对应。
- 所有可判分来源参考仍保留原数值精度及离散误差，现有 provisional 容差与资源没有因本工具通过检查而正式校准。

## 缓存、预算与恢复

默认范围缓存为 `runs/pdebench-direct/cache`，单文件磁盘缓存上限 64 MiB，内存 4 个块。使用 `--cache-root` 可指定独立缓存；`--source-dir` 可改读已有完整文件，完整文件验证大小和 MD5，网络子集不能声称已核验整文件 MD5。

`--network-mb` 是本次命令的响应体字节上限，十进制 MB。发请求前保守预扣最大响应体，重试也扣额；部分读取失败保留预扣，成功完整响应体另行实测。该账目不含 HTTP 头、TLS 等传输开销。压缩 HDF5 chunk 和元数据也占预算，不能用目标数组大小代替流量。Range 必须返回精确 206/Content-Range，否则停止，不下载整文件。`cache/last-transfer.json` 即使失败也保留本轮账目。

`--disk-mb` 覆盖当前工作树、缓存与暂存峰值估算；高维字段读取前检查空间。完整条目以来源/转换/契约和实际文件摘要复用；损坏或人工修改的已提交条目拒绝覆盖。中断安装由本工具的逐例事务记录恢复；不认识的同名目录要求检查。缓存及工作区持有排他锁，避免重复写入。

退出码：0 完成该命令；1 输入、网络、预算或完整性错误；2 已取得输入/候选参考但来源审核未就绪。`assembled` 不等于模型评测已完成。

## 模块和维护

| 模块 | 职责 |
|---|---|
| prepare | CLI，无自动装依赖/求解/付费动作 |
| selection、models、catalog | 显式来源身份、题目路由和契约绑定 |
| storage、sources | 有预算的 Range 缓存、HDF5 布局及完整初态恢复 |
| conversion | 现有 JSON/Gmsh/HDF5 字段转换 |
| checks | 只读来源适用性/一致性检查 |
| pipeline | 原子制作、回执、恢复、验证与既有装配入口 |

历史数值重算实现与旧 CLI 已删除，不保留兼容执行路径。2026-10-13 的结果和局限保存在[历史审核](../../../qbank/design/reviews/pdebench-20261013/AUDIT.md)，不是当前数据就绪证明。设计背景见[按需取数方案](../../../qbank/design/pdebench-direct-cases.md)。

开发检查：

```sh
PYTHONPATH=src python -m unittest discover -s tests -p 'test_pdebench*.py' -v
```
