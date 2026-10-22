# 输入与输出

本题采用通用 CONTRACT 的 JSON/HDF5 规则。`problem.json` 的相对引用以该文件所在目录为基准。所有数组是根组 dataset，SI 单位，坐标/向量均在同一个全局笛卡尔系中，分量顺序 x、y、z。驱动将输入转换为真实 Chrono 系统；考生提交源码，不自行编写文件读写入口。

## 清单与对象

固定 `task: "constrained-assembly-repair"`，`spatial_dimension: 3`，`geometries: {}`，`meshes: {}`，`conditions: []`。`data_file` 指向输入 HDF5。`physics.model` 为 `constrained-assembly-v1`。

`physics.parameters` 必须包含 `action`、`gravity_x`、`gravity_y`、`gravity_z` 四个常量。每个常量均采用 `{"value": 数值, "unit": 单位}`：`action` 的单位为 `1`，取 1（位置装配）、2（速度装配）或 4（加速度装配）；重力各分量单位为 `m/s^2`。重力是对所有活动体的加速度，另给的外力不含重力。

`time_axes` 仅含 `state: "times"`，输入 `times` 为 `float64[1]`，唯一元素为 0。这是一个瞬时状态，不是积分起点或输出时间序列。

`locations.bodies` 为 `{"kind":"entities", "ids":"body_ids"}`。`body_ids` 是严格递增、非负、唯一的 `int64[N]`，不要求连续。含固定体及活动体。1 ≤ N ≤ 16，至少一个活动体。

有约束时，`locations.links` 为 `{"kind":"entities", "ids":"link_ids"}`，`link_ids` 是严格递增、非负、唯一的 `int64[M]`，1 ≤ M ≤ 24。无约束时不声明此 location、两个约束输入场及反力输出，不使用空 IDs 数组。一个约束连接两个不同物体，端点不能同时固定；不含冗余约束。

## 输入场

`fields` 按下表使用固定对象名及 HDF5 key。各场均引用 `time_axis: "state"`，`value_kind: "point"`，采样声明固定为 `{"space":"uniform","time":"constant","extrapolation":"forbid"}`；这里每个离散实体仅有一个值，不进行空间插值。`component_shape` 为表中 C，标量的 `kind` 为 `scalar`，三分量向量为 `vector`，端点对为 `components`。向量 `components` 为 `["x","y","z"]`，端点对为 `["first","second"]`，标量为 `["value"]`。

| 对象名 / array | location | dtype | C | unit | quantity / 含义 |
|---|---|---|---|---|---|
| `mass` | bodies | float64 | [1] | kg | mass，质量；固定体也给出正值，但不参加惯性求解 |
| `fixed` | bodies | bool | [1] | 1 | fixed，true 为固定体 |
| `position` | bodies | float64 | [3] | m | position，质心全局位置 |
| `velocity` | bodies | float64 | [3] | m/s | velocity，质心全局速度 |
| `force` | bodies | float64 | [3] | N | force，施加于质心的外力，不含重力和约束力 |
| `endpoints` | links | int64 | [2] | 1 | endpoints，按 first/second 顺序给出 body_ids 的实际值，不是行号 |
| `length` | links | float64 | [1] | m | length，两个端点质心距离的固定目标值 |

实际 shape 为 `[1,N,C]` 或 `[1,M,C]`，C 指分量数。每行对应该 location 的 IDs 行，不能按 ID 直接下标。固定体输入速度及外力均为零。所有值有限；质量 0.2–5 kg，长度 0.2–5 m，各坐标绝对值不超过 20 m，各速度分量绝对值不超过 10 m/s，各外力分量绝对值不超过 50 N，重力模不超过 20 m/s²。

## 装配模式与输入保证

### action = 4：瞬时加速度与约束力

初始位置满足每条距离约束，初始相对速度垂直于相应连线，双精度残差不超过 `1e-12 m`、`1e-12 m/s`。约束与质量加权系统非奇异；对活动体平移自由度建立的单位方向约束雅可比 J 满足 `cond_2(J M^-1 J^T) <= 100`。无约束时不适用该条件数。不会依靠相容性容差注入可观测的任意冲量。

输出是输入瞬时状态的物理线加速度和双边约束力。约束可以受拉或受压，不是单边绳索。反力定义为**该约束施加在 second 端点物体上的力**，在全局坐标系中表示；即使 second 是固定体，也输出它受的力。first 端点受力为其反向。各约束按 link_ids 排序，不能只给模长、合力或求解器局部坐标分量。固定体线加速度输出零。

### action = 1：位置装配回归

此模式只有一个固定体、一个活动体及它们之间的一条约束。重力、外力、输入速度均为零。活动体的输入质心位置与固定点距离为目标长度的 0.8–1.2 倍，连线非零。要求保持固定点不变、保持固定点到活动体的原始方向，将两者距离装配到指定长度。输出装配后的全部质心位置。此回归不要求加速度或反力。

### action = 2：速度装配回归

位置相容，速度可不相容，重力及外力为零，固定体速度为零。要求位置不变，将活动体速度作满足全部法向相对速度为零的最小质量加权改动；即在可行速度中最小化 `sum_i m_i*||v_i-v_i_input||^2`。质量和约束独立性保证投影唯一。输出装配后的全部速度。此回归不要求加速度或反力。

## 输出

由可信驱动写入一个 HDF5。必须复制 `body_ids`、`times`；有链接观测时还复制 `link_ids`。dtype、值和顺序与输入一致。`outputs` 中的字段元数据沿用输入场格式，但输出字段不包含 `sampling`；按 action 只声明下列必需字段：

| action | 对象名 / array | quantity | location | dtype | kind / component_shape | unit | shape |
|---|---|---|---|---|---|---|---|
| 4 | acceleration | acceleration | bodies | float64 | vector / [3] | m/s^2 | [1,N,3] |
| 4 且 M>0 | reaction | reaction_force | links | float64 | vector / [3] | N | [1,M,3] |
| 1 | position | position | bodies | float64 | vector / [3] | m | [1,N,3] |
| 2 | velocity | velocity | bodies | float64 | vector / [3] | m/s | [1,N,3] |

所有输出字段 `components: ["x","y","z"]`，`time_axis: "state"`，`value_kind: "point"`。数值必须有限。未声明的场不写入结果。DATA 定义数据和观测；提交文件、编译、资源及评分要求以 instruction.md 为准。
