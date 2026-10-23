# 输入与输出

本题采用 CONTRACT 的 JSON/HDF5 规则。清单固定 `task: "diffusion-element-heat-repair"`、`spatial_dimension: 1`，`geometries: {}`、`meshes: {}`、`conditions: []`。`data_file` 是相对输入 HDF5 路径；所有数值有限。每个 case 包含若干相互独立的瞬时状态，不表示状态演化序列。

## 模型、位置与时间

`physics.model` 固定为 `ecm-diffusion-heat-v1`。`physics.parameters` 恰含 `grid_count` 和 `rc_count`，均为 `{ "value": 整数, "unit": "1" }`。网格数 K 为4至64，RC元件数 R 为0至3；另有一个串联元件，所以其他元件总数 E=R+1。K、R 在一个 case 内相同。

`locations` 恰含 `states: { "kind": "entities", "ids": "state_ids" }`。`state_ids` 为严格递增、非负且唯一的 `int64[N]`，1≤N≤32，不要求连续。`time_axes` 固定为 `{ "instant": "times" }`，`times` 为 `float64[1]`，唯一值0；N个状态均由 IDs 区分，不沿时间轴排列。

## 输入场

所有输入场使用对象名与 HDF5 key 相同，引用 `location: "states"`、`time_axis: "instant"`、`value_kind: "point"`；采样声明为 `{ "space": "uniform", "time": "constant", "extrapolation": "forbid" }`，不对实体ID做空间插值。数组 shape 为 `[1,N,C]`，`component_shape: [C]`。C=1的 `kind` 为 `scalar`，`components: ["value"]`；其他场为 `kind: "components"`，分量见表。

| 对象名／array | quantity | dtype | C及components | unit | 含义 |
|---|---|---|---|---|---|
| current | current | float64 | 1 | A | 放电为正的端口电流，−100≤I≤100 |
| average_soc | state_of_charge | float64 | 1 | 1 | 平均SoC，记为s_average |
| diffusion_enabled | enabled | bool | 1 | 1 | true调用扩散元件，false调用关闭扩散元件 |
| soc_profile | state_of_charge | float64 | K，cell_0至cell_(K−1) | 1 | 在ξ_j=(j+1/2)/K处的SoC，j=0…K−1 |
| ocv_coefficients | voltage_coefficients | float64 | 4，[c0,c1,c2,c3] | V | U(s)=c0+c1s+c2s²+c3s³ |
| element_heat | irreversible_heat_power | float64 | E；E=1时[value]，否则element_0至element_R | W | 各其他元件不可逆热功率，不含扩散与可逆热 |
| reversible_heat | reversible_heat_power | float64 | 1 | W | 可逆热功率，可为负 |

每个状态的分布来自线性函数 s(ξ)=s_average+b(ξ−1/2)，b可正可负。输入值与该函数及平均值一致，绝对残差不超过 `1e-12`；两个端点SoC均在[0.05,0.95]，因此给定分布的精确表面值为s_average+b/2。可信驱动使用库内均匀一维有限体积边界求值；对上述线性分布，其表面端点值应与线性外推一致。关闭扩散时b=0，驱动忽略分布场并使用平均SoC的常值广播。

c0∈[2,5] V，c1∈[0.1,2] V，c2、c3∈[−0.2,0.2] V，并保证U′(s)≥0.05 V，对所有s∈[0,1]成立。每个element_heat值在[0,100] W，reversible_heat在[−50,50] W。不同状态可以有不同OCV系数、电流、分布、热源和扩散开关。

## 输出

以下四个输出均为 `float64[1,N,1]`，引用相同states和instant，`kind: "scalar"`、`component_shape: [1]`、`components: ["value"]`、`value_kind: "point"`，不声明输入场的sampling。对象名与输出根组HDF5 key相同，行序与state_ids完全相同。

| 对象名／array | quantity | unit | 定义 |
|---|---|---|---|
| surface_soc | state_of_charge | 1 | ξ=1的表面SoC；关闭扩散时等于平均SoC |
| diffusion_overpotential | voltage | V | η=U(s_surface)−U(s_average)；关闭扩散时为0 |
| irreversible_heat | irreversible_heat_power | W | Σ element_heat−current×η |
| total_heat | heat_power | W | irreversible_heat+reversible_heat |

U(s_average)不等于U(s)的空间平均，除非输入恰好使二者相同。输出均为瞬时量，不积分时间，不裁剪负热功率。所有输入字段均由本文件定义；输入的配方保证不意味着任意电流与分布必须处于准稳态。
