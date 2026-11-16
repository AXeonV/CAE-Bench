# Case 级判题

题目 instruction.md、DATA.md 和通用 CONTRACT.md 构成完整考生契约。实际判题配置位于每例 `reference/grading.json`，属于本例数据；不存在题目级运行时评分配置。作者可在 `author/grading-template.json` 保存制数模板，但运行器不读取模板。

`atol`、`rtol` 仍分别表示绝对与相对容差，适用指标必须在数值规则中显式给出。它们不是独立的评分入口；CLI 不接受单独的容差参数，也不提供隐式默认容差。

## 执行与材料边界

先用 `prepare_case(problem, grading_path)` 预检配置、参考及观测，再完整校验提交并执行评价。CLI、公开样例和 Harbor 共用 `caeoj.case_grading`；Harbor 的独立 worker 有单独评价时限，超时属于基础设施错误。

```sh
python -m caeoj grade --input problem.json --output result.h5 --grading reference/grading.json
```

隐藏例的配置和参考只进入 verifier；公开包提供随机格式样例及必要工具，随机样例不附数值参考或判分材料。考生无需阅读机器配置补题意。观察什么、采用何种重建、误差和通过含义必须由题面／DATA完整说明；配置不能增加隐藏要求。

## 配置与扩展

外层固定 `version: 1`，`checks` 为非空数组，每项有唯一 `id` 和可信 `evaluator` 标识；未声明 `scoring` 时全部评价项通过才得到本例1分，否则0分（第0章继续使用此二元规则）。未知标识、未知参数、重复键／ID、缺失资产和非有限配置均拒绝。

最小整场配置如下（阈值仅示范，不是正式校准值）：

```json
{
  "version": 1,
  "checks": [{
    "id": "outputs",
    "evaluator": "direct_outputs",
    "reference": "reference.h5",
    "policy": {"version": 2, "default": {
      "metric": "pointwise", "time": "per_time", "components": "per_component",
      "atol": 0.01, "rtol": 0
    }}
  }]
}
```

标准 `direct_outputs` 项包含 `id`、`evaluator`、`reference`（相对配置目录的HDF5文件）和 `policy`。参考按完整输出契约校验，policy采用下述当前数值策略形式，所有提交字段均比较。整数／布尔值精确一致。

`field.sample_points` 项包含 `id`、`evaluator`、`source_output`、`components`、`observations`、`reference` 和 `rule`。它不改变提交契约：即使只评一个速度分量，考生仍须提交本题全部输出。

- `source_output` 是实际 outputs 逻辑名；仅支持二维一阶三角形网格的float64节点点值场。
- `components` 为非空、无重复、按原输出顺序排列的标签子集。
- `observations` 恰含 `file`、`points`、`ids`、`times`、`cells`，后四者为同一个HDF5中的key。points为float64[N,2]，ids为唯一int64[N]，times为有限严格递增float64[T]，cells为int64[N]包含三角形tag。
- 包含单元由作者预计算；共享实现检查单元、测点位置及节点覆盖，再按P1重建。节点按tag映射，不按行号推断。仅允许请求提交已有的精确时刻，不做时间插值。三角形重心坐标允许64倍机器epsilon的边界舍入误差，随后夹到[0,1]并归一化；其他域外点拒绝，退化单元拒绝。
- `reference` 恰含 `file`、`array`、`ids`、`times`、`unit`。参考是float64[T,N,K]，单位与源场一致，IDs及时间轴与观测严格一致。仅提供这些稀疏值即可形成完整参考。
- `rule` 使用下述数值条件树；首期点取样采用等采样权重，不接受weight_field或输入参数形式的偏置。显式数值reference_offset仍按相同含义计算。

路径全部相对配置所在目录，不允许越界、链接、外部载荷或下载。所有读取的HDF5数组必须被绑定，不能用额外数组藏另一套评价条件。

核心提供上述标识。可信已安装provider可在所选extension运行描述的 `evaluators` 中声明 `标识: 模块:prepare函数`；HF不指定导入目标。prepare接口为 `(problem, check, assets) -> evaluate`，使用assets绑定并校验全部参考；evaluate接收已通过完整契约检查的结果数组，返回含bool passed的诊断。共享数值比较使用 `evaluate_observation`，不制造临时problem。标识不能覆盖其他实现，公开装配核对声明函数所在文件闭包。扩展代码及依赖由维护者安装，不能由case动态加载。

提取算法不得读取参考值来调整结果。自定义实现必须有公开数学定义、适用性检查和独立测试，不能自行放宽规则或补物理。

## 连续 NRMSE 评分

当前源码第1、2章的连续评分模板在每例配置顶层显式声明：

```json
"scoring": {"metric": "rms_nrmse", "full_credit": 0.05, "zero_credit": 0.10}
```

各浮点输出按物理量、每个分量、每个输出时刻分别计算空间加权 NRMSE：`√(Σw(result−reference)²/Σw) / max(√(Σw(reference−reference_offset)²/Σw), scale_floor)`。空间权重和尺度下限按本题公开规则显式配置；没有权重字段时采用等采样权重。原始误差不跨物理量、分量或时刻拼接；先分别归一化，再聚合 NRMSE。

本例 `E` 为所有评价项、输出字段、分量、时刻的 NRMSE 等权均方根 `E=√(Σ_j e_j²/M)`，其中 `M` 为 NRMSE 组数；不先按物理量分层平均，也不按空间点数给组加权。`E≤0.05` 得1分，`E≥0.10` 得0分；中间得 `(0.10−E)/0.05`。题目 reward 为全部正式 case 得分的算术平均，运行失败和未通过输出契约的 case 计0分；基础设施错误不生成正式成绩。报告 `total_nrmse` 和逐组诊断，`accepted` 表示满分、`partial_credit` 表示严格介于0和1、`wrong_answer` 表示数值零分。浮点数按实际计算结果比较，不进行隐式四舍五入。

此模式仅允许逐时刻、逐分量的 `nrmse` 叶子及其 `all` 组合，叶子 `limit` 必须等于 `full_credit`；不允许通过 `any`、合并分量或合并时刻改变规定的聚合分组。整数、布尔输出仍精确比较，任一不符整例0分。归一化扩展先按题面固定偏置及允许的压力常数基准变换，再应用同一 NRMSE；候选变换溢出计0分，参考变换溢出归基础设施错误。

Harbor 报告 `score` 为各例得分之和，`passed_cases` 仅统计满分例数，`partial_cases` 统计部分得分例数；`reward=score/total_cases`。部分完成报告保留正式总例数为分母，不将已完成例归一成满分。CLI 退出0表示满分，退出1包含部分得分与候选零分；须读取 JSON `score` 获取连续分值，不能把退出1一律替换为零分。

逐组及评价项的 `passed` 仍表示各组是否全部达到满分阈值，仅作诊断；连续模式的 case 状态由聚合分数决定，因此个别组未通过时 case 仍可能满分。任一组 NRMSE 溢出时聚合误差为 `overflow`，整例0分。

旧 `max_nrmse` 配置不自动解释为新规则，新引擎会在预检时拒绝。迁移已有数据时，仅将连续 case 配置的 `scoring.metric` 改为 `rms_nrmse`，保留其参考、尺度、权重、偏置、评价项和阈值；重新打包数据池并更新选样摘要，再重建公开材料和 verifier。不得直接修改已冻结发行包或沿用旧成绩解释新规则。作者模板更新不代表 HF 数据及既有发行包已迁移；均方根聚合的5%／10%阈值沿用原设计，尚不代表重新校准。

## 证据与错误

报告按case记录grading、配置及参考资产、输入资产、选中运行绑定和评价实现闭包摘要，以及组合evaluation_sha256；评价项记录分量与观测诊断。预检后文件变化拒绝，Harbor核对worker证据与预检一致。

坏输入返回input_error；坏配置、参考、提取实现或评价预算返回evaluation_error，score为null，CLI退出2。非法候选输出返回invalid_output，score为0；二元模式数值不通过为wrong_answer；连续模式按上节区分部分得分。满分为accepted。CLI对应非满分／满分退出1／0。结构校验不能被OR或稀疏评价绕过。

文件摘要完整、参考覆盖完整、数值可信和能力覆盖是不同证据。这里只验证前两者及确定的计算过程，不认证参考精度或运行资源校准。

## 数值策略

下面的version 1／2是内层数值规则的两种当前绑定方式，不是外层case配置。

## 配置与逻辑

```json
{
  "version": 1,
  "fields": {
    "velocity": {
      "all": [
        {
          "metric": "pointwise",
          "time": "per_time",
          "components": "per_component",
          "atol": 0.1,
          "rtol": 0.2
        },
        {
          "any": [
            {
              "metric": "nrmse",
              "time": "per_time",
              "components": "per_component",
              "scale_floor": 0.1,
              "limit": 0.05
            },
            {
              "metric": "violation_fraction",
              "time": "per_time",
              "components": "joint",
              "count": "spatial_points",
              "atol": 0.01,
              "rtol": 0.02,
              "limit": 0.05
            }
          ]
        }
      ]
    }
  }
}
```

以上是仅输出速度的配置示例，数值不代表任何题目的正式校准阈值。表示全部值满足较宽的逐值容差，且满足以下两者之一：全部时刻与分量 NRMSE 达标，或者每个时刻至少 95% 的空间点满足较严格的容差。

version 1 的 `fields` 键必须恰好覆盖 `problem.json.outputs` 的全部 float64 输出，用逻辑字段名关联 HDF5 数组。各字段必须同时通过。整数与布尔输出始终精确比较，不在此配置中声明。version 2 按下节规则逐例绑定，数值指标及通过含义相同。

`all` 表示 AND，`any` 表示 OR，可嵌套至 32 层，子节点不能为空。叶节点是指标。未知属性、指标、负阈值、非有限数值、漏配或多配字段均是配置错误，不会变成选手的答案错误。版本为 1 或 2；JSON 重复键也会被拒绝。不执行自定义表达式，不提供 NOT 或跨字段 OR。

## 按 quantity 逐例绑定（version 2）

输出逻辑字段名、HDF5 array key 和 quantity 可以不同。字段名或可选输出随算例变化时，使用公开模板：

```json
{
  "version": 2,
  "quantities": {
    "pressure": {
      "unit": "Pa",
      "rule": {
        "metric": "pointwise", "time": "per_time", "components": "per_component",
        "atol": 1, "rtol": 0.03,
        "reference_offset": {"parameter": "pressure_reference"}
      }
    }
  }
}
```

本例仅演示配置形式，不给其他题目规定容差。遍历本例实际 `outputs`，根据每个 float64 输出的 quantity 找规则，精确检查 unit，再绑定其逻辑名和 array；同 quantity 的多个输出分别检查。未请求的 quantity 不参与，不要求可选量同时出现；未声明规则的实际 quantity 或单位不一致是配置／数据错误，须在运行候选程序前发现。不能用 quantity 猜测或重命名数组。

version 2 可显式提供 `default` 条件树，作为未匹配 quantity 的 float64 规则；该分支没有单位限制，适用于第 0 章任意标签的回传测试。第二章不提供 default，未知 quantity 必须报错。`fields` 不能与 version 2 并用，quantities/default 不能与 version 1 并用。

version 2 的 `reference_offset` 可为有限数值，或 `{"parameter":"pressure_reference"}`：仅从本例 `physics.parameters.pressure_reference` 的带单位有限标量绑定，单位必须与该输出完全一致。不接受 bool、表达式、参考／候选答案拟合值或隐含压力参数；缺失、错误类型／单位属于基础设施错误。其他物理 `reference_pressure` 不会自动启用评分偏置。未请求的量不绑定其参数。

每个 case 的 quantity 策略绑定本 case 的输出声明，产生数值型 version 1 规则交给同一评分引擎。正式 CLI、样例预检和私有 verifier 读取该 case 的 `reference/grading.json`，报告通过 `grading_sha256` 和 `evaluation_sha256` 绑定策略、资产和运行代码。`author/grading-template.json` 仅供制数工具生成 case 策略，运行时不读取；不能按第一个样例冻结其他 case 的字段集合。

## 指标定义

令误差 `e = result − reference`，局部容差 `τ = atol + rtol × |reference − reference_offset|`，其中 reference_offset 默认为0。

| metric | value | 必需参数 |
|---|---|---|
| `pointwise` | 全部值满足 `|e| ≤ τ` | atol、rtol |
| `rmse` | √加权平均(e²) | limit |
| `nrmse` | RMSE / max(参考减偏置后的 RMS, scale_floor) | limit、scale_floor > 0 |
| `max_abs` | max \|e\| | limit |
| `max_scaled` | max(\|e\| / τ) | limit、atol、rtol |
| `violation_fraction` | 不满足局部容差的数量 / 总数量 | limit ∈ [0,1]、atol、rtol |

所有比较采用 `≤`。RMSE、最大绝对误差、atol 和 scale_floor 使用对应字段单位，rtol、NRMSE、缩放误差及比例无量纲；不转换单位，不将密度、压力和速度原始数值混在一起平均。

`pointwise`、`violation_fraction`、`max_scaled`、`nrmse` 的叶节点允许可选 `reference_offset`，数值规则中必须是有限的带符号数值（禁止bool/字符串），单位与输出字段一致；其他指标和逻辑节点禁止此键。version 1 只接受公开冻结的数值；version 2 还允许上述显式参数绑定，解析后仍为同样的数值规则。不改写物理输入、参考或提交输出；误差始终直接计算 `result-reference`，在相对容差尺度或 NRMSE 的分母参考 RMS 中使用 `reference-reference_offset`。RMSE 分子、最大绝对误差及报告的最大绝对误差位置不受它影响。同一树的不同叶可以使用不同公开偏置，统计缓存按偏置区分。

例如绝对压力输出 `reference=100010 Pa`、`result=100012 Pa`，公开 `reference_offset=100000 Pa`、atol=0.5 Pa、rtol=0.1，则允许误差为1.5 Pa，实际误差2 Pa，判失败；省略偏置时允许误差10001.5 Pa。偏置并非允许改变压力基准：两份HDF5仍存绝对静压。以每例输入中的 pressure_reference 固定尺度时，可用 version 2 显式绑定；version 1 仍须逐例公开对应的数值策略。没有真实算例时只能完成模板及临时工具验证，不能据此宣称数据绑定或正式评测已发布。

省略或显式给 0 时，公式等价于不减背景值的相对误差。非零偏置的计算以浮点尾数/指数处理可能溢出的差与容差乘积，避免把有限输入中的巨大相对尺度错误当作无条件通过，也避免先减去两个背景值后再相减造成额外消减。

`max_scaled` 的 τ 为零时，零误差记为 0，非零误差记为 ∞。报告将非有限的指标值写为字符串 `overflow`，不输出非法 JSON 的 Infinity。有限数组产生非常大的误差属于答案错误；非有限的提交数组先由结构校验拒绝。

`violation_fraction.count` 默认为 `scalar_values`，按单个标量数值计数。`spatial_points` 必须与 `components: joint` 同用：一个点的全部分量满足局部容差，才将该点算作通过。时间合并时，每个 `(时刻, 空间点)` 是一项；不能理解为要求某个空间点在全部时刻都通过。比例始终按数量计算，不按体积或权重计算。

## 聚合范围与权重

每个叶节点必须显式写 `time` 与 `components`。

- `time: per_time`：每个输出时刻分别计算，全部时刻须满足本叶条件。
- `time: pooled`：合并所有输出时刻，按等采样时刻权重计算，不是时间积分。
- `components: per_component`：每个分量分别计算，全部分量须满足本叶条件。
- `components: joint`：将同一字段的分量合并计算。联合 RMSE 为全部标量分量的均方根，不是空间向量模长的均方根。

各叶先在全部范围完成判断，然后求值条件树。例如 `A OR B` 要求 A 在全部范围通过，或 B 在全部范围通过；不是允许每个时刻随意选择 A 或 B。所有输出时刻参与计算，包括初始时刻。

默认等空间采样权重。可选 `weight_field` 引用输入中已经声明的 float64 标量字段，必须与输出 location 相同、shape 为 `[1,N,1]`，每项有限且严格为正。按 `√(Σ w e² / Σ w)` 计算 RMS；同一权重应用于每个分量和时刻。单位任意但内部一致，整体缩放权重不改变结果。权重只影响 RMSE、参考 RMS 和 NRMSE，不影响最大值或超限比例。不会自动从 Gmsh 网格猜测积分权重。
