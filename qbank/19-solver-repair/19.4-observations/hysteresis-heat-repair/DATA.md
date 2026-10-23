# 数据定义

采用包内 CONTRACT.md。每例输入为problem.json和input.h5，输出为result.h5。全部状态相互独立，时刻轴`times=[0.0]`；除实体ID外，输入输出数组均为有限float64。不存在外部附件或连续场插值。

## 元数据和形状

`task=hysteresis-heat-repair`，`spatial_dimension=1`，`physics.model=ocp-hysteresis-heat-v1`，geometries、meshes为空对象，conditions为空数组。locations恰为`{"states":{"kind":"entities","ids":"state_ids"}}`，state_ids为1至16个非负、严格递增int64，时间轴声明`{"instant":"times"}`。

physics.parameters恰有phases_n、phases_p、mask_n、mask_p、pairs，单位均为1。两phases取整数1或2，表示负/正极相数P；mask为0至2^P−1整数，第k位为1表示第k相采用current sigmoid滞回选项，为0表示single选项；pairs为整数1至32的并联电极对数。mask和相数在该case所有状态中固定，不作为考生的算法选择。

字段形状均为[1,N,C]，N为状态数；`array`与字段同名，`location=states`、`time_axis=instant`、`dtype=float64`、`value_kind=point`、`component_shape=[C]`。C=1时kind=scalar且components=["value"]；C=2时kind=components，分量严格依次["primary","secondary"]。单相时唯一分量代表primary相。输入另有`sampling={"space":"uniform","time":"constant","extrapolation":"forbid"}`，输出没有sampling。

## 输入

后缀n/p分别为负/正极，C=P为对应相数。以下相字段均有两极版本，每行均必需，不提供缺省值。

| 字段 | quantity | unit | C | 范围与含义 |
|---|---|---|---|---|
| current_n、current_p | volumetric_current_density | A.m-3 | P | J绝对值≤1e7；正负按上游电极局部界面电流约定，直接用于公开热公式，不再按充放电翻号 |
| eta_n、eta_p | voltage | V | P | 反应过电势绝对值≤1 |
| ocp_n、ocp_p | voltage | V | P | 工作U∈[−2,6] |
| equilibrium_n、equilibrium_p | voltage | V | P | 明确平衡U_eq∈[−2,6]；single相U_eq=U，差≤1e-12 |
| entropy_n、entropy_p | voltage_temperature_derivative | V.K-1 | P | dU/dT绝对值≤0.003 |
| temperature | temperature | K | 1 | T∈[250,400]，所有层与相共用 |
| length_n、length_p | length | m | 1 | 两电极厚度，各∈[1e-6,1e-2] |
| length_s | length | m | 1 | 隔膜厚度，范围相同 |
| length_cn、length_cp | length | m | 1 | 两集流体厚度，范围相同 |
| area | area | m2 | 1 | 电极面积A∈[1e-4,10] |
| volume | volume | m3 | 1 | 实际电池热体积V_cell∈[1e-10,1] |

局部界面状态不要求与固定零输运电流场共同满足完整DFN；这是热子模型的已定义瞬时输入。没有用输入相数隐含活性材料体积分数加权：J已是按电极体积计的各相界面电流，必须对各相直接求和。

## 输出

输出均C=1，components=["value"]，数组[1,N,1]，不包含sampling。

| 字段 | quantity | unit | 定义 |
|---|---|---|---|
| heat_negative | volumetric_heat_power | W.m-3 | 负极Σ_phase J[η+T dU/dT+(U−U_eq)]，single相最后项为0 |
| heat_positive | volumetric_heat_power | W.m-3 | 正极同一定义 |
| area_heat | area_heat_power | W.m-2 | L_n heat_negative+L_p heat_positive；每个电极对单位面积 |
| cell_heat | heat_power | W | pairs×area×area_heat |
| volume_heat | volumetric_heat_power | W.m-3 | cell_heat/volume |

可信运行器写出result.h5。考生只交库内替换源码，不负责另写SDK输出程序。各输出独立评分，不允许只匹配两极相互抵消的总功率。
