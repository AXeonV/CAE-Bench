# MOOSE #30236 全数据独立终审

结论：**通过（本报告列明的有界范围）**。2026-10-23 对最终公开题面、DATA、CONTRACT、12 个正式 case、2 个公开 sample、各自输入/参考/评分及样例完整输出执行实际加载；未发现需修订的 P0/P1/P2 问题。数值合格来自本次独立计算与原生 raw 的交叉核验，不来自作者自评摘要或 Oracle 分数。

本次只写本目录与 `runs/configure-judge/repair22-moose30236`，不改公开材料、池、活动 prepared 或中央状态；未启动收费模型、完整框架 build、12 次 native 重算或新 benchmark。审阅采用 caeoj-data-review、caeoj-configure-judge 及其 workflow/current-backend、DATA-SYNC、CASE-SOURCING、EVALUATION 的责任边界。

## 完整消费与契约

`review.py` 不导入作者生成器、解析导数、参考补丁或 `audit_decimal.py`。以公开 DATA 自行实现标量值定义，用 80 位 mpmath 中心微分产生所有一、二阶导数；步长 1e-20。FE 从两个节点分别插值、逐节点扰动，重新执行两点 Gauss 积分，化学势扰动步长 1e-42，其余为 1e-20。端点中央差分跨夹持分支，有限步长截断量保留；没有把端点导数直接置零以规避检查。

12 case 共 8,216 个评分标量，2 sample 共 1,264 个评分标量：20 个输出全分量均小于公开容差。最大比例为 **0.0002449538567898475**（case10）；逐输出最大比例和完整文件 SHA256 见 `checks.json`。比较采用 HDF5 读取的真实二进制浮点输入，80 位计算保留其准确值，避免将十进制重写当作相同输入。

| DATA 声明 | 实际审计覆盖 |
|---|---|
| task/model、1D、无 geometries/meshes/conditions | 全14输入均核对；不存在需另行加载的用户 mesh 文件 |
| programs/instant、严格递增正 int64 IDs、float64 [0] | 全量加载，并逐参考/样例/正式 Harbor 结果核对支持数组 dtype、shape、值和顺序 |
| 5 输入字段、sampling、quantity/unit/components | 核验 JSON 和全部 HDF5 值；实际仅7个输入数组，无隐藏未引用数组 |
| 26 带单位参数、n/strict/naming、SI、inactive padding | 扩展逐输入核对 DATA 限界；实际 n=1..4，strict 0/1，名称0/1，夹持/端点/近端点及8程序稀疏IDs覆盖 |
| 四材料系数、完整gradient/Hessian | 4×(1+5+25)全分量独立数值微分；包括零项、inactive、混合项及两侧对称位置 |
| 原有密度/巨势四值 | 直接从 DATA 四公式在80位计算，不以修复参考重新自比较 |
| 残量与3种Jacobian | 两节点独立扰动和实际积分，全部2+20+4+4分量；不将局部点导数充当积分Jacobian |
| 完整20输出、支持轴和无额外key | 全12参考、2样例reference与output实际load_result；实际评分prepare_case/evaluate均1 |
| 每case唯一grading | 全14配置的单位、pointwise/per_time/per_component、rtol、各输出atol逐项对照公开规则；C/D尺度按各输入Va·kv/ks独立重算 |

所有12份正式 Harbor H5 的全部数组与现行参考 **逐值完全相等**，并独立经当前真实评分入口得1；该结论不是仅比文件摘要。两样例完整输出同样逐数组完全等于样例参考。

## 独立变体与池身份

75 项 DATA 选择的变体全部符合预期：3合法输入边界/模式；13非法输入（越界phi、零/重复ID、额外key、错单位、缺sampling、inactive状态/交叉项、非整数grain_count、过大potential、非零time、NaN、float32）；5代表输出的零参考点分别测试阈值内侧/等号/相邻外侧共15项；缺/多输出、错IDs、NaN输出4项；全部20输出各测试0.5倍与2倍实际容差共40项。逆能量atol经浮点乘法写入配置，与80位精确乘积的微小ULP差异已核对；等号测试针对已核实公开规则生成的实际策略值，未把任意放宽容差视为正确。

独立 `data verify --strict` 返回 valid=true，见 `data-verify.json`，明确两样例仍是正式 case01/02，不减少12分母。固定 HF `e3180f4f7c955107dbba20247d7756cdd95a8785` 的作者 fresh-cache 回执已实际读取，消费文件SHA与本次加载材料绑定；本次未再次联网下载远端，故“重新 fresh fetch”属于已有生产回执的可追溯证据，不冒称审阅者重新下载。

## 真实生产者资格

配套配置终审 `evidence_review.py` 重新解析36份原生 raw（reference/upstream/defect各12）：INITIAL材料CSV、原生PETSc首个残量与 **Hand-coded Jacobian**、实际libMesh DOF CSV。逐case重建公开适配器生成的case.i并逐字节等于raw输入；材料124分量与FE30分量全部重新提取，reference与当前标答逐值完全吻合，其余与各自保存H5完全吻合。没有读取有限差分矩阵充作解析Jacobian。

三版本分列：原件2/12、PR原样3/12、上游加作者混合项12/12。父提交、PR head、作者参考的两个目标文件分别按真实归档、作者冻结源、保留镜像核对；PR原样不冒称覆盖φ–η混合导数。36份raw身份和分数字段见配套 `evidence-checks.json`。原始SinteringParabolic.i三版本两步运行raw、Exodus摘要亦核对；这只证明实际执行，不声称独立形貌正确或Exodiff gold认证。

最终ZIP SHA256 `04563d1ff3576d2ee759f620f3f8ae3d73dfb40a7aacab75912ccefde57e26cc`。包内源码closure全部25,078文件逐字节等于固定原始归档，closure SHA256 `1ba9047d2fed89afc71e3ecf0c934629b9afaad45dbe79ef9272753930f948b7`；25,078文件又在真实 native `43029e45...` 镜像中逐项核对。该链条支持真实MOOSE源生产者资格，80位全输出独立验证支持其数值资格，两者分别成立。

## 未验证项与复用限制

本次没有重新build框架或重算12 native，未做完整烧结演化、额外自由能分支或连续体物理有效性认证；它们均非公开范围。审阅者没有重新执行付费考生。正式容器退出后不能重新采样其cgroup；资源实采复用同后端/ZIP的固定探针，正式新judge完整消费另有12/12 raw与冻结SHA。源码已本地固定归档核对，未再次访问GitHub认证远端历史；没有把维护的新增算例称作issue原始工况。上述边界不影响本题公开局部算子与数据契约在已绑定材料上的通过结论。

所有审阅脚本、JSON和原始检查记录SHA见两个目录的 `materials-sha256.json`。后续若公开三文件、数据、评分、适配器或实际源身份变化，需重跑受影响项。
