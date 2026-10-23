# 输入与输出

每个输入是静止介质内一个稳态二维矩形条带。坐标单位 m，长方向为全局 +y，宽方向为 +x；令底边 y=y0、顶边 y=y0+L。所有系数在整个条带上恒定，所有边界值沿相应边恒定。无体源、无流动、无瞬态项。温度 T 和电势 φ 分别由单位热导率与单位电导率的稳态 Laplace 方程求解；热容固定为 1，不影响稳态解。左右两侧对三个场均为齐次自然边界。

## 物理与离散

浓度模式 0（Relative Mass）中的未知量为质量分数 Y，单位 1；模式 1（Absolute Mass）为质量浓度 c=ρY，单位 kg/m³。以下统一以 u 表示该模式的未知量，令 χ=ρ（模式 0）或 χ=1（模式 1）。密度 ρ 为 kg/m³，扩散系数 D 为 m²/s。热扩散系数 DT 在模式 0 为 m²/(s·K)，模式 1 为 kg/(m·s·K)，描述同一物理问题时 DTabs=ρDTrel。质量分数允许为零并始终在 [0,1]，质量浓度相应在 [0,ρ]。

电迁移模式：温度恒定、DT=0、底顶浓度均为 Dirichlet。通量为 J=−χD[∇u+(ze/(kB T))u∇φ]，求 ∇·J=0。z 是有符号整数电荷数，e=1.602176634e−19 C，kB=1.380649e−23 J/K。此题不包含非等温电迁移。

Soret 模式：z=0、电势恒定，底边浓度 Dirichlet，顶边为零总扩散与热扩散通量。通量为 J=−χ(D∇u+DT∇T)，求 ∇·J=0。顶边条件是 n·J=0，包含热扩散，不能替换为零浓度梯度。DT 可正、负或零，正 DT 在升温方向产生降低的平衡浓度。有限元方程采用 ∫χD∇v·∇u=−∫χDT∇v·∇T（加边界项），热扩散项的符号据此确定。

使用给定完整网格的双线性 QUAD4、标准 Galerkin 离散；关闭 bubbles 和 stabilization，直接 UMFPACK 求解。驱动先计算温度、电势，再计算浓度，每个场保存全部节点最终稳态值。无网格细化或重建。原生模块的温度与电势场绑定分别为 `Temperature Field Variable="ThermalField"` 和 `Conc EPotential Field Variable="ElectricField"`；浓度变量名为 `Conc`。绝对质量模式的 `Concentration Units="Absolute Mass"` 位于 Equation；相对质量使用默认值。材料收到原样 ρ、D、DT、z；DT 或 z 为零时对应可选材料关键词省略。

## 声明、网格与条件

`task="migration-soret-scaling-repair"`，`spatial_dimension=2`，`physics.model="steady-migration-soret-strip-v1"`。`geometries` 与 `fields` 为空对象。`meshes={"main":{"file":"mesh.msh"}}`。网格为 Gmsh 4.1 ASCII；二维物理组 (2,1) 包含所有体单元，边界物理组 (1,1)、(1,2)、(1,3)、(1,4) 分别为 bottom、right、top、left。体为逆时针 QUAD4，边界为 LINE2，允许无物理组的零维点元素。节点与元素标签可以不连续。

矩形是完整均匀笛卡尔网格，宽向 nx=1..3，长向 ny=100..400；L=1e−4..0.05 m，W/L=0.05..0.2，坐标各分量绝对值不超过 1 m。每个格点恰有一个节点，每个网格胞恰有一个单元，四个边界组恰好覆盖外边界，每条外边恰有一个父单元。

`physics.parameters` 恰含下表六个常量，均采用 `{"value":数值,"unit":单位}`，不使用数组或 option 对象。

|名称|单位|范围与含义|
|---|---|---|
|mode|1|0 电迁移，1 Soret|
|concentration_units|1|0 Relative Mass，1 Absolute Mass|
|density|kg/m3|0.2..5000，严格正|
|diffusivity|m2/s|1e−12..1e−7|
|soret_diffusivity|m2/(s.K) 或 kg/(m.s.K)|按浓度模式，DT 绝对值除以 D·(ρ 若绝对模式，否则 1) 不超过 0.01 K⁻¹|
|ion_charge|1|−3..3 的整数|

底顶温度均为 250..700 K，温差绝对值≤200 K；电势绝对值≤1 V，电势差绝对值≤0.1 V。电迁移还要求 |ze(φtop−φbottom)/(kB T)|≤3。Soret 的底边浓度及零通量所对应整个平衡剖面必须处于物理浓度范围（端点检查允许 1e−12 倍浓度单位尺度的浮点舍入）。

`conditions` 恰有六条 boundary 声明：变量 `temperature`、`potential`、`concentration` 各在 `bottom`、`top` 一条。除 Soret 顶边浓度外，operator 均为 `dirichlet`，`data={"value":{"value":数值,"unit":单位}}`，单位分别为 K、V 和当前浓度单位。Soret 顶边浓度 operator 为 `zero_total_diffusive_thermal_flux`，同样的 data 结构，value=0，unit=`kg/(m2.s)`。无其他条件。

HDF5 输入仅保存 int64 一维数组 `node_ids`、`bottom_ids`、`right_ids`、`top_ids`、`left_ids`，以及 float64 一维 `times=[0]`。node_ids 为所有网格节点的唯一正整数标签；四个边界 ids 为各自边界组全部元素标签。位置 `nodes={"kind":"mesh","mesh":"main","entity":"node","ids":"node_ids"}`；边界位置为 `{"kind":"mesh","mesh":"main","entity":"element","dimension":1,"ids":"对应边界_ids","physical_group":{"dimension":1,"tag":对应标签}}`。`time_axes={"instant":"times"}`，零时刻只是稳态存储索引。

## 输出

输出 HDF5 的本题结果 field 恰为下列三个 float64 数组，形状均为 `(1,N,1)`，N 为 node_ids 长度，严格按 node_ids 顺序。此外必须按 CONTRACT 保存节点位置身份数据 `node_ids` 和时间轴 `times`；这里的“三个”不限制这些通用必需数据。每项结果声明 `array` 等于名称，`location="nodes"`、`time_axis="instant"`、`dtype="float64"`、`kind="scalar"`、`component_shape=[1]`、`components=["value"]`、`value_kind="point"`。

|名称|quantity|unit|
|---|---|---|
|concentration|mass_fraction（模式 0）或 mass_concentration（模式 1）|1 或 kg/m3|
|temperature|temperature|K|
|potential|electric_potential|V|

所有输出必须有限，不能只给边界、平均量或归一化后的浓度。有限元节点解与连续场剖面的区别不会通过输出适配器补偿。
