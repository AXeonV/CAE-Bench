# HF 云端迁移试验

## 当前直接迁移入口

用户当前范围为直接转换 HF 归档，见[迁移规划](../../../qbank/design/pdebench-hf-migration.md)。使用 `--phase archive-pilot --hardware cpu-basic --per-file <1..100> --batch-start <起始行>`，另显式传固定 `--source-revision`、目标 `--revision` 和检查点 `--prefix`；加 `--submit` 才提交 Job。该阶段覆盖全部 25 文件的同一连续行范围，不接受替代数据来源，不运行求解器。大数组只在 HF Job 内流转。

每族使用独立的归档 case 池，保留原初态、后续轨迹、坐标、属性和来源身份。源文件多余尾部时间坐标保留在输入来源记录，只按实际帧数关联有效时间。参数属性与文件名冲突时两者均保留，不静默猜测。标准浮点场以 float64 无损保存；支持 float32 精确提升，未重采样。归档字段逐值回比，远端按固定提交重取并通过真实装配、严格核验和归档身份检查。

复用统一分片池；planned/prepared/verified 检查点绑定来源、代码和运行包身份。verified 可从远端重新消费且不读源；prepared 状态停止核对，不能盲目重发。当前是有界先导入口，不是千行全量控制器。归档池的零容差配置仅作传输一致性检查；正式评分、资源和选样尚未设定，不运行考生。

CPU Basic 分钟价格由提交时 API 获取并设置价格上涨阻断；Job 硬超时 30 分钟，内部 25 分钟停止，包含启动余量的最大预留进入已有 USD 1 总账。本阶段同时计入既有 USD .10 准备活动上限；新阶段不另起账本。当前结果见[直接迁移先导记录](../../../qbank/design/reviews/pdebench-direct-archive-20261018/README.md)。

## 全量归档执行

`--phase archive-full --hardware cpu-basic --baseline-revision <先导固定提交> --source-revision <固定来源报告提交> --revision <全量分支> --prefix <全量进度路径> --submit` 提交一个72小时硬超时的云端执行器，按250个来源跨度顺序推进，交错三个问题族。全量分支从固定先导提交创建；核对并复用400条既有记录，再处理249600条。只计入已有USD 1总账，不另开预算，也不纳入已结束的先导USD .10准备阶段。

每个跨度984或1000条，逐批沿用同一pack/upload/assemble/verify，远端verified才推进；每批释放自身临时数据及下载/解包缓存，防止50GB临时盘积累。未知提交或prepared状态停止核对，不自动重试Job；已有相同recipe的verified跨度可从固定远端重新消费。内部时限留发布余量，HF硬超时独立承担费用停止。不得并发写入这个运行分支，包括旁路上传维护报告。

实时状态使用 `hf_archive_status.py --job-id <已登记全量Job> --output <小型快照>`；它不获取源场或case。可加 `--settle-terminal`，仅终态时按共享锁及既有API身份/时长校验结算费用；未知或取消无时长继续保留预留。执行与监视状态见[全量运行记录](../../../qbank/design/reviews/pdebench-full-20261018/README.md)。

## 本地小规模评测导出

需要在本地小规模评测已迁移数据时，可用 `--phase benchmark-export --hardware cpu-basic --export-plan <冻结选择JSON> --source-revision <已迁移池固定提交> --revision <独立导出分支> --prefix <导出路径> --submit`。选择JSON按advection、burgers、compressible包含三个标准manifest，每族恰选三个case，不含samples。云端沿用assemble/verify获取必要分片，只把这九例重打小ZIP；本机核对固定提交、ZIP大小与摘要后获取，不把完整来源或大TAR搬回本地。不运行求解器，不修改迁移分支或正式选样；导出Job仍进入原USD1总账，硬超时十分钟。

## 历史试验入口

下文平流解析参考和上游重跑属于历史试验，不作为当前直接迁移的先决条件。`migration`/`migration-prep` 仍是旧平流生产器，不用于这次归档直接迁移。

本入口只读取 HF 已有的三个一维数据仓库，固定来源提交，不消费旧题或冻结选样。阶段与数学范围见[试验规划](../../../qbank/design/pdebench-hf-trial.md)，实际完成记录另记[验收](../../../qbank/design/reviews/pdebench-hf-trial.md)。原始数组不在本地获取。

## 认证与预算

先执行 `hf auth login`。令牌需要 Jobs 执行和目标数据仓库写权限，不写入代码或日志。`hf_trial_launch.py` 通过 Jobs secret 传入凭据，只上传明确列出的代码和新题契约；worker 必须在 HF Jobs 内执行。

先预览，再提交：

```sh
python src/utils/PDEBench/hf_trial_launch.py
python src/utils/PDEBench/hf_trial_launch.py --submit
```

预算账本默认在忽略目录 runs/pdebench-cloud-trial/budget.json。每次提交检查实时分钟单价与共享 USD 1 总账本。普通试验预留一小时及一分钟；preflight 每次 USD .04，readiness/migration-prep 每次 USD .02、硬超时 30 分钟，各自准备活动累计不超过 USD .10。完成 Job 可用整个服务端生命周期向上取整、另加一分钟的保守费用界替换最大预留；这不是账单。活动、未知、未能核实的 Job 保留最大预留。未知提交结果保留预留，不自动重试；查询 Job 状态后再处理。不要删除账本绕过预算，也不要并发启动多个 launcher。

计算费用上限不等同最终账单，不包含持久存储费用；提交前另查目标仓库可用空间。默认不暴露端口、不用 GPU，不开启自动重试。

## 来源诊断

首个 worker 每文件提取 10 条按索引等距选择的完整轨迹，保留全部有效帧及原始精度。它检查有限值、字段 shape、坐标与时间，并记录尚需核查的尾部时间坐标差异。它只产生作者来源子集和报告，不宣称题目、数值参考或评测已就绪。索引等距不代表覆盖物理困难。

子集直接写入目标 HF 的试验分支，报告保存固定源仓库、提交、文件内容摘要、实际读取记录及所选载荷摘要。远端整文件摘要来自上游元数据；不声称已读取并核验完整原文件。只在云端下载完整子集供后续处理，本地只取 JSON 报告。

## 首题 case 试验

来源诊断完成后固定其实际 HF 提交，再运行：

```sh
python src/utils/PDEBench/hf_trial_launch.py --phase transport \
  --source-revision <已完成诊断的HF提交> \
  --prefix migration-trials/pdebench/2026-10-18/transport-cases --submit
```

此阶段仅建设 linear-periodic-transport-1d。输入采用 HF 的初始数字和速度，明确将初态解释为原单元内常数；原归档的连续初态解释并未因此得到认证。参考由文献中的周期平移公式对原单元积分产生，归档后续帧只记录差异，不能重贴为新题精确参考。

运行时使用非 editable 安装的公共核心、现有网格工具及 data_pool.pack/upload/assemble/verify，真实检查正例及错误输出，并从固定上传提交重取全部本批数据核验。新题只登记空正式选择；试验选择保存在作者报告中，不能覆盖正式清单。不会启动 Agent benchmark。

该早期试验使用直接目录格式；后续分区池和恢复准备见下文。

## 长跑前预检

`hf_trial_launch.py --phase preflight --source-revision <固定源核查提交> --revision <独立试验分支> --prefix <独立路径> --submit` 在 HF 内复用原 80 例、验证 TAR 分片消费与一次实际上传子进程中断，随后构建 1000 条连续来源的平流 case，并做全量远端装配、严格校验和判分。它还检查已有两族来源子集的结构和物理诊断，诊断不等于数值精度认证。

另加 `--reference-only` 运行较高黏性 Burgers 子集的 Cole–Hopf 公式对照。公式来源、周期化推导、初态新解释、两种系数假设和未认证范围均写入报告；它不产生正式 Burgers case。两种预检均归 phase=preflight，累计最坏预留不得超过 USD 0.10，同时计入既有 USD 1 总账本。每个一小时 Job 保留 USD 0.04，含启动余量；未知提交不得重试，远端差异不得覆盖。可同时运行无写入冲突的工作；固定父提交冲突停止后核对，不盲目重发。

preflight 保存历史传输试验，后续正式分区池沿用其 TAR 字节格式；不自动覆盖历史池。Job 只将小报告返回用户电脑；大数组留 HF。受限公式提交检查使用 2 CPU affinity、120 秒 CPU/墙钟、2 GiB 虚拟内存上限，不能冒充 Harbor 容器/cgroup 隔离验收。当前费用按 Running/Starting 状态或保守生命周期区间估算，最终账单须单列核对。


## 有界生产批次与恢复准备

正式 CLI 已统一支持分区池。`--phase readiness` 验证安装后的 pack/upload/select/assemble/verify：首个 Job 故意在成功发布后退出 75，`--resume` 在全新 Job 从远端索引补齐回执，再只构建缺失批次。此阶段只消费已有云端 80 例，不读原始大文件。

`--phase migration-prep` 使用实际迁移入口，从固定源文件连续读取 1～1000 行，完整制数、交叉核查、判分、上传、重取验收。提交时明确以下参数；不加 `--submit` 仅预览：

```sh
python src/utils/PDEBench/hf_trial_launch.py --phase migration-prep \
  --source-revision <固定来源诊断提交> --revision <准备分支> \
  --prefix <本轮检查点路径> --source-file 1D_Advection_Sols_beta0.1.hdf5 \
  --batch-start 1000 --batch-count 16 --submit
```

同样命令在新 Job 再运行会先查云端检查点；已绑定 case 全部存在时重新装配、严格校验和实际判分，不重新读取源数组。recipe 绑定来源文件摘要、行范围、题目契约、worker 模板和运行包的稳定内容摘要，ZIP 时间戳不影响身份。检查点只允许 planned→prepared→verified，拒绝未知状态、已绑定选择/transport 差异和状态回退；每次更新使用父提交保护。prepared 身份先于池发布保存，提交结果未知时先核对远端。

`--phase migration` 为相同的有界平流生产入口，继续受共享预算约束；它不是自动全量控制器。一次 launcher 只提交一个 Job，默认不连续提交下一批，也不启动 scheduled task。批次清单是覆盖计划，不是已完成计数。Burgers/CNS 尚无放行的制数入口。

预备验收和当前成本估计见[迁移准备记录](../../../qbank/design/reviews/pdebench-readiness-20261018/README.md)。容器验证只取两个小 case，明确记录本地字节；原始 HDF5 和大分片仍留 HF。

## 全来源成本校准

`--phase calibration --calibration-mode mechanical|references|auxiliary` 在独立试验路径测成本，不生成 Burgers/CNS 正式 case。该阶段计入 readiness/migration-prep 共用的准备活动 USD .10 上限，每个 Job 仍有硬超时与预留；活动或未知取消结果不会因缺少 API 时长就释放。

mechanical 逐一读全部 25 个固定源文件的两段连续范围，各 256 条、共 6400 条；检查完整帧，写 float64 HDF5，上传后固定提交重取、核摘要及逐字段重读。它测的是来源处理与存储，不代替 case 包装和判分。HF Hub 下载使用当时默认后端；独立文件缓存不能证明底层 Xet 块缓存完全冷，网络字节未单独仪表化。

references 对 12 个 Burgers、5 个 CNS 参数层各两条既有轨迹重跑完整时段，分别记录冷编译和预热耗时；超时报告不换算成每条耗时下界。源码固定版本并核 SHA，随机初始化和文件输出 driver 换成既有源初态及计时 wrapper，数值内核 AST 对照不改；旧 JAX `.loc` 只作 `.at` 索引 API 适配。auxiliary 在预算允许后测 Cole–Hopf 全时刻 64/128 模态及最高黏性单例完整求解。配置假设、同源误差和未认证项必须留报告，不将运行通过冒充独立参考认证。

同分支的 pool 原子发布不要与其他诊断提交并发。来源报告可写各自路径，正式千例制池用单独分支；未知提交先核对。最终实测与按文件分层外推的范围见[成本校准记录](../../../qbank/design/reviews/pdebench-calibration-20261018/README.md)。

实际迁移入口可显式加 `--hardware cpu-basic` 作低价 CPU 对照；默认仍为 cpu-upgrade，其他试验阶段不允许 Basic。提交使用已选硬件，捕获分钟单价用于预算和终态结算；API 实际 flavor 与请求不符时不自动释放预留。两种硬件都有价格上涨阻断，基础 CPU API 分钟微美元取整与官网小时展示可能有微小舍入差异。Basic 是资源对照，不自动改变题目解题资源配置。预算验证包括无网络模拟的完整 main→Jobs 提交参数，不能只验证账本里的硬件名字。

## 多作业分片迁移

单作业停止并固定已核验提交后，可用 `hf_parallel_launch.py` 对已审查计划进行只读检查；明确授权提交才加 `--submit`。提交器复用原制例实现及运行依赖，先锁定累计预算、一次性预留五个 CPU Basic 作业，再逐个提交并核对实际硬件；同一计划拒绝重复提交，未知提交结果保留预留。

各作业写独立分支，指定作业在全部来源分片核验完成后负责云端复制不可变资产与合并分区索引，最终根索引原子发布。原 case 绑定或载荷冲突停止，不以覆盖根索引代替合并。`hf_parallel_status.py --settle-terminal` 只读小型报告和 API 状态，在账本锁内按实际终态结算；不会启动新作业或下载数值载荷。源跨度、硬件、限时、实际 Job ID 和验收证据归运行记录维护。当前实例见[五路迁移记录](../../../qbank/design/reviews/pdebench-parallel-20261019/README.md)。

## 停止后收束与恢复规划

停止所有写入并固定源分支后，`hf_partial_audit.py` 核对终态费用与 verified 检查点；`hf_partial_merge.py` 默认只读预检，显式 `--apply` 才以低频提交合并已核验数据，保留 prepared 批次供后续核查。`hf_partial_check.py` 在最终固定提交独立核对全部描述、完整性和唯一来源覆盖。这些维护步骤不启动 HF Job，不下载数值载荷；TAR 使用 HF 服务端复制。它们是现有池合并和检查机制的迁移编排，不能替代标准数据消费工具。

`hf_recovery_plan.py` 只生成恢复分工和预算，不提交作业。`hf_commit_policy.py` 提供五路确定时隙的纯调度规则；恢复执行器必须将门控接在实际 commit HTTP 请求上，并验证双提交事务和故障恢复。旧七提交执行器不作为新计划入口。最新状态、精确来源范围、计划及启动门禁见[低频恢复记录](../../../qbank/design/reviews/pdebench-low-commit-20261019/README.md)。

## 低频执行轮次

`hf_prepared_preflight.py` 分类待恢复物理包，仅在证明整个原包及原 case 绑定都未发布时允许重新制备：保留旧候选，逐行比较固定来源、全部源/映射场数组、坐标时间及输入 JSON 摘要；允许无数值变化的 HDF5 容器重新序列化产生新候选身份，禁止重绑既有条目。完整远端消费仍是计入完成量的门槛。`hf_low_commit_readiness.py` 运行本地事务、真实 SDK HTTP 路径的限流故障注入和池消费检查，并绑定当前代码摘要。`hf_low_commit_launch.py --cohort rN --plan <计划>` 默认只读；显式 `--submit` 时在旧配额冷却后锁定累计预算、一次预留五份，再逐个提交。已有轮次拒绝重发，未知结果保留预留。

`hf_low_commit_status.py --settle-terminal --logs` 跟随当前轮次注册表，只读取小型报告、根索引及有限 non-following 控制日志。一次事务原子发布不可变路径、分区根和 prepared/进度，完整远端核验后一次提交 verified/累计进度；所有实际 commit POST 经过同一门控。库内 `data_pool_shards.publish(..., atomic=True, extra_operations=...)` 复用原校验及分区归并，默认发布路径保持原行为。自主恢复边界与当前证据见[操作记录](../../../qbank/design/reviews/pdebench-low-commit-20261019/OPERATOR.md)。

恢复限时按已核验来源排除余量，再用分族生产实测估算。生产 `elapsed_seconds` 在 verified 提交前截取，必须另计每批核验提交的轮转等待、最终归并和启动时间；`hf_commit_policy.measured_recovery_timeout_hours` 集中维护这些留额和取整方式，并对当前累计预算校验。它是场景估算而非完成保证；不能通过压低可信时限凑预算。半小时粒度的小时数转换成整数秒后才传给 API 和 alarm。操作参数与当前证据以冻结计划和共享账本为准。
