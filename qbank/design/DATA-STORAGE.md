# 题库数据存储设计

HF 使用题内数据池，**一个具体 case 一个自包含目录**。本地 `cases/`、`reference/`、`samples/` 是选样后的装配结果。正式仓库为 [jimzhouzzy2006/CAE-Bench-OJ](https://huggingface.co/datasets/jimzhouzzy2006/CAE-Bench-OJ)，数据全部公开。

## 职责与目录

```text
HF: qbank/<章>/<节>/<题>/pool/
  index.json
  cases/<case-id>/
    case.json
    input/problem.json
    input/…本算例所需全部资产…
    reference/reference.h5

代码仓库: qbank/<章>/<节>/<题>/
  instruction.md
  DATA.md
  data-manifest.json
  author/data-evidence/…解析、审核、catalog、验证记录…
```

HF 只存可直接使用的输入和参考，包括 JSON、网格、数组与 CSV，不按文件大小区分。case 内输入包含所需全部文件，引用不越出输入包；参考目录只含 `reference.h5`。本题不同 case 即使网格相同也各自保存，不设通用 shared、attachments、附件描述或外部载荷跳转。相同输入被选作样例时复用同一个 case，不复制样例目录到 HF。

维护证据、解析推导、生成配方和样例验证记录归代码仓库 `author/data-evidence/`，不影响考生题意，也不进入公开包。原始来源下载、数值中间结果和制作缓存另放本地忽略目录；不因清理 HF 而把大文件归档进代码仓库。

## 身份、索引与选样

题目具有全库唯一的无章节含义 ID，例如 `caeoj-000123`，唯一权威记录为本题 `data-manifest.json` 的 `task_id`。文案、数据修复或路径变化保留 ID；考查任务实质变化时新建 ID。新题显式分配并核对已有编号。

case ID 独立于测试/样例角色、本地编号与路径。当前自主/已转换数据以输入文件相对名称及摘要集合的 SHA-256 前 24 位加 `case-` 前缀确定，完整摘要记在来源身份中；输入不变则 ID 不变，参考更新仍需更新摘要绑定。来源数据额外保留固定源文件、轨迹索引与转换绑定的必要身份信息，完整证据留作者材料。

| 材料 | 版本与职责 |
|---|---|
| HF `pool/index.json` | `schema_version: 2`，`cases` 按 ID 列出描述路径、SHA-256 和派生完整性摘要，用于浏览/筛选 |
| HF `pool/cases/<id>/case.json` | `schema_version: 2`；`case_id`、`origin`、`files`、`input`、`reference`，不接受其他扩展字段 |
| 代码侧 `data-manifest.json` | `schema_version: 3`；题目 ID、`repository`、`pool.index`、测试和样例的明确选择，可含维护说明 `notes` |

`files` 的键是本 case 内的相对路径，值只含 `size_bytes` 和 `sha256`。输入键位于 `input/` 下，参考键仅为 `reference/reference.h5`；不支持 `source` 重定向。`input`、`reference` 分别声明 `complete` 和 `files`，二者文件列表必须无重叠且恰好覆盖全部文件。参考待补时列表可为空并明确不完整。

选择的 `cases`、`samples` 按本地编号映射到 `{case_id, case: {path, sha256}}`。描述绑定路径必须是 `pool/cases/<case-id>/case.json`。代码清单不重复列出全池载荷；通过描述摘要绑定其文件集合。选样落为明确 ID 和摘要，索引增长、重排或随机种子不能隐式改变已选集合。

## 获取与装配

一次获取固定同一个 HF 提交，先校验描述绑定，再按大小和 SHA-256 校验文件。每个 case 默认获取输入与参考，样例也需要完整输入输出；缺少参考可用于开发，但必须报告不完整。

输入按原字节装配到 `cases/<编号>/` 或 `samples/<编号>/input/`；参考映射到 `reference/<编号>/reference.h5` 或样例 `output/result.h5`。不修改物理声明、不重写路径、不处理附件或旧目录还原映射。装配回执仅为本地忽略的运行证据，校验从其中保留的 SHA 绑定原始描述推导预期数据，不信任可随意修改的回执文件摘要。

相同文件跳过，不同文件先提示，显式更新才覆盖。新集合暂存并预检后写入，失败回滚，回执最后提交。只清理工具管理且未被用户修改的旧装配文件，未知或修改过的文件不静默删除。开发不一致时 warning；正式准备遇到缺失、摘要不符、不完整参考或重复输入/来源轨迹即停止，作为基础设施/选样问题处理。

数据公开不改变考生边界：公开发布只取选中样例、题面和必要工具；池索引、描述、整题选择、回执、作者证据和非样例参考不进入考生包。发布器严格核验样例，Harbor 准备严格核验全部选择，均离线执行。具体白名单见[公开接口](PUBLIC-INTERFACE.md)。网络策略由评测配置明确，不推定现有隔离已经完成。

## 维护与验证

通用操作见[数据池操作](../maintenance/DATA-SYNC.md)。`pack` 读取生成材料，输入和消费参考进入上传树，其他参考侧记录与样例验证记录输出到独立 `evidence/`，审核后保存在作者目录；数字中间件不直接提交 Git。上传白名单仅允许索引、case 描述及其自包含载荷，不上传 evidence。

文件完整、契约合法、来源审核、参考精度和资源校准分别验证。PDEBench 原输出不自动成为参考；模型修正和独立计算仍由来源/出题工具负责。当前固定选样工具不等于完成了 PDEBench 全轨迹转换。

只维护最新数据，不承诺长期历史数据可用；一次固定快照和摘要用于防止混读，不构成历史复现承诺。题目移动时同步两边路径，稳定 ID 不变。

## 迁移与收束

旧选择版本 2、`pool/items/*/item.json`、shared 和 attachments 布局已被替换。新版工具明确拒绝旧格式，不保留兼容分支或 `--no-auxiliary` 等废弃入口。迁移先保存维护证据，核对输入与消费参考，上传并从固定提交取回验证，再更新选择与本地装配、移除旧 HF 路径。HF 历史保留，不改写 Git 历史。

首批既有样例/测试重叠仍如实保留，不在存储迁移中擅自重选；正式准备继续阻断这些重叠。证据见[存储迁移记录](reviews/data-storage-migration.md)，工具验证见[实施记录](reviews/data-pool-tools.md)。
