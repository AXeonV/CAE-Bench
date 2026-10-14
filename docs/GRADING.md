# 数值评分策略

`grading.json` 是公开、可追踪的数值评分配置。CLI、公开样例和 Harbor 使用同一套 `caeoj.grading` 实现；配置结构见 `src/caeoj/grading.schema.json`。运行资源仍由 `judge-config.json` 与 `harbor/task.toml` 定义，不进入 `problem.json` 数据协议。

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

`fields` 的键必须恰好覆盖 `problem.json.outputs` 的全部 float64 输出，用逻辑字段名关联 HDF5 数组。各字段必须同时通过。整数与布尔输出始终精确比较，不在此配置中声明。

`all` 表示 AND，`any` 表示 OR，可嵌套至 32 层，子节点不能为空。叶节点是指标。未知属性、指标、负阈值、非有限数值、漏配或多配字段均是配置错误，不会变成选手的答案错误。版本必须为整数 1；JSON 重复键也会被拒绝。不执行自定义表达式，不提供 NOT 或跨字段 OR。

## 指标定义

令误差 `e = result − reference`，局部容差 `τ = atol + rtol × |reference|`。

| metric | value | 必需参数 |
|---|---|---|
| `pointwise` | 全部值满足 `|e| ≤ τ` | atol、rtol |
| `rmse` | √加权平均(e²) | limit |
| `nrmse` | RMSE / max(参考 RMS, scale_floor) | limit、scale_floor > 0 |
| `max_abs` | max \|e\| | limit |
| `max_scaled` | max(\|e\| / τ) | limit、atol、rtol |
| `violation_fraction` | 不满足局部容差的数量 / 总数量 | limit ∈ [0,1]、atol、rtol |

所有比较采用 `≤`。RMSE、最大绝对误差、atol 和 scale_floor 使用对应字段单位，rtol、NRMSE、缩放误差及比例无量纲；不转换单位，不将密度、压力和速度原始数值混在一起平均。

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

## 接口与兼容

```bash
python -m caeoj grade \
  --input problem.json --output result.h5 --reference reference.h5 \
  --grading grading.json
```

Python 接口为 `grade_arrays(problem, result, reference, policy=policy)` 和 `grade_files(input, output, reference, policy=policy)`，可用 `load_policy(path)` 读取和校验配置。

未指定策略时，原有 `atol/rtol` 接口、默认容差、逐值判定及诊断字段保持不变。显式策略与显式 atol/rtol 不能同时提供。作者目录若添加 `grading.json`，应移除 `judge-config.json` 中的 atol/rtol；运行时限与输出大小等参数保留。否则沿用旧配置。

发布器始终导出公开 `grading.json` 与从该策略生成的 `GRADING.md`，旧任务会从既有容差派生等价策略。Harbor 组装会校验 ZIP 内策略与实际评分策略的哈希一致，过期发布包必须重发。公开包包含指标实现、配置 Schema 和样例判分命令，不包含隐藏输入、参考轨迹或审核信息。现有 PDEBench 的阈值不因本次重构自动改变。

## 报告和失败分类

结构校验不允许被 OR 绕过，IDs、时间轴、shape、dtype 与有限值要求保持严格。输入或参考错误返回 score=null；配置错误在开始求解前报告。运行超时、程序报错和缺失输出由执行器记录，不尝试数值评分。

新策略报告包含策略版本、规范化 JSON 的 SHA-256、各字段条件树、全部叶节点的各范围指标值与通过情况，及最大绝对误差所在的时间、ID 和扁平分量索引。OR 的未决定分支也会报告，便于解释。整数/布尔字段沿用精确比较报告。实际数组不会被改写或纠正。

Harbor 每例完成后写该例 `report.json`，并原子更新汇总报告。汇总包含 completed_cases、complete、每例求解墙钟耗时 elapsed_seconds（不含判分计算与输入复制）。中间 reward 为已通过数除以计划总例数；只有全部完成后才写 reward.txt。基础设施错误仍会中止评测，不能伪装为答案错误。

指标采用分块统计与尺度归一化，避免为每个条件复制完整三维数组或直接计算巨大浮点数的平方；相同范围和容差的指标复用统计量。
