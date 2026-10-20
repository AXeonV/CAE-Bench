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

在忽略的运行目录创建 `spec.json`，内容为条目列表或含 `entries`、`examples` 的对象。例如先选两条独立计分 case，再将它们引用为公开 example（本例两条均已公开）：

```json
{
  "entries": [
    {"task":"advection-1d","source_id":255674,"index":0,"frames":[0,1,3,7,15,31,61,101,200],"role":"case","id":"001"},
    {"task":"advection-1d","source_id":255674,"index":1,"frames":[0,1,3,7,15,31,61,101,200],"role":"case","id":"002"}
  ],
  "examples": {
    "advection-1d": {"01":{"case":"001"}, "02":{"case":"002"}}
  }
}
```

```sh
python src/utils/PDEBench/prepare.py plan --spec runs/my-trial/spec.json --output runs/my-trial/selection.json
```

- 每条明确 task、来源文件 ID、零基轨迹索引、原始帧索引、角色及本地数字 ID。计分 case 只登记一次；`examples` 按题目和样例 ID 引用已有 case，不能另填来源或帧。
- 帧索引严格递增且含 0，case 最多 9 帧；引用式 example 完整继承 case 的输入、时间轴、参考和评分，支持全部 9 帧，不裁剪。独立 `role=sample` 条目仍最多 5 帧。索引是否越界及实际时间在读取源元数据后检查，不重新生成时间值。
- 可选任意合法轨迹，工具不先扫描候选池；随机选择应先在真实已知索引范围生成 spec，保存种子及选择依据。当前 CLI 不自动随机选样。
- 同一来源轨迹不能登记两次；制作时再以初态指纹排除本次同题重复。允许且只允许 `examples` 显式引用计分 case 来公开，不把时间裁剪、重编号或样例副本当成额外独立 case。一个 case 只对应一个公开样例，样例 ID 不能与独立 sample 冲突。
- selection（schema_version=2）绑定 examples 引用、catalog、题面/DATA、评分模板和转换器摘要；任一变更需新计划、新工作目录。少量选择仅表示本次子集，不替换正式选样或改变题面总例数。

## 制作、核验、装配

```sh
python src/utils/PDEBench/prepare.py prepare --selection runs/my-trial/selection.json --workspace runs/my-trial/workspace --network-mb 64 --disk-mb 2048
python src/utils/PDEBench/prepare.py verify --selection runs/my-trial/selection.json --workspace runs/my-trial/workspace
python src/utils/PDEBench/prepare.py assemble --selection runs/my-trial/selection.json --workspace runs/my-trial/workspace
```

需要把数据放回当前仓库的题目目录时，先完成独立工作区，再安装并核验：

```sh
python src/utils/PDEBench/prepare.py install --selection runs/my-trial/selection.json --workspace runs/my-trial/workspace --replace
python src/utils/PDEBench/prepare.py verify-installed --selection runs/my-trial/selection.json
```

默认目标为当前仓库，也可用 `--target-root` 指定具有相同题面与配置的项目。目标已有 cases/reference/samples 时必须显式 `--replace`；旧数据保存在目标的 runs/pdebench-install/，不静默删除。安装前核验整个工作区、目标定义、磁盘空间和 HF 冲突；复制中断保留阻断标记，异常回滚旧数据。安装回执 author/direct-source.json 记录冻结选择、完整载荷摘要及公开身份，安装后的发布／Harbor 装配继续核验，不伪造 HF 回执。生成数据、公开绑定和安装回执均不进入 Git；题面、DATA 和评分配置不随数据覆盖。正常安装只复制本地已核验数据，不重新下载来源。

每个工作根必须为空或属于同一 selection。`prepare` 不向代码目录和原题库写入数据；本地得到：

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

引用式 example 不再读取源数据；从已核验的 case 复制全部必要输入与参考，并以完整 reference 生成 output/result.h5。工作区冻结公开引用和全部 case/sample 身份，样例文件摘要与原 case 完全一致才可发布。缺失绑定、额外样例、修改帧/参考或身份错配均拒绝；中断恢复不重新下载轨迹。

每题 20 个 case + 2 个引用式 example，仍只计分 20 例，其中 2 例已公开、18 例未公开。`verify` 报告包含 `case_count`、逐题 `public_cases` 和 example 状态；Harbor 的 tests/selection.json 与判题报告保留相同公开身份，逐例标为 `public_sample`。公开样例仍参与总分，不作为未见输入解释。HF 清单与本地公开绑定不允许混用，不伪造下载回执。

`assemble` 使用现有 `publish_dist.publish` 与 `prepare_harbor.prepare`，不启动考生。两者 CLI 也支持 `--root <workspace>`；运行方式见[评测维护说明](../../../qbank/maintenance/EVALUATION.md)和[运行技能](../../../.agents/skills/caeoj-run-benchmark/SKILL.md)。首次真实模型运行需明确模型、推理档、次数与预算；本工具不默认调用模型或重用历史提交。

存在未通过来源适用性检查的条目时只生成 input 与私有 `candidate.h5`，不生成可判分参考或假 example，返回退出码 2，`assemble` 不产出评测包。具体限制：

- Darcy 核对实际 `beta` 属性、坐标、布局及系数值域后保留发布单帧参考；不因未认证稳态收敛而阻断，不补算修正。零虚单元与题面零 Dirichlet 的离散差异记录在作者证据中。
- 二维不可压缩流按实际分片校验单位域、网格、黏度、边界、标量/向量布局及真实时刻；初态保留原始预投影首帧，参考保留原速度采样，不执行投影或再采样修正。只读取输运标量的初帧作为输入，不下载不参与判分的标量后续轨迹。
- 一维 logistic 反应扩散直接保留 DaRUS 发布参考，历史后期停滞记录不再触发全题门禁；不补算或修正参考，不把迁移验收解释为数值精度认证。
- FHN 恢复题面要求的完整 512² 初态，必须逐值匹配发布初值子集；不重新求解 PDE。其他族也校验源参数、边界映射、真实网格/时间和首帧对应。
- 所有可判分来源参考仍保留原数值精度及离散误差，现有 provisional 容差与资源没有因本工具通过检查而正式校准。

## 缓存、预算与恢复

默认范围缓存为 `runs/pdebench-direct/cache`，单文件磁盘缓存上限 64 MiB，内存 4 个块。使用 `--range-block-kb 64` 可减少稀疏一维读取的响应体，默认 1024 KiB；不同块大小应使用不同 cache-root。使用 `--cache-root` 可指定独立缓存；`--source-dir` 可改读已有完整文件，完整文件验证大小和 MD5，网络子集不能声称已核验整文件 MD5。

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
| installation | 已核验工作区安装到题目目录、备份、回滚与安装核验 |

历史数值重算实现与旧 CLI 已删除，不保留兼容执行路径。2026-10-13 的结果和局限保存在[历史审核](../../../qbank/design/reviews/pdebench-20261013/AUDIT.md)，不是当前数据就绪证明。设计背景见[按需取数方案](../../../qbank/design/pdebench-direct-cases.md)。

当前真实消费范围与证据见[平流、Burgers、一维可压缩流验收](../../../qbank/design/reviews/pdebench-direct-20261019/REPORT.md)、[引用式 example 验收](../../../qbank/design/reviews/pdebench-public-examples-20261019/REPORT.md)及[其余四题验收](../../../qbank/design/reviews/pdebench-four-task-20261019/REPORT.md)。来源转换、隔离执行与连续数值精度分别说明。

开发检查：

```sh
PYTHONPATH=src python -m unittest discover -s tests -p 'test_pdebench*.py' -v
```
