# 2.2.1 数据声明

继承[公共数据说明](../DATA.md)和[配置规范](../../../../docs/FLUID-ENERGY.md)的全部定义。

| 项 | 本题要求 |
|---|---|
| task | `newtonian-lowmach-steady-2d` |
| physics.model | `fluid-energy-lowmach-laminar-steady-v1` |
| spatial_dimension | `2` |
| 材料 | 热膨胀牛顿液体，Boussinesq密度反馈；黏度和导热率按温度幂律变化。 |
| 分析及方法 | `steady` / `laminar` |
| 参数 | 规范参数表中本模型适用项的精确集合，无未声明缺省 |
| 初态 | 无物理初态，禁止time_start/time_end |
| 压力 | 表压p-p0，reference_pressure给绝对p0，全域体积平均表压为0 |
| 边界 | 全部外面不可穿透；moving_wall且速度纯切向；每外面恰有temperature或outward_heat_flux热条件，稳态至少一片温度锚 |
| 输出 | `velocity`, `pressure`, `temperature`；全部全域体积平均float64 |
| 输出时间 | [0]，稳态存储标记 |

条件参数键、场quantity、单位、采样规则和统计平均次序均以配置规范为准。对象名、tag和数组key不由task推断。二维输出只含x/y空间分量，无出平面自由度。
