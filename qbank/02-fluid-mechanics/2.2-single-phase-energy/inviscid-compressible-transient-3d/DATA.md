# 2.2.8 数据声明

继承[公共数据说明](../DATA.md)和[配置规范](../../../../docs/FLUID-ENERGY.md)的全部定义。

| 项 | 本题要求 |
|---|---|
| task | `inviscid-compressible-transient-3d` |
| physics.model | `fluid-energy-inviscid-laminar-transient-v1` |
| spatial_dimension | `3` |
| 材料 | 热完全理想气体，忽略黏性和导热。 |
| 分析及方法 | `transient` / `laminar` |
| 参数 | 规范参数表中本模型适用项的精确集合，无未声明缺省 |
| 初态 | velocity, temperature, density；每变量一条全域initial/assign |
| 压力 | 绝对静压；稳态给mean_density，瞬态由初密度确定库存 |
| 边界 | 全部外面不可穿透；slip_wall，严格绝热，不接受热条件 |
| 输出 | `velocity`, `pressure`, `temperature`, `density`；全部全域体积平均float64 |
| 输出时间 | 请求时刻均在[time_start,time_end]内 |

条件参数键、场quantity、单位、采样规则和统计平均次序均以配置规范为准。对象名、tag和数组key不由task推断。本题为三维，速度及其他空间矢量包含x/y/z全部分量，空间二阶张量为完整3×3矩阵。
