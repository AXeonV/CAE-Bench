# 独立实际数据审计：滞回材料试探状态恢复

结论：**通过（全量实际数据、独立骨架/离散功核查及公开SDK契约）**。10个正式case、40条程序和2sample的8条重复程序均已完整检查，无实际资料缺口、未读数组或未决数据问题。此结论不代表本轮重跑真实材料或Harbor生命周期。

## 审计范围、来源和版本

按caeoj-data-review技能只读执行。题意唯一依据为instruction.md、DATA.md、docs/CONTRACT.md；读取本题manifest、全部cases/reference/samples、实际装配回执及明确许可的source.json、cases.json、reference-replay.json、defect-replay.json、author/README.md。为独立重建来源payload摘要，协调方另授权读取public/run_case.py中programs/serialize中性转换函数；仅读相应函数，没有读取run包装器、driver、solver、材料算法、作者独立参考或生成器。没有用维护来源说明补题意。

最终公开ZIP实际SHA256为`ac438c25f7416d325897acb6b763642fc27e518af2e205035d30e53bd9bc16c9`，与指定版本完全匹配。其MANIFEST中14项已审实际资产（3公开文档、2sample×5文件、中性适配器）摘要均吻合。公开样例身份为01/02。全部材料路径和SHA见`runs/data-review/repair22-opensees/evidence.json`，含62文件；其中10case×4输入/参考资产、2sample×5资产全部完整读取。

| 解释文件 | SHA256 |
|---|---|
| instruction.md | 5045d7fa19c08ce613269a0ba9aba12083ce14f3157f011abe7e9bd37a861b17 |
| DATA.md | 54d476fc8d62e3006e857455082bf2476c4d714e945108873accfb53f9c523ef |
| docs/CONTRACT.md | 130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063 |

selection SHA为`c314edae10f388f697e22ea659843728995beb423c3235b1e35de3d4b3c314d5`，装配固定revision为`05a921e30ad641028ec7f07b1cfb403f5995d8c0`。独立复算全部case描述原文摘要、case ID、complete、文件size/SHA、回执绑定全部吻合。官方`data verify --strict`返回valid=true、errors=[]；public_cases准确标识01-hysteretic-public与sample01、02-sm-public与sample02。inventory发现12入口，gaps=0；其not_evaluated不是本轮审计结论。没有重选或刷新绑定掩盖差异。

## 全字段和数组对照

从最终DATA独立手写17输入及4输出元数据表，逐对象比较array、quantity、unit、dtype、kind、component_shape、components、location、time_axis、value_kind、sampling。每例4个正int64严格递增program_ids，float64 times=[0]；输入shape完整为[1,4,C]，输出[1,4,6]。所有有限性、复制ID/time及HDF5扁平结构通过：仅根dataset，无属性/子组/软外链/别名/外存储/虚拟dataset，使用允许过滤器。没有未读大数组。

| 路径或字段组 | 公开依据 | 全量检查 |
|---|---|---|
| task/spatial_dimension/physics/conditions/geometries/meshes | DATA声明与数组 | task/model固定、D=1、parameters={}、conditions=[]、无几何网格及外部依赖 |
| locations.programs、program_ids、instant/times | DATA声明与CONTRACT | 实体ID与行号区分，正int64、顺序、轴全量检查 |
| material_kind、positive_count、negative_count | DATA输入表及有效范围 | float64中的整数值；kind0两侧同为2/3点，kind1两侧各2..7点 |
| positive/negative_strain/stress | DATA骨架定义 | 每侧7槽，前count有效、尾零；符号、范围、绝对值递增、各段正刚度和非增容差检查 |
| pinching、beta | DATA输入表及固定范围 | .05..1、0..1；没有额外损伤/退化/限值输入 |
| history_count/history、trial_count/trials、continuation_count/continuation | DATA操作 | count整数及0..8/1..8/1..8，8槽尾零，所有实际应变位于终点包络内，提交序列方向和最小推进步长检查 |
| return_delta、rollback_probe | DATA操作 | 输入delta范围、真实float64目标和差值、严格EPS分支、probe范围检查 |
| strain/stress/tangent/work_density | DATA输出 | 四quantity/unit精确绑定，6组件严格committed/returned/accepted/continued/rolled_back/reset，无sampling |

无额外conditions或字段，没有把空历史当作缺省字段。初始/continued单向骨架加载与任意未提交跨零试探明确区分；未提交probe响应不在本题输出中，未额外构造卸载/捏拢材料模型。

## 正式覆盖和实际float64阈值

| case | 重点实际分支 |
|---|---|
| 01-hysteretic-public | Hysteretic两点，正负方向及多次跨零试探 |
| 02-sm-public | HystereticSM七点，正负方向 |
| 03-asymmetric-three-point | 三点及两侧不对称 |
| 04-sm-intermediate-points | SM中间点数 |
| 05-independent-side-counts | SM两侧不同点数 |
| 06-zero-committed | history_count=0、原点与微小非零方向 |
| 07-machine-threshold | 实际浮点阈值邻域 |
| 08-multiple-trial-excursions | 多次未提交跨段/跨零 |
| 09-elastic-nontrigger | 正常非触发回归 |
| 10-monotonic-nontrigger | 正常非触发单向加载 |

两真实类和骨架点数2、3、4、5、6、7均出现。逐程序以float64执行εr=εc+delta，再以实际Δ=εr−εc分支，未只看delta或字符串值。40条中31条满足严格`|Δ|<2^-52`，9条走正常推进。实际Δ/EPS集合为−2、−0.75、0、+0.25，以及约±45035996.2734/±45035996.2737；不能把−2EPS归为near。

正式40条没有恰等EPS的数据。本轮额外构造±EPS契约副本，确认实际float64差精确为[+1,+1,−1,−1]EPS且满足加载方向，正式SDK接受；这不被冒称为正式数值参考验证。所有正式非reset计分非零应变与任一正/负非零骨架点的最小距离为0.0002975238895772288，显著大于1e-7，未出现未定义的折点切线计分。

## 独立数值核查

依据公开骨架从原点及有效折点计算分段线性应力、分段斜率；零态切线用正侧首段。没有实现材料反向循环、卸载或pinching求解器。按有效history的每次提交，用`0.5(σold+σnew)(εnew−εold)`累计离散功，跨折点仍使用此步进而非连续积分。

严格near返回恢复εc及完整已提交应力/切线，returned功仍为Wc，accepted保持Wc；非near按同方向骨架求值，returned功仍为Wc，accepted才累加离散步进。continuation逐步累加，rolled_back直接等最近提交态，reset恢复零应变/应力/功与正侧首段切线。四输出全部6检查点、所有48条实际/重复程序都符合公开容差。

| 输出 | 正式40条最大绝对误差 | 公开atol/rtol |
|---|---:|---|
| strain | 0 | 1e-19 / 0 |
| stress | 4.6566128731e-10 Pa | 1e-6 Pa / 1e-10 |
| tangent | 1.0430812836e-7 Pa | 1e-4 Pa / 1e-10 |
| work_density | 7.2759576142e-12 Pa | 1e-8 Pa / 1e-10 |

全部10正式及2sample grading.json精确对应完整direct_outputs，4quantity、单位、逐时刻逐分量pointwise规则和容差一致；没有稀疏参考或独立触发加分。两sample的output/result.h5与各自reference全数组相同，且绑定正式case身份；正式case没有承诺额外输出文件。未把参考自判分当作独立数值正确证据。

## 参考来源、payload和生命周期区别

source.json固定OpenSees issue1817/PR1818及基线915a5d0...、head e9a890e...、merge 3c546b4...，列明两个真实cpp基线/修复SHA与机械patch匹配声明。README和cases.json明确是作者直接材料API适配，没有声称完整桥梁/重力/特征值重现。全部cases.json逐条程序参数与实际数组按有效count解释后精确一致。

reference-replay.json声明由真实上游修复材料生产，固定参考镜像2c0509cd...；其10个result_sha256逐个匹配现有reference.h5。defect-replay.json为固定缺陷镜像34f3561d...，记录8case失败、两个正常非触发case通过。该缺陷重放输出文件不在本轮白名单/正式装配中，因此未独立读取或复验其result_sha，只核对记录、实际输入payload及它与参考模式的区别。

两记录最终hash_semantics明确driver_input_sha256为精确UTF-8 input.txt协议payload，不是raw HDF5；result_sha256为由真实观测写出的HDF5，不是raw output.txt。依获准中性programs/serialize格式，从本轮完整实际输入独立重建数值文本和17g浮点编码，20个payload摘要全部吻合；raw HDF5另由manifest/HF固定revision、回执和本审计完整SHA绑定。没有根据泛化字段名把payload摘要误判成raw H5摘要。

参考生产重放与正式Harbor生命周期是两种证据。本报告审计的是上述固定参考来源/数值数据及最终ZIP，不把旧Harbor v1/v2当成最终ZIP的验证。协调方告知v3已10/10无异常；本轮未读取其独立生命周期工件或重跑Harbor，不以该状态替代本轮数据核查。公开命令/链接和资源说明修订没有被推断为数值数据变动。

## 最终ZIP SDK和独立变体

从已核实SHA的最终ZIP仅提取src/caeoj、caeoj_bundle、caeoj_task_ext运行包。每次新子进程用ZIP的src优先PYTHONPATH，正式SDK中性validate-input/output检查12输入、12参考和2公开输出，共26次，全部通过；未运行题目solver或driver。详见`runs/data-review/repair22-opensees/check_sdk.py`、`runs/data-review/repair22-opensees/sdk-evidence.json`。

6个合法变体均接受：SM两点、pinch=.05、beta=1、沿加载方向实际±EPS、阈值内负微增量、独立正递增ID。19个非法变体均拒绝：ID含0、kind=2、count=2.5、Hysteretic四点或两侧点数不相等、非零尾槽、trial_count=0、pinch/beta越界、delta越界、非near反方向返回、continuation反向、骨架刚度上升、非零计分应变落在折点、probe越包络、输出组件倒序、缺tangent、times非零、应力错误单位。预期来自公开定义，非生成器同源表。

最初exact-EPS副本误给负向加载程序正增量，SDK正确拒绝；已将副本更正为实际continuation方向并独立重验，最终诊断保留该原型更正说明。正式数据未改。

## 限制与复现

复现顺序为`inspect_all.py`、`check_source_bindings.py`、`check_sdk.py`，脚本只写本审计目录。未检查未提交probe即时响应（题目未输出），未构造完整反向循环求解器；未执行实际材料、候选编译、付费benchmark或CPU/内存/耗时实测。没有重新下载上游源码或核验镜像源码树，来源证书只按允许维护记录和实际输入/参考绑定审计。缺陷重放文件及最终Oracle工件未在本轮单独读取，已明确限定，当前实际数据和参考四输出独立检查通过。

存档说明：原始诊断与脚本在上述runs维护目录；本存档将原相对链接改为维护路径，不改变审阅结论和数值。
