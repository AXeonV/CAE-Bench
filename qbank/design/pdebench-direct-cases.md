# PDEBench 按需取数与工具收束方案

本方案规划从 DaRUS 直接取得少量轨迹，转换成第一章现有题目的输入、参考和公开 example，再使用现有评测链。本文定义待实施的改造；不是已完成的数据或评测报告。

## 范围与约束

- 保持现有 instruction.md、DATA.md、评分含义和资源要求不变。范围内为当前 `models.py` 已路由的 11 道 PDEBench 来源题目，不等于第一章全部题目。
- DaRUS 是原始数据来源；无需先迁移到本项目 HF 仓库，也不依赖已撤回的归档适配器。HF 制池是以后有发布需求时的可选步骤，不是本地评测前提。
- 默认只读来源数据、做必要格式转换和契约检查。不运行上游求解器，不重算或自动替换参考，不根据考生成绩调整参考或阈值。
- 网络与磁盘预算分开：只取指定轨迹所需初态、输出帧、坐标及必要配置；不默认扫描候选初态，不整库下载，不在 Range 失败时回退整文件。
- example 指 `samples/<ID>/input/` 与 `output/result.h5`，以及可自判分的公开参考。它是来源数据转换的完整输出示例，不冒充一份能够求解其他 case 的 solver。
- 已有正式来源选择和选样保持不变。探索选择写入独立运行目录，少量冒烟数据不能声称覆盖正式题目全量要求。

## 现有代码与职责问题

| 当前文件 | 可复用内容 | 改造方向 |
|---|---|---|
| `storage.py` | RangeReader、缓存摘要、重试、磁盘预算 | 保留；补网络字节预算与请求统计，覆盖元数据、重试、探测，不能只统计成功载荷 |
| `catalog.json` | DaRUS V8 文件 ID、URL、大小、MD5、生成器定位 | 保留固定版本；不自动跟随 latest，不把统一 generator_commit 当成每个发布文件的已证生成版本 |
| `sources.py` | Reader、分族 HDF5 布局、真实时间和指定帧读取 | 保留；读取器与选样策略分开，支持显式轨迹和帧索引 |
| `models.py` | task 路由、参数换算、字段及域信息 | 保留声明；移出隐藏点数量、默认公开配置等选样策略；逐项与本题 DATA 核对 |
| `conversion.py` | Gmsh、字段/IDs 映射、build_input、首帧校验 | 保留格式转换；移出解析求解相关函数，不引入参考生成职责 |
| `pipeline.py` | 原子安装、缓存身份和文件绑定 | 拆开选择、制数、校验；移除默认候选扫描和隐式参考回退的耦合 |
| `source_audit.py`、`references.py` | 历史差异证据及独立比较实现 | 不进入默认来源转换链；有仍被使用的维护研究功能才迁入单独作者研究模块，未使用的实现删除并清理引用 |
| `prepare.py` | 单入口、离线预览 | 原地收束成明确子命令；迁移调用方和文档后删除旧参数与默认执行路径，不长期叠加第二套入口 |
| `AUDIT.md`、`STATEMENT_REVIEW.md` | 历史证据 | 移入 design/reviews 的历史记录目录，保留日期和原文；更新链接 |
| `EVALUATION.md` | 已有操作和历史试跑配置说明 | 公共流程引用 maintenance/EVALUATION.md；历史配置记录归入 reviews，资源数值继续以题内配置为准 |

现有 `official` 路径会调用平流/Burgers 独立比较，并重算一维反应扩散与 Darcy 参考；名称不能代表“只复制官方数值”。新默认路径必须从调用关系上隔离这些计算，不仅换一个 CLI 名称。

实现先保持当前包名 `utils.PDEBench`，避免无关目录重命名。目标约为入口、catalog/models、storage、sources、selection、conversion、pipeline 七项职责；按职责拆分，不为每族增加整套重复流水线。

## 面向使用者的工作流

拟继续使用 `prepare.py`，以下子命令尚未实现：

1. `list`：离线查看题目、来源文件和已知限制。轨迹总数只有读取真实 HDF5 布局后才确认；单轨迹文件和分组文件不能统一猜为 10000 条。
2. `plan`：按 task、source ID、trajectory index、原始 frame indices 生成运行选择；支持固定种子的小量随机选择。初期先支持显式索引，随机选择只在可核实的索引范围中进行，不扫描整库。输出预计空间、未知网络开销、公开/隐藏身份和绑定摘要。
3. `prepare --selection ...`：执行 Range 读取、转换及来源/契约校验，生成输入、来源参考、example、逐例 grading.json 与私有制作回执。支持断点复用和独立输出目录。
4. `verify --selection ...`：逐例校验所有实际输入、参考和公开输出，再经现有 case 评价入口检查正反例；产生可装配状态。

`plan` 默认离线；源布局探测必须显式执行且计入网络预算。读取前能确定的费用/空间先检查，压缩 chunk 的实际网络开销如未知应标 unknown，不能把目标数组大小当作下载量。

selection 至少固定：数据集 DOI/版本、catalog 摘要、task、source ID/文件摘要、轨迹或 group、原始帧索引、sample/case 角色、本地 ID、题面/DATA 摘要及转换版本。公开与隐藏按源轨迹拆分，并复用已有初态指纹排重；重编号、时间截取不能把同一轨迹拆进两组。

输出放在忽略的运行目录，布局保持现有契约：

```text
<run>/workspace/qbank/<chapter>/<section>/<task>/
  instruction.md、DATA.md                 原文件逐字节复制
  samples/01/input/{problem.json,input.h5,mesh.msh}
  samples/01/output/result.h5
  samples/01/reference/{reference.h5,grading.json}
  cases/001/{problem.json,input.h5,mesh.msh}
  reference/001/{reference.h5,grading.json}
<run>/selection.json
<run>/evidence/                           来源、映射、文件摘要、网络账目与制作状态
```

公开样例与隐藏 case 使用同一个转换器和逐例评分配置生成机制，不再通过另一套简化字段/点格式或历史模型 I/O 桥接。example 输出与其参考数值一致属于转换自检，不是独立数值验证。

## 题面与来源的对应

每族需核对：模型/参数、边界、初态、原坐标、空间量含义、字段/分量、实际时间以及 reference 的来源。沿用当前转换中已有的正确映射，但以下表为待逐例复核的清单，而非全族就绪承诺。

| 现有 task | 来源到本题的关键映射 | 直接来源模式处理 |
|---|---|---|
| advection-1d | tensor → state/initial_state；beta → velocity；周期域 [0,1] | 首批闭环；选源真实帧，避免所有时刻都恰好整周期平移 |
| burgers-1d | tensor → state/initial_state；Nu/π → diffusion_coefficient；周期域 [0,1] | 首批闭环；不调用 Cole–Hopf 求值作为制数前提 |
| compressible-navier-stokes-1d | density/Vx/pressure → density/velocity/pressure；gamma、eta/zeta；周期或 trans 按来源与 DATA 明示 | 首批闭环；保留守恒量导出速度/压力的题意，不直接宣称是原始变量体积平均 |
| compressible-navier-stokes-2d | Vx/Vy 合为向量；参数与 128²/512² 分辨率对应 | 第二批；不为降低流量改变题目空间采样 |
| compressible-navier-stokes-3d | Vx/Vy/Vz 合为向量；随机场和湍流真实分辨率分别核对 | 第二批；先给出单例实际流量与内存测量，再扩大 |
| diffusion-sorption-1d | group data → concentration；固定物性及题面已有的外部单元耦合边界 | 第二批；检查实际 group 配置，不能改成普通 Robin 边界 |
| shallow-water-2d | group data → depth；真实域、重力及初态 | 第二批；来源未给出的输出不补造 |
| reaction-diffusion-2d | 源 y/x/channel → 本题 x/y 字段；完整细网格初态与输出子集 | 条件支持：现有历史 MT19937 初态恢复须逐值匹配发布子集；这是必要输入恢复，不是重新求解 PDE；不能只给缺失的粗网格初态 |
| incompressible-navier-stokes-2d | velocity、particles、force → 既有速度/示踪/强迫输入语义；真实时间；单位 Box | 条件支持：先复核现有域尺度证据与当前源身份；证据不足时待审核，不在默认制数中启动新输运计算 |
| reaction-diffusion-1d | tensor、Nu、Rho 与本题 logistic 模型 | 已有记录指出部分发布轨迹停滞；直接来源模式不沿用旧重算结果冒充 DaRUS 输出。可先取得输入和候选参考；只有逐例适用性证据充分的条目才能进入评测 |
| darcy-flow-2d | nu → 系数场；beta → source_strength；tensor → 稳态候选 | 已有记录指出部分快照未达稳态；按既有准则做逐例残差/相容性检查，有问题则拒绝该候选，不自动做 spsolve 修正 |

不适用条目记录原因及精确来源身份，不改题面迁就数据，也不把所有族一概判为不可用。对后两族，缺口是某些来源参考能否直接使用，不是现有题目没有定义。

状态分开记录：`input_ready`、`reference_ready`、`example_ready`、`assembly_ready`、`benchmark_completed`。候选参考不等于可判分参考；来源一致性、数值可信度和正式阈值校准分别描述。

## 接通现有判题与评测

直接生成正常题目格式，不新建 judge，不要求考生读取 PDEBench 原格式：

```text
DaRUS Range → Reader → 本题 input/reference/example
→ validate_input / validate_output / prepare_case / grade_case
→ publish_dist.py → prepare_harbor.py → 既有 Harbor benchmark
```

当前 publish_dist.collect_materials 和 prepare_harbor.prepare 均已有 Python `root` 参数；CLI 尚无对应 root 参数。优先让这两个现有入口接受受校验的隔离工作根，复用 task_directory、runtime_materials 与原判题器，避免写专用 PDEBench 发布器。

隔离工作根必须包含由现有装配机制收集的 CONTRACT、扩展运行资源、题目配置和 Harbor 模板；不是只复制三份输入文件。先检查公开 ZIP 和 verifier 的真实文件闭包，再进入评测。

HF data-manifest 存在时现有入口会做 strict verify。DaRUS 临时工作树不携带不适用的 HF 清单/回执，改由此次制作回执绑定实际本地文件；不得伪造 HF 回执或放松真实 HF 消费的严格校验。这一接入方式需在修改入口时验证。

题面规定的样例/测试规模保持原义。少量 smoke 必须显式标识为工具连通验证；正式运行仍采用该题已声明的完整规模，或等待用户另行指定明确的试评测范围。模型、推理档、次数与运行预算在实际启动前冻结；本规划不启动考生、不默认复用历史 Luna 提交。

## 分阶段实施与验收

| 阶段 | 内容 | 完成证据 |
|---|---|---|
| 1：收束与离线选择 | 拆选样职责，显式索引/帧；隔离重算路径；清理旧入口、文档与测试引用 | CLI 离线 plan、11 题路由、重复轨迹拒绝、无 solver 调用；题面/DATA 字节不变 |
| 2：三族直接制数 | 平流、Burgers、1D 可压缩流各 2 个 example + 2 个隐藏 case，共 12 个独立来源轨迹，在隔离目录验证 | 真 DaRUS 少量 Range 读取；源字段逐值映射、t=0、IDs/轴、参数与边界核验；example 自判分及错误输出控制；第二次执行缓存复用 |
| 3：真实装配和小评测准备 | 现有发布/Harbor 入口支持隔离工作根，冻结题目与数据 | 移走源码后的公开包可读、隐藏资产不泄露、trusted judge 实际隔离/资源生效；形成可执行 benchmark 计划，再按模型授权启动 |
| 4：其余八族 | 按上表处理每族布局、初态与参考适用性；复用同一流水线 | 每族至少一个真实可消费闭环或明确缺口；按单例流量/运行资源决定后续规模 |

开发验证集中在有实际风险的边界：HTTP 206/Content-Range、拒绝 200 整文件回退、超预算、缓存失效、源变更、chunk 开销、参数/BC/空间关联、重算路径不会被调用、公开包和 trusted judge 消费。不为纯文件搬移增加镜像实现的重复测试。

网络开销尚不能给出可信总数：HDF5 元数据及压缩 chunk 布局会放大请求。先记录阶段 2 的每例冷缓存字节、重试字节、热缓存复用、墙钟、峰值空间，再估计更大选样。此路线不需要付费 HF Jobs；模型推理费用另计，不混入取数费用。

清理与实现同阶段提交：删除被替换调用与参数、更新 README 和使用该入口的技能/维护说明；历史证据只迁移不改写。最终 PDEBench 目录保留当前操作和来源适配代码，不累积监视脚本、云作业账本、历史成绩或废弃兼容层。

## 依据

- 当前实现：[PDEBench README](../../src/utils/PDEBench/README.md)、[checks.py](../../src/utils/PDEBench/checks.py)、[pipeline.py](../../src/utils/PDEBench/pipeline.py)。
- 已有差异记录：[AUDIT.md](reviews/pdebench-20261013/AUDIT.md)、[STATEMENT_REVIEW.md](reviews/pdebench-20261013/STATEMENT_REVIEW.md)。这些记录是历史证据，不代表本分支已经重新取数验收。
- 职责与验收：[核心与扩展](CORE-AND-EXTENSIONS.md)、[算例制作](../maintenance/CASE-SOURCING.md)、[评测消费](../maintenance/EVALUATION.md)。
