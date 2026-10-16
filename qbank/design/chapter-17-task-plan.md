# 第十七章有限逐题清单

所有题均一维连续体、均匀实系数；给定模型，方法与内部离散自由。表中标识冻结，参数和载荷是问题族变化轴，不按算例来源拆题。各题均输出至少两场共同观测；不要求隐藏算法或专有软件变量。

| 编号 | 稳定task标识 | 范围／责任／观测 | 不覆盖 |
|---|---|---|---|
| 17.1.1 | compliant-tube-wave | 瞬态线性液柱、薄壁环向弹性；求p、v、径向w | 管壁惯性、弯曲、湍流与自由界面 |
| 17.1.2 | acoustic-piston-feedback | 瞬态声学PDE与有限质量端活塞；求p、v、活塞位移 | 大位移、泄漏与碰撞 |
| 17.2.1 | constrained-thermal-expansion | 稳态导热驱动约束杆；求温升、位移、轴向应力 | 反向热源、塑性 |
| 17.2.2 | reciprocal-thermoelastic-wave | 瞬态线性热弹性双向耦合；求温升、位移 | 大温变与有限应变 |
| 17.3.1 | steady-joule-feedback | 稳态温敏电导、自洽Joule源；求电势、温升 | 热失控多解分支 |
| 17.3.2 | transient-joule-feedback | 瞬态热扩散、准静态电流；求电势、温升 | 电磁波、电容与熔化 |
| 17.4.1 | static-piezoelectric-rod | 静态应力电荷型压电；求位移、电势、D | 铁电畴、非线性极化 |
| 17.4.2 | shunted-piezoelectric-rod | 谐波惯性压电、电极并联G/C反馈；求位移、电势 | 任意外电路与开关 |
| 17.5.1 | magnetic-diffusion-elasticity | 厚度方向剪切／磁扩散、小信号压磁；求位移、H | 非线性磁滞、直流大变形 |
| 17.6.1 | biot-consolidation | 准静态骨架、瞬态压力储存；求位移、孔压 | 惯性、非饱和／多相 |
| 17.7.1 | thermo-poroelastic-transient | 准静态骨架、互易热孔压耦合；求位移、孔压、温升 | 对流、大温变与相变 |
| 17.7.2 | thermoelectric-leg | 稳态Seebeck/Peltier/Joule一维腿；求电势、绝对温度、总热流 | 接触热阻与温变Seebeck |

按17.1—17.3、17.4—17.7两批编写三文件契约和配置，再实现共享检查和验证。独立考生审阅只给最终题面、DATA、CONTRACT。正式数据、参考、模型适用性、精度与预算校准及发布均后补。
