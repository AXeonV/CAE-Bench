# 独立实际数据审计：开路电势滞回热源修复

结论：**通过**。全部14个正式case共84个状态、2个公开sample共12个重复状态，输入、完整参考、公开输出及评分绑定均符合公开定义。五项热输出按公开公式独立重算通过；三对闭环的分支功与热账本相符。无本轮未决缺陷、缺失必需资产或未读数组。

## 范围、版本和读取边界

按caeoj-data-review技能，只读审计。解释依据仅为instruction.md、DATA.md、docs/CONTRACT.md。允许的全量cases/reference/samples、data-manifest和实际装配回执均已检查。另审阅source.json、cases.json、reference-replay.json、final-reference-validation.json、loop-energy-check.json，定位来源及参考生产者；未用这些维护材料补充题意。

为核实input_sha256的含义，协调方后续明确许可读取author/replay.py和public/run_case.py的serialize函数。实际一次文件读取意外还显示了同一中性适配器的run包装器；未运行该包装器，也未读取driver或solver源码。只独立重建中性JSON序列化payload用于摘要比较。author/independent.py实际不存在，协调方确认此白名单名称为误述；本轮数学预期直接来自公开公式，没有用作者generate.py中的热公式或独立检查结果作预期。仅对generate.py做过定位摘要关键字的搜索。

完整实际材料路径与SHA256见`runs/data-review/repair22-hysteresis/evidence.json`，计79文件：3解释文件、manifest与回执、14×4正式输入/参考文件、2×5样例文件、5来源证据文件、上述2定位文件及仅搜索定位关键字的generate.py。源码归档、求解源码、driver未读，正式数据和实现未改。

| 解释文件 | SHA256 |
|---|---|
| instruction.md | ca86fb7865ea5360cbf8d2ca7a2b6c1d4bf0db816947a5ad6dc096797aa25600 |
| DATA.md | 2e77b479eb5109d206b7ce949ce7a5b8a2b5834bc829d04facef74ca5d573028 |
| docs/CONTRACT.md | 130d4416fd533812493780c8bc6afbc0a158de6800b59bbec14a852f3cf1c063 |

selection SHA256为`94568587c81c5b81f46d6c93343117a021f8238c5f711af6461ef7dd8b690d41`，装配固定revision为`c2da4f591c0f5764226c9f0d0f12e70fbf13b89a`。逐个复算原始case描述SHA、case ID、输入/参考complete、载荷大小及SHA、回执文件绑定均一致。官方`data verify --strict`返回valid=true、errors=[]；明确列出sample01/02与正式case01/02共享身份。inventory发现16入口、gaps=0；其not_evaluated不是本审计结论。

## 字段、数组和条件全量覆盖

从最终DATA手写18输入字段及5输出的对照表，独立比较每个JSON字段的array、quantity、unit、dtype、kind、component_shape、components、location、time_axis、value_kind及sampling。所有实际入口：task/model正确、spatial_dimension=1、geometries/meshes={}、conditions=[]；没有未定义边界分支、连续插值、附件或跨case依赖。

| 对照对象 | 公开依据 | 检查结果 |
|---|---|---|
| physics.parameters的phases_n/phases_p/mask_n/mask_p/pairs | DATA“元数据和形状” | 恰5项、unit=1、整数；相数1/2、mask在对应位域内、pairs在1–32 |
| locations.states、state_ids、instant/times | DATA元数据、CONTRACT实体和时间节 | 非负int64严格递增，实际每例N=6；times为float64[0]，输出轴逐值/类型复制 |
| current/eta/ocp/equilibrium/entropy的n/p版本 | DATA输入表及single条件 | 全部必需、[1,6,P]、有限float64；相顺序和单位一致，全部范围通过，single相|U−Ueq|≤1e-12 |
| temperature | DATA输入表 | [1,6,1]，K，250–400；在公开热公式中同温度用于各相 |
| length_n/p/s/cn/cp、area、volume | DATA输入表、instruction几何积分 | 全部[1,6,1]，单位/范围完整；V_cell独立于叠层体积，没有默认替换 |
| 五项输出 | DATA输出表 | [1,6,1]、scalar/value，无sampling；所需key完整，逐字段quantity/unit及固定轴一致 |
| HDF5物理结构 | CONTRACT | 仅根dataset，无属性/子组/软外链/别名/外存储/虚拟dataset，允许过滤器；全部dataset完整读取 |

公开数据无缺省条件，未把任何缺字段解释为零。完整输入包含18场、ID和times共20个dataset；输出包含5场、ID和times共7个dataset。没有以展平缓冲区、少轴或非float64替换数组。

| 正式case | Pn/Pp | mask_n/mask_p | pairs | 实际区分 |
|---|---|---|---:|---|
| 01-both-hysteretic-public | 1/1 | 1/1 | 1 | 两极滞回 |
| 02-no-hysteresis-public | 1/1 | 0/0 | 1 | 两极single，关闭滞回 |
| 03-negative-only | 1/1 | 1/0 | 2 | 仅负极滞回 |
| 04-positive-only | 1/1 | 0/1 | 3 | 仅正极滞回 |
| 05-two-negative-phases | 2/1 | 3/1 | 2 | 负极双相 |
| 06-two-positive-phases | 1/2 | 1/3 | 4 | 正极双相 |
| 07-mixed-phase-switches | 2/2 | 1/2 | 3 | 两极混合相开关 |
| 08-all-phases | 2/2 | 3/3 | 2 | 四活性相 |
| 09-zero-current | 2/2 | 3/3 | 1 | J=0，所有热为0 |
| 10-zero-gap | 2/1 | 3/1 | 2 | 滞回选项开而U=Ueq |
| 11-isolated-hysteresis | 1/2 | 1/3 | 1 | η和熵项为0，仅滞回热 |
| 12-negative-instant | 2/2 | 3/1 | 2 | 含负瞬时贡献，不能裁剪 |
| 13-loop-states | 1/1 | 1/1 | 2 | 三对反向电流局部状态 |
| 14-geometry-scales | 2/2 | 3/3 | 32 | 并联上界及独立几何尺度 |

每case均6状态；sample01/02分别完整复用正式01/02。实际V_cell/(A×五层总厚度)范围约0.002872–9.561752，足以区分实际体积和叠层体积。case02有1个、case12有9个负输出分量，结构检查与数值核查均保留负值。

## 五项热输出和评分的独立核查

未运行求解器。逐极、逐相从输入独立计算反应ΣJη、可逆ΣJT·entropy、滞回ΣJ(U−Ueq)，single项严格置零；不加活性体积分数、不额外改电流符号、不裁剪。再按公开Ln/Lp、pairs、A、V_cell计算三项几何观测。逐状态及完整输出比较如下：

| 输出 | 全部正式及样例最大绝对误差 | 公开atol |
|---|---:|---:|
| heat_negative | 3.6379788071e-12 W/m³ | 1e-6 W/m³ |
| heat_positive | 3.6379788071e-12 W/m³ | 1e-6 W/m³ |
| area_heat | 0 W/m² | 1e-8 W/m² |
| cell_heat | 2.2204460493e-16 W | 1e-9 W |
| volume_heat | 1.4551915228e-11 W/m³ | 1e-6 W/m³ |

全部14份正式和2份样例grading.json精确对应direct_outputs、reference.h5、3个quantity的单位、逐时刻逐分量pointwise规则、rtol=1e-8及上述atol。五输出没有省略其中一极或只比较总功率。2份公开output/result.h5与各自参考全数组相同；正式case没有承诺独立output文件。未用参考自判分作为数值正确证据。

## 三对闭环热账本

仅作维护材料中的独立输入反例验证，不向题目增加轨迹或DFN要求。由实际case13输入确认每对状态(0,1)、(2,3)、(4,5)：各极J严格反向、Ueq相同、几何和温度固定、η=entropy=0。各态假设持续1秒，逐极电荷收支为0，平衡电势功相消。独立分支功为Σ_side pairs·A·L_side·Σ_phase[J_iU_i+J_jU_j]。

| 状态对 | 分支功J | 参考cell_heat积分J | 绝对差J |
|---|---:|---:|---:|
| 0/1 | 0.28753123735541103 | 0.2875312373554106 | 4.441e-16 |
| 2/3 | 0.28753123735541103 | 0.2875312373554106 | 4.441e-16 |
| 4/5 | 0.28753123735541103 | 0.2875312373554106 | 4.441e-16 |

均与loop-energy-check.json约0.2875312373554113 J的记录在浮点求和舍入内一致；该记录不是公开热定义的替代。实际为三个相同工况复制对，未把它们当成三个不同电池轨迹来源。

## 生产者和来源绑定

source.json固定PyBaMM issue3867、PR4893、基线commit `273ccd4ec832efd9d5d783aa51a4421a4d8f70e4`、修复commit `f04a1f8ed421fc4653071eaa089be9b85b0855de`及归档/树摘要；它声明仅移植真实base_thermal.py。cases.json逐例参数、6状态和“作者适配局部状态、非电池实验”描述与实际输入相符，没有冒称独立电池试验或DFN轨迹。

reference-replay.json声明生产者为真实固定PyBaMM热子模型，修复覆盖SHA `316ba29de5564d39d286b28e4810818a59bd955737f7759fce5ff1c9b51cc53f`与source记录相符。final-reference-validation.json记录固定镜像、无源码overlay。两份记录各14case的score和全部热核查均通过，全部output_sha256与现有reference.h5完全匹配。

两份记录的input_sha256是**传入driver的UTF-8 JSON payload**，不是raw input.h5；协调方已在证据顶层补input_sha256_definition标签。按获准的serialize格式从当前problem.json与完整输入数组独立重建payload，全部28个摘要绑定一致。raw HDF5 SHA另由固定清单、回执及本审计文件清单独立绑定；本报告没有冒称原回放已单列raw摘要。实际回放没有在本轮重跑，外部issue/PR、归档内容及镜像安装树未重新下载核验，因此以上来源结论是现有生产记录及数据绑定审计，区别于本轮亲自执行真实库。

## 正式SDK与独立合法/非法变体

仅从公开ZIP提取src的caeoj、caeoj_bundle、caeoj_task_ext中性运行器和题目契约扩展，不读或提取求解源码/driver。使用项目.venv的依赖，新子进程设ZIP的src为优先PYTHONPATH，避免本地已缓存任务装配。脚本`runs/data-review/repair22-hysteresis/check_sdk.py`及`runs/data-review/repair22-hysteresis/sdk-evidence.json`记录34次实际检查（16输入、16参考、2公开输出），全部通过。

从最终DATA独立选择6合法变体均接受：ID含0、pairs=32、T=400、V_cell=1e-10独立取值、负J=−1e7、single相Ueq与U差5e-13。17非法变体均拒绝：single差1e-9、相数3、mask越位或负、pairs=0或2.0非整数、参数错误单位、T低于250、J越界、U低于−2、entropy越界、隔膜厚度0、体积0、负ID、额外输出key、单相错误分量标签、非空conditions。预期来自公开定义，不取自生成器。

## 限制

无未检查数据数组，无材料缺口。本轮不改题、不生成参考、不运行driver或solver，不做付费benchmark。未重跑真实库、构建或资源限额；没有把维护记录中的约2秒执行历史当成本轮资源验证。合法/非法fixture不是额外正式测试case，也不证明所有极端参数组合的数值表现。所有实际五热输出及本题声明条件已独立核对，本轮数据审计通过。

存档说明：本报告引用的原始诊断和检查脚本保留在上述runs目录，不随题目公开包发布；本存档将其原相对链接改为完整维护路径，审阅结论与数值不变。
