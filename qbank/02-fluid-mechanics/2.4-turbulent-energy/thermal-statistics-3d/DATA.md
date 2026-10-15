# 2.4.3 数据声明

继承[公共数据说明](../DATA.md)和[配置规范](../../../../docs/FLUID-ENERGY.md)的全部定义。

| 项 | 本题要求 |
|---|---|
| task | `thermal-statistics-3d` |
| physics.model | `fluid-energy-lowmach-resolved-statistics-v1` |
| spatial_dimension | `3` |
| 材料 | 热膨胀牛顿液体，Boussinesq密度反馈；黏度和导热率按温度幂律变化。 |
| 分析及方法 | `statistics` / `resolved` |
| 参数 | 规范参数表中本模型适用项的精确集合，无未声明缺省 |
| 初态 | velocity, temperature；每变量一条全域initial/assign |
| 压力 | 表压p-p0，reference_pressure给绝对p0，全域体积平均表压为0 |
| 边界 | 全部外面不可穿透；moving_wall且速度纯切向；每外面恰有temperature或outward_heat_flux热条件，稳态至少一片温度锚 |
| 输出 | `velocity`, `pressure`, `temperature`, `velocity_covariance`, `temperature_variance`, `turbulent_heat_flux`；全部全域体积平均float64 |
| 输出时间 | [statistics_end]，按给定区间离散统计 |

条件参数键、场quantity、单位、采样规则和统计平均次序均以配置规范为准。对象名、tag和数组key不由task推断。本题为三维，速度及其他空间矢量包含x/y/z全部分量，空间二阶张量为完整3×3矩阵。
