# 输入与输出

本题采用 包内 CONTRACT.md。每例由 `problem.json` 和 `input.h5` 组成，输出为 `result.h5`。所有数组名称与字段名称相同；输入没有外部附件。除ID外均为有限 float64。所有字段为单一时刻的独立状态，`times=[0.0]`，不进行时间插值。

## 声明与布局

`task=graded-electrode-inventory-repair`，`spatial_dimension=1`，`physics.model=graded-electrode-inventory-v1`。`geometries`、`meshes`为空对象，`conditions`为空数组。离散状态用实体和分量表达，不声明空间查询点。

`physics.parameters` 恰有 `x_count_n`、`x_count_p`、`r_count_n`、`r_count_p`，值均为整数3至32，单位为`1`。后缀n、p分别表示负极、正极，分辨率可不同。各电极 x_j 单元边界为j/X、径向r_i边界为i/R。端点值在本题不另行外推。

`locations.states={"kind":"entities","ids":"state_ids"}`；`state_ids`为1至16个非负且严格递增的int64，顺序决定状态顺序，不承诺连续。`time_axes.instant="times"`。各输入字段形状为 `[1,N,C]`，输出相同，其中N是状态数，C见下表。各字段均指定`location=states`、`time_axis=instant`、`dtype=float64`、`value_kind=point`、`component_shape=[C]`；C=1时`kind=scalar`且`components=["value"]`，其他为`kind=components`及表中分量名。

## 输入字段

| 名称 | quantity | unit | C及分量 | 范围与解释 |
|---|---|---|---|---|
| epsilon_n、epsilon_p | active_material_fraction | 1 | X；`x_0`至`x_(X-1)` | 每单元ε∈[0.1,0.9] |
| concentration_n、concentration_p | concentration | mol.m-3 | X×R；按j先、i后排列，`x_j_r_i` | c_ij∈[0,c_max]；球壳内分片常数 |
| thickness_n、thickness_p | length | m | 1 | L∈[1e-6,1e-2] |
| area | area | m2 | 1 | A∈[1e-4,10]，两个电极共用 |
| cmax_n、cmax_p | concentration | mol.m-3 | 1 | c_max∈[100,1e6] |

输入字段还指定 `sampling={"space":"uniform","time":"constant","extrapolation":"forbid"}`，该声明不授权从未给出的连续场插值。`concentration_*`分量的索引为j×R+i；两个电极各用自身X、R。

## 输出字段

| 名称 | quantity | unit | C及分量 | 定义 |
|---|---|---|---|---|
| radial_n、radial_p | concentration | mol.m-3 | X；`x_j` | Σ_i[(r_(i+1)³-r_i³)c_ij] |
| volume_n、volume_p | concentration | mol.m-3 | 1 | Σ_j Δx_j ε_j radial_j / Σ_j Δx_j ε_j |
| stoichiometry_n、stoichiometry_p | stoichiometry | 1 | 1 | volume/c_max |
| inventory_n、inventory_p | amount_of_substance | mol | 1 | A L Σ_j Δx_j ε_j radial_j |
| total_inventory | amount_of_substance | mol | 1 | inventory_n+inventory_p |

输出不包含`sampling`。权重中的Δx_j=1/X，球壳体积分数差立方之和为1；不能用径向单元算术平均替代球形平均，也不能在ε和浓度有相关性时交换乘积与厚度平均。评分覆盖全部输出与状态，不只核对两极抵消后的总和。
