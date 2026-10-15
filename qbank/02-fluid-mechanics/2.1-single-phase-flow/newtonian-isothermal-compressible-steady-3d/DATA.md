# 2.1.11 数据声明

本题使用 [公共数据说明](../DATA.md) 的全部约定，采用[通用协议](../../../../docs/CONTRACT.md)。以下条件进一步限定本题；参数的单位、响应公式、条件键及输出解释均见公共数据说明。

| 项 | 本题要求 |
|---|---|
| task | `newtonian-isothermal-compressible-steady-3d` |
| contract_version / profile | `2` / `cfd-2.1` |
| spatial_dimension | `3` |
| analysis.type | `steady` |
| analysis.compressibility | `isothermal_compressible` |
| analysis.flow_regime | `laminar` |
| materials 中唯一材料的 density.kind | `isothermal_ideal_gas` 或 `linear_barotropic` |
| materials 中唯一材料的 viscosity.kind | `newtonian` |
| 黏性参数 | dynamic_viscosity 和 bulk_viscosity 必有 |
| 初态 | 无 initial 条件；无 time_interval |
| 压力规范 | 禁止 pressure_gauge，绝对水平由物理状态决定 |
| 边界 | 公共数据说明中除 traction 外的全部边界；入口同时给密度 |
| 输出 | 至少速度、压力；可请求公共数据说明的其他适用观测，全部 float64 |
| 矢量 shape | `[T,N,3]`，分量 x、y、z |
| 标量 shape | `[T,N,1]` |
| 输出时刻 | 仅存储标记 [0.0]，不代表瞬态初态 |

对象名、位置名、数组 key、实体 tag 和时间轴名不固定。通过声明读取，不从 task 标识推断未声明的材料参数或条件。
