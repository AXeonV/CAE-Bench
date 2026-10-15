# 2.3.2 数据声明

继承[公共数据说明](../DATA.md)和[配置规范](../../../../docs/FLUID-ENERGY.md)的全部定义。

| 项 | 本题要求 |
|---|---|
| task | `rans-steady-3d` |
| physics.model | `fluid-energy-incompressible-rans-steady-v1` |
| spatial_dimension | `3` |
| 材料 | 恒密度牛顿流体，等温，不求能量。 |
| 分析及方法 | `steady` / `rans` |
| 参数 | 规范参数表中本模型适用项的精确集合，无未声明缺省 |
| 初态 | 无物理初态，禁止time_start/time_end |
| 压力 | 表压p-p0，reference_pressure给绝对p0，全域体积平均表压为0 |
| 边界 | 全部外面不可穿透；moving_wall且速度纯切向；无热条件 |
| 输出 | `velocity`, `pressure`；全部全域体积平均float64 |
| 输出时间 | [0]，稳态存储标记 |

条件参数键、场quantity、单位、采样规则和统计平均次序均以配置规范为准。对象名、tag和数组key不由task推断。本题为三维，速度及其他空间矢量包含x/y/z全部分量，空间二阶张量为完整3×3矩阵。
