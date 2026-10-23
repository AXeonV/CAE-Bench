# 输入与输出

每个 `problem.json` 和相邻 `input.h5` 描述一个三维瞬时颗粒状态。`task=granular-pair-stress-repair`，`physics.model=instantaneous-granular-contact-v1`。`geometries`、`meshes` 均为空对象，`conditions=[]`。数值均为有限实数；HDF5 名称与下述字段名称相同。

`locations.particles={"kind":"entities","ids":"particle_ids"}`，其中 `particle_ids` 是长度 N 的严格递增 int64 ID，2≤N≤32，ID 在 1..1000000。`locations.system={"kind":"entities","ids":"system_ids"}`，`system_ids` 为 int64 `[0]`。`time_axes.instant="times"`，float64 `times=[0]`。时间索引是初始观察，不推进物理时间。输出必须保持输入粒子 ID 对应关系，不能按数值位置替换 ID。

所有输入场使用 float64、`location=particles`、`time_axis=instant`、`value_kind=point`，采样声明 `{"space":"uniform","time":"constant","extrapolation":"forbid"}`。以下为全部输入字段；数组形状为 `[1,N,C]`，`component_shape=[C]`，C=1 时 `kind=scalar`，否则 `kind=components`。

|字段|quantity|unit|components|取值|
|---|---|---|---|---|
|position|position|m|x,y,z|球及额外0.1m余量严格位于箱内|
|diameter|diameter|m|value|0.1..1.5|
|material_density|mass_density|kg/m^3|value|100..10000|
|velocity|velocity|m/s|x,y,z|每分量-0.1..0.1|
|angular_velocity|angular_velocity|rad/s|x,y,z|每分量-0.2..0.2|

`physics.parameters` 恰含以下键；每个值均为通用常量对象 `{"value":数值,"unit":"单位"}`，不在 HDF5 中重复存储。单位依次为 m、N/m、N/m、1/s、1/s、1、1。

|键|定义|范围|
|---|---|---|
|box_length|立方箱边长L，m|3..20|
|normal_stiffness|法向弹簧系数kn，N/m|100..1e6|
|tangential_stiffness|切向弹簧系数kt，N/m|10..1e6|
|normal_damping|法向阻尼gamma_n，1/s|0..10|
|tangential_damping|切向阻尼gamma_t，1/s|0..10|
|friction|Coulomb系数mu|0.1..1|
|tally_mode|请求的统计量|数值0=global，1=particle，2=both|

箱为各轴 `[-L/2,L/2]`，非周期固定边界，无墙相互作用。固定 `newton pair off`。各对中心距离至少0.05m。半径R为直径一半，质量为材料密度乘球体积。中心距离 r≥Ri+Rj 时无接触。对接触对，令 n=(xi-xj)/r，dv=vi-vj，vn=dv·n，m_eff=mi*mj/(mi+mj)，法向力 Fn=kn*(Ri+Rj-r)-m_eff*gamma_n*vn。接触面切向相对速度为 vt=dv-vn*n-(Ri*omega_i+Rj*omega_j)×n。零历史时切向作用为 Ft=-m_eff*gamma_t*vt。全部输入满足 Fn>0 且 |Ft|≤0.8*mu*Fn，故不进入摩擦截断分支；没有初始切向弹簧变形。kn、kt 对应 `gran/hooke/history` 参数，不使用 Hertz 半径缩放。力作用在i上为 Fn*n+Ft，在j上反向；接触力矩符号遵循这些力在两球接触点的力臂。

输出文件使用通用结果协议；考生只提交源码，由可信运行器调用 SDK `write_result`。输出都为 float64、`time_axis=instant`、`value_kind=point`，形状和kind规则同输入。全部模式必须输出 `force` 与 `torque`；global模式再输出pressure_tensor，particle模式再输出particle_virial，both模式同时输出两者，不声明额外量。

|字段|quantity|unit|location|components|
|---|---|---|---|---|
|force|force|N|particles|x,y,z|
|torque|torque|N*m|particles|x,y,z|
|particle_virial|pair_virial|N*m|particles|xx,yy,zz,xy,xz,yz|
|pressure_tensor|configurational_pressure|Pa|system|xx,yy,zz,xy,xz,yz|

成对维里矩阵为 W_ij=(xi-xj)外积F_ij，其中F_ij是i所受j的接触力。逐粒子维里量为每个接触对各分一半的 W；它是 LAMMPS `compute stress/atom NULL pair` 的相反数，不除以任何粒子体积。全局压力为 sum_pairs(W_ij)/L³，是 `compute pressure NULL pair`，压缩为正且不含动能项。切向力可能使完整矩阵不对称；本题只取规定的六个矩阵分量，不对非对角分量作对称平均。力和力矩同样不含其它外力。

`samples/01` 与 `samples/02` 各含可运行输入、参考与结果示例。其输入不是对正式参数的限制，合法域以上述约束为准。
