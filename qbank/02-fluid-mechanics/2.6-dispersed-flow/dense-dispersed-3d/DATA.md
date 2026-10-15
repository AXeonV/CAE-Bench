# 2.6.4 数据契约

继承 [本节公共数据说明](../DATA.md) 与 [多相配置](../../../../docs/FLUID-MULTIPHASE.md)。完整模型标识为 `fluid-multiphase-dense-dispersed-v1`；spatial_dimension必须为3，不可用task代替model。输入使用固定Euler网格，不要求也不接受隐含移动粒子坐标。

## 参数与条件

physics.parameters必须恰含下表各项，每项为带单位有限标量；严格正值/非负值及跨字段限制按协议参数表，不允许额外的求解器控制参数或未声明物理参数：

| name | unit |
|---|---|
| time_start | s |
| time_end | s |
| density_a | kg/m3 |
| viscosity_a | Pa.s |
| pressure_reference | Pa |
| density_b | kg/m3 |
| relaxation_time | s |
| diameter | m |
| packing_fraction | 1 |
| particle_modulus | Pa |

全域初态变量恰为：**alpha, flux_a, flux_b**；每个变量一个initial/assign条件，data恰为value。初态空间含义、相标识和相容性按模型定义。另必须有一个全域source/acceleration/assign条件，即使加速度为零亦显式提供向量场。

本题仅支持wall；所有外面为静止固壁，压力全域体积平均固定为pressure_reference。

所有条件data键、数值类型、场单位、温度和含率范围、外面覆盖及不相容组合均由公共协议“条件清单与组合”规定。未列算子、未知参数、缺初态、重叠边界、错误维度/单位/shape均拒绝；不以网格组名称猜边界物理。

## 输出

必需quantity恰为：**alpha, flux_a, flux_b, pressure**。逐项一份，全域体单元、float64、average，同一请求轴，末时刻time_end；单位和分量轴按公共协议。场对象名与HDF5 dataset键可不同，按声明引用，不按行号或名字猜测。

相体积、常相密度下相质量及已请求的总相变率可由单元平均场线性积分复算。分散模型的总动量可由rho_a*flux_a+rho_b*flux_b线性积分；共速变密度动量、溶质量和热量/焓含乘积相关项，不能由各因子单元均值精确恢复，只可作带重建误差的近似，不能据此严格守恒判分。二维结果按单位出平面厚度；压力不在判分时重新定零。允许输出的精确物理含义和本题相变率符号（若适用）按model规范，不能替换为内部平滑/颗粒专有量。

pressure和派生phase_change_rate在time_start若被请求，必须是制作方已证明有限且唯一的连续问题右迹；未建立该证据时输出公共轴必须严格晚于time_start开始。检查器不靠求解验证该制作方保证。

## 数据状态

examples、references、cases尚无数据。当前交付是可审查的题面和协议，正式算例、参考、数值/物理适用性和资源校准留待后续。没有可运行样例不表示可以自选缺失物理；公开协议已经定义本题输入支持集合。
