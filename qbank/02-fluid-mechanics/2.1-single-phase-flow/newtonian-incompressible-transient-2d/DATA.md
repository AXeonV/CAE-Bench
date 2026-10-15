# 2.1.2 数据声明

本题使用 [公共数据说明](../DATA.md) 的全部约定，采用[通用协议](../../../../docs/CONTRACT.md)。以下条件进一步限定本题；参数的单位、响应公式、条件键及输出解释均见公共数据说明。

| 项 | 本题要求 |
|---|---|
| task | `newtonian-incompressible-transient-2d` |
| contract_version / profile | `2` / `cfd-2.1` |
| spatial_dimension | `2` |
| analysis.type | `transient` |
| analysis.compressibility | `incompressible` |
| analysis.flow_regime | `laminar` |
| materials 中唯一材料的 density.kind | `constant` |
| materials 中唯一材料的 viscosity.kind | `newtonian` |
| 黏性参数 | 严格采用所选 kind 的参数集合，不含 bulk_viscosity |
| 初态 | 完整域的初始速度，恰在 time_interval.start 一帧 |
| 压力规范 | 有压力出口或牵引时禁止；否则必须给域平均或单点规范 |
| 边界 | 公共数据说明中的全部边界 |
| 输出 | 至少速度、压力；可请求公共数据说明的其他适用观测，全部 float64 |
| 矢量 shape | `[T,N,2]`，分量 x、y |
| 标量 shape | `[T,N,1]` |
| 输出时刻 | 输入 time_interval 内的请求时刻 |

对象名、位置名、数组 key、实体 tag 和时间轴名不固定。通过声明读取，不从 task 标识推断未声明的材料参数或条件。
