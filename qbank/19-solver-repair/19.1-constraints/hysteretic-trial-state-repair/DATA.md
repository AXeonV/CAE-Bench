# 输入与输出

本题是一组相互独立的单轴材料程序。材料应变无量纲，应力与切线模量单位 Pa；`getEnergy()` 是已提交的应力—应变累计功密度，单位 Pa=J/m³。它不是总能量，也不是连续曲线积分或每次未提交试探的功。

## 声明与数组

`task` 为 `hysteretic-trial-state-repair`，`spatial_dimension` 为 1，`physics` 为 `{"model":"hysteretic-trial-state-v1","parameters":{}}`。`geometries`、`meshes` 为空对象，`conditions` 为空数组。位置唯一为 `programs`：`{"kind":"entities","ids":"program_ids"}`；`program_ids` 是 1..32 个唯一正整数的 int64 一维数组。`time_axes` 为 `{"instant":"times"}`，`times` 是 float64 数组 `[0]`，只是单次程序的存储索引。

以下输入都是 float64，形状 `(1,N,C)`；表中的标量 C=1。数量、单位、组件名称与公开扩展声明一致。每项使用 `location="programs"`、`time_axis="instant"`、`value_kind="point"`，标量 `kind="scalar"`，其余 `kind="components"`，`component_shape=[C]`；输入采样统一为 `{"space":"uniform","time":"constant","extrapolation":"forbid"}`。数量 count 与 material_kind 虽以 float64 存储，值必须是整数。

|数组|C / 组件|quantity|单位|含义|
|---|---|---|---|---|
|material_kind|1 / value|material_kind|1|0 为 Hysteretic，1 为 HystereticSM|
|positive_count, negative_count|各 1 / value|positive_point_count, negative_point_count|1|两侧有效骨架点数|
|positive_strain, negative_strain|各 7 / point_0..point_6|positive_envelope_strain, negative_envelope_strain|1|两侧有效点的有符号应变|
|positive_stress, negative_stress|各 7 / point_0..point_6|positive_envelope_stress, negative_envelope_stress|Pa|与应变配对的有符号应力|
|pinching|2 / pinch_x,pinch_y|pinching_parameters|1|材料 pinching 参数|
|beta|1 / value|unloading_exponent|1|卸载刚度指数|
|history_count|1 / value|history_step_count|1|初始提交步数|
|history|8 / step_0..step_7|committed_strain_history|1|初始提交应变序列|
|trial_count|1 / value|trial_step_count|1|未提交试探次数|
|trials|8 / step_0..step_7|uncommitted_strain_probes|1|未提交试探应变序列|
|return_delta|1 / value|return_strain_increment|1|相对已提交应变的返回增量|
|continuation_count|1 / value|continuation_step_count|1|继续提交步数|
|continuation|8 / step_0..step_7|continuation_strain_history|1|继续提交应变序列|
|rollback_probe|1 / value|rollback_trial_strain|1|显式回滚前的最后试探应变|

所有数组及声明须齐全且无额外字段。`array` 是该数组的名称。有效点/步使用前 count 项，剩余项严格为零。Hysteretic 两侧点数相同且为 2 或 3；HystereticSM 两侧分别为 2..7。每侧从原点出发，应变绝对值严格增加，范围 1e-4..0.1；应力绝对值严格增加，范围 1e3..1e9 Pa。正侧应变/应力为正，负侧为负。包含原点至第一点在内的各段刚度均为正且非增；只允许相邻斜率最大值乘 1e-12 的浮点舍入偏差。应力在有效点之间线性插值。两侧可不对称。pinch_x、pinch_y 为 .05..1，beta 为 0..1；损伤、包络退化和 rotY 参数固定为零，未提供限值状态。

## 操作与有效范围

每条程序使用全新材料、应变率为零。初始应变/应力/已提交功密度为零，初始切线为正侧第一段斜率。history_count 为 0..8，trial_count 与 continuation_count 为 1..8。全部操作应变均在两侧最后有效骨架应变之间。

1. 按 history 顺序执行 `setTrialStrain`、`commitState`，每一步都提交。记录 committed。
2. 按 trials 顺序执行 `setTrialStrain`，均不提交，也不回滚。
3. 以步骤 1 的已提交应变 εc 计算 float64 目标 εr=εc+return_delta，调用 `setTrialStrain(εr)`。记录 returned。
4. 调用 `commitState`。记录 accepted。
5. 按 continuation 顺序执行 `setTrialStrain`、`commitState`，每一步都提交。记录 continued。
6. 调用 `setTrialStrain(rollback_probe)`，随后 `revertToLastCommit`。记录 rolled_back。
7. 调用 `revertToStart`。记录 reset。

history 和 continuation 沿同一非零方向推进，方向由 continuation 首项的符号确定。history 非空时各项同号，其应变绝对值从零开始每步增加至少 1e-7。`|return_delta|≤1e-8`。令实际 float64 差 Δ=εr−εc，机器常数 EPS=2^-52。若 `|Δ|<EPS`，步骤 3 应恢复完整已提交状态，包括应变、应力、切线及内部提交状态；目标 εr 的微小差不保留。否则目标应沿同方向推进，按正常材料求值处理。continuation 各项沿同一方向，首项从实际返回应变起、后续从上一项起，绝对值每步增加至少 1e-7。

所有非 reset 计分状态的非零应变，与任一正负侧非零骨架点的应变距离均至少为 1e-7。初始历史的中间点及未提交试探仍可跨越或落在折点；这些中间点的切线不计分。因此不要求选取折点处哪一侧导数。零初始态与 reset 切线为正侧第一段斜率；非零微小应变属于其符号对应侧。

初始提交历史与继续提交沿单向骨架加载。未提交试探可跨零或跨段，允许改变试探响应，但不得改变已经提交的历史。回滚恢复最近一次完整提交态。重置恢复初始零态。本题不评价完整已提交反向循环的损伤、退化或结构求解。

## 输出

输出 `strain`、`stress`、`tangent`、`work_density`，形状均为 `(1,N,6)`。六个组件严格为 `committed,returned,accepted,continued,rolled_back,reset`，顺序与上述操作对应。数量分别为 `strain`、`stress`、`tangent_modulus`、`committed_work_density`，单位分别为 `1,Pa,Pa,Pa`，其余位置和轴信息与输入一致，输出无 sampling。

每个检查点直接观测实际材料的 `getStrain/getStress/getTangent/getEnergy`。未提交状态的 getEnergy 仍为最近一次已提交功密度。接受正常非零增量后，离散累计功密度按 Wnew=Wold+0.5(σold+σnew)(εnew−εold) 更新；跨过折点也使用该离散步进公式。阈值内返回及随后接受保持原功密度，显式回滚保持最近提交功密度，reset 为零。结果写出方式遵循 CONTRACT。
